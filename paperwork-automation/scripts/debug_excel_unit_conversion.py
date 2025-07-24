#!/usr/bin/env python3
"""
Debug script to examine Excel file structure and 物料单位 column content.
This helps identify why unit conversion rates are not being extracted properly.
"""

import pandas as pd
import sys
import os
from pathlib import Path


def debug_excel_unit_conversion(file_path: str):
    """Debug Excel file structure and unit conversion data"""
    print("🔍 DEBUGGING EXCEL UNIT CONVERSION EXTRACTION")
    print("=" * 60)
    print(f"File: {file_path}")
    print()

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        # Read Excel file and show structure
        print("1️⃣ EXCEL FILE STRUCTURE")
        print("-" * 40)

        # Get sheet names
        try:
            xl_file = pd.ExcelFile(file_path)
            sheet_names = xl_file.sheet_names
            print(f"Available sheets: {sheet_names}")
        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")
            return False

        # Focus on the '计算' sheet (where dish-material relationships are)
        if '计算' not in sheet_names:
            print("❌ '计算' sheet not found in Excel file")
            print(f"Available sheets: {sheet_names}")
            return False

        print(f"✅ Found '计算' sheet")

        # Read the sheet
        df = pd.read_excel(file_path, sheet_name='计算')
        print(f"Sheet dimensions: {df.shape[0]} rows × {df.shape[1]} columns")

        # Show column names
        print("\n2️⃣ COLUMN NAMES")
        print("-" * 40)
        print("All columns in the sheet:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. {col}")

        # Look for 物料单位 column specifically
        print("\n3️⃣ UNIT CONVERSION COLUMN SEARCH")
        print("-" * 40)

        unit_columns = []
        for col in df.columns:
            if '物料单位' in str(col) or '单位' in str(col):
                unit_columns.append(col)

        if unit_columns:
            print(f"✅ Found unit-related columns: {unit_columns}")

            for col in unit_columns:
                print(f"\nColumn: '{col}'")
                print(f"Data type: {df[col].dtype}")
                print(f"Non-null values: {df[col].notna().sum()}/{len(df)}")

                # Show sample values
                sample_values = df[col].dropna().head(10).tolist()
                print(f"Sample values: {sample_values}")

                # Check if values are numeric
                numeric_values = []
                text_values = []

                for val in sample_values:
                    try:
                        float_val = float(val)
                        numeric_values.append(float_val)
                    except (ValueError, TypeError):
                        text_values.append(val)

                print(f"Numeric values: {numeric_values}")
                print(f"Text values: {text_values}")

                # Check for the expected 0.354 value
                if 0.354 in numeric_values:
                    print("✅ Found expected conversion rate 0.354!")
                elif numeric_values and all(v == 1.0 for v in numeric_values):
                    print("⚠️  All conversion rates are 1.0")
                elif not numeric_values:
                    print("❌ No numeric conversion rates found")
        else:
            print("❌ No unit-related columns found")
            print("💡 The Excel file might not have a '物料单位' column")

        # Look for dish 1060062 and material 1500882 specifically
        print("\n4️⃣ SPECIFIC EXAMPLE SEARCH")
        print("-" * 40)

        # Check if we have the required columns
        dish_code_col = None
        material_number_col = None

        for col in df.columns:
            if '菜品编码' in str(col):
                dish_code_col = col
            elif '物料号' in str(col) or '物料' in str(col):
                material_number_col = col

        if dish_code_col and material_number_col:
            print(f"Dish code column: '{dish_code_col}'")
            print(f"Material number column: '{material_number_col}'")

            # Look for the specific example
            # Convert to string for comparison
            df_search = df.copy()
            df_search[dish_code_col] = df_search[dish_code_col].astype(
                str).str.replace('.0', '')
            df_search[material_number_col] = df_search[material_number_col].astype(
                str).str.replace('.0', '').str.lstrip('0')

            example_rows = df_search[
                (df_search[dish_code_col] == '1060062') &
                (df_search[material_number_col] == '1500882')
            ]

            if not example_rows.empty:
                print("✅ Found example relationship (dish 1060062 + material 1500882):")

                for unit_col in unit_columns:
                    if unit_col in example_rows.columns:
                        value = example_rows[unit_col].iloc[0]
                        print(f"   {unit_col}: {value}")

                        if pd.notna(value):
                            try:
                                float_val = float(value)
                                print(f"   → Numeric value: {float_val}")
                                if float_val == 0.354:
                                    print("   ✅ Correct conversion rate found!")
                                else:
                                    print(
                                        f"   ⚠️  Expected 0.354, found {float_val}")
                            except (ValueError, TypeError):
                                print(f"   ❌ Cannot convert to float: {value}")
                        else:
                            print("   ❌ Value is null/empty")
            else:
                print("❌ Example relationship not found in Excel")
                print("💡 Check if the data exists in the file")
        else:
            print("❌ Missing required columns for dish code or material number")

        # Show extraction simulation
        print("\n5️⃣ EXTRACTION SIMULATION")
        print("-" * 40)

        if unit_columns:
            print("Simulating extraction logic:")

            # Simulate the extraction logic from the automation script
            extracted_rates = []

            for index, row in df.head(5).iterrows():
                unit_conversion_rate = 1.0  # Default

                # Look for unit conversion rate in "物料单位" column
                for col_name in df.columns:
                    if '物料单位' in str(col_name):
                        if pd.notna(row[col_name]):
                            try:
                                unit_conversion_rate = float(row[col_name])
                                if unit_conversion_rate <= 0:
                                    unit_conversion_rate = 1.0
                                break
                            except (ValueError, TypeError):
                                unit_conversion_rate = 1.0

                extracted_rates.append(unit_conversion_rate)
                print(f"Row {index+1}: {unit_conversion_rate}")

            unique_rates = set(extracted_rates)
            print(f"Unique extracted rates: {unique_rates}")

            if len(unique_rates) == 1 and 1.0 in unique_rates:
                print("⚠️  All rates extracted as 1.0 (default)")
                print("💡 The 物料单位 column might be empty or non-numeric")
            else:
                print("✅ Custom conversion rates found")

        print("\n" + "=" * 60)
        print("🎯 DIAGNOSIS:")

        if not unit_columns:
            print("❌ No 物料单位 column found in Excel file")
            print("💡 SOLUTIONS:")
            print("   1. Check if the Excel file has the correct column")
            print("   2. Verify column name spelling")
            print("   3. Update extraction script to look for alternative column names")
        elif all(df[col].isna().all() for col in unit_columns):
            print("❌ 物料单位 columns are empty")
            print("💡 The Excel file structure might be different")
        else:
            print("✅ 物料单位 columns found with data")
            print("💡 Check if extraction script logic is working correctly")

    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """Main function to run the debug"""
    print("🍲 Haidilao Excel Unit Conversion Debug Tool")
    print()

    # Default file path - user can override
    default_file = "Input/monthly_report/calculated_dish_material_usage/material_usage.xls"

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_file
        print(f"Using default file: {file_path}")
        print("(You can specify a different file as command line argument)")
        print()

    if debug_excel_unit_conversion(file_path):
        print("\n✅ Debug completed successfully")
    else:
        print("\n❌ Debug failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
