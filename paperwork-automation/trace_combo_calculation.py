#!/usr/bin/env python3
"""
Trace Combo Calculation

This script traces where the combo usage value 0.8824 comes from in the monthly automation.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from utils.database import DatabaseConfig, DatabaseManager
from datetime import datetime
import pandas as pd

def trace_combo_value():
    """Trace the combo value 0.8824 to understand its calculation"""
    
    try:
        # Setup database connection
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, let's find the lunch meat material
            cursor.execute("""
                SELECT m.id, m.material_number, m.name, m.store_id
                FROM material m
                WHERE m.name LIKE '%午餐肉%'
                ORDER BY m.store_id, m.name
                LIMIT 10
            """)
            
            lunch_materials = cursor.fetchall()
            print(f"Found {len(lunch_materials)} lunch meat materials")
            
            # First let's specifically check for the 0.8824 value in combo totals
            print("\nSearching for combo total = 0.8824...")
            cursor.execute("""
                SELECT 
                    m.id as material_id,
                    m.name as material_name,
                    m.material_number,
                    s.name as store_name,
                    SUM(mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) / COALESCE(dm.unit_conversion_rate, 1.0)) as combo_total_division,
                    SUM(mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) * COALESCE(dm.unit_conversion_rate, 1.0)) as combo_total_multiply
                FROM material m
                JOIN dish_material dm ON m.id = dm.material_id
                JOIN dish d ON dm.dish_id = d.id
                JOIN monthly_combo_dish_sale mcds ON d.id = mcds.dish_id
                JOIN store s ON mcds.store_id = s.id
                WHERE mcds.year = 2025 AND mcds.month = 5
                AND m.name LIKE '%午餐肉%'
                GROUP BY m.id, m.name, m.material_number, s.name
                HAVING ABS(SUM(mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) / COALESCE(dm.unit_conversion_rate, 1.0)) - 0.8824) < 0.001
                   OR ABS(SUM(mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) * COALESCE(dm.unit_conversion_rate, 1.0)) - 0.8824) < 0.001
            """)
            
            exact_matches = cursor.fetchall()
            if exact_matches:
                print(f"Found {len(exact_matches)} exact matches for 0.8824:")
                for match in exact_matches:
                    div_val = float(match['combo_total_division'])
                    mult_val = float(match['combo_total_multiply'])
                    print(f"  Material: {match['material_name']} (Store: {match['store_name']})")
                    print(f"    Division result: {div_val:.4f}")
                    print(f"    Multiply result: {mult_val:.4f}")
                    if abs(div_val - 0.8824) < 0.001:
                        print("    ✅ 0.8824 comes from DIVISION!")
                    elif abs(mult_val - 0.8824) < 0.001:
                        print("    ❌ 0.8824 comes from MULTIPLICATION!")
            
            # For each lunch meat material, check combo dish sales
            for mat in lunch_materials[:3]:  # Check first 3
                material_id = mat['id']
                print(f"\nChecking material: {mat['name']} (ID: {material_id}, Store: {mat['store_id']})")
                
                # Get combo dish sales for dishes using this material
                cursor.execute("""
                    SELECT 
                        d.id as dish_id,
                        d.name as dish_name,
                        d.store_id,
                        dm.standard_quantity,
                        dm.loss_rate,
                        dm.unit_conversion_rate,
                        mcds.sale_amount as combo_sales,
                        mcds.store_id as sale_store_id,
                        -- Calculate with division
                        mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) / COALESCE(dm.unit_conversion_rate, 1.0) as combo_usage_division,
                        -- Calculate with multiplication (wrong)
                        mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) * COALESCE(dm.unit_conversion_rate, 1.0) as combo_usage_multiply
                    FROM dish_material dm
                    JOIN dish d ON dm.dish_id = d.id
                    LEFT JOIN monthly_combo_dish_sale mcds ON d.id = mcds.dish_id 
                        AND mcds.year = 2025 AND mcds.month = 5
                    WHERE dm.material_id = %s
                    AND mcds.sale_amount IS NOT NULL
                    AND mcds.sale_amount > 0
                    ORDER BY combo_usage_division DESC
                    LIMIT 10
                """, (material_id,))
                
                combo_results = cursor.fetchall()
                
                if combo_results:
                    print(f"  Found {len(combo_results)} combo dishes using this material:")
                    total_combo_division = 0
                    total_combo_multiply = 0
                    
                    for combo in combo_results:
                        print(f"    Dish: {combo['dish_name']}")
                        print(f"      Combo Sales: {combo['combo_sales']}")
                        print(f"      Standard Qty: {combo['standard_quantity']}")
                        print(f"      Loss Rate: {combo['loss_rate']}")
                        print(f"      Unit Conversion: {combo['unit_conversion_rate']}")
                        print(f"      Combo Usage (÷): {combo['combo_usage_division']:.4f}")
                        print(f"      Combo Usage (×): {combo['combo_usage_multiply']:.4f}")
                        
                        total_combo_division += float(combo['combo_usage_division'])
                        total_combo_multiply += float(combo['combo_usage_multiply'])
                    
                    print(f"    Total Combo Usage (÷): {total_combo_division:.4f}")
                    print(f"    Total Combo Usage (×): {total_combo_multiply:.4f}")
                    
                    # Check if 0.8824 matches either calculation
                    if abs(total_combo_division - 0.8824) < 0.01:
                        print("    ✅ 0.8824 matches DIVISION calculation!")
                    elif abs(total_combo_multiply - 0.8824) < 0.01:
                        print("    ❌ 0.8824 matches MULTIPLICATION calculation!")
                    
                    # Also check for specific values from the user's report
                    if abs(total_combo_division - 0.8824) < 0.0001:
                        print(f"    🎯 EXACT MATCH: 0.8824 = {total_combo_division:.4f} (DIVISION)")
                    elif abs(total_combo_multiply - 0.8824) < 0.0001:
                        print(f"    🎯 EXACT MATCH: 0.8824 = {total_combo_multiply:.4f} (MULTIPLICATION)")
                else:
                    print(f"  No combo sales found for this material")
                    
    except Exception as e:
        print(f"Error tracing combo value: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    trace_combo_value()