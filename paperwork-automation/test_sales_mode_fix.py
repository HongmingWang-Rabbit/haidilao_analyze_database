#!/usr/bin/env python3
"""
Test Sales Mode Fix

This script tests that the sales mode constraint fix is working properly by:
1. Checking that both 堂食 and 外卖 sales modes can be stored separately
2. Verifying theoretical usage calculations include both modes
3. Testing the specific dish mentioned by the user
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


def test_sales_mode_fix():
    """Test the sales mode constraint fix"""
    
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                
                logger.info("Testing sales mode constraint fix...")
                
                # Test 1: Check for the specific dish mentioned by user
                logger.info("Test 1: Checking specific dish '去骨牛仔骨肉' (4510316)")
                cursor.execute("""
                    SELECT 
                        d.name as dish_name,
                        d.full_code as dish_code,
                        dms.store_id,
                        s.name as store_name,
                        dms.sales_mode,
                        dms.sale_amount,
                        dms.return_amount,
                        (dms.sale_amount - dms.return_amount) as net_sales
                    FROM dish_monthly_sale dms
                    JOIN dish d ON dms.dish_id = d.id
                    JOIN store s ON dms.store_id = s.id
                    WHERE d.full_code = '4510316'
                    AND dms.year = 2025 AND dms.month = 5
                    ORDER BY dms.store_id, dms.sales_mode;
                """)
                
                beef_dish_results = cursor.fetchall()
                if beef_dish_results:
                    logger.info(f"Found {len(beef_dish_results)} records for dish 4510316:")
                    total_sales = 0
                    for row in beef_dish_results:
                        logger.info(f"  Store {row['store_id']} ({row['store_name']}), Mode: {row['sales_mode']}, Net Sales: {row['net_sales']}")
                        total_sales += row['net_sales']
                    logger.info(f"  Total Net Sales: {total_sales}")
                    
                    # Check if we now have both sales modes
                    sales_modes = set(row['sales_mode'] for row in beef_dish_results)
                    if len(sales_modes) > 1:
                        logger.info(f"✅ SUCCESS: Found multiple sales modes: {sales_modes}")
                    else:
                        logger.warning(f"⚠️  Only found one sales mode: {sales_modes}")
                else:
                    logger.warning("❌ No records found for dish 4510316")
                
                # Test 2: Check overall statistics for dishes with multiple sales modes
                logger.info("\nTest 2: Checking dishes with multiple sales modes")
                cursor.execute("""
                    SELECT 
                        dish_id,
                        store_id,
                        COUNT(DISTINCT sales_mode) as sales_mode_count,
                        STRING_AGG(DISTINCT sales_mode, ', ') as sales_modes,
                        SUM(sale_amount - return_amount) as total_net_sales
                    FROM dish_monthly_sale 
                    WHERE year = 2025 AND month = 5
                    GROUP BY dish_id, store_id
                    HAVING COUNT(DISTINCT sales_mode) > 1
                    ORDER BY total_net_sales DESC
                    LIMIT 10;
                """)
                
                multi_mode_dishes = cursor.fetchall()
                if multi_mode_dishes:
                    logger.info(f"✅ Found {len(multi_mode_dishes)} dishes with multiple sales modes:")
                    for dish in multi_mode_dishes:
                        logger.info(f"  Dish {dish['dish_id']}, Store {dish['store_id']}: {dish['sales_modes']} (Total: {dish['total_net_sales']})")
                else:
                    logger.warning("⚠️  No dishes found with multiple sales modes")
                
                # Test 3: Compare theoretical usage calculation before and after
                logger.info("\nTest 3: Testing theoretical usage calculation with both sales modes")
                cursor.execute("""
                    SELECT 
                        m.material_number,
                        m.name as material_name,
                        mmu.store_id,
                        s.name as store_name,
                        mmu.material_used as system_record,
                        SUM(dms.sale_amount - dms.return_amount) as total_dish_sales,
                        COUNT(DISTINCT dms.sales_mode) as sales_mode_count,
                        STRING_AGG(DISTINCT dms.sales_mode, ', ') as sales_modes,
                        -- Theoretical usage calculation (fixed formula)
                        SUM((dms.sale_amount - dms.return_amount) * 
                            COALESCE(dm.standard_quantity, 0) * 
                            COALESCE(dm.loss_rate, 1.0) * 
                            COALESCE(dm.unit_conversion_rate, 1.0)) as theoretical_usage
                    FROM material_monthly_usage mmu
                    JOIN material m ON mmu.material_id = m.id AND mmu.store_id = m.store_id
                    JOIN store s ON mmu.store_id = s.id
                    JOIN dish_material dm ON m.id = dm.material_id AND m.store_id = dm.store_id
                    JOIN dish_monthly_sale dms ON dm.dish_id = dms.dish_id AND dm.store_id = dms.store_id
                    WHERE mmu.year = 2025 AND mmu.month = 5
                    AND dms.year = 2025 AND dms.month = 5
                    AND m.material_number = '1500677'  -- Beef material
                    GROUP BY m.material_number, m.name, mmu.store_id, s.name, mmu.material_used
                    ORDER BY mmu.store_id;
                """)
                
                theoretical_results = cursor.fetchall()
                if theoretical_results:
                    logger.info(f"Theoretical usage calculation for beef material (1500677):")
                    for row in theoretical_results:
                        variance_pct = 0
                        if row['theoretical_usage'] > 0:
                            variance_pct = ((row['system_record'] - row['theoretical_usage']) / row['theoretical_usage']) * 100
                        
                        logger.info(f"  Store {row['store_id']} ({row['store_name']}):")
                        logger.info(f"    System Record: {row['system_record']}")
                        logger.info(f"    Total Dish Sales: {row['total_dish_sales']}")
                        logger.info(f"    Sales Modes: {row['sales_modes']} ({row['sales_mode_count']} modes)")
                        logger.info(f"    Theoretical Usage: {row['theoretical_usage']:.2f}")
                        logger.info(f"    Variance: {variance_pct:.1f}%")
                else:
                    logger.warning("❌ No theoretical usage data found for beef material")
                
    except Exception as e:
        logger.error(f"Error testing sales mode fix: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_sales_mode_fix()
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed!")