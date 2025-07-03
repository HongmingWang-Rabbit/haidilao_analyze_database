#!/usr/bin/env python3
"""Check material_detail Excel file structure and beverage materials"""

import sys
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).parent))


def check_material_detail_structure():
    """Check the structure of material_detail Excel file"""

    excel_file = Path("Input/monthly_report/material_detail/export(1).XLSX")

    if not excel_file.exists():
        print(f"ERROR: File not found: {excel_file}")
        return

    try:
        print("=== CHECKING MATERIAL_DETAIL EXCEL STRUCTURE ===")
        print(f"File: {excel_file}")
        print()

        # Check all sheets first
        print("1. Checking Excel sheets...")
        excel_sheets = pd.ExcelFile(excel_file)
        print(f"   Available sheets: {excel_sheets.sheet_names}")

        # Read Excel file
        print("\n2. Reading Excel file...")
        df = pd.read_excel(excel_file)

        print(f"   Total rows: {len(df)}")
        print(f"   Total columns: {len(df.columns)}")

        # Show sample of material codes
        print(f"\n   Sample material codes from '物料' column:")
        sample_materials = df.iloc[:, 4].dropna().head(10)
        for i, material in enumerate(sample_materials, 1):
            print(f"   {i}. {material} (type: {type(material)})")
        print()

        # Show column names
        print("3. Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        print()

        # Show first few rows
        print("4. First 5 rows:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(df.head())
        print()

        # Check for beverage-related materials
        print("5. Searching for 可口可乐 (Coca Cola):")
        coca_cola = df[df.iloc[:, 5].astype(
            str).str.contains('可口可乐', na=False)]
        if not coca_cola.empty:
            print(f"   Found {len(coca_cola)} rows with 可口可乐:")
            for idx, row in coca_cola.iterrows():
                print(
                    f"   Row {idx + 1}: Material: {row.iloc[4]} - {row.iloc[5]}, 大类: {row.iloc[8]}")
        else:
            print("   No 可口可乐 found")
        print()

        # Check material number 000000000001500902 specifically
        print("6. Searching for material number 000000000001500902:")
        # Check both as string and as float in the "物料" column (column index 4)
        material_1500902 = df[
            (df.iloc[:, 4].astype(str).str.contains('1500902', na=False)) |
            (df.iloc[:, 4].astype(str).str.contains('000000000001500902', na=False)) |
            (df.iloc[:, 4] == 1500902.0)
        ]
        if not material_1500902.empty:
            print(f"   Found material 1500902:")
            for idx, row in material_1500902.iterrows():
                print(f"   Row {idx + 1}:")
                for i, value in enumerate(row):
                    col_name = df.columns[i]
                    print(f"     {col_name}: {value}")
        else:
            print("   Material 1500902 not found")

        # Search more broadly for beverage keywords in material descriptions
        print("\n7. Searching for beverage keywords in material descriptions:")
        beverage_keywords = ['可口可乐', '可乐', '雪碧',
                             '啤酒', '红酒', '白酒', '茶', '咖啡', '果汁', '牛奶']

        for keyword in beverage_keywords:
            # Search in material description column (index 5)
            keyword_matches = df[df.iloc[:, 5].astype(
                str).str.contains(keyword, na=False)]
            if not keyword_matches.empty:
                print(
                    f"   Found {len(keyword_matches)} materials with '{keyword}':")
                for idx, row in keyword_matches.head(3).iterrows():
                    material_code = row.iloc[4]
                    material_desc = row.iloc[5]
                    material_type = row.iloc[8] if len(
                        row) > 8 else "Unknown"  # 大类
                    print(
                        f"   - {material_code}: {material_desc} (大类: {material_type})")
                if len(keyword_matches) > 3:
                    print(f"     ... and {len(keyword_matches) - 3} more")

        # Check what values are in the "大类" column
        print(f"\n8. Unique values in '大类' column:")
        unique_types = df.iloc[:, 8].dropna().unique()
        for utype in sorted(unique_types):
            count = len(df[df.iloc[:, 8] == utype])
            print(f"   - {utype}: {count} materials")

    except Exception as e:
        print(f"ERROR: Failed to check material detail structure: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_material_detail_structure()
