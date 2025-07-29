#!/usr/bin/env python3
"""
Debug Store-Specific Material Calculation

This script examines the store-specific material calculation logic
to match what the actual material report generates.
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from utils.database import DatabaseManager, DatabaseConfig
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


def debug_store_specific_calculation():
    """Debug store-specific material calculation for dish 90000413 and material 4505163"""
    if not DATABASE_AVAILABLE:
        print("❌ Database utilities not available")
        return

    db_manager = DatabaseManager(DatabaseConfig(is_test=False))

    print("🔍 DEBUGGING STORE-SPECIFIC MATERIAL CALCULATION")
    print("="*60)
    print("Target: Dish 90000413 (冬阴功锅底) - Material 4505163 (冬阴功酱)")
    print("Target Period: May 2025")
    print("="*60)

    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Replicate the exact query logic from material variance calculation
            year = 2025
            month = 5

            # Check if unit_conversion_rate column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'dish_material' 
                AND column_name = 'unit_conversion_rate'
            """)
            has_conversion_rate = cursor.fetchone() is not None

            print(
                f"✅ Unit conversion rate column exists: {has_conversion_rate}")

            # Build the calculation SQL
            if has_conversion_rate:
                calculation_sql = "SUM(ds.net_sales * COALESCE(dm.standard_quantity, 0) * COALESCE(dm.loss_rate, 1.0) / COALESCE(dm.unit_conversion_rate, 1.0)) as theoretical_total"
            else:
                calculation_sql = "SUM(ds.net_sales * COALESCE(dm.standard_quantity, 0) * COALESCE(dm.loss_rate, 1.0)) as theoretical_total"

            # Get material ID for our target material
            cursor.execute("""
                SELECT id FROM material WHERE material_number = %s
            """, ('4505163',))

            material_result = cursor.fetchone()
            if not material_result:
                print("❌ Material 4505163 not found")
                return

            material_id = material_result['id']
            material_ids = [material_id]

            # Execute the exact query from material variance calculation
            regular_theoretical_sql = f"""
            WITH aggregated_dish_sales AS (
                SELECT 
                    dish_id,
                    store_id,
                    SUM(COALESCE(sale_amount, 0)) as total_sale_amount,
                    SUM(COALESCE(return_amount, 0)) as total_return_amount
                FROM dish_monthly_sale
                WHERE year = %s AND month = %s
                GROUP BY dish_id, store_id
            ),
            dish_sales AS (
                SELECT 
                    d.id as dish_id,
                    d.name as dish_name,
                    ads.store_id,
                    s.name as store_name,
                    COALESCE(ads.total_sale_amount, 0) - COALESCE(ads.total_return_amount, 0) as net_sales
                FROM dish d
                LEFT JOIN aggregated_dish_sales ads ON d.id = ads.dish_id
                LEFT JOIN store s ON ads.store_id = s.id
                WHERE d.is_active = TRUE AND ads.store_id IS NOT NULL
            ),
            regular_theoretical_usage AS (
                SELECT 
                    m.id as material_id,
                    m.name as material_name,
                    m.material_number,
                    m.unit as material_unit,
                    m.package_spec,
                    ds.store_id,
                    ds.store_name,
                    {calculation_sql}
                FROM material m
                LEFT JOIN dish_material dm ON m.id = dm.material_id
                LEFT JOIN dish_sales ds ON dm.dish_id = ds.dish_id
                WHERE m.is_active = TRUE AND ds.store_id IS NOT NULL
                    AND m.id = ANY(%s)
                GROUP BY m.id, m.name, m.material_number, m.unit, m.package_spec, ds.store_id, ds.store_name
            )
            SELECT * FROM regular_theoretical_usage
            ORDER BY store_name, material_name
            """

            cursor.execute(regular_theoretical_sql,
                           (year, month, material_ids))
            results = cursor.fetchall()

            print(f"\n📊 STORE-SPECIFIC MATERIAL CALCULATION RESULTS:")
            print("="*60)

            if results:
                total_across_stores = 0
                for result in results:
                    store_name = result['store_name']
                    theoretical_total = float(result['theoretical_total'] or 0)
                    total_across_stores += theoretical_total

                    print(f"{store_name:15s}: {theoretical_total:8.2f}")

                print(f"{'TOTAL':15s}: {total_across_stores:8.2f}")

                # Compare with expected values
                print(f"\n🎯 COMPARISON:")
                print(f"Current system shows: 101.7")
                print(f"Expected result: 45.6")
                print(f"Our calculation total: {total_across_stores:.2f}")

                # Check if 加拿大一店 matches expected values
                store_1_result = [
                    r for r in results if '一店' in r['store_name']]
                if store_1_result:
                    store_1_value = float(
                        store_1_result[0]['theoretical_total'] or 0)
                    print(f"加拿大一店 result: {store_1_value:.2f}")

                    if abs(store_1_value - 45.6) < 1.0:
                        print("✅ Store 1 result closely matches expected value!")
                        print(
                            "💡 The issue might be that the report should filter to specific store(s)")
                    else:
                        print("❌ Store 1 result doesn't match expected value")

            else:
                print("❌ No results found")

            # Debug: Check individual dish sales by store
            print(f"\n🔍 INDIVIDUAL DISH SALES BY STORE:")
            print("="*60)

            cursor.execute("""
                SELECT 
                    d.full_code,
                    d.size,
                    s.name as store_name,
                    SUM(COALESCE(dms.sale_amount, 0)) as total_sale,
                    SUM(COALESCE(dms.return_amount, 0)) as total_return,
                    SUM(COALESCE(dms.sale_amount, 0)) - SUM(COALESCE(dms.return_amount, 0)) as net_sales
                FROM dish d
                LEFT JOIN dish_monthly_sale dms ON d.id = dms.dish_id
                LEFT JOIN store s ON dms.store_id = s.id
                WHERE d.full_code = %s 
                    AND dms.year = %s AND dms.month = %s
                GROUP BY d.full_code, d.size, s.name, dms.store_id
                ORDER BY s.name, d.size
            """, ('90000413', year, month))

            dish_sales = cursor.fetchall()

            current_store = None
            store_totals = {}

            for sale in dish_sales:
                store_name = sale['store_name']
                dish_size = sale['size']
                net_sales = float(sale['net_sales'] or 0)

                if store_name != current_store:
                    if current_store:
                        print()  # Add space between stores
                    current_store = store_name
                    store_totals[store_name] = {}
                    print(f"\n{store_name}:")

                store_totals[store_name][dish_size] = net_sales
                print(f"  {dish_size:8s}: {net_sales:6.0f} net sales")

            # Calculate expected material usage for each store
            print(f"\n🧮 EXPECTED MATERIAL USAGE BY STORE:")
            print("="*60)

            expected_standard_qty = {
                '单锅': 0.6,
                '拼锅': 0.3,
                '四宫格': 0.15
            }
            expected_unit_conversion = 3.0

            for store_name, sizes in store_totals.items():
                store_total_usage = 0
                print(f"\n{store_name}:")

                for size, net_sales in sizes.items():
                    if size in expected_standard_qty:
                        std_qty = expected_standard_qty[size]
                        usage = net_sales * std_qty / expected_unit_conversion
                        store_total_usage += usage
                        print(
                            f"  {size:8s}: {net_sales:6.0f} × {std_qty:4.2f} ÷ {expected_unit_conversion} = {usage:6.2f}")

                print(f"  {'TOTAL':8s}: {store_total_usage:6.2f}")

                if abs(store_total_usage - 45.6) < 1.0:
                    print(f"  ✅ This store matches expected result!")

    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    debug_store_specific_calculation()


if __name__ == "__main__":
    main()
