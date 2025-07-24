#!/usr/bin/env python3
"""
Debug script for unit conversion rate calculations.
This script helps identify why 理论用量 and 套餐用量 are not calculating correctly.
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


def debug_unit_conversion_calculations():
    """Debug unit conversion rate calculations step by step"""
    print("🔍 DEBUGGING UNIT CONVERSION RATE CALCULATIONS")
    print("=" * 60)

    try:
        # Connect to database
        db_manager = DatabaseManager(DatabaseConfig(is_test=False))
        print("✅ Connected to production database")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Check unit_conversion_rate column status
            print("\n1️⃣ CHECKING UNIT CONVERSION RATE COLUMN")
            print("-" * 40)

            cursor.execute("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'dish_material' 
                AND column_name = 'unit_conversion_rate'
            """)

            column_info = cursor.fetchone()

            if not column_info:
                print("❌ unit_conversion_rate column does not exist!")
                print("💡 Run the migration first: Database Management → Option 7")
                return False

            print("✅ unit_conversion_rate column exists")
            print(f"   Data type: {column_info['data_type']}")
            print(f"   Default: {column_info['column_default']}")

            # 2. Check unit conversion rate distribution
            print("\n2️⃣ UNIT CONVERSION RATE DISTRIBUTION")
            print("-" * 40)

            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN unit_conversion_rate = 1.0 THEN 1 END) as default_rates,
                    COUNT(CASE WHEN unit_conversion_rate != 1.0 THEN 1 END) as custom_rates,
                    COUNT(CASE WHEN unit_conversion_rate IS NULL THEN 1 END) as null_rates,
                    COUNT(CASE WHEN unit_conversion_rate = 0 THEN 1 END) as zero_rates,
                    MIN(unit_conversion_rate) as min_rate,
                    MAX(unit_conversion_rate) as max_rate,
                    AVG(unit_conversion_rate) as avg_rate
                FROM dish_material
            """)

            stats = cursor.fetchone()

            print(f"Total dish-material records: {stats['total_records']}")
            print(f"Default rates (1.0): {stats['default_rates']}")
            print(f"Custom rates (≠1.0): {stats['custom_rates']}")
            print(f"NULL rates: {stats['null_rates']}")
            print(f"Zero rates: {stats['zero_rates']}")
            print(f"Min rate: {stats['min_rate']}")
            print(f"Max rate: {stats['max_rate']}")
            print(f"Average rate: {stats['avg_rate']:.4f}")

            if stats['zero_rates'] > 0:
                print(
                    "⚠️  WARNING: Found zero conversion rates! This will cause division by zero.")

            if stats['custom_rates'] == 0:
                print(
                    "⚠️  WARNING: No custom conversion rates found. All rates are default (1.0).")
                print("💡 This means 物料单位 field is not being extracted properly.")

            # 3. Check specific example (dish 1060062 + material 1500882)
            print("\n3️⃣ SPECIFIC EXAMPLE CHECK")
            print("-" * 40)

            cursor.execute("""
                SELECT 
                    d.full_code as dish_code,
                    d.name as dish_name,
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
                WHERE d.full_code = '1060062' AND m.material_number = '1500882'
                LIMIT 1
            """)

            example = cursor.fetchone()

            if example:
                print("✅ Found example relationship:")
                print(
                    f"   Dish: {example['dish_code']} - {example['dish_name']} ({example['size']})")
                print(
                    f"   Material: {example['material_number']} - {example['material_name']}")
                print(f"   Standard quantity: {example['standard_quantity']}")
                print(f"   Loss rate: {example['loss_rate']}")
                print(
                    f"   Unit conversion rate: {example['unit_conversion_rate']}")
                print(f"   Last updated: {example['updated_at']}")

                if example['unit_conversion_rate'] == 1.0:
                    print("⚠️  Expected conversion rate 0.354, but found 1.0")
                    print("💡 The extraction script may not be capturing 物料单位 properly")
            else:
                print("❌ Example relationship not found")
                print("💡 Run dish-material extraction first")

            # 4. Sample calculation comparison
            print("\n4️⃣ CALCULATION COMPARISON")
            print("-" * 40)

            cursor.execute("""
                SELECT 
                    d.full_code,
                    m.material_number,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate,
                    -- Sample sales amount for calculation
                    100 as sample_sales,
                    -- Old calculation (without conversion)
                    (100 * dm.standard_quantity * dm.loss_rate) as old_calculation,
                    -- New calculation (with conversion)
                    (100 * dm.standard_quantity * dm.loss_rate / NULLIF(dm.unit_conversion_rate, 0)) as new_calculation,
                    -- Difference
                    (100 * dm.standard_quantity * dm.loss_rate / NULLIF(dm.unit_conversion_rate, 0)) - 
                    (100 * dm.standard_quantity * dm.loss_rate) as difference
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id
                JOIN material m ON dm.material_id = m.id
                WHERE dm.unit_conversion_rate != 1.0
                LIMIT 5
            """)

            calculations = cursor.fetchall()

            if calculations:
                print("Sample calculations (for custom conversion rates):")
                print(
                    "Dish Code | Material | Std Qty | Loss | Conv Rate | Old Calc | New Calc | Difference")
                print("-" * 80)

                for calc in calculations:
                    print(f"{calc['full_code']:<9} | {calc['material_number']:<8} | {calc['standard_quantity']:<7.2f} | {calc['loss_rate']:<4.2f} | {calc['unit_conversion_rate']:<9.4f} | {calc['old_calculation']:<8.2f} | {calc['new_calculation']:<8.2f} | {calc['difference']:<8.2f}")
            else:
                print("No custom conversion rates to compare")

            # 5. Check recent dish_monthly_sale data
            print("\n5️⃣ RECENT SALES DATA CHECK")
            print("-" * 40)

            cursor.execute("""
                SELECT 
                    year, month,
                    COUNT(*) as sale_records,
                    SUM(sale_amount) as total_sales,
                    COUNT(DISTINCT dish_id) as unique_dishes,
                    COUNT(DISTINCT store_id) as unique_stores
                FROM dish_monthly_sale
                WHERE year >= 2024
                GROUP BY year, month
                ORDER BY year DESC, month DESC
                LIMIT 3
            """)

            sales_data = cursor.fetchall()

            if sales_data:
                print("Recent monthly sales data:")
                for sale in sales_data:
                    print(
                        f"   {sale['year']}-{sale['month']:02d}: {sale['sale_records']} records, {sale['total_sales']:.0f} total sales")
            else:
                print("❌ No recent sales data found")
                print("💡 Load sales data first")

            # 6. Check if variance analysis would find data
            print("\n6️⃣ VARIANCE ANALYSIS PREVIEW")
            print("-" * 40)

            cursor.execute("""
                WITH test_variance AS (
                    SELECT 
                        m.id as material_id,
                        m.name as material_name,
                        COUNT(dm.id) as dish_relationships,
                        COUNT(mmu.id) as usage_records,
                        SUM(COALESCE(mmu.material_used, 0)) as total_system_usage
                    FROM material m
                    LEFT JOIN dish_material dm ON m.id = dm.material_id
                    LEFT JOIN material_monthly_usage mmu ON m.id = mmu.material_id
                        AND mmu.year = 2024 AND mmu.month = 6
                    WHERE m.is_active = TRUE
                    GROUP BY m.id, m.name
                    HAVING COUNT(dm.id) > 0 OR COUNT(mmu.id) > 0
                )
                SELECT 
                    COUNT(*) as materials_with_data,
                    COUNT(CASE WHEN dish_relationships > 0 THEN 1 END) as materials_with_relationships,
                    COUNT(CASE WHEN usage_records > 0 THEN 1 END) as materials_with_usage,
                    SUM(total_system_usage) as total_usage
                FROM test_variance
            """)

            variance_preview = cursor.fetchone()

            if variance_preview:
                print(
                    f"Materials that would appear in variance analysis: {variance_preview['materials_with_data']}")
                print(
                    f"Materials with dish relationships: {variance_preview['materials_with_relationships']}")
                print(
                    f"Materials with usage records: {variance_preview['materials_with_usage']}")
                print(
                    f"Total system usage: {variance_preview['total_usage']:.2f}")

                if variance_preview['materials_with_data'] == 0:
                    print("❌ No materials would show in variance analysis")
                    print(
                        "💡 Need to extract dish-material relationships and usage data")

            print("\n" + "=" * 60)
            print("🎯 DIAGNOSIS SUMMARY:")

            if stats['custom_rates'] == 0:
                print("❌ PRIMARY ISSUE: No custom conversion rates found")
                print("💡 SOLUTION: Check 物料单位 extraction in automation scripts")
                print("   - Verify Excel file has 物料单位 column")
                print("   - Check extraction scripts are reading this column")
                print("   - Re-run dish-material extraction")
            elif stats['zero_rates'] > 0:
                print("❌ DIVISION BY ZERO: Found zero conversion rates")
                print("💡 SOLUTION: Fix zero rates in database or extraction logic")
            elif variance_preview and variance_preview['materials_with_data'] == 0:
                print("❌ NO DATA: Missing dish-material relationships or usage data")
                print("💡 SOLUTION: Run complete data extraction workflow")
            else:
                print("✅ Configuration looks correct")
                print("💡 Check specific calculation queries in variance analysis")

    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    print("🍲 Haidilao Unit Conversion Rate Calculation Debugger")
    print()

    if debug_unit_conversion_calculations():
        print("\n✅ Debug completed successfully")
    else:
        print("\n❌ Debug failed")
        sys.exit(1)
