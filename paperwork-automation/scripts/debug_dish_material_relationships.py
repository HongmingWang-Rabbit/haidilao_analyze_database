#!/usr/bin/env python3
"""
Debug Dish-Material Relationships

This script examines the dish_material relationships to understand
how different sizes of the same dish (90000413) are set up with
different standard quantities for the same material.
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


def examine_dish_material_relationships():
    """Examine dish-material relationships for dish 90000413"""
    if not DATABASE_AVAILABLE:
        print("❌ Database utilities not available")
        return

    db_manager = DatabaseManager(DatabaseConfig(is_test=False))

    print("🔍 EXAMINING DISH-MATERIAL RELATIONSHIPS")
    print("="*60)

    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check all dishes with code 90000413
            cursor.execute("""
                SELECT id, full_code, name, size, specification
                FROM dish
                WHERE full_code = %s
                ORDER BY size
            """, ('90000413',))

            dishes = cursor.fetchall()
            print(f"🍽️ Found {len(dishes)} dish records for code 90000413:")

            for dish in dishes:
                print(
                    f"  ID: {dish['id']}, Size: {dish['size']}, Name: {dish['name']}")

            if not dishes:
                print("❌ No dishes found with code 90000413")
                return

            # Check material 4505163
            cursor.execute("""
                SELECT id, name, material_number, unit
                FROM material
                WHERE material_number = %s
            """, ('4505163',))

            materials = cursor.fetchall()
            print(
                f"\n🧪 Found {len(materials)} material records for number 4505163:")

            for material in materials:
                print(f"  ID: {material['id']}, Name: {material['name']}")

            if not materials:
                print("❌ No materials found with number 4505163")
                return

            material_id = materials[0]['id']

            # Check dish-material relationships for each dish size
            print(f"\n🔗 DISH-MATERIAL RELATIONSHIPS:")
            print("="*60)

            for dish in dishes:
                dish_id = dish['id']
                dish_size = dish['size']

                cursor.execute("""
                    SELECT dm.*, m.name as material_name
                    FROM dish_material dm
                    JOIN material m ON dm.material_id = m.id
                    WHERE dm.dish_id = %s AND dm.material_id = %s
                """, (dish_id, material_id))

                relationships = cursor.fetchall()

                if relationships:
                    for rel in relationships:
                        print(f"Dish {dish_id} ({dish_size}):")
                        print(f"  Material: {rel['material_name']}")
                        print(
                            f"  Standard Quantity: {rel['standard_quantity']}")
                        print(f"  Loss Rate: {rel['loss_rate']}")
                        print(
                            f"  Unit Conversion Rate: {rel['unit_conversion_rate']}")
                        print()
                else:
                    print(
                        f"❌ No relationship found between dish {dish_id} ({dish_size}) and material {material_id}")

            # Check monthly sales data for each dish size for May 2025
            print(f"\n📊 MONTHLY SALES DATA (May 2025):")
            print("="*60)

            total_net_sales_by_size = {}

            for dish in dishes:
                dish_id = dish['id']
                dish_size = dish['size']

                cursor.execute("""
                    SELECT dms.*, s.name as store_name
                    FROM dish_monthly_sale dms
                    JOIN store s ON dms.store_id = s.id
                    WHERE dms.dish_id = %s AND dms.year = 2025 AND dms.month = 5
                    ORDER BY s.id
                """, (dish_id,))

                sales_data = cursor.fetchall()

                if sales_data:
                    size_total = 0
                    print(f"\n{dish_size} (Dish ID: {dish_id}):")
                    for sale in sales_data:
                        net_sales = sale['sale_amount'] - sale['return_amount']
                        size_total += net_sales
                        if net_sales != 0:  # Only show non-zero sales
                            print(
                                f"  {sale['store_name']}: {sale['sale_amount']} - {sale['return_amount']} = {net_sales}")

                    print(f"  TOTAL for {dish_size}: {size_total}")
                    total_net_sales_by_size[dish_size] = size_total
                else:
                    print(
                        f"\n{dish_size} (Dish ID: {dish_id}): No sales data found")
                    total_net_sales_by_size[dish_size] = 0

            # Manual calculation based on expected values
            print(f"\n🧮 MANUAL CALCULATION VERIFICATION:")
            print("="*60)

            expected_standard_qty = {
                '单锅': 0.6,
                '拼锅': 0.3,
                '四宫格': 0.15
            }

            expected_unit_conversion = 3.0
            total_material_usage = 0

            print("Expected material usage calculation:")
            for size, expected_qty in expected_standard_qty.items():
                actual_sales = float(total_net_sales_by_size.get(size, 0))
                usage = actual_sales * expected_qty
                total_material_usage += usage
                print(
                    f"  {size:8s}: {actual_sales:3.0f} sales × {expected_qty:4.2f} std_qty = {usage:6.2f}")

            final_usage = total_material_usage / expected_unit_conversion
            print(
                f"\nTotal before unit conversion: {total_material_usage:6.2f}")
            print(
                f"After unit conversion (÷{expected_unit_conversion}): {final_usage:6.2f}")

            # Check what's actually in the database
            print(f"\n🔍 ACTUAL DATABASE RELATIONSHIPS:")
            print("="*60)

            cursor.execute("""
                SELECT 
                    d.id, d.full_code, d.size, d.name,
                    dm.standard_quantity, dm.loss_rate, dm.unit_conversion_rate,
                    m.material_number, m.name as material_name
                FROM dish d
                JOIN dish_material dm ON d.id = dm.dish_id
                JOIN material m ON dm.material_id = m.id
                WHERE d.full_code = %s AND m.material_number = %s
                ORDER BY d.size
            """, ('90000413', '4505163'))

            actual_relationships = cursor.fetchall()

            if actual_relationships:
                print("Actual relationships in database:")
                for rel in actual_relationships:
                    print(
                        f"  {rel['size']:8s}: standard_qty={rel['standard_quantity']}, loss_rate={rel['loss_rate']}, unit_conversion={rel['unit_conversion_rate']}")

                # Calculate with actual database values
                print(f"\nCalculation with actual database values:")
                db_total_usage = 0
                for rel in actual_relationships:
                    size = rel['size']
                    std_qty = float(rel['standard_quantity'] or 0)
                    loss_rate = float(rel['loss_rate'] or 1.0)
                    unit_conversion = float(rel['unit_conversion_rate'] or 1.0)
                    actual_sales = float(total_net_sales_by_size.get(size, 0))

                    usage = actual_sales * std_qty * loss_rate / unit_conversion
                    db_total_usage += usage
                    print(
                        f"  {size:8s}: {actual_sales:3.0f} × {std_qty:4.2f} × {loss_rate:4.2f} ÷ {unit_conversion:4.2f} = {usage:6.2f}")

                print(f"\nTotal with actual DB values: {db_total_usage:6.2f}")
                print(f"Current system shows: 101.7")
                print(f"Expected result: 45.6")
                print(
                    f"Discrepancy explanation: WRONG standard quantities and unit conversion rate!")
            else:
                print("❌ No actual relationships found in database")

    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    print("🔍 DEBUGGING DISH-MATERIAL RELATIONSHIPS")
    print("="*60)
    print("Target: Dish 90000413 (冬阴功锅底) - Material 4505163 (冬阴功酱)")
    print("="*60)

    examine_dish_material_relationships()


if __name__ == "__main__":
    main()
