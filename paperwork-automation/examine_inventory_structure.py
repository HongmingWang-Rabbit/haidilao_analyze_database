#!/usr/bin/env python3
"""
Examine Inventory Structure

This script examines the structure of inventory checking result files to understand
where to find 出品分量(kg), 损耗, and 物料单位 data.
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def examine_inventory_files():
    """Examine the structure of inventory checking result files"""
    
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
                # Try reading with different engines
                try:
                    # Try xlrd for .xls files
                    if file_path.suffix == '.xls':
                        df = pd.read_excel(file_path, engine='xlrd')
                    else:
                        df = pd.read_excel(file_path, engine='openpyxl')
                except:
                    # Fallback to openpyxl
                    df = pd.read_excel(file_path, engine='openpyxl')
                
                print(f"Shape: {df.shape}")
                print(f"\nColumns: {list(df.columns)}")
                
                # Show first few rows
                print("\nFirst 5 rows:")
                print(df.head())
                
                # Check if specific columns exist
                target_columns = ['出品分量(kg)', '损耗', '物料单位']
                found_columns = [col for col in target_columns if col in df.columns]
                
                if found_columns:
                    print(f"\nFound target columns: {found_columns}")
                    # Show sample data from these columns
                    print(df[found_columns].head())
                else:
                    print("\nTarget columns not found in main sheet")
                    
                    # Check all sheets
                    xl_file = pd.ExcelFile(file_path)
                    if len(xl_file.sheet_names) > 1:
                        print(f"\nMultiple sheets found: {xl_file.sheet_names}")
                        
                        for sheet_name in xl_file.sheet_names[:3]:  # Check first 3 sheets
                            print(f"\n--- Sheet: {sheet_name} ---")
                            try:
                                sheet_df = pd.read_excel(file_path, sheet_name=sheet_name)
                                print(f"Columns: {list(sheet_df.columns)[:10]}...")  # First 10 columns
                                
                                # Check for target columns
                                sheet_found = [col for col in target_columns if col in sheet_df.columns]
                                if sheet_found:
                                    print(f"Found in this sheet: {sheet_found}")
                            except Exception as e:
                                print(f"Error reading sheet: {e}")
                                
            except Exception as e:
                print(f"Error reading file: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    examine_inventory_files()