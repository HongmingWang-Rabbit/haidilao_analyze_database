#!/usr/bin/env python3
"""
Debug Material Calculation Issue

This script investigates the discrepancy in material usage calculation for:
- Material: 冬阴功酱（PENTA，3KG*6包/件） (material_number: 4505163)
- Dish: 冬阴功锅底 (dish_code: 90000413)

Expected calculation:
- 单锅: 1 * 0.6 = 0.6
- 拼锅: 231 * 0.3 = 69.3 
- 四宫格: 446 * 0.15 = 66.9
- Total: 136.8 / 3 (unit_conversion_rate) = 45.6

Current result: 101.7 (incorrect)
"""

from utils.database import DatabaseManager, DatabaseConfig
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def examine_excel_data():
    """Examine the Excel file structure for dish 90000413"""
    excel_path = project_root / "history_files" / "monthly_report_inputs" / \
        "2025-05" / "monthly_dish_sale" / "海外菜品销售报表_20250706_0957.xlsx"

    if not excel_path.exists():
        print(f"❌ Excel file not found: {excel_path}")
        return

    print(f"📊 Examining Excel file: {excel_path.name}")

    try:
        # Read Excel file
        df = pd.read_excel(excel_path, engine='openpyxl')
        print(f"📋 Total rows: {len(df)}")
        print(f"📋 Columns: {list(df.columns)}")

        # Find dish 90000413 (冬阴功锅底)
        dish_code_cols = [col for col in df.columns if '编码' in str(col)]
        dish_name_cols = [col for col in df.columns if '名称' in str(col)]

        print(f"\n🔍 Dish code columns: {dish_code_cols}")
        print(f"🔍 Dish name columns: {dish_name_cols}")

        if dish_code_cols:
            dish_code_col = dish_code_cols[0]
            print(f"\n🎯 Using dish code column: {dish_code_col}")

            # Convert to string and clean .0 suffix
            df[dish_code_col] = df[dish_code_col].astype(
                str).str.replace('.0', '', regex=False)

            # Find target dish
            target_dish = df[df[dish_code_col] == '90000413'].copy()

            if not target_dish.empty:
                print(
                    f"\n✅ Found {len(target_dish)} records for dish 90000413:")

                # Display relevant columns
                relevant_cols = [col for col in df.columns if any(keyword in str(col) for keyword in
                                                                  ['编码', '名称', '规格', '销售', '退菜', '大类', '子类', '单锅', '拼锅', '四宫格'])]

                print(f"📋 Relevant columns: {relevant_cols}")

                for col in relevant_cols:
                    if col in target_dish.columns:
                        print(f"{col}: {target_dish[col].tolist()}")

                # Look for quantity columns
                qty_cols = [col for col in df.columns if any(keyword in str(col) for keyword in
                                                             ['数量', '份数', '销售数', '销量', '出品'])]

                print(f"\n📊 Quantity columns: {qty_cols}")

                # Check for size-specific columns
                size_cols = [col for col in df.columns if any(keyword in str(col) for keyword in
                                                              ['单锅', '拼锅', '四宫格', '小份', '大份', '中份'])]

                print(f"📏 Size-specific columns: {size_cols}")

                # Show the actual data for our target dish
                print("\n📋 Target dish data:")
                for idx, row in target_dish.iterrows():
                    print(f"Row {idx}:")
                    for col in target_dish.columns:
                        if not pd.isna(row[col]) and row[col] != 0:
                            print(f"  {col}: {row[col]}")
                    print()

            else:
                print("❌ Dish 90000413 not found in Excel file")

                # Show some sample dish codes for reference
                print("\n📋 Sample dish codes in file:")
                sample_codes = df[dish_code_col].dropna().astype(
                    str).head(20).tolist()
                for code in sample_codes:
                    print(f"  {code}")

    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")


