#!/usr/bin/env python3
"""
Fix Incorrect Standard Quantities in Database

The issue: dm.standard_quantity contains sales quantities instead of serving sizes.
This script updates the dish_material table with correct standard_quantity values
from the inventory calculation data.
"""

import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import DatabaseConfig, DatabaseManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fix_incorrect_standard_quantities():
    """Fix incorrect standard quantities in the database"""
    
    try:
        # Load the corrected inventory calculation data
        corrected_file = "output/inventory_calculation_data_from_sheets_only.xlsx"
        
        if not Path(corrected_file).exists():
            logger.error(f"Corrected file not found: {corrected_file}")
            logger.info("Please run apply_calculation_sheet_data_only.py first")
            return False
        
        logger.info(f"Loading corrected data from: {corrected_file}")
        df = pd.read_excel(corrected_file)
        logger.info(f"Loaded {len(df)} records")
        
        # Connect to database
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        updates_made = 0
        errors = 0
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Group by unique dish-material combinations
            grouped = df.groupby(['门店名称', '菜品名称', '规格', '物料号']).first().reset_index()
            logger.info(f"Processing {len(grouped)} unique dish-material combinations")
            
            for idx, row in grouped.iterrows():
                try:
                    store_name = row['门店名称']
                    dish_name = row['菜品名称']
                    dish_spec = row.get('规格', '')
                    material_number = str(row['物料号']).replace('.0', '')
                    correct_serving_size = float(row['出品分量(kg)'])
                    
                    # Map store name to ID
                    store_id_map = {
                        '加拿大一店': 1, '加拿大二店': 2, '加拿大三店': 3,
                        '加拿大四店': 4, '加拿大五店': 5, '加拿大六店': 6,
                        '加拿大七店': 7
                    }
                    
                    store_id = store_id_map.get(store_name)
                    if not store_id:
                        logger.warning(f"Unknown store: {store_name}")
                        continue
                    
                    # Find the dish and material IDs
                    cursor.execute("""
                        SELECT d.id as dish_id, d.name, d.specification
                        FROM dish d
                        WHERE d.store_id = %s
                        AND d.name = %s
                        AND (d.specification = %s OR (d.specification IS NULL AND %s = ''))
                        AND d.is_active = TRUE
                    """, (store_id, dish_name, dish_spec, dish_spec))
                    
                    dish_result = cursor.fetchone()
                    if not dish_result:
                        continue
                    
                    dish_id = dish_result['dish_id']
                    
                    # Find material ID
                    cursor.execute("""
                        SELECT m.id as material_id
                        FROM material m
                        WHERE m.store_id = %s
                        AND m.material_number = %s
                        AND m.is_active = TRUE
                    """, (store_id, material_number))
                    
                    material_result = cursor.fetchone()
                    if not material_result:
                        continue
                    
                    material_id = material_result['material_id']
                    
                    # Check current standard_quantity
                    cursor.execute("""
                        SELECT standard_quantity
                        FROM dish_material
                        WHERE dish_id = %s AND material_id = %s AND store_id = %s
                    """, (dish_id, material_id, store_id))
                    
                    current_result = cursor.fetchone()
                    if not current_result:
                        continue
                    
                    current_quantity = float(current_result['standard_quantity'])
                    
                    # Only update if significantly different (not just rounding differences)
                    if abs(current_quantity - correct_serving_size) > 0.01:
                        # Special check for beers where current might be sales quantity
                        if current_quantity > 10 and correct_serving_size <= 2:
                            logger.info(f"  Fixing {dish_name} {dish_spec}: {current_quantity} -> {correct_serving_size}")
                            
                            cursor.execute("""
                                UPDATE dish_material
                                SET standard_quantity = %s
                                WHERE dish_id = %s AND material_id = %s AND store_id = %s
                            """, (correct_serving_size, dish_id, material_id, store_id))
                            
                            updates_made += 1
                            
                            # Log specific fixes for beer items
                            if '啤酒' in dish_name or 'beer' in dish_name.lower():
                                logger.info(f"    ✅ Fixed beer: {dish_name} in Store {store_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {e}")
                    errors += 1
                    continue
            
            # Commit all updates
            if updates_made > 0:
                conn.commit()
                logger.info(f"\n✅ Successfully updated {updates_made} records")
            else:
                logger.info("\nNo updates needed - all values appear correct")
            
            # Verify the fix for Store 5 beers
            logger.info("\n\nVerifying Store 5 beer items after fix:")
            cursor.execute("""
                SELECT 
                    d.name as dish_name,
                    d.specification,
                    dm.standard_quantity
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                WHERE dm.store_id = 5
                AND d.name LIKE '%朝日%'
                ORDER BY d.name
            """)
            
            results = cursor.fetchall()
            for row in results:
                logger.info(f"  {row['dish_name']} {row['specification'] or ''}: standard_quantity = {row['standard_quantity']}")
        
        return updates_made > 0
        
    except Exception as e:
        logger.error(f"Error fixing standard quantities: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_incorrect_standard_quantities()
    if success:
        print("\n✅ Standard quantities have been fixed in the database!")
        print("The monthly reports should now show correct 出品分量(kg) values.")
    else:
        print("\n❌ Failed to fix standard quantities")