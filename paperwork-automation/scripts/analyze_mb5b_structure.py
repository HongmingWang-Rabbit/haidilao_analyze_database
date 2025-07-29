#!/usr/bin/env python3
"""
Analyze MB5B file structure to understand available material information
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_mb5b_structure():
    """Analyze the complete structure of MB5B files"""
    
    print("ANALYZING MB5B FILE STRUCTURE")
    print("=" * 40)
    
    # Test file
    test_file = Path("history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls")
    
    if not test_file.exists():
        print(f"File not found: {test_file}")
        return False
    
    print(f"File: {test_file}")
    print(f"Size: {test_file.stat().st_size} bytes")
    
    try:
        # Read as UTF-16 tab-delimited text
        df = pd.read_csv(
            test_file, 
            sep='\t', 
            encoding='utf-16',
            dtype={'物料': str},
            nrows=100  # Read more rows for analysis
        )
        
        print(f"\nShape: {df.shape}")
        print(f"Columns ({len(df.columns)}):")
        
        # Print all columns with sample data (safe for Unicode)
        for i, col in enumerate(df.columns):
            try:
                print(f"  {i+1:2d}. {col}")
            except UnicodeEncodeError:
                print(f"  {i+1:2d}. [Unicode column name {i+1}]")
            
            # Show sample non-null values
            non_null_values = df[col].dropna().unique()[:5]
            if len(non_null_values) > 0:
                try:
                    print(f"      Sample values: {non_null_values}")
                except UnicodeEncodeError:
                    print(f"      Sample values: [Unicode values - {len(non_null_values)} items]")
            else:
                print(f"      Sample values: [All null/empty]")
        
        # Look for material-related columns
        print(f"\nMATERIAL-RELATED COLUMN ANALYSIS:")
        print("-" * 40)
        
        material_info_cols = {}
        
        for col in df.columns:
            col_str = str(col).lower()
            if '物料' in col_str:
                material_info_cols[col] = 'Material number/code'
            elif '描述' in col_str or 'description' in col_str:
                material_info_cols[col] = 'Description'
            elif '名称' in col_str or 'name' in col_str:
                material_info_cols[col] = 'Name'
            elif '单位' in col_str or 'unit' in col_str:
                material_info_cols[col] = 'Unit'
            elif '规格' in col_str or 'spec' in col_str:
                material_info_cols[col] = 'Specification'
            elif '类型' in col_str or 'type' in col_str:
                material_info_cols[col] = 'Type'
            elif '组' in col_str or 'group' in col_str:
                material_info_cols[col] = 'Group'
        
        for col, description in material_info_cols.items():
            try:
                print(f"{col:20s} -> {description}")
                sample_values = df[col].dropna().head(3).tolist()
                print(f"  Sample: {sample_values}")
                print()
            except UnicodeEncodeError:
                print(f"[Unicode column] -> {description}")
                print(f"  Sample: [Unicode values]")
                print()
        
        # Show a few complete sample records
        print(f"\nSAMPLE COMPLETE RECORDS (first 3):")
        print("-" * 50)
        
        for idx in range(min(3, len(df))):
            print(f"\nRecord {idx + 1}:")
            row = df.iloc[idx]
            for col in df.columns:
                value = row[col]
                if pd.notna(value) and str(value).strip() != '':
                    try:
                        print(f"  {col:25s}: {value}")
                    except UnicodeEncodeError:
                        print(f"  [Unicode column]: {value}")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_mb5b_structure()