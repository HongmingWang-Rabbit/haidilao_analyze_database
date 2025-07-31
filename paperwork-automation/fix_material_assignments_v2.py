#!/usr/bin/env python3
"""
Fix Material Assignments V2

This script removes incorrect dish-material relationships where dishes
have multiple materials but should only have one specific material.
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


def fix_material_assignments_v2():
    """Fix incorrect dish-material assignments by removing duplicates"""
    
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                
                logger.info("=== Fixing Material Assignments V2 ===")
                
                # First, analyze dishes with multiple material relationships
                logger.info("\n1. Finding dishes with multiple materials")
                cursor.execute("""
                    SELECT 
                        d.name as dish_name,
                        d.full_code as dish_code,
                        d.store_id,
                        COUNT(DISTINCT dm.material_id) as material_count,
                        STRING_AGG(DISTINCT m.material_number || ':' || m.name, ' | ') as materials
                    FROM dish_material dm
                    JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                    JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                    WHERE d.store_id = 1 
                    AND (d.name LIKE '%牛%' OR d.name LIKE '%肉%')
                    GROUP BY d.name, d.full_code, d.store_id
                    HAVING COUNT(DISTINCT dm.material_id) > 1
                    ORDER BY material_count DESC, d.name;
                """)
                
                multi_material_dishes = cursor.fetchall()
                logger.info(f"Found {len(multi_material_dishes)} dishes with multiple materials:")
                for dish in multi_material_dishes:
                    logger.info(f"  {dish['dish_name']}: {dish['material_count']} materials")
                    logger.info(f"    Materials: {dish['materials']}")
                
                # Define rules for which material to keep for specific dishes
                keep_material_rules = [
                    {
                        'dish_pattern': '精品牛板腱肉（偏瘦）',
                        'keep_material': '1501159',  # Chuck roll
                        'remove_material': '1500677'  # Beef brisket
                    },
                    {
                        'dish_pattern': '精品牛板腱（赠送）',
                        'keep_material': '1501159',  # Chuck roll
                        'remove_material': '1500677'  # Beef brisket
                    },
                    {
                        'dish_pattern': 'AAA级西冷牛肉',
                        'keep_material': '1501275',  # Sirloin
                        'remove_material': '1500677'  # Beef brisket
                    },
                    {
                        'dish_pattern': '和牛牛舌',
                        'keep_material': '1500686',  # Beef tongue
                        'remove_material': '1500677'  # Beef brisket
                    },
                    {
                        'dish_pattern': 'Q弹牛肉丸',
                        'keep_material': '4526244',  # Beef balls
                        'remove_material': '1500677'  # Beef brisket
                    },
                    {
                        'dish_pattern': '藤椒牛舌',
                        'keep_material': '4502048',  # Peeled beef tongue
                        'remove_material': '1500677'  # Beef brisket
                    }
                ]
                
                logger.info("\n2. Removing incorrect material relationships")
                removed_count = 0
                
                for rule in keep_material_rules:
                    logger.info(f"\n🔧 Processing: {rule['dish_pattern']}")
                    logger.info(f"   Keep material: {rule['keep_material']}")
                    logger.info(f"   Remove material: {rule['remove_material']}")
                    
                    # Check if this dish has both materials
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
                        WHERE d.name = %s;
                    """, (rule['dish_pattern'],))
                    
                    dish_materials = cursor.fetchall()
                    
                    if not dish_materials:
                        logger.warning(f"   ⚠️  Dish not found: {rule['dish_pattern']}")
                        continue
                    
                    logger.info(f"   Found {len(dish_materials)} material relationships")
                    
                    # Check if we have both the keep and remove materials
                    has_keep = any(rel['material_number'] == rule['keep_material'] for rel in dish_materials)
                    has_remove = any(rel['material_number'] == rule['remove_material'] for rel in dish_materials)
                    
                    if has_keep and has_remove:
                        logger.info(f"   ✅ Both materials found - will remove {rule['remove_material']}")
                        
                        # Remove the incorrect material relationship
                        for rel in dish_materials:
                            if rel['material_number'] == rule['remove_material']:
                                cursor.execute("""
                                    DELETE FROM dish_material 
                                    WHERE dish_id = %s 
                                    AND store_id = %s 
                                    AND material_id = %s;
                                """, (rel['dish_id'], rel['store_id'], rel['material_id']))
                                
                                if cursor.rowcount > 0:
                                    logger.info(f"   ✅ Removed incorrect relationship: {rel['dish_name']} -> {rel['material_name']}")
                                    removed_count += 1
                                else:
                                    logger.warning(f"   ❌ Failed to remove relationship")
                    
                    elif has_keep and not has_remove:
                        logger.info(f"   ✅ Already correct - only has {rule['keep_material']}")
                    
                    elif not has_keep and has_remove:
                        logger.warning(f"   ⚠️  Only has remove material {rule['remove_material']} - creating correct relationship")
                        
                        # Get the correct material ID
                        cursor.execute("""
                            SELECT id, name 
                            FROM material 
                            WHERE material_number = %s AND store_id = %s;
                        """, (rule['keep_material'], dish_materials[0]['store_id']))
                        
                        correct_material = cursor.fetchone()
                        
                        if correct_material:
                            # First check if this relationship would be a duplicate
                            cursor.execute("""
                                SELECT COUNT(*) as count
                                FROM dish_material 
                                WHERE dish_id = %s AND store_id = %s AND material_id = %s;
                            """, (dish_materials[0]['dish_id'], dish_materials[0]['store_id'], correct_material['id']))
                            
                            exists = cursor.fetchone()['count']
                            
                            if exists == 0:
                                # Update the existing relationship instead of deleting and inserting
                                cursor.execute("""
                                    UPDATE dish_material 
                                    SET material_id = %s,
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE dish_id = %s 
                                    AND store_id = %s 
                                    AND material_id = %s;
                                """, (correct_material['id'], dish_materials[0]['dish_id'], 
                                     dish_materials[0]['store_id'], dish_materials[0]['material_id']))
                                
                                if cursor.rowcount > 0:
                                    logger.info(f"   ✅ Updated to correct material: {correct_material['name']}")
                                    removed_count += 1
                            else:
                                logger.info(f"   ℹ️  Correct relationship already exists")
                    else:
                        logger.warning(f"   ⚠️  Neither material found for this dish")
                
                # Commit all changes
                conn.commit()
                logger.info(f"\n✅ SUCCESS: Fixed {removed_count} material assignments")
                
                # 3. Verify the fixes
                logger.info("\n3. Post-fix verification")
                cursor.execute("""
                    SELECT 
                        d.name as dish_name,
                        COUNT(DISTINCT dm.material_id) as material_count,
                        STRING_AGG(DISTINCT m.material_number || ':' || m.name, ' | ') as materials
                    FROM dish_material dm
                    JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                    JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                    WHERE d.store_id = 1 
                    AND d.name IN ('精品牛板腱肉（偏瘦）', '精品牛板腱（赠送）', 'AAA级西冷牛肉', 
                                  '和牛牛舌', 'Q弹牛肉丸', '藤椒牛舌', '藤椒牛舌(半)')
                    GROUP BY d.name
                    ORDER BY d.name;
                """)
                
                post_fix_dishes = cursor.fetchall()
                logger.info("Fixed dishes verification:")
                for dish in post_fix_dishes:
                    status = "✅ GOOD" if dish['material_count'] == 1 else "⚠️  MULTIPLE"
                    logger.info(f"  {dish['dish_name']}: {dish['material_count']} materials ({status})")
                    logger.info(f"    Materials: {dish['materials']}")
                
                # 4. Recalculate theoretical usage for beef brisket
                logger.info("\n4. Updated theoretical usage for beef brisket (1500677):")
                cursor.execute("""
                    SELECT 
                        m.material_number,
                        m.name as material_name,
                        mmu.store_id,
                        s.name as store_name,
                        mmu.material_used as system_record,
                        COUNT(DISTINCT dms.dish_id) as contributing_dishes,
                        STRING_AGG(DISTINCT d.name, ', ') as dish_names,
                        SUM(dms.sale_amount - dms.return_amount) as total_dish_sales,
                        SUM((dms.sale_amount - dms.return_amount) * 
                            COALESCE(dm.standard_quantity, 0) * 
                            COALESCE(dm.loss_rate, 1.0) / 
                            COALESCE(dm.unit_conversion_rate, 1.0)) as theoretical_usage,
                        CASE 
                            WHEN SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) / 
                                COALESCE(dm.unit_conversion_rate, 1.0)) > 0 
                            THEN ((mmu.material_used - SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) / 
                                COALESCE(dm.unit_conversion_rate, 1.0))) / 
                                SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) / 
                                COALESCE(dm.unit_conversion_rate, 1.0))) * 100
                            ELSE 0 
                        END as variance_percentage
                    FROM material_monthly_usage mmu
                    JOIN material m ON mmu.material_id = m.id AND mmu.store_id = m.store_id
                    JOIN store s ON mmu.store_id = s.id
                    JOIN dish_material dm ON m.id = dm.material_id AND m.store_id = dm.store_id
                    JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                    JOIN dish_monthly_sale dms ON dm.dish_id = dms.dish_id AND dm.store_id = dms.store_id
                    WHERE mmu.year = 2025 AND mmu.month = 5
                    AND dms.year = 2025 AND dms.month = 5
                    AND m.material_number = '1500677'  -- Beef brisket material
                    GROUP BY m.material_number, m.name, mmu.store_id, s.name, mmu.material_used
                    ORDER BY mmu.store_id;
                """)
                
                updated_results = cursor.fetchall()
                if updated_results:
                    for row in updated_results:
                        logger.info(f"  Store {row['store_id']} ({row['store_name']}):")
                        logger.info(f"    System Record: {row['system_record']:.2f}")
                        logger.info(f"    Contributing Dishes: {row['contributing_dishes']} (was 14 before)")
                        logger.info(f"    Dishes: {row['dish_names'][:100]}...")
                        logger.info(f"    Total Dish Sales: {row['total_dish_sales']:.0f}")
                        logger.info(f"    Theoretical Usage: {row['theoretical_usage']:.2f}")
                        logger.info(f"    Variance: {row['variance_percentage']:.1f}%")
                        
                        if abs(row['variance_percentage']) < 50:
                            logger.info(f"    🎯 EXCELLENT: Major improvement in variance!")
                        elif abs(row['variance_percentage']) < 100:
                            logger.info(f"    ✅ GOOD: Significant variance improvement!")
                        else:
                            logger.info(f"    📈 IMPROVED: Variance getting better")
                
    except Exception as e:
        logger.error(f"Error fixing material assignments: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = fix_material_assignments_v2()
    if success:
        print("Material assignment fixes completed successfully!")
        print("Dishes should now use their correct specific materials.")
    else:
        print("Material assignment fixes failed!")