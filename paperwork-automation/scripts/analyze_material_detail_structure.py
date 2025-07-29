#!/usr/bin/env python3
"""
Analyze material detail files to understand proper material information structure
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_material_detail_structure():
    """Analyze material detail file structure for proper material info"""
    
    print("ANALYZING MATERIAL DETAIL FILE STRUCTURE")
    print("=" * 50)
    
    # Test file
    test_file = Path("history_files/monthly_report_inputs/2025-05/material_detail/1/ca01-202505.XLSX")
    
    if not test_file.exists():
        print(f"File not found: {test_file}")
        return False
    
    print(f"File: {test_file}")
    print(f"Size: {test_file.stat().st_size} bytes")
    
    try:
        # Read Excel file
        df = pd.read_excel(test_file, engine='openpyxl', nrows=10)
        
        print(f"\nShape: {df.shape}")
        print(f"Columns ({len(df.columns)}):")
        
        # Print column analysis
        for i, col in enumerate(df.columns):
            col_str = str(col)
            # Get first few non-null values
            sample_values = df[col].dropna().head(3).tolist()
            print(f"  {i+1:2d}. Column: {col_str[:30]}...")
            print(f"      Sample: {sample_values}")
        
        # Look for specific material information columns
        print(f"\nKEY MATERIAL COLUMNS:")
        print("-" * 30)
        
        material_number_col = None
        material_name_col = None
        unit_col = None
        spec_col = None
        
        for col in df.columns:
            col_str = str(col).lower()
            if '物料' in col_str and ('号' in col_str or 'number' in col_str):
                material_number_col = col
            elif '物料' in col_str and ('名' in col_str or 'name' in col_str or '描述' in col_str):
                material_name_col = col
            elif '单位' in col_str or 'unit' in col_str:
                unit_col = col
            elif '规格' in col_str or 'spec' in col_str:
                spec_col = col
        
        if material_number_col:
            print(f"Material Number: {material_number_col}")
            print(f"  Sample: {df[material_number_col].dropna().head(3).tolist()}")
        
        if material_name_col:
            print(f"Material Name: {material_name_col}")
            print(f"  Sample: {df[material_name_col].dropna().head(3).tolist()}")
        
        if unit_col:
            print(f"Unit: {unit_col}")
            print(f"  Sample: {df[unit_col].dropna().head(3).tolist()}")
        
        if spec_col:
            print(f"Specification: {spec_col}")
            print(f"  Sample: {df[spec_col].dropna().head(3).tolist()}")
        
        # Show complete sample record
        print(f"\nSAMPLE COMPLETE RECORD:")
        print("-" * 30)
        
        if len(df) > 0:
            row = df.iloc[0]
            for col in df.columns:
                value = row[col]
                if pd.notna(value) and str(value).strip() != '':
                    # Show first 50 chars to avoid long strings
                    value_str = str(value)[:50]
                    print(f"  {str(col)[:25]:25s}: {value_str}")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_material_detail_structure()