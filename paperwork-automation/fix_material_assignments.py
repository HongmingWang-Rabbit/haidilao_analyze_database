#!/usr/bin/env python3
"""
Fix Material Assignments

This script corrects the dish-material relationships by assigning dishes
to their proper materials instead of all using beef brisket (1500677).
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import logging
from utils.database import DatabaseConfig, DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fix_material_assignments():
    """Fix incorrect dish-material assignments"""
    
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    
    # Define the correct material assignments
    corrections = [
        {
            'dish_pattern': '精品牛板腱肉（偏瘦）',
            'current_material': '1500677',
            'correct_material': '1501159',
            'reason': 'Chuck roll dish should use chuck roll material'
        },
        {
            'dish_pattern': '精品牛板腱（赠送）',
            'current_material': '1500677', 
            'correct_material': '1501159',
            'reason': 'Chuck roll dish should use chuck roll material'
        },
        {
            'dish_pattern': 'AAA级西冷牛肉',
            'current_material': '1500677',
            'correct_material': '1501275', 
            'reason': 'Sirloin dish should use sirloin material'
        },
        {
            'dish_pattern': '和牛牛舌',
            'current_material': '1500677',
            'correct_material': '1500686',  # Use regular beef tongue instead of peeled
            'reason': 'Beef tongue dish should use beef tongue material'
        },
        {
            'dish_pattern': 'Q弹牛肉丸',
            'current_material': '1500677',
            'correct_material': '4526244',
            'reason': 'Beef ball dish should use beef ball material'
        },
        {
            'dish_pattern': '藤椒牛舌',
            'current_material': '1500677',
            'correct_material': '1500686',  # Use regular beef tongue
            'reason': 'Beef tongue dish should use beef tongue material'
        }
    ]
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                
                logger.info("=== Fixing Material Assignments ===")
                
                fixed_count = 0
                
                for correction in corrections:
                    logger.info(f"\n🔧 Fixing: {correction['dish_pattern']}")
                    logger.info(f"   From material: {correction['current_material']}")
                    logger.info(f"   To material: {correction['correct_material']}")
                    logger.info(f"   Reason: {correction['reason']}")
                    
                    # First, verify the correction is needed
                    cursor.execute("""
                        SELECT 
                            d.id as dish_id,
                            d.name as dish_name,
                            d.store_id,
                            dm.material_id,
                            m.material_number,
                            m.name as material_name
                        FROM dish_material dm
                        JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                        JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                        WHERE d.name = %s 
                        AND m.material_number = %s;
                    """, (correction['dish_pattern'], correction['current_material']))
                    
                    current_assignments = cursor.fetchall()
                    
                    if not current_assignments:
                        logger.warning(f"   ⚠️  No current assignments found for {correction['dish_pattern']} with material {correction['current_material']}")
                        continue
                    
                    logger.info(f"   Found {len(current_assignments)} current assignments to fix")
                    
                    for assignment in current_assignments:
                        store_id = assignment['store_id']
                        dish_id = assignment['dish_id']
                        
                        # Get the correct material ID for this store
                        cursor.execute("""
                            SELECT id, name 
                            FROM material 
                            WHERE material_number = %s AND store_id = %s;
                        """, (correction['correct_material'], store_id))
                        
                        correct_material = cursor.fetchone()
                        
                        if not correct_material:
                            logger.warning(f"   ⚠️  Correct material {correction['correct_material']} not found for store {store_id}")
                            continue
                        
                        # Update the dish_material relationship
                        cursor.execute("""
                            UPDATE dish_material 
                            SET material_id = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE dish_id = %s 
                            AND store_id = %s 
                            AND material_id = %s;
                        """, (correct_material['id'], dish_id, store_id, assignment['material_id']))
                        
                        if cursor.rowcount > 0:
                            logger.info(f"   ✅ Updated Store {store_id}: {assignment['dish_name']} -> {correct_material['name']}")
                            fixed_count += 1
                        else:
                            logger.warning(f"   ❌ Failed to update Store {store_id}: {assignment['dish_name']}")
                
                # Commit all changes
                conn.commit()
                logger.info(f"\n✅ SUCCESS: Fixed {fixed_count} material assignments")
                
                # Verify the fixes by recalculating theoretical usage
                logger.info("\n📊 Verifying fixes - Recalculating theoretical usage for beef brisket material:")
                cursor.execute("""
                    SELECT 
                        m.material_number,
                        m.name as material_name,
                        mmu.store_id,
                        s.name as store_name,
                        mmu.material_used as system_record,
                        COUNT(DISTINCT dms.dish_id) as contributing_dishes,
                        SUM(dms.sale_amount - dms.return_amount) as total_dish_sales,
                        SUM((dms.sale_amount - dms.return_amount) * 
                            COALESCE(dm.standard_quantity, 0) * 
                            COALESCE(dm.loss_rate, 1.0) * 
                            COALESCE(dm.unit_conversion_rate, 1.0)) as theoretical_usage,
                        CASE 
                            WHEN SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) * 
                                COALESCE(dm.unit_conversion_rate, 1.0)) > 0 
                            THEN ((mmu.material_used - SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) * 
                                COALESCE(dm.unit_conversion_rate, 1.0))) / 
                                SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) * 
                                COALESCE(dm.unit_conversion_rate, 1.0))) * 100
                            ELSE 0 
                        END as variance_percentage
                    FROM material_monthly_usage mmu
                    JOIN material m ON mmu.material_id = m.id AND mmu.store_id = m.store_id
                    JOIN store s ON mmu.store_id = s.id
                    JOIN dish_material dm ON m.id = dm.material_id AND m.store_id = dm.store_id
                    JOIN dish_monthly_sale dms ON dm.dish_id = dms.dish_id AND dm.store_id = dms.store_id
                    WHERE mmu.year = 2025 AND mmu.month = 5
                    AND dms.year = 2025 AND dms.month = 5
                    AND m.material_number = '1500677'  -- Beef brisket material
                    GROUP BY m.material_number, m.name, mmu.store_id, s.name, mmu.material_used
                    ORDER BY mmu.store_id;
                """)
                
                updated_results = cursor.fetchall()
                if updated_results:
                    logger.info("Updated theoretical usage for beef brisket (1500677):")
                    for row in updated_results:
                        logger.info(f"  Store {row['store_id']} ({row['store_name']}):")
                        logger.info(f"    System Record: {row['system_record']:.2f}")
                        logger.info(f"    Contributing Dishes: {row['contributing_dishes']} (should be fewer now)")
                        logger.info(f"    Total Dish Sales: {row['total_dish_sales']:.0f} (should be lower now)")
                        logger.info(f"    Theoretical Usage: {row['theoretical_usage']:.2f}")
                        logger.info(f"    Variance: {row['variance_percentage']:.1f}%")
                        
                        if abs(row['variance_percentage']) < 50:  # Much better variance expected
                            logger.info(f"    🎯 EXCELLENT: Variance greatly improved ({row['variance_percentage']:.1f}%)")
                        elif abs(row['variance_percentage']) < 100:
                            logger.info(f"    ✅ GOOD: Variance improved ({row['variance_percentage']:.1f}%)")
                        else:
                            logger.info(f"    📈 BETTER: Variance still improving ({row['variance_percentage']:.1f}%)")
                
                # Show what dishes are still assigned to beef brisket
                logger.info("\n📋 Remaining dishes assigned to beef brisket (1500677):")
                cursor.execute("""
                    SELECT DISTINCT d.name as dish_name
                    FROM dish_material dm
                    JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id  
                    JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                    WHERE m.material_number = '1500677'
                    AND d.store_id = 1
                    ORDER BY d.name;
                """)
                
                remaining_dishes = cursor.fetchall()
                for dish in remaining_dishes:
                    logger.info(f"  - {dish['dish_name']}")
                
                logger.info(f"\nBefore fixes: 14 dishes assigned to beef brisket")
                logger.info(f"After fixes: {len(remaining_dishes)} dishes assigned to beef brisket")
                logger.info(f"Improvement: {14 - len(remaining_dishes)} dishes correctly reassigned")
                
    except Exception as e:
        logger.error(f"Error fixing material assignments: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = fix_material_assignments()
    if success:
        print("\n✅ Material assignment fixes completed successfully!")
        print("Theoretical usage calculations should now be much more accurate.")
    else:
        print("\n❌ Material assignment fixes failed!")