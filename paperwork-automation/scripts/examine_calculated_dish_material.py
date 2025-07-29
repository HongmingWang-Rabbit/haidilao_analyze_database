#!/usr/bin/env python3
"""
Examine Calculated Dish Material Usage Excel File

This script examines the structure of the calculated dish material usage Excel file
to understand how standard quantities are set for different dish sizes.
"""

import pandas as pd
from pathlib import Path


def examine_calculated_dish_material_file():
    """Examine the calculated dish material usage Excel file structure"""
    project_root = Path(__file__).parent.parent
    excel_path = project_root / "history_files" / "monthly_report_inputs" / \
        "2025-06" / "calculated_dish_material_usage" / "material_usage.xls"

    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        return

    print(f"Examining calculated dish material file: {excel_path.name}")

    try:
        # Read Excel file and check available sheets
        excel_file = pd.ExcelFile(excel_path)
        print(f"Available sheets: {excel_file.sheet_names}")

        # Try to read the '计算' worksheet that the extraction script expects
        if '计算' in excel_file.sheet_names:
            df = pd.read_excel(excel_path, sheet_name='计算', engine='xlrd')
            print(
                f"\nFound '计算' worksheet with {len(df)} rows and {len(df.columns)} columns")
        else:
            # Try the first sheet
            sheet_name = excel_file.sheet_names[0]
            df = pd.read_excel(
                excel_path, sheet_name=sheet_name, engine='xlrd')
            print(
                f"\nUsing first sheet '{sheet_name}' with {len(df)} rows and {len(df.columns)} columns")

        print(f"\nColumns:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. {col}")

        # Look for columns that might contain dish codes, sizes, and standard quantities
        dish_code_cols = [col for col in df.columns if '编码' in str(col)]
        size_cols = [col for col in df.columns if '规格' in str(col)]
        material_cols = [col for col in df.columns if '物料' in str(col)]
        quantity_cols = [col for col in df.columns if any(
            keyword in str(col) for keyword in ['用量', '分量', '重量', '数量'])]

        print(f"\nKey columns identified:")
        print(f"  Dish code columns: {dish_code_cols}")
        print(f"  Size/spec columns: {size_cols}")
        print(f"  Material columns: {material_cols}")
        print(f"  Quantity columns: {quantity_cols}")

        # Look for our target dish 90000413 and material 4505163
        if dish_code_cols:
            dish_code_col = dish_code_cols[0]
            print(
                f"\nSearching for dish 90000413 using column: {dish_code_col}")

            # Convert to string and clean
            df[dish_code_col] = df[dish_code_col].astype(
                str).str.replace('.0', '', regex=False)

            # Find target dish
            target_dish_rows = df[df[dish_code_col] == '90000413'].copy()

            if not target_dish_rows.empty:
                print(
                    f"SUCCESS: Found {len(target_dish_rows)} records for dish 90000413:")

                # Show the data
                for idx, row in target_dish_rows.iterrows():
                    print(f"\nRow {idx}:")
                    for col in df.columns:
                        value = row[col]
                        if pd.notna(value) and value != '' and value != 0:
                            print(f"  {col:30s}: {value}")

            else:
                print("ERROR: Dish 90000413 not found in file")

                # Show some sample dish codes
                print("\nSample dish codes in file:")
                sample_codes = df[dish_code_col].dropna().head(20).tolist()
                for code in sample_codes:
                    print(f"  {code}")

        # Look for our target material 4505163
        if material_cols:
            for material_col in material_cols:
                if '号' in material_col:  # Look for material number column
                    print(
                        f"\nSearching for material 4505163 using column: {material_col}")

                    # Convert to string and clean
                    df[material_col] = df[material_col].astype(
                        str).str.replace('.0', '', regex=False)

                    # Find target material
                    target_material_rows = df[df[material_col]
                                              == '4505163'].copy()

                    if not target_material_rows.empty:
                        print(
                            f"SUCCESS: Found {len(target_material_rows)} records for material 4505163:")

                        # Show the data
                        for idx, row in target_material_rows.iterrows():
                            print(f"\nRow {idx}:")
                            for col in df.columns:
                                value = row[col]
                                if pd.notna(value) and value != '' and value != 0:
                                    print(f"  {col:30s}: {value}")
                        break
                    else:
                        print("ERROR: Material 4505163 not found in this column")

        # Check for dish 90000413 AND material 4505163 combinations
        if dish_code_cols and material_cols:
            dish_code_col = dish_code_cols[0]
            material_col = None
            for col in material_cols:
                if '号' in col:
                    material_col = col
                    break

            if material_col:
                print(
                    f"\nSearching for dish 90000413 + material 4505163 combinations:")

                # Clean both columns
                df[dish_code_col] = df[dish_code_col].astype(
                    str).str.replace('.0', '', regex=False)
                df[material_col] = df[material_col].astype(
                    str).str.replace('.0', '', regex=False)

                # Find combinations
                combination_rows = df[
                    (df[dish_code_col] == '90000413') &
                    (df[material_col] == '4505163')
                ].copy()

                if not combination_rows.empty:
                    print(
                        f"SUCCESS: Found {len(combination_rows)} combinations of dish 90000413 + material 4505163:")

                    for idx, row in combination_rows.iterrows():
                        print(f"\nCombination {idx}:")

                        # Focus on key columns
                        key_info = {}
                        for col in df.columns:
                            value = row[col]
                            if pd.notna(value) and value != '' and value != 0:
                                key_info[col] = value

                        # Show important columns first
                        priority_keys = ['菜品编码', '规格', '物料号',
                                         '出品分量', '出品分量(kg)', '标准用量', '物料单位', '损耗']

                        for key in priority_keys:
                            if key in key_info:
                                print(f"  {key:30s}: {key_info[key]}")

                        # Show other columns
                        for key, value in key_info.items():
                            if key not in priority_keys:
                                print(f"  {key:30s}: {value}")
                else:
                    print("ERROR: No combinations found")

        # Show data sample for understanding structure
        print(f"\nSample data (first 5 rows):")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(df.head().to_string())

    except Exception as e:
        print(f"ERROR reading Excel file: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    print("EXAMINING CALCULATED DISH MATERIAL USAGE FILE")
    print("="*60)

    examine_calculated_dish_material_file()


if __name__ == "__main__":
    main()
