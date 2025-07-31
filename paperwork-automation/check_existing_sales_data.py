#!/usr/bin/env python3
"""
Check Existing Sales Data

This script checks what sales data currently exists in the database to understand
what needs to be reprocessed.
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


def check_existing_sales_data():
    """Check what sales data currently exists"""
    
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                
                logger.info("Checking existing sales data...")
                
                # Check 1: Look for dishes with names containing "牛仔骨" or similar
                logger.info("Check 1: Looking for beef rib dishes")
                cursor.execute("""
                    SELECT DISTINCT 
                        d.id,
                        d.name as dish_name,
                        d.full_code as dish_code,
                        d.size
                    FROM dish d
                    WHERE d.name LIKE '%牛仔骨%' OR d.name LIKE '%去骨%' OR d.name LIKE '%排骨%'
                    ORDER BY d.name;
                """)
                
                beef_rib_dishes = cursor.fetchall()
                if beef_rib_dishes:
                    logger.info(f"Found {len(beef_rib_dishes)} beef rib dishes:")
                    for dish in beef_rib_dishes:
                        logger.info(f"  ID: {dish['id']}, Code: {dish['dish_code']}, Name: {dish['dish_name']}, Size: {dish['size']}")
                        
                        # Check sales for this specific dish
                        cursor.execute("""
                            SELECT 
                                dms.sales_mode,
                                dms.sale_amount,
                                dms.return_amount,
                                (dms.sale_amount - dms.return_amount) as net_sales,
                                dms.store_id
                            FROM dish_monthly_sale dms
                            WHERE dms.dish_id = %s
                            AND dms.year = 2025 AND dms.month = 5
                            ORDER BY dms.store_id, dms.sales_mode;
                        """, (dish['id'],))
                        
                        sales_data = cursor.fetchall()
                        if sales_data:
                            total_net = sum(row['net_sales'] for row in sales_data)
                            modes = set(row['sales_mode'] for row in sales_data)
                            logger.info(f"    Sales data: {len(sales_data)} records, Total Net: {total_net}, Modes: {modes}")
                            for sale in sales_data:
                                logger.info(f"      Store {sale['store_id']}, Mode: {sale['sales_mode']}, Net: {sale['net_sales']}")
                        else:
                            logger.info(f"    No sales data found for this dish")
                
                # Check 2: Look at all sales modes currently in the database
                logger.info("\nCheck 2: All sales modes in database")
                cursor.execute("""
                    SELECT DISTINCT sales_mode, COUNT(*) as count
                    FROM dish_monthly_sale 
                    WHERE year = 2025 AND month = 5
                    GROUP BY sales_mode
                    ORDER BY count DESC;
                """)
                
                sales_modes = cursor.fetchall()
                logger.info(f"Found {len(sales_modes)} distinct sales modes:")
                for mode in sales_modes:
                    logger.info(f"  {mode['sales_mode']}: {mode['count']} records")
                
                # Check 3: Look for dishes with highest sales to see if they have multiple modes
                logger.info("\nCheck 3: Top selling dishes and their sales modes")
                cursor.execute("""
                    SELECT 
                        d.name as dish_name,
                        d.full_code as dish_code,
                        dms.store_id,
                        SUM(dms.sale_amount - dms.return_amount) as total_net_sales,
                        COUNT(DISTINCT dms.sales_mode) as mode_count,
                        STRING_AGG(DISTINCT dms.sales_mode, ', ') as modes
                    FROM dish_monthly_sale dms
                    JOIN dish d ON dms.dish_id = d.id
                    WHERE dms.year = 2025 AND dms.month = 5
                    GROUP BY d.name, d.full_code, dms.store_id
                    ORDER BY total_net_sales DESC
                    LIMIT 20;
                """)
                
                top_dishes = cursor.fetchall()
                logger.info(f"Top 20 selling dishes:")
                for dish in top_dishes:
                    logger.info(f"  {dish['dish_name']} ({dish['dish_code']}) Store {dish['store_id']}: {dish['total_net_sales']} sales, {dish['mode_count']} modes ({dish['modes']})")
                
                # Check 4: Look for existing material usage data
                logger.info("\nCheck 4: Material usage patterns")
                cursor.execute("""
                    SELECT 
                        m.material_number,
                        m.name as material_name,
                        mmu.store_id,
                        mmu.material_used,
                        COUNT(DISTINCT dm.dish_id) as related_dishes
                    FROM material_monthly_usage mmu
                    JOIN material m ON mmu.material_id = m.id AND mmu.store_id = m.store_id
                    LEFT JOIN dish_material dm ON m.id = dm.material_id AND m.store_id = dm.store_id
                    WHERE mmu.year = 2025 AND mmu.month = 5
                    AND m.material_number IN ('1500677', '4510316')  -- Check both beef material and the dish code
                    GROUP BY m.material_number, m.name, mmu.store_id, mmu.material_used
                    ORDER BY mmu.store_id, m.material_number;
                """)
                
                material_usage = cursor.fetchall()
                if material_usage:
                    logger.info(f"Material usage data:")
                    for usage in material_usage:
                        logger.info(f"  Material {usage['material_number']} ({usage['material_name']}) Store {usage['store_id']}: {usage['material_used']} used, {usage['related_dishes']} related dishes")
                else:
                    logger.info("No material usage data found for target materials")
                
    except Exception as e:
        logger.error(f"Error checking sales data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = check_existing_sales_data()
    if success:
        print("Data check completed!")
    else:
        print("Data check failed!")