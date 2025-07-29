#!/usr/bin/env python3
"""
Analyze the generated Excel report to see what data is actually present.
"""

import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_excel_file(file_path):
    """Analyze Excel file contents sheet by sheet."""
    print("Analyzing Excel file...")
    print("=" * 80)
    
    try:
        # Read all sheets
        xl_file = pd.ExcelFile(file_path)
        print(f"Found {len(xl_file.sheet_names)} sheets:")
        
        for sheet_name in xl_file.sheet_names:
            print(f"\nSheet: {sheet_name}")
            print("-" * 40)
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"   Size: {df.shape[0]} rows × {df.shape[1]} columns")
                
                if df.empty:
                    print("   Sheet is EMPTY")
                else:
                    print(f"   Has data:")
                    print(f"      Columns: {list(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
                    
                    # Show sample data
                    non_empty_rows = df.dropna(how='all').shape[0]
                    print(f"      Non-empty rows: {non_empty_rows}")
                    
                    if non_empty_rows > 0:
                        print("      Sample data (first 3 rows):")
                        sample = df.head(3)
                        for idx, row in sample.iterrows():
                            row_data = [str(val)[:20] + '...' if len(str(val)) > 20 else str(val) 
                                       for val in row.values[:3]]
                            print(f"        Row {idx}: {row_data}")
                    
            except Exception as e:
                print(f"   Error reading sheet: {e}")
    
    except Exception as e:
        print(f"Error analyzing file: {e}")

if __name__ == "__main__":
    file_path = "output/monthly_gross_margin/毛利相关分析指标-202505.xlsx"
    analyze_excel_file(file_path)