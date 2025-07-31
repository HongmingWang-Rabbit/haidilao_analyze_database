#!/usr/bin/env python3
"""
Test Dish Material Extraction

This script tests the dish material extraction logic to see if conversion rates
are being properly extracted and saved to the database.
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


def test_dish_material_extraction():
    """Test the dish material extraction process"""
    
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    
    usage_file = Path("Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx")
    
    if not usage_file.exists():
        logger.error(f"File not found: {usage_file}")
        return False
    
    try:
        # Read the file
        df = pd.read_excel(usage_file, sheet_name='Sheet1')
        logger.info(f"Loaded {len(df)} rows from calculated usage file")
        
        # Test extraction for one specific dish that we know has different values
        test_dish_code = '1060066'  # 番茄火锅
        test_material = '3002745'
        
        test_rows = df[(df['菜品编码'] == int(test_dish_code)) & (df['物料号'] == int(test_material))]
        
        if len(test_rows) == 0:
            logger.error(f"No test rows found for dish {test_dish_code} and material {test_material}")
            return False
        
        logger.info(f"Found {len(test_rows)} test rows for dish {test_dish_code}")
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check current database values before extraction
            logger.info("\n=== Before Extraction ===")
            cursor.execute("""
                SELECT 
                    d.name as dish_name,
                    d.full_code as dish_code,
                    d.size,
                    m.material_number,
                    m.name as material_name,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                WHERE d.full_code = %s AND m.material_number = %s
                AND d.store_id = 1
                ORDER BY dm.standard_quantity;
            """, (test_dish_code, test_material))
            
            before_results = cursor.fetchall()
            logger.info("Current database values:")
            for result in before_results:
                logger.info(f"  {result['dish_name']} (size: {result['size']}) -> {result['material_name']}")
                logger.info(f"    standard_quantity: {result['standard_quantity']}")
                logger.info(f"    loss_rate: {result['loss_rate']}")
                logger.info(f"    conversion_rate: {result['unit_conversion_rate']}")
            
            # Now simulate the extraction logic for our test rows
            logger.info(f"\n=== Simulating Extraction for {len(test_rows)} rows ===")
            
            extraction_count = 0
            
            for _, row in test_rows.iterrows():
                # Extract values using the same logic as monthly automation
                full_code = str(int(float(row['菜品编码'])))
                material_number = str(int(float(row['物料号'])))
                
                dish_size = row.get('规格', None)
                if pd.notna(dish_size):
                    dish_size = str(dish_size).strip()
                else:
                    dish_size = None
                
                standard_qty = float(row['出品分量(kg)'])
                loss_rate = float(row['损耗'])
                
                # Get unit conversion rate from "物料单位" field
                unit_conversion_rate = 1.0
                for col_name in df.columns:
                    if '物料单位' in str(col_name):
                        if pd.notna(row[col_name]):
                            try:
                                unit_conversion_rate = float(row[col_name])
                                if unit_conversion_rate <= 0:
                                    unit_conversion_rate = 1.0
                                break
                            except (ValueError, TypeError):
                                unit_conversion_rate = 1.0
                
                input_store_id = 1  # Store 1 for testing
                
                logger.info(f"\n  Processing row:")
                logger.info(f"    dish_code: {full_code}, size: {dish_size}")
                logger.info(f"    material_number: {material_number}")
                logger.info(f"    standard_qty: {standard_qty}")
                logger.info(f"    loss_rate: {loss_rate}")
                logger.info(f"    unit_conversion_rate: {unit_conversion_rate}")
                
                # Execute the same SQL as monthly automation
                try:
                    if dish_size:
                        cursor.execute("""
                            INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate, store_id)
                            SELECT d.id, m.id, %s, %s, %s, d.store_id
                            FROM dish d, material m
                            WHERE d.full_code = %s 
                            AND d.size = %s
                            AND d.store_id = %s
                            AND m.material_number = %s
                            AND m.store_id = %s
                            ON CONFLICT (dish_id, material_id, store_id) DO UPDATE SET
                                standard_quantity = EXCLUDED.standard_quantity,
                                loss_rate = EXCLUDED.loss_rate,
                                unit_conversion_rate = EXCLUDED.unit_conversion_rate,
                                updated_at = CURRENT_TIMESTAMP
                        """, (standard_qty, loss_rate, unit_conversion_rate, full_code, dish_size, input_store_id, material_number, input_store_id))
                    else:
                        cursor.execute("""
                            INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate, store_id)
                            SELECT d.id, m.id, %s, %s, %s, d.store_id
                            FROM dish d, material m
                            WHERE d.full_code = %s 
                            AND d.size IS NULL
                            AND d.store_id = %s
                            AND m.material_number = %s
                            AND m.store_id = %s
                            ON CONFLICT (dish_id, material_id, store_id) DO UPDATE SET
                                standard_quantity = EXCLUDED.standard_quantity,
                                loss_rate = EXCLUDED.loss_rate,
                                unit_conversion_rate = EXCLUDED.unit_conversion_rate,
                                updated_at = CURRENT_TIMESTAMP
                        """, (standard_qty, loss_rate, unit_conversion_rate, full_code, input_store_id, material_number, input_store_id))
                    
                    rows_affected = cursor.rowcount
                    logger.info(f"    SQL executed, rows affected: {rows_affected}")
                    extraction_count += rows_affected
                    
                except Exception as e:
                    logger.error(f"    SQL error: {e}")
            
            # Commit the changes
            conn.commit()
            logger.info(f"\nCommitted {extraction_count} dish-material updates")
            
            # Check database values after extraction
            logger.info("\n=== After Extraction ===")
            cursor.execute("""
                SELECT 
                    d.name as dish_name,
                    d.full_code as dish_code,
                    d.size,
                    m.material_number,
                    m.name as material_name,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                WHERE d.full_code = %s AND m.material_number = %s
                AND d.store_id = 1
                ORDER BY dm.standard_quantity;
            """, (test_dish_code, test_material))
            
            after_results = cursor.fetchall()
            logger.info("Updated database values:")
            for result in after_results:
                logger.info(f"  {result['dish_name']} (size: {result['size']}) -> {result['material_name']}")
                logger.info(f"    standard_quantity: {result['standard_quantity']}")
                logger.info(f"    loss_rate: {result['loss_rate']}")
                logger.info(f"    conversion_rate: {result['unit_conversion_rate']}")
            
            # Compare before vs after
            logger.info("\n=== Comparison ===")
            if len(before_results) == len(after_results):
                for i, (before, after) in enumerate(zip(before_results, after_results)):
                    if abs(float(before['unit_conversion_rate']) - float(after['unit_conversion_rate'])) > 0.0001:
                        logger.info(f"  ✅ UPDATED: Row {i+1} conversion rate: {before['unit_conversion_rate']} -> {after['unit_conversion_rate']}")
                    else:
                        logger.info(f"  ➡️  UNCHANGED: Row {i+1} conversion rate: {before['unit_conversion_rate']}")
            else:
                logger.info(f"  ⚠️  Row count changed: {len(before_results)} -> {len(after_results)}")
        
    except Exception as e:
        logger.error(f"Error testing dish material extraction: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_dish_material_extraction()
    if success:
        print("Dish material extraction test completed!")
    else:
        print("Dish material extraction test failed!")