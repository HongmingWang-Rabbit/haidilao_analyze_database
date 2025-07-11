#!/usr/bin/env python3
"""
Diagnostic script to examine Excel files and understand extraction failures
"""

import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def examine_excel_file(file_path):
    """Examine an Excel file in detail."""
    print(f"\n🔍 EXAMINING FILE: {file_path.name}")
    print("=" * 60)

    try:
        # Read the Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        print(f"📊 Total rows: {len(df)}")
        print(f"📊 Total columns: {len(df.columns)}")

        # Show column names
        print("\n📋 COLUMN NAMES:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. {col}")

        # Show first few rows
        print("\n📄 FIRST 5 ROWS:")
        print(df.head().to_string())

        # Check for specific columns the script looks for
        print("\n🔍 CHECKING FOR EXPECTED COLUMNS:")
        expected_cols = [
            '菜品名称', '菜品名称(门店pad显示名称)', '菜品名称(系统统一名称)',
            '菜品编码', '菜品短编码', '编码',
            '大类名称', '子类名称'
        ]

        found_cols = []
        for col in expected_cols:
            if col in df.columns:
                found_cols.append(col)
                print(f"  ✅ Found: {col}")
            else:
                print(f"  ❌ Missing: {col}")

        if found_cols:
            print(f"\n📊 DATA SAMPLES FROM FOUND COLUMNS:")
            for col in found_cols[:3]:  # Show first 3 found columns
                print(f"\n  Column: {col}")
                sample_data = df[col].dropna().head(10)
                for i, value in enumerate(sample_data):
                    print(f"    Row {i+1}: {value}")

        # Check for store columns (for sales data)
        print("\n🏪 CHECKING FOR STORE COLUMNS:")
        store_patterns = ['店', '门店', '加拿大', '一店',
                          '二店', '三店', '四店', '五店', '六店', '七店']
        store_cols = []
        for col in df.columns:
            if any(pattern in str(col) for pattern in store_patterns):
                store_cols.append(col)
                print(f"  ✅ Found store column: {col}")

        if store_cols:
            print(f"\n📊 STORE COLUMN SAMPLES:")
            for col in store_cols[:3]:  # Show first 3 store columns
                print(f"\n  Column: {col}")
                sample_data = df[col].dropna().head(5)
                for i, value in enumerate(sample_data):
                    print(f"    Row {i+1}: {value}")

        # Check for numeric columns (prices, quantities)
        print("\n💰 CHECKING FOR NUMERIC COLUMNS:")
        numeric_cols = []
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                numeric_cols.append(col)
                print(
                    f"  ✅ Found numeric column: {col} (dtype: {df[col].dtype})")

        return True

    except Exception as e:
        print(f"❌ Error examining file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🔍 EXCEL FILE DIAGNOSTIC TOOL")
    print("=" * 60)

    # Check a few different types of files
    test_files = [
        # 2024-05 dish sales file
        Path("history_files/monthly_report_inputs/2024-05/monthly_dish_sale/海外菜品销售报表_20250706_1147.xlsx"),

        # 2024-05 material usage file
        Path("history_files/monthly_report_inputs/2024-05/monthly_material_usage/202405mb5b.xls"),

        # 2024-05 material detail file (store 1)
        Path("history_files/monthly_report_inputs/2024-05/material_detail/1").glob("*.xlsx"),
    ]

    # Check dish sales file
    dish_file = Path(
        "history_files/monthly_report_inputs/2024-05/monthly_dish_sale/海外菜品销售报表_20250706_1147.xlsx")
    if dish_file.exists():
        examine_excel_file(dish_file)
    else:
        print(f"❌ Dish sales file not found: {dish_file}")

    # Check material usage file
    material_file = Path(
        "history_files/monthly_report_inputs/2024-05/monthly_material_usage/202405mb5b.xls")
    if material_file.exists():
        examine_excel_file(material_file)
    else:
        print(f"❌ Material usage file not found: {material_file}")

    # Check material detail file (any store)
    material_detail_folder = Path(
        "history_files/monthly_report_inputs/2024-05/material_detail/1")
    if material_detail_folder.exists():
        detail_files = list(material_detail_folder.glob("*.xlsx"))
        if detail_files:
            examine_excel_file(detail_files[0])
        else:
            print(f"❌ No Excel files found in: {material_detail_folder}")
    else:
        print(f"❌ Material detail folder not found: {material_detail_folder}")


if __name__ == "__main__":
    main()
