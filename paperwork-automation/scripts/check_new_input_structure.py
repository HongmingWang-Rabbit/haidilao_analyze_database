#!/usr/bin/env python3
"""
Check the structure of the new inventory calculation data file
"""

import pandas as pd
from pathlib import Path

def check_file_structure():
    """Check the structure of the new input file"""
    
    # Find the file
    file_path = Path("Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_20250725_231102.xlsx")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    print(f"Checking file: {file_path}")
    
    # Try to read the file and check if it has sheets
    try:
        # Check if it has multiple sheets
        xl_file = pd.ExcelFile(file_path)
        print(f"\\nSheets found: {xl_file.sheet_names}")
        
        # Read the first sheet (or default sheet)
        df = pd.read_excel(file_path)
        
        print(f"\\nFile structure:")
        print(f"- Total rows: {len(df)}")
        print(f"- Total columns: {len(df.columns)}")
        
        print(f"\\nColumns:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print(f"\\nFirst 3 rows sample:")
        sample_cols = ["门店名称", "菜品编码", "菜品名称", "物料号", "物料描述"]
        available_cols = [col for col in sample_cols if col in df.columns]
        
        if available_cols:
            for idx, row in df[available_cols].head(3).iterrows():
                print(f"\\nRow {idx + 1}:")
                for col in available_cols:
                    try:
                        value = str(row[col])[:30] + "..." if len(str(row[col])) > 30 else str(row[col])
                        print(f"  {col}: {value}")
                    except UnicodeEncodeError:
                        print(f"  {col}: <display error>")
        
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_file_structure()