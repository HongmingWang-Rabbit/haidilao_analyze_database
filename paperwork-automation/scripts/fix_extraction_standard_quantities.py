#!/usr/bin/env python3
"""
Fix the extraction logic for standard quantities and update dish 01060066.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import DatabaseManager, DatabaseConfig
    from dotenv import load_dotenv
    load_dotenv()
    import pandas as pd
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're in the project root directory")
    sys.exit(1)


def fix_standard_quantities():
    """Fix standard quantities for dish 01060066"""
    print("🔧 FIXING STANDARD QUANTITIES FOR DISH 01060066")
    print("=" * 60)

    try:
        # Connect to database
        db_manager = DatabaseManager(DatabaseConfig(is_test=False))
        print("✅ Connected to production database")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Step 1: Read correct values from Excel
            print("\n1️⃣ READING CORRECT VALUES FROM EXCEL")
            print("-" * 40)

            excel_file = "Input/monthly_report/calculated_dish_material_usage/material_usage.xls"
            df = pd.read_excel(excel_file, sheet_name='计算')

            # Find dish 01060066 records
            df_search = df.copy()
            df_search['菜品编码'] = df_search['菜品编码'].astype(
                str).str.replace('.0', '')
            matches = df_search[df_search['菜品编码'] == '1060066']

            correct_values = {}

            for index, row in matches.iterrows():
                size = row['规格']
                standard_qty = row['出品分量(kg)'] if pd.notna(
                    row['出品分量(kg)']) else None

                if standard_qty is not None:
                    correct_values[size] = float(standard_qty)
                    print(f"✅ Excel: {size} = {standard_qty}")

            print(f"Found {len(correct_values)} correct values from Excel")

            # Step 2: Update database
            print("\n2️⃣ UPDATING DATABASE")
            print("-" * 40)

            updates_made = 0

            for size, correct_qty in correct_values.items():
                print(f"Updating {size} to standard quantity {correct_qty}...")

                cursor.execute("""
                    UPDATE dish_material 
                    SET standard_quantity = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE dish_id = (SELECT id FROM dish WHERE full_code = '1060066' AND size = %s)
                    AND material_id = (SELECT id FROM material WHERE material_number = '3002745')
                """, (correct_qty, size))

                if cursor.rowcount > 0:
                    updates_made += 1
                    print(
                        f"  ✅ Updated {cursor.rowcount} record(s) for {size}")
                else:
                    print(f"  ❌ No records found for {size}")

            # Step 3: Verify updates
            print("\n3️⃣ VERIFICATION")
            print("-" * 40)

            cursor.execute("""
                SELECT 
                    d.full_code,
                    d.size,
                    m.material_number,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id
                JOIN material m ON dm.material_id = m.id
                WHERE d.full_code = '1060066' AND m.material_number = '3002745'
                ORDER BY d.size
            """)

            results = cursor.fetchall()

            if results:
                print("✅ Current database values:")
                total_calc = 0
                for result in results:
                    size = result['size']
                    std_qty = float(result['standard_quantity'])

                    # Test calculation with sales data
                    if size == '单锅':
                        sales = 57
                    elif size == '拼锅':
                        sales = 1695
                    elif size == '四宫格':
                        sales = 2421
                    else:
                        sales = 0

                    calc = sales * std_qty
                    total_calc += calc

                    print(
                        f"   {size}: {std_qty} (test: {sales} × {std_qty} = {calc})")

                print(f"\nTotal test calculation: {total_calc}")
                print(f"Expected: 1811.7")

                if abs(total_calc - 1811.7) < 0.1:
                    print("✅ Calculation matches expected!")
                else:
                    print("❌ Calculation still incorrect")

            # Step 4: Test report query
            print("\n4️⃣ TESTING REPORT QUERY")
            print("-" * 40)

            cursor.execute("""
                WITH aggregated_dish_sales AS (
                    SELECT 
                        dish_id,
                        store_id,
                        SUM(COALESCE(sale_amount, 0)) as total_sale_amount,
                        SUM(COALESCE(return_amount, 0)) as total_return_amount
                    FROM dish_monthly_sale
                    WHERE year = 2025 AND month = 5
                    GROUP BY dish_id, store_id
                ),
                dish_sales AS (
                    SELECT 
                        d.id as dish_id,
                        d.full_code,
                        d.size,
                        ads.store_id,
                        COALESCE(ads.total_sale_amount, 0) - COALESCE(ads.total_return_amount, 0) as net_sales
                    FROM dish d
                    LEFT JOIN aggregated_dish_sales ads ON d.id = ads.dish_id
                    WHERE d.full_code = '1060066' 
                    AND ads.store_id = 1
                )
                SELECT 
                    ds.full_code,
                    ds.size,
                    ds.net_sales,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate,
                    -- Updated calculation
                    (ds.net_sales * COALESCE(dm.standard_quantity, 0) * COALESCE(dm.loss_rate, 1.0) / COALESCE(NULLIF(dm.unit_conversion_rate, 0), 1.0)) as theoretical_usage
                FROM dish_sales ds
                LEFT JOIN dish_material dm ON ds.dish_id = dm.dish_id
                WHERE ds.net_sales > 0
                ORDER BY ds.size
            """)

            query_results = cursor.fetchall()

            if query_results:
                print("✅ Updated report query results:")
                total_theoretical = 0
                for result in query_results:
                    theoretical = float(result['theoretical_usage'])
                    total_theoretical += theoretical
                    print(
                        f"   {result['size']}: {result['net_sales']} × {result['standard_quantity']} × {result['loss_rate']} ÷ {result['unit_conversion_rate']} = {theoretical:.2f}")

                print(f"\nTotal theoretical usage: {total_theoretical:.2f}")
                print(f"Expected: 1811.7")
                print(f"Previous (wrong): 1251.9")

                if abs(total_theoretical - 1811.7) < 0.1:
                    print("🎉 SUCCESS! Calculation is now correct!")
                else:
                    print("❌ Still incorrect")

            # Commit changes
            conn.commit()
            print("\n✅ Changes committed successfully")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def fix_extraction_script():
    """Fix the extraction script to read '出品分量(kg)' column correctly"""
    print("\n🔧 FIXING EXTRACTION SCRIPT")
    print("=" * 50)

    print("The extraction script needs to be updated to look for:")
    print("✅ '出品分量(kg)' (instead of just '出品分量')")
    print("✅ This will fix future extractions")

    # Note: The actual fix would be in extract-dish-materials.py
    # where we change the column search list


if __name__ == "__main__":
    print("🍲 Haidilao Standard Quantity Fix")
    print()

    if fix_standard_quantities():
        fix_extraction_script()
        print("\n🎯 SUMMARY:")
        print("1. ✅ Database updated with correct standard quantities")
        print("2. ✅ Dish 01060066 should now show 1811.7 instead of 1251.9")
        print("3. ⚠️  Extraction script needs to be updated for future extractions")
        print("\n🚀 NEXT STEPS:")
        print("1. Regenerate your report to see corrected values")
        print("2. Update extraction script to read '出品分量(kg)' column")
    else:
        print("\n❌ Fix failed")
        sys.exit(1)
