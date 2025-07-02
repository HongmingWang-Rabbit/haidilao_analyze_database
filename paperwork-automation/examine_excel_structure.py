#!/usr/bin/env python3
"""Examine Excel file structures for monthly automation workflow."""

import pandas as pd
from pathlib import Path
import sys


def examine_file(file_path, sheet_name=None, description=""):
    """Examine an Excel file structure."""
    print(f"\n{'='*60}")
    print(f"FILE: {description}")
    print(f"PATH: {file_path}")

    if sheet_name:
        print(f"SHEET: {sheet_name}")

    try:
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5)
        else:
            df = pd.read_excel(file_path, nrows=5)

        print(f"\nCOLUMNS ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")

        print(f"\nFIRST 3 ROWS:")
        print(df.head(3))

        print(f"\nDATA TYPES:")
        print(df.dtypes)

    except Exception as e:
        print(f"ERROR: {e}")


def main():
    """Main function to examine all Excel files."""
    print("EXAMINING MONTHLY REPORT EXCEL FILES")
    print("="*60)

    # Monthly dish sale
    dish_sale_file = "Input/monthly_report/monthly_dish_sale/菜品销售报表2025-07-02_00-23-28.150-e422587dfe992aeaa5f2516b7689a573.xlsx"
    examine_file(dish_sale_file, description="Monthly Dish Sale Report")

    # Material detail
    material_file = "Input/monthly_report/material_detail/export(1).XLSX"
    examine_file(material_file, description="Material Detail Export")

    # Monthly material usage
    material_usage_file = "Input/monthly_report/monthly_material_usage/mb5b202506.xls"
    examine_file(material_usage_file, description="Monthly Material Usage")

    # Calculated dish material usage - 计算 sheet
    calc_file = "Input/monthly_report/calculated_dish_material_usage/CA02-盘点结果-2505-待回复.xls"
    examine_file(calc_file, sheet_name="计算",
                 description="Calculated Dish Material Usage - 计算 Sheet")

    # Inventory checking result - store 7
    inventory_file = "Input/monthly_report/inventory_checking_result/7/CA07-6月-盘点结果 (1).xls"
    examine_file(inventory_file,
                 description="Inventory Checking Result - Store 7")


if __name__ == "__main__":
    main()