def examine_database_data():
    """Examine the database structure for dish and material relationships"""
    db_manager = DatabaseManager(DatabaseConfig(is_test=False))

    print("\n" + "="*60)
    print("🗄️ EXAMINING DATABASE DATA")
    print("="*60)

    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check dishes with code 90000413
            cursor.execute("""
                SELECT id, full_code, name, size, specification, is_active
                FROM dish
                WHERE full_code = %s
                ORDER BY size
            """, ('90000413',))

            dishes = cursor.fetchall()
            print(f"\n🍽️ Found {len(dishes)} dish records for code 90000413:")

            for dish in dishes:
                print(
                    f"  ID: {dish['id']}, Code: {dish['full_code']}, Name: {dish['name']}, Size: {dish['size']}")

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
                print(
                    f"  ID: {material['id']}, Number: {material['material_number']}, Name: {material['name']}, Unit: {material['unit']}")

            if not materials:
                print("❌ No materials found with number 4505163")
                return

            material_id = materials[0]['id']

            # Check dish-material relationships
            cursor.execute("""
                SELECT dm.*, d.full_code, d.name as dish_name, d.size, m.name as material_name
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id
                JOIN material m ON dm.material_id = m.id
                WHERE d.full_code = %s AND m.material_number = %s
                ORDER BY d.size
            """, ('90000413', '4505163'))

            relationships = cursor.fetchall()
            print(
                f"\n🔗 Found {len(relationships)} dish-material relationships:")

            for rel in relationships:
                print(f"  Dish: {rel['dish_name']} ({rel['size']})")
                print(f"    Standard Quantity: {rel['standard_quantity']}")
                print(f"    Loss Rate: {rel['loss_rate']}")
                print(
                    f"    Unit Conversion Rate: {rel['unit_conversion_rate']}")
                print()

            # Check monthly sales data for May 2025
            cursor.execute("""
                SELECT dms.*, d.full_code, d.name as dish_name, d.size, s.name as store_name
                FROM dish_monthly_sale dms
                JOIN dish d ON dms.dish_id = d.id
                JOIN store s ON dms.store_id = s.id
                WHERE d.full_code = %s AND dms.year = 2025 AND dms.month = 5
                ORDER BY s.id, d.size
            """, ('90000413',))

            sales_data = cursor.fetchall()
            print(
                f"\n📊 Found {len(sales_data)} monthly sales records for May 2025:")

            total_net_sales = 0
            for sale in sales_data:
                net_sales = sale['sale_amount'] - sale['return_amount']
                total_net_sales += net_sales
                print(f"  Store: {sale['store_name']}")
                print(f"    Dish: {sale['dish_name']} ({sale['size']})")
                print(
                    f"    Sale Amount: {sale['sale_amount']}, Return: {sale['return_amount']}, Net: {net_sales}")
                print()

            print(
                f"🔢 Total net sales across all stores and sizes: {total_net_sales}")

            # Calculate theoretical usage manually
            print("\n🧮 MANUAL CALCULATION:")

            theoretical_total = 0
            for rel in relationships:
                dish_size = rel['size']
                standard_qty = float(rel['standard_quantity'] or 0)
                loss_rate = float(rel['loss_rate'] or 1.0)
                unit_conversion = float(rel['unit_conversion_rate'] or 1.0)

                # Find sales for this dish size
                size_sales = [s for s in sales_data if s['size'] == dish_size]
                size_net_sales = sum(
                    s['sale_amount'] - s['return_amount'] for s in size_sales)

                theoretical_usage = size_net_sales * standard_qty * loss_rate / unit_conversion
                theoretical_total += theoretical_usage

                print(f"  {dish_size}: {size_net_sales} sales × {standard_qty} std_qty × {loss_rate} loss ÷ {unit_conversion} conversion = {theoretical_usage:.2f}")

            print(f"\n🎯 Manual calculation total: {theoretical_total:.2f}")

    except Exception as e:
        print(f"❌ Database error: {e}")


def main():
    """Main diagnostic function"""
    print("🔍 DEBUGGING MATERIAL CALCULATION ISSUE")
    print("="*60)

    # Step 1: Examine Excel data
    examine_excel_data()

    # Step 2: Examine database data
    examine_database_data()


if __name__ == "__main__":
    main()
