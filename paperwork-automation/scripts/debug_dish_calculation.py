#!/usr/bin/env python3
"""
Debug script for dish calculation issues.
This investigates dish 01060066 番茄火锅 calculation discrepancy.
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
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're in the project root directory")
    sys.exit(1)


def debug_dish_calculation():
    """Debug dish calculation for 01060066"""
    print("🔍 DEBUGGING DISH 01060066 番茄火锅 CALCULATION")
    print("=" * 70)

    try:
        # Connect to database
        db_manager = DatabaseManager(DatabaseConfig(is_test=False))
        print("✅ Connected to production database")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Step 1: Check dish data in database
            print("\n1️⃣ DISH DATA IN DATABASE")
            print("-" * 50)

            cursor.execute("""
                SELECT 
                    id, full_code, name, size, unit, is_active
                FROM dish 
                WHERE full_code LIKE '%1060066%' OR full_code = '01060066' OR full_code = '1060066'
                ORDER BY full_code, size
            """)

            dishes = cursor.fetchall()

            if dishes:
                print("✅ Found dishes:")
                for dish in dishes:
                    print(
                        f"   ID: {dish['id']}, Code: {dish['full_code']}, Name: {dish['name']}")
                    print(
                        f"   Size: {dish['size']}, Unit: {dish['unit']}, Active: {dish['is_active']}")
                    print()
            else:
                print("❌ No dishes found with code 01060066 or 1060066")
                print("💡 Check if dish extraction was done correctly")
                return False

            # Step 2: Check sales data for 2025-05-31
            print("\n2️⃣ SALES DATA FOR 2025-05 (Store 1) - AGGREGATED")
            print("-" * 50)

            cursor.execute("""
                SELECT 
                    d.full_code,
                    d.name as dish_name,
                    d.size,
                    SUM(dms.sale_amount) as total_sale_amount,
                    SUM(COALESCE(dms.return_amount, 0)) as total_return_amount,
                    (SUM(dms.sale_amount) - SUM(COALESCE(dms.return_amount, 0))) as net_sales
                FROM dish_monthly_sale dms
                JOIN dish d ON dms.dish_id = d.id
                WHERE d.full_code IN ('01060066', '1060066')
                AND dms.year = 2025 AND dms.month = 5
                AND dms.store_id = 1
                GROUP BY d.full_code, d.name, d.size
                ORDER BY d.size
            """)

            sales_data = cursor.fetchall()

            if sales_data:
                print("✅ Found aggregated sales data:")
                total_manual = 0
                for sale in sales_data:
                    net_sales = float(sale['net_sales'])
                    print(
                        f"   {sale['size']}: Sale={sale['total_sale_amount']}, Return={sale['total_return_amount']}, Net={net_sales}")

                    # Manual calculation based on user's data
                    if sale['size'] == '单锅':
                        expected = 57
                        total_manual += expected
                    elif sale['size'] == '拼锅':
                        expected = 1695
                        total_manual += expected
                    elif sale['size'] == '四宫格':
                        expected = 2421
                        total_manual += expected
                    else:
                        expected = "unknown"

                    print(f"   Expected: {expected}, Actual DB: {net_sales}")

                print(f"\nTotal expected net sales: {total_manual}")
                total_db = sum(float(sale['net_sales']) for sale in sales_data)
                print(f"Total DB net sales: {total_db}")

                if abs(total_manual - total_db) > 1:
                    print("⚠️  Sales data mismatch - check extraction process")
                else:
                    print("✅ Sales data matches expected")
            else:
                print("❌ No sales data found for 2025-05")
                print("💡 Check if sales data extraction was done for this month")

            # Step 3: Check dish-material relationships
            print("\n3️⃣ DISH-MATERIAL RELATIONSHIPS")
            print("-" * 50)

            cursor.execute("""
                SELECT 
                    d.full_code,
                    d.size,
                    m.material_number,
                    m.name as material_name,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate,
                    dm.created_at,
                    dm.updated_at
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id
                JOIN material m ON dm.material_id = m.id
                WHERE d.full_code IN ('01060066', '1060066')
                ORDER BY d.size, m.material_number
            """)

            relationships = cursor.fetchall()

            if relationships:
                print("✅ Found dish-material relationships:")
                for rel in relationships:
                    print(
                        f"   {rel['full_code']} ({rel['size']}) + {rel['material_number']} - {rel['material_name']}")
                    print(
                        f"   Standard Qty: {rel['standard_quantity']}, Loss Rate: {rel['loss_rate']}")
                    print(f"   Unit Conversion: {rel['unit_conversion_rate']}")
                    print(f"   Last Updated: {rel['updated_at']}")
                    print()
            else:
                print("❌ No dish-material relationships found")
                print("💡 Need to extract dish-material relationships first")

            # Step 4: Manual calculation vs DB calculation
            print("\n4️⃣ CALCULATION COMPARISON")
            print("-" * 50)

            if sales_data and relationships:
                print("Manual calculation (based on your data):")
                manual_total = 0

                for sale in sales_data:
                    size = sale['size']
                    net_sales = float(sale['net_sales'])

                    # Your expected values
                    if size == '单锅':
                        expected_sales = 57
                        expected_std_qty = 1.2
                    elif size == '拼锅':
                        expected_sales = 1695
                        expected_std_qty = 0.6
                    elif size == '四宫格':
                        expected_sales = 2421
                        expected_std_qty = 0.3
                    else:
                        continue

                    # Find DB standard quantity for this size
                    db_std_qty = None
                    for rel in relationships:
                        if rel['size'] == size:
                            db_std_qty = float(rel['standard_quantity'])
                            break

                    manual_calc = expected_sales * expected_std_qty
                    db_calc = net_sales * (db_std_qty if db_std_qty else 0)

                    print(f"   {size}:")
                    print(
                        f"     Manual: {expected_sales} × {expected_std_qty} = {manual_calc}")
                    print(f"     DB: {net_sales} × {db_std_qty} = {db_calc}")
                    print(f"     Difference: {abs(manual_calc - db_calc):.2f}")

                    manual_total += manual_calc

                print(f"\nTotal manual calculation: {manual_total}")
                print(f"Expected in report: 1811.7")
                print(f"Actual in report: 1251.9")
                print(f"Difference: {1811.7 - 1251.9:.1f}")

                # Step 5: Test actual query used in reports
                print("\n5️⃣ TESTING REPORT QUERY")
                print("-" * 50)

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
                        WHERE d.full_code IN ('01060066', '1060066') 
                        AND ads.store_id = 1
                    )
                    SELECT 
                        ds.full_code,
                        ds.size,
                        ds.net_sales,
                        dm.standard_quantity,
                        dm.loss_rate,
                        dm.unit_conversion_rate,
                        -- Calculation used in reports
                        (ds.net_sales * COALESCE(dm.standard_quantity, 0) * COALESCE(dm.loss_rate, 1.0) / COALESCE(NULLIF(dm.unit_conversion_rate, 0), 1.0)) as theoretical_usage
                    FROM dish_sales ds
                    LEFT JOIN dish_material dm ON ds.dish_id = dm.dish_id
                    WHERE ds.net_sales > 0
                    ORDER BY ds.size
                """)

                query_results = cursor.fetchall()

                if query_results:
                    print("✅ Report query results:")
                    total_theoretical = 0
                    for result in query_results:
                        print(
                            f"   {result['size']}: {result['net_sales']} × {result['standard_quantity']} × {result['loss_rate']} ÷ {result['unit_conversion_rate']} = {result['theoretical_usage']:.2f}")
                        total_theoretical += float(result['theoretical_usage'])

                    print(
                        f"\nTotal theoretical usage from query: {total_theoretical:.2f}")
                    print(f"Expected: 1811.7")
                    print(f"Actual report: 1251.9")
                else:
                    print("❌ No results from report query")

            print("\n" + "=" * 70)
            print("🎯 DIAGNOSIS:")

            # Determine the issue
            if not dishes:
                print("❌ ISSUE: Dish not found in database")
                print("💡 SOLUTION: Re-run dish extraction")
            elif not sales_data:
                print("❌ ISSUE: Sales data missing")
                print("💡 SOLUTION: Re-run sales data extraction for 2025-05")
            elif not relationships:
                print("❌ ISSUE: Dish-material relationships missing")
                print("💡 SOLUTION: Re-run dish-material extraction")
            else:
                print("✅ All data present - issue is likely WRONG STANDARD QUANTITIES")
                print("💡 SOLUTION:")
                print(
                    "   1. Check extraction Excel file for correct standard quantities")
                print("   2. Re-run dish-material extraction")
                print("   3. Expected standard quantities:")
                print("      - 单锅: 1.2 (current DB: 0.3)")
                print("      - 拼锅: 0.6 (current DB: 0.3)")
                print("      - 四宫格: 0.3 (current DB: 0.3) ✅")

    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    print("🍲 Haidilao Dish Calculation Debugger")
    print()

    if debug_dish_calculation():
        print("\n✅ Debug completed")
    else:
        print("\n❌ Debug failed")
        sys.exit(1)
