#!/usr/bin/env python3
"""
Analyze the manual reference file to understand expected data structure
"""

import pandas as pd
import sys
import os

def analyze_manual_file():
    """Analyze the manual reference file"""
    file_path = "data/dishes_related/附件3-毛利相关分析指标-2505.xlsx"
    
    try:
        xl_file = pd.ExcelFile(file_path, engine='openpyxl')
        print(f"Manual Reference File Analysis")
        print("=" * 60)
        print(f"Total sheets: {len(xl_file.sheet_names)}")
        
        for i, sheet_name in enumerate(xl_file.sheet_names):
            print(f"\n--- Sheet {i+1}: {sheet_name} ---")
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"Size: {df.shape[0]} rows x {df.shape[1]} columns")
                
                non_empty_rows = df.dropna(how='all').shape[0]
                print(f"Non-empty rows: {non_empty_rows}")
                
                if non_empty_rows > 0:
                    print(f"Columns: {list(df.columns)}")
                    
                    # Show first few rows of actual data
                    print("Sample data (first 5 non-empty rows):")
                    clean_df = df.dropna(how='all')
                    sample = clean_df.head(5)
                    
                    for idx, row in sample.iterrows():
                        print(f"  Row {idx}: {dict(zip(df.columns, row.values))}")
                        
            except Exception as e:
                print(f"Error reading sheet: {e}")
                
    except Exception as e:
        print(f"Error analyzing manual file: {e}")

if __name__ == "__main__":
    analyze_manual_file()