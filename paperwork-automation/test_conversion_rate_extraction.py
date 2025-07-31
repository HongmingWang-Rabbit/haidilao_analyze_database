#!/usr/bin/env python3
"""
Test Conversion Rate Extraction

This script tests whether the monthly automation is properly extracting
unit conversion rates from the calculated usage file.
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


def test_conversion_rate_extraction():
    """Test conversion rate extraction from calculated usage file"""
    
    usage_file = Path("Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx")
    
    if not usage_file.exists():
        logger.error(f"File not found: {usage_file}")
        return False
    
    try:
        # Read the file like the monthly automation does
        df = pd.read_excel(usage_file, sheet_name='Sheet1')
        logger.info(f"Loaded {len(df)} rows from calculated usage file")
        
        # Test the extraction logic for a few rows
        logger.info("\nTesting conversion rate extraction logic:")
        
        for i, row in df.head(10).iterrows():
            logger.info(f"\nRow {i+1}:")
            logger.info(f"  菜品编码: {row['菜品编码']}")
            logger.info(f"  菜品名称: {row['菜品名称']}")
            logger.info(f"  物料号: {row['物料号']}")
            logger.info(f"  出品分量(kg): {row['出品分量(kg)']}")
            logger.info(f"  损耗: {row['损耗']}")
            logger.info(f"  物料单位: {row['物料单位']}")
            
            # Test the extraction logic like in the monthly automation
            unit_conversion_rate = 1.0  # Default
            
            # Look for unit conversion rate in "物料单位" column
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
            
            logger.info(f"  Extracted unit_conversion_rate: {unit_conversion_rate}")
            
            # Check if it matches the expected value
            expected = row['物料单位']
            if pd.notna(expected) and abs(float(expected) - unit_conversion_rate) < 0.0001:
                logger.info(f"  ✅ CORRECT: Extracted value matches expected")
            else:
                logger.info(f"  ❌ MISMATCH: Expected {expected}, got {unit_conversion_rate}")
        
        # Check what values are actually in the database
        logger.info("\n=== Checking Database Values ===")
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check a few sample dishes to see their conversion rates
                cursor.execute("""
                    SELECT 
                        d.name as dish_name,
                        d.full_code as dish_code,
                        m.material_number,
                        m.name as material_name,
                        dm.unit_conversion_rate,
                        dm.standard_quantity,
                        dm.loss_rate
                    FROM dish_material dm
                    JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                    JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                    WHERE d.store_id = 1
                    AND d.full_code IN ('1060066', '9010019', '90002067')  -- Sample dish codes from file
                    ORDER BY d.full_code, m.material_number;
                """)
                
                db_results = cursor.fetchall()
                logger.info("Database values for sample dishes:")
                for result in db_results:
                    logger.info(f"  {result['dish_name']} ({result['dish_code']}) -> {result['material_name']}")
                    logger.info(f"    conversion_rate: {result['unit_conversion_rate']}")
                    logger.info(f"    standard_quantity: {result['standard_quantity']}")
                    logger.info(f"    loss_rate: {result['loss_rate']}")
                
                # Compare with file values
                logger.info("\nComparing database vs file values:")
                for _, row in df.head(5).iterrows():
                    dish_code = str(int(float(row['菜品编码']))) if pd.notna(row['菜品编码']) else None
                    material_number = str(int(float(row['物料号']))) if pd.notna(row['物料号']) else None
                    
                    if dish_code and material_number:
                        # Find matching database record
                        db_match = None
                        for result in db_results:
                            if result['dish_code'] == dish_code and result['material_number'] == material_number:
                                db_match = result
                                break
                        
                        file_conversion_rate = float(row['物料单位']) if pd.notna(row['物料单位']) else 1.0
                        
                        if db_match:
                            db_conversion_rate = float(db_match['unit_conversion_rate'])
                            if abs(file_conversion_rate - db_conversion_rate) < 0.0001:
                                logger.info(f"  ✅ MATCH: {row['菜品名称']} conversion rate: {file_conversion_rate}")
                            else:
                                logger.info(f"  ❌ MISMATCH: {row['菜品名称']}")
                                logger.info(f"    File: {file_conversion_rate}")
                                logger.info(f"    Database: {db_conversion_rate}")
                        else:
                            logger.info(f"  ⚠️  NOT FOUND: {row['菜品名称']} ({dish_code} -> {material_number}) not in database")
        
    except Exception as e:
        logger.error(f"Error testing conversion rate extraction: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_conversion_rate_extraction()
    if success:
        print("Conversion rate extraction test completed!")
    else:
        print("Conversion rate extraction test failed!")