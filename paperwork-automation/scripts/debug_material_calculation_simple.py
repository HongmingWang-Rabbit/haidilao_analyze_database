#!/usr/bin/env python3
"""
Simple Debug Script for Material Calculation Issue

This script examines the Excel file structure for dish 90000413 (冬阴功锅底)
to understand the sales data that should be used in the calculation.
"""

import pandas as pd
from pathlib import Path


def examine_excel_data():
    """Examine the Excel file structure for dish 90000413"""
    # Path to the May 2025 dish sales file
    project_root = Path(__file__).parent.parent
    excel_path = project_root / "history_files" / "monthly_report_inputs" / \
        "2025-05" / "monthly_dish_sale" / "海外菜品销售报表_20250706_0957.xlsx"

    if not excel_path.exists():
        print(f"❌ Excel file not found: {excel_path}")
        # Try alternative path based on user's input path
        excel_path = project_root / "Input" / "monthly_report" / \
            "monthly_dish_sale" / "海外菜品销售报表_20250706_0957.xlsx"
        if not excel_path.exists():
            print(f"❌ Alternative path also not found: {excel_path}")
            return

    print(f"📊 Examining Excel file: {excel_path.name}")

    try:
        # Read Excel file with a reasonable limit
        df = pd.read_excel(excel_path, engine='openpyxl', nrows=2000)
        print(f"📋 Total rows loaded: {len(df)}")
        print(f"📋 Total columns: {len(df.columns)}")

        # Show first few columns for understanding
        print(f"\n📋 First 10 columns: {list(df.columns[:10])}")

        # Find columns related to dish identification
        dish_code_cols = [col for col in df.columns if '编码' in str(col)]
        dish_name_cols = [col for col in df.columns if '名称' in str(col)]

        print(f"\n🔍 Dish code columns: {dish_code_cols}")
        print(f"🔍 Dish name columns: {dish_name_cols}")

        if not dish_code_cols:
            print("❌ No dish code columns found")
            return

        dish_code_col = dish_code_cols[0]
        print(f"\n🎯 Using dish code column: {dish_code_col}")

        # Convert to string and clean .0 suffix that pandas adds
        df[dish_code_col] = df[dish_code_col].astype(
            str).str.replace('.0', '', regex=False)

        # Find our target dish: 冬阴功锅底 (code 90000413)
        target_dish_rows = df[df[dish_code_col] == '90000413'].copy()

        if target_dish_rows.empty:
            print("❌ Dish 90000413 not found in Excel file")

            # Show some sample dish codes for debugging
            print("\n📋 Sample dish codes in file (first 20):")
            sample_codes = df[dish_code_col].dropna().head(20).tolist()
            for i, code in enumerate(sample_codes):
                print(f"  {i+1:2d}. {code}")

            # Try searching for similar codes
            similar_codes = df[df[dish_code_col].str.contains(
                '90000', na=False)][dish_code_col].unique()
            if len(similar_codes) > 0:
                print(
                    f"\n🔍 Found similar codes starting with '90000': {similar_codes[:10]}")

            # Try searching for 冬阴功 in dish names
            if dish_name_cols:
                dish_name_col = dish_name_cols[0]
                winter_dishes = df[df[dish_name_col].str.contains(
                    '冬阴功', na=False)]
                if not winter_dishes.empty:
                    print(f"\n🔍 Found dishes containing '冬阴功':")
                    for idx, row in winter_dishes.iterrows():
                        print(
                            f"  Code: {row[dish_code_col]}, Name: {row[dish_name_col]}")

            return

        print(
            f"\n✅ Found {len(target_dish_rows)} records for dish 90000413 (冬阴功锅底)")

        # Look for columns that might contain size/specification info
        spec_cols = [col for col in df.columns if any(keyword in str(col) for keyword in
                                                      ['规格', '大小', '尺寸', '单锅', '拼锅', '四宫格', '小份', '大份', '中份'])]

        print(f"\n📏 Specification/size related columns: {spec_cols}")

        # Look for quantity columns
        qty_cols = [col for col in df.columns if any(keyword in str(col) for keyword in
                                                     ['数量', '份数', '销售数', '销量', '出品', '销售', '退菜'])]

        print(f"\n📊 Quantity related columns: {qty_cols}")

        # Show the actual data for our target dish
        print(f"\n📋 Data for dish 90000413 (冬阴功锅底):")
        print("="*80)

        for idx, row in target_dish_rows.iterrows():
            print(f"\nRow {idx}:")
            for col in target_dish_rows.columns:
                value = row[col]
                if pd.notna(value) and value != 0 and value != '':
                    print(f"  {col:30s}: {value}")

        # Look for size-specific sales data
        print(f"\n🧮 LOOKING FOR SIZE-SPECIFIC SALES DATA:")
        print("="*80)

        size_keywords = ['单锅', '拼锅', '四宫格']
        size_data = {}

        for size in size_keywords:
            # Look for columns that might contain this size data
            size_cols = [col for col in df.columns if size in str(col)]
            if size_cols:
                print(f"\n📏 Columns for {size}: {size_cols}")
                for col in size_cols:
                    values = target_dish_rows[col].tolist()
                    non_zero_values = [
                        v for v in values if pd.notna(v) and v != 0]
                    if non_zero_values:
                        print(f"  {col}: {non_zero_values}")
                        # Calculate expected quantities
                        total_qty = sum(non_zero_values)
                        size_data[size] = total_qty

        # Manual calculation based on user's expected numbers
        print(f"\n🎯 EXPECTED CALCULATION (from user's manual calculation):")
        print("="*80)

        expected_sizes = {
            '单锅': 1,
            '拼锅': 231,  # 231+2-2 = 231
            '四宫格': 446  # 448+2-4 = 446
        }

        expected_standard_qty = {
            '单锅': 0.6,
            '拼锅': 0.3,
            '四宫格': 0.15
        }

        expected_unit_conversion = 3.0

        total_material_usage = 0
        print("Expected material usage calculation:")

        for size, qty in expected_sizes.items():
            std_qty = expected_standard_qty[size]
            usage = qty * std_qty
            total_material_usage += usage
            print(f"  {size:8s}: {qty:3d} × {std_qty:4.2f} = {usage:6.2f}")

        final_usage = total_material_usage / expected_unit_conversion
        print(f"\nTotal before conversion: {total_material_usage:6.2f}")
        print(
            f"After unit conversion (÷{expected_unit_conversion}): {final_usage:6.2f}")
        print(f"Expected result: 45.6")
        print(f"Current system shows: 101.7")

        # Show what data we actually found in Excel
        if size_data:
            print(f"\n📊 ACTUAL DATA FOUND IN EXCEL:")
            print("="*40)
            for size, qty in size_data.items():
                print(f"  {size}: {qty}")
        else:
            print(f"\n⚠️  No size-specific data found in Excel columns")
            print("The issue might be in how the data is structured or extracted")

    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main diagnostic function"""
    print("🔍 SIMPLE MATERIAL CALCULATION DIAGNOSIS")
    print("="*60)
    print("Target: Dish 90000413 (冬阴功锅底) - Material 4505163 (冬阴功酱)")
    print("="*60)

    examine_excel_data()


if __name__ == "__main__":
    main()
