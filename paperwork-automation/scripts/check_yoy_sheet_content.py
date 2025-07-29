#!/usr/bin/env python3
"""
Check the actual content of the YoY/MoM analysis sheet
"""

import pandas as pd
import numpy as np

def check_yoy_sheet():
    """Check what's actually in the YoY/MoM sheet"""
    
    file_path = "output/monthly_gross_margin/毛利相关分析指标-202505.xlsx"
    
    try:
        # Read all sheets to identify which is YoY/MoM
        xl_file = pd.ExcelFile(file_path, engine='openpyxl')
        print(f"Total sheets: {len(xl_file.sheet_names)}")
        
        # Read sheet 6 (index 5) which should be YoY/MoM
        df = pd.read_excel(file_path, sheet_name=5, header=None)
        
        print("Raw sheet content (first 10 rows):")
        for i in range(min(10, len(df))):
            row_data = []
            for j in range(min(10, len(df.columns))):
                cell_value = df.iloc[i, j]
                if pd.isna(cell_value):
                    row_data.append("(empty)")
                else:
                    # Truncate long values
                    str_val = str(cell_value)
                    if len(str_val) > 15:
                        str_val = str_val[:15] + "..."
                    row_data.append(str_val)
            print(f"Row {i}: {row_data}")
        
        # Check for actual data (non-header rows with numbers)
        print(f"\nSheet shape: {df.shape}")
        
        # Count rows with numeric data (likely actual data vs headers)
        numeric_rows = 0
        for i in range(len(df)):
            has_numbers = False
            for j in range(len(df.columns)):
                cell_value = df.iloc[i, j]
                if pd.notna(cell_value) and isinstance(cell_value, (int, float)) and cell_value != 0:
                    has_numbers = True
                    break
            if has_numbers:
                numeric_rows += 1
        
        print(f"Rows with numeric data: {numeric_rows}")
        print(f"Assessment: {'HAS DATA' if numeric_rows > 0 else 'EMPTY (headers only)'}")
        
    except Exception as e:
        print(f"Error checking sheet: {e}")

if __name__ == "__main__":
    check_yoy_sheet()