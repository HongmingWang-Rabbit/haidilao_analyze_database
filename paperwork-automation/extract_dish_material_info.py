#!/usr/bin/env python3
"""
Extract Dish Material Information

This script extracts 出品分量(kg), 损耗, and 物料单位 data from the calculated dish material usage file.
"""

import pandas as pd
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_dish_material_info():
    """Extract dish material information from calculated usage file"""
    
    file_path = "Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx"
    
    try:
        # Read the Excel file
        print(f"Reading file: {file_path}")
        
        # Check all sheets in the file
        xl_file = pd.ExcelFile(file_path)
        print(f"\nSheets in file: {xl_file.sheet_names}")
        
        # Try each sheet to find the data
        for sheet_name in xl_file.sheet_names:
            print(f"\n{'='*60}")
            print(f"Sheet: {sheet_name}")
            print('='*60)
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"Shape: {df.shape}")
                print(f"Columns: {list(df.columns)}")
                
                # Show first few rows
                if len(df) > 0:
                    print("\nFirst 5 rows:")
                    print(df.head())
                
                # Check for target columns
                target_columns = ['出品分量(kg)', '损耗', '物料单位', '标准数量', '标准单位', '损耗率']
                found_columns = [col for col in df.columns if any(target in col for target in target_columns)]
                
                if found_columns:
                    print(f"\nFound relevant columns: {found_columns}")
                    
                    # If this looks like the right sheet, extract the data
                    if '菜品' in str(df.columns) or 'dish' in str(df.columns).lower():
                        print("\nThis appears to be a dish-material mapping sheet!")
                        
                        # Save the extracted data
                        output_file = "extracted_dish_material_info.csv"
                        df.to_csv(output_file, index=False, encoding='utf-8-sig')
                        print(f"\nData saved to: {output_file}")
                        
                        # Show summary statistics
                        print("\nSummary:")
                        print(f"Total rows: {len(df)}")
                        if '出品分量(kg)' in df.columns:
                            print(f"Unique 出品分量 values: {df['出品分量(kg)'].nunique()}")
                        if '损耗' in df.columns:
                            print(f"Unique 损耗 values: {df['损耗'].nunique()}")
                        if '物料单位' in df.columns:
                            print(f"Unique 物料单位 values: {df['物料单位'].nunique()}")
                            
            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {e}")
                
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    extract_dish_material_info()