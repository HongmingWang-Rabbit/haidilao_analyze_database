#!/usr/bin/env python3
"""
Check the column structure of the material cost changes sheet
"""

import pandas as pd
import os

def check_column_structure():
    """Check column structure and find cost impact column"""
    
    file_path = "output/monthly_gross_margin/毛利相关分析指标-202505.xlsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        # Read the material cost changes sheet (index 1)
        df = pd.read_excel(file_path, sheet_name=1, header=None)
        
        print("Material Cost Changes Sheet Column Structure:")
        
        # Show first few rows to understand structure
        print("First 3 rows (headers):")
        for i in range(min(3, len(df))):
            row_data = []
            for j in range(min(15, len(df.columns))):  # Show first 15 columns
                cell_value = df.iloc[i, j]
                if pd.notna(cell_value):
                    row_data.append(f"Col{j}: '{cell_value}'")
                else:
                    row_data.append(f"Col{j}: Empty")
            print(f"  Row {i}: {', '.join(row_data[:8])}")  # Show first 8 columns
            if len(row_data) > 8:
                print(f"         {', '.join(row_data[8:])}")
        
        # Look for cost impact column (成本影响金额)
        cost_impact_col = None
        for i in range(min(3, len(df))):
            for j in range(len(df.columns)):
                cell_value = df.iloc[i, j]
                if pd.notna(cell_value) and '成本影响金额' in str(cell_value):
                    cost_impact_col = j
                    print(f"\nFound '成本影响金额' in Row {i}, Column {j}")
                    break
            if cost_impact_col is not None:
                break
        
        if cost_impact_col is not None:
            # Show some actual cost impact values
            print(f"\nSample Cost Impact Values (Column {cost_impact_col}):")
            data_start = 2  # Skip header rows
            for i in range(data_start, min(data_start + 5, len(df))):
                material = df.iloc[i, 1] if len(df.columns) > 1 else 'Unknown'
                cost_impact = df.iloc[i, cost_impact_col]
                print(f"  Row {i}, Material {material}: {cost_impact}")
        else:
            print("\n'成本影响金额' column not found in headers")
            
    except Exception as e:
        print(f"Error checking column structure: {e}")
        return False

if __name__ == "__main__":
    check_column_structure()