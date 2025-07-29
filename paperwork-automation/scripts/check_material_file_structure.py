#!/usr/bin/env python3
"""
Check the structure of material files to debug extraction issues
"""

import pandas as pd
import sys
from pathlib import Path

# Fix encoding
import codecs
if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def check_material_files():
    """Check material file structure"""
    
    print("CHECKING MATERIAL FILE STRUCTURE")
    print("=" * 60)
    
    # Check material usage file
    material_usage_file = "history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls"
    
    print(f"\n1. Checking material usage file: {material_usage_file}")
    
    try:
        # Try different engines
        df = None
        try:
            df = pd.read_excel(material_usage_file, engine='xlrd', nrows=10)
            print("   ✅ Read with xlrd engine")
        except:
            try:
                df = pd.read_excel(material_usage_file, engine='openpyxl', nrows=10)
                print("   ✅ Read with openpyxl engine")
            except Exception as e:
                print(f"   ❌ Failed to read: {e}")
                return
        
        if df is not None:
            print(f"\n   Columns found: {list(df.columns)}")
            print(f"   Total columns: {len(df.columns)}")
            print(f"   Shape: {df.shape}")
            
            # Check for material-related columns
            material_cols = [col for col in df.columns if '物料' in str(col)]
            print(f"\n   Material-related columns: {material_cols}")
            
            # Show first few rows
            print("\n   First 5 rows:")
            print(df.head())
            
            # Check total rows without limit
            df_full = pd.read_excel(material_usage_file, engine='xlrd' if material_usage_file.endswith('.xls') else 'openpyxl')
            print(f"\n   Total rows in file: {len(df_full)}")
            
            # Check if materials start after certain row
            for i in range(0, min(1000, len(df_full)), 100):
                sample = df_full.iloc[i:i+5]
                non_empty = sample.dropna(how='all')
                if len(non_empty) > 0:
                    print(f"\n   Rows {i}-{i+5} sample:")
                    print(non_empty.head(2))
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check material price file
    print("\n" + "=" * 60)
    material_price_file = "history_files/monthly_report_inputs/2025-05/material_detail/1/ca01-202505.XLSX"
    
    print(f"\n2. Checking material price file: {material_price_file}")
    
    try:
        df_price = pd.read_excel(material_price_file, nrows=10)
        print(f"\n   Columns found: {list(df_price.columns)}")
        print(f"   Shape: {df_price.shape}")
        
        # Check for price-related columns
        price_cols = [col for col in df_price.columns if '价' in str(col) or '金额' in str(col) or 'price' in str(col).lower()]
        print(f"\n   Price-related columns: {price_cols}")
        
        print("\n   First 5 rows:")
        print(df_price.head())
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    check_material_files()