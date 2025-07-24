#!/usr/bin/env python3
"""
Check standard quantities for dish 01060066 in Excel file.
"""

import pandas as pd
import sys
import os


def check_excel_standard_quantities():
    """Check standard quantities for dish 01060066"""
    print("🔍 CHECKING EXCEL STANDARD QUANTITIES FOR DISH 01060066")
    print("=" * 70)

    excel_file = "Input/monthly_report/calculated_dish_material_usage/material_usage.xls"

    try:
        # Read Excel file
        df = pd.read_excel(excel_file, sheet_name='计算')
        print(f"✅ Loaded Excel file: {excel_file}")
        print(
            f"📊 Sheet dimensions: {df.shape[0]} rows × {df.shape[1]} columns")

        # Show all column names again
        print("\n📋 ALL COLUMN NAMES:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. '{col}'")

        # Look for dish 01060066 or 1060066
        print("\n🔍 SEARCHING FOR DISH 01060066...")

        # Try different ways to find the dish
        dish_found = False

        # Check different dish code formats
        for dish_code_format in ['01060066', '1060066', 1060066]:
            if '菜品编码' in df.columns:
                # Convert column to string and remove .0 suffix
                df_search = df.copy()
                df_search['菜品编码'] = df_search['菜品编码'].astype(
                    str).str.replace('.0', '')

                matches = df_search[df_search['菜品编码'] == str(dish_code_format)]

                if not matches.empty:
                    dish_found = True
                    print(
                        f"✅ Found {len(matches)} rows for dish code '{dish_code_format}':")

                    for index, row in matches.iterrows():
                        print(f"\n   Row {index + 1}:")
                        print(f"   菜品编码: {row['菜品编码']}")
                        print(f"   菜品名称: {row['菜品名称']}")
                        print(f"   规格: {row['规格']}")

                        # Check for standard quantity columns
                        print(f"   📊 STANDARD QUANTITY SEARCH:")
                        standard_qty_found = False

                        # Look for standard quantity in potential columns
                        for col_name in ['标准用量', '出品分量', '出品分量(kg)', '菜品用量', '物料用量']:
                            if col_name in df.columns:
                                value = row[col_name] if pd.notna(
                                    row[col_name]) else 'NULL'
                                print(f"     {col_name}: {value}")
                                if pd.notna(row[col_name]) and value != 'NULL':
                                    standard_qty_found = True

                        if not standard_qty_found:
                            print(f"     ❌ No standard quantity found!")

                        # Check for other relevant data
                        print(f"   🔍 OTHER DATA:")

                        # Material info
                        if '物料号' in df.columns:
                            material_num = row['物料号'] if pd.notna(
                                row['物料号']) else 'NULL'
                            print(f"     物料号: {material_num}")

                        if '物料描述' in df.columns:
                            material_desc = row['物料描述'] if pd.notna(
                                row['物料描述']) else 'NULL'
                            print(f"     物料描述: {material_desc}")

                        # Unit conversion rate
                        if '物料单位' in df.columns:
                            unit_conv = row['物料单位'] if pd.notna(
                                row['物料单位']) else 'NULL'
                            print(f"     物料单位 (conversion): {unit_conv}")

                        # Loss rate
                        if '损耗' in df.columns:
                            loss = row['损耗'] if pd.notna(row['损耗']) else 'NULL'
                            print(f"     损耗: {loss}")

                    break

        if not dish_found:
            print("❌ Dish 01060066 not found in Excel file")
            print("💡 Available dish codes (first 10):")
            if '菜品编码' in df.columns:
                df_codes = df.copy()
                df_codes['菜品编码'] = df_codes['菜品编码'].astype(
                    str).str.replace('.0', '')
                unique_codes = df_codes['菜品编码'].unique()[:10]
                for code in unique_codes:
                    print(f"     {code}")

        # Check if any standard quantity columns exist at all
        print("\n📋 STANDARD QUANTITY COLUMN ANALYSIS:")
        std_qty_columns = ['标准用量', '出品分量', '出品分量(kg)', '菜品用量', '物料用量']

        for col in std_qty_columns:
            if col in df.columns:
                non_null_count = df[col].notna().sum()
                unique_values = df[col].dropna().unique()[
                    :5]  # First 5 unique values
                print(
                    f"✅ Column '{col}': {non_null_count}/{len(df)} non-null values")
                print(f"   Sample values: {list(unique_values)}")
            else:
                print(f"❌ Column '{col}': NOT FOUND")

        # Summary
        print("\n" + "=" * 70)
        print("🎯 DIAGNOSIS:")

        if dish_found:
            print("✅ Dish 01060066 found in Excel")
            print("💡 Check if standard quantities are in a different column")
            print("💡 The issue might be column name matching in extraction script")
        else:
            print("❌ Dish 01060066 not found in Excel")
            print("💡 Check if this dish is in a different Excel file")

        print("\n🔧 EXTRACTION SCRIPT ISSUE:")
        print("The extraction script looks for these columns:")
        for col in std_qty_columns:
            status = "✅ FOUND" if col in df.columns else "❌ MISSING"
            print(f"   '{col}': {status}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    print("🍲 Haidilao Excel Standard Quantity Checker")
    print()

    if check_excel_standard_quantities():
        print("\n✅ Check completed")
    else:
        print("\n❌ Check failed")
        sys.exit(1)
