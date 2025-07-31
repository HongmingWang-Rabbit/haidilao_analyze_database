#!/usr/bin/env python3
"""
Debug Dish Usage Details

This script debugs why material_quantity is showing the same value as net_sales
in the get_dish_usage_details function output.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import DatabaseConfig, DatabaseManager
from lib.monthly_dishes_worksheet import MonthlyDishesWorksheetGenerator

# Fix encoding for Windows console
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'


class DataProvider:
    """Simple data provider for testing"""
    def __init__(self, db_manager):
        self.db_manager = db_manager


def debug_dish_usage_details():
    """Debug the dish usage details for Store 5 朝日啤酒"""
    
    try:
        # Setup database connection
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        data_provider = DataProvider(db_manager)
        
        # Create worksheet generator
        generator = MonthlyDishesWorksheetGenerator(['加拿大五店'], '2025-05-31')
        
        print("=== DEBUGGING DISH USAGE DETAILS ===\n")
        
        # First, find the 朝日啤酒 material in Store 5
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Find 朝日啤酒 material
            cursor.execute("""
                SELECT m.id, m.material_number, m.name, m.store_id
                FROM material m
                WHERE m.store_id = 5 
                AND (m.name LIKE '%朝日%' OR m.name LIKE '%ASAKI%')
                ORDER BY m.name
                LIMIT 5
            """)
            
            asahi_materials = cursor.fetchall()
            
            if not asahi_materials:
                print("No 朝日 materials found in Store 5")
                return
            
            print(f"Found {len(asahi_materials)} 朝日 materials in Store 5:")
            for mat in asahi_materials:
                print(f"  Material ID: {mat['id']}, Number: {mat['material_number']}, Name: {mat['name']}")
            
            # Test the first material
            test_material = asahi_materials[0]
            material_id = test_material['id']
            store_id = 5
            
            print(f"\n\nTesting material {material_id} for Store 5, May 2025...")
            
            # First, let's manually run the query to see what data is returned
            print("\n1. Running the SQL query manually to check data:")
            
            cursor.execute("""
                WITH aggregated_dish_sales AS (
                    SELECT 
                        dish_id,
                        store_id,
                        SUM(COALESCE(sale_amount, 0)) as total_sale_amount,
                        SUM(COALESCE(return_amount, 0)) as total_return_amount
                    FROM dish_monthly_sale
                    WHERE year = 2025 AND month = 5 AND store_id = 5
                    GROUP BY dish_id, store_id
                ),
                dish_net_sales AS (
                    SELECT 
                        dish_id,
                        store_id,
                        (total_sale_amount - total_return_amount) as net_sales
                    FROM aggregated_dish_sales
                )
                SELECT 
                    d.name as dish_name,
                    d.specification as dish_spec,
                    dns.net_sales,
                    COALESCE(dm.standard_quantity, 0) as material_quantity,
                    COALESCE(dm.loss_rate, 1.0) as loss_rate,
                    COALESCE(dm.unit_conversion_rate, 1.0) as unit_conversion_rate,
                    m.unit as material_unit
                FROM dish_net_sales dns
                INNER JOIN dish d ON dns.dish_id = d.id AND d.store_id = dns.store_id
                INNER JOIN dish_material dm ON d.id = dm.dish_id AND d.store_id = dm.store_id
                INNER JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                WHERE dm.material_id = %s AND m.store_id = %s
                    AND dns.net_sales > 0
                    AND dns.store_id = %s
                ORDER BY dns.net_sales DESC
                LIMIT 5
            """, (material_id, store_id, store_id))
            
            results = cursor.fetchall()
            
            print(f"\nQuery returned {len(results)} rows:")
            for i, row in enumerate(results):
                print(f"\n  Row {i+1}:")
                print(f"    dish_name: {row['dish_name']}")
                print(f"    dish_spec: {row['dish_spec']}")
                print(f"    net_sales: {row['net_sales']}")
                print(f"    material_quantity: {row['material_quantity']} (from dm.standard_quantity)")
                print(f"    loss_rate: {row['loss_rate']}")
                print(f"    unit_conversion_rate: {row['unit_conversion_rate']}")
                
                # Check if material_quantity equals net_sales
                if abs(row['material_quantity'] - row['net_sales']) < 0.001:
                    print(f"    ⚠️  ERROR: material_quantity ({row['material_quantity']}) = net_sales ({row['net_sales']})")
                    print(f"    This suggests dm.standard_quantity in the database is wrong!")
            
            # Now call the actual function to see what it returns
            print("\n\n2. Calling get_dish_usage_details function:")
            usage_details = generator.get_dish_usage_details(
                data_provider, material_id, store_id, 2025, 5)
            
            print("\nFunction returned:")
            print(usage_details)
            
            # Parse the output to check values
            print("\n\n3. Parsing the output:")
            lines = usage_details.split('\n')
            for line in lines:
                if 'sale-' in line and '出品分量(kg)-' in line:
                    # Extract values from the formatted string
                    import re
                    sale_match = re.search(r'sale-([\d.]+)', line)
                    serving_match = re.search(r'出品分量\(kg\)-([\d.]+)', line)
                    
                    if sale_match and serving_match:
                        sale_value = float(sale_match.group(1))
                        serving_value = float(serving_match.group(1))
                        
                        print(f"\n  Line: {line[:50]}...")
                        print(f"    Sale amount: {sale_value}")
                        print(f"    出品分量(kg): {serving_value}")
                        
                        if abs(sale_value - serving_value) < 0.001:
                            print(f"    ⚠️  CONFIRMED: 出品分量(kg) = sale amount!")
                            print(f"    This means dm.standard_quantity = {serving_value} in the database")
            
            # Let's check the dish_material table directly
            print("\n\n4. Checking dish_material table directly:")
            cursor.execute("""
                SELECT 
                    d.name as dish_name,
                    d.specification,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                WHERE dm.material_id = %s AND dm.store_id = %s
                    AND d.name LIKE '%朝日%'
                ORDER BY d.name
                LIMIT 5
            """, (material_id, store_id))
            
            dm_results = cursor.fetchall()
            print(f"\nFound {len(dm_results)} dish-material records:")
            for row in dm_results:
                print(f"  {row['dish_name']} {row['specification'] or ''}")
                print(f"    standard_quantity: {row['standard_quantity']}")
                print(f"    loss_rate: {row['loss_rate']}")
                print(f"    unit_conversion_rate: {row['unit_conversion_rate']}")
                
                if row['standard_quantity'] > 10:
                    print(f"    ⚠️  WARNING: standard_quantity = {row['standard_quantity']} seems too high!")
                    print(f"    This might be the sales quantity instead of serving size!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_dish_usage_details()