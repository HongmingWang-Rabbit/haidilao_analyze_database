#!/usr/bin/env python3
"""
Examine Calculation Sheets

This script examines the "计算" sheets in inventory checking result files
to understand the structure and extract dish-material data.
"""

import pandas as pd
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def examine_calculation_sheets():
    """Examine the 计算 sheets in inventory files"""
    
    base_path = Path("Input/monthly_report/inventory_checking_result")
    
    # Check each store's inventory file
    for store_num in range(1, 8):
        store_path = base_path / str(store_num)
        
        # Find the inventory file for this store
        inventory_files = list(store_path.glob("*.xls*"))
        
        if inventory_files:
            file_path = inventory_files[0]
            print(f"\n{'='*60}")
            print(f"Store {store_num}: {file_path.name}")
            print('='*60)
            
            try:
                # Try to read the 计算 sheet
                try:
                    df = pd.read_excel(file_path, sheet_name='计算')
                    print(f"\n计算 sheet found!")
                    print(f"Shape: {df.shape}")
                    print(f"\nColumns: {list(df.columns)}")
                    
                    # Show first few rows
                    print("\nFirst 10 rows:")
                    pd.set_option('display.max_columns', None)
                    pd.set_option('display.width', None)
                    print(df.head(10))
                    
                    # Look for specific columns related to dish-material mapping
                    relevant_cols = []
                    for col in df.columns:
                        if any(keyword in str(col) for keyword in ['菜品', '物料', '出品', '损耗', '单位', '分量', '标准']):
                            relevant_cols.append(col)
                    
                    if relevant_cols:
                        print(f"\nRelevant columns found: {relevant_cols}")
                        # Show sample data from these columns
                        print("\nSample data from relevant columns:")
                        print(df[relevant_cols].head(10))
                    
                    # Check for non-null values in key columns
                    print("\nNon-null value counts:")
                    for col in df.columns:
                        non_null = df[col].notna().sum()
                        if non_null > 0:
                            print(f"  {col}: {non_null} non-null values")
                    
                except Exception as e:
                    print(f"Could not read 计算 sheet: {e}")
                    
                    # List all available sheets
                    xl_file = pd.ExcelFile(file_path)
                    print(f"\nAvailable sheets: {xl_file.sheet_names}")
                    
                    # Look for sheets with similar names
                    calc_sheets = [s for s in xl_file.sheet_names if '计算' in s or 'calc' in s.lower()]
                    if calc_sheets:
                        print(f"Found calculation-related sheets: {calc_sheets}")
                        for sheet in calc_sheets:
                            try:
                                df = pd.read_excel(file_path, sheet_name=sheet)
                                print(f"\n{sheet} - Shape: {df.shape}")
                                print(f"Columns: {list(df.columns)[:10]}...")
                            except:
                                pass
                    
            except Exception as e:
                print(f"Error reading file: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    examine_calculation_sheets()