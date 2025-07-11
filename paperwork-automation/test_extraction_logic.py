#!/usr/bin/env python3
"""
Test script to debug extraction logic
"""

import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_dish_extraction():
    """Test dish extraction logic."""
    print("🔍 TESTING DISH EXTRACTION LOGIC")
    print("=" * 50)

    file_path = Path(
        "history_files/monthly_report_inputs/2024-05/monthly_dish_sale/海外菜品销售报表_20250706_1147.xlsx")

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    try:
        # Read Excel file with limited rows for testing
        df = pd.read_excel(file_path, engine='openpyxl', nrows=100)
        print(f"📊 Loaded {len(df)} rows (limited to 100 for testing)")

        # Find dish name column
        dish_name_col = None
        possible_columns = [
            '菜品名称',
            '菜品名称(门店pad显示名称)',
            '菜品名称(系统统一名称)'
        ]
        for col in possible_columns:
            if col in df.columns:
                dish_name_col = col
                break

        if not dish_name_col:
            print("❌ No dish name column found")
            return

        print(f"✅ Using dish name column: {dish_name_col}")

        # Find dish code column
        dish_code_col = None
        for col in ['菜品编码', '菜品短编码', '编码']:
            if col in df.columns:
                dish_code_col = col
                break

        if not dish_code_col:
            print("❌ No dish code column found")
            return

        print(f"✅ Using dish code column: {dish_code_col}")

        # Clean and validate data
        df_clean = df.copy()
        print(f"📊 Before cleaning: {len(df_clean)} rows")

        # Remove rows where dish name or code is missing/invalid
        df_clean = df_clean.dropna(subset=[dish_name_col, dish_code_col])
        print(f"📊 After removing NaN: {len(df_clean)} rows")

        # Apply the same validation logic as the original script
        def is_valid_dish_row(row):
            try:
                dish_name = str(row[dish_name_col]) if pd.notna(
                    row[dish_name_col]) else ''
                dish_code = str(row[dish_code_col]) if pd.notna(
                    row[dish_code_col]) else ''

                # Skip header rows
                if dish_name in ['菜品名称', '菜品名称(门店pad显示名称)', '菜品名称(系统统一名称)']:
                    return False
                if dish_code in ['菜品编码', '菜品短编码', '编码']:
                    return False

                # Skip empty or very short values
                if len(dish_name.strip()) < 2 or len(dish_code.strip()) < 1:
                    return False

                return True
            except Exception as e:
                print(f"❌ Error validating row: {e}")
                return False

        # Test validation on first 20 rows
        print("\n🔍 TESTING VALIDATION ON FIRST 20 ROWS:")
        for i in range(min(20, len(df_clean))):
            row = df_clean.iloc[i]
            is_valid = is_valid_dish_row(row)
            dish_name = str(row[dish_name_col]) if pd.notna(
                row[dish_name_col]) else 'NaN'
            dish_code = str(row[dish_code_col]) if pd.notna(
                row[dish_code_col]) else 'NaN'

            status = "✅" if is_valid else "❌"
            print(
                f"  Row {i:2d}: {status} {dish_name[:20]:<20} | {dish_code:<15}")

        # Apply filter
        valid_mask = df_clean.apply(is_valid_dish_row, axis=1)
        df_valid = df_clean[valid_mask]
        print(f"\n📊 After validation: {len(df_valid)} valid rows")

        if len(df_valid) > 0:
            print("\n✅ SAMPLE VALID DATA:")
            for i in range(min(5, len(df_valid))):
                row = df_valid.iloc[i]
                dish_name = str(row[dish_name_col])
                dish_code = str(row[dish_code_col])
                print(f"  {dish_name} | {dish_code}")
        else:
            print("\n❌ NO VALID DATA FOUND!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_material_extraction():
    """Test material extraction logic."""
    print("\n🔍 TESTING MATERIAL EXTRACTION LOGIC")
    print("=" * 50)

    file_path = Path(
        "history_files/monthly_report_inputs/2024-05/monthly_material_usage/202405mb5b.xls")

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    try:
        # Try reading with xlrd engine for .xls files
        df = pd.read_excel(file_path, engine='xlrd', nrows=50)
        print(f"📊 Loaded {len(df)} rows (limited to 50 for testing)")
        print(f"📊 Columns: {list(df.columns)}")

        # Check for material columns
        material_cols = ['物料', '物料描述', '物料编码']
        found_cols = [col for col in material_cols if col in df.columns]

        if found_cols:
            print(f"✅ Found material columns: {found_cols}")

            # Show sample data
            print("\n📊 SAMPLE MATERIAL DATA:")
            for col in found_cols[:2]:
                print(f"\n  Column: {col}")
                sample_data = df[col].dropna().head(5)
                for i, value in enumerate(sample_data):
                    print(f"    Row {i+1}: {value}")
        else:
            print("❌ No material columns found")

    except Exception as e:
        print(f"❌ Error reading .xls file: {e}")
        print("💡 Trying with openpyxl engine...")
        try:
            df = pd.read_excel(file_path, engine='openpyxl', nrows=50)
            print(f"📊 Loaded {len(df)} rows with openpyxl")
        except Exception as e2:
            print(f"❌ Also failed with openpyxl: {e2}")


def main():
    print("🧪 EXTRACTION LOGIC TEST")
    print("=" * 60)

    test_dish_extraction()
    test_material_extraction()


if __name__ == "__main__":
    main()
