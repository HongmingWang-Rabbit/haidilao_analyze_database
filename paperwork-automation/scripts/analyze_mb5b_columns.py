#!/usr/bin/env python3
"""
Analyze mb5b file structure to identify correct columns for material usage extraction.
"""

import pandas as pd
import sys
from pathlib import Path

def analyze_mb5b_structure():
    """Analyze the structure of mb5b files to understand column meanings"""
    
    print("=== ANALYZING MB5B FILE STRUCTURE ===\n")
    
    # Test with 2025-05 file
    file_path = "history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls"
    
    try:
        # Read the file
        df = pd.read_csv(file_path, sep='\t', encoding='utf-16')
        print(f"File shape: {df.shape[0]} rows, {df.shape[1]} columns\n")
        
        # Show column information
        print("=== COLUMN INFORMATION ===")
        for i, col_name in enumerate(df.columns):
            # Count non-null, non-zero values
            try:
                col_data = df.iloc[:, i]
                non_null = col_data.notna().sum()
                
                # Try to count numeric non-zero values
                numeric_nonzero = 0
                try:
                    numeric_vals = pd.to_numeric(col_data, errors='coerce')
                    numeric_nonzero = (numeric_vals != 0).sum()
                except:
                    pass
                
                print(f"[{i:2d}] {repr(str(col_name)[:30]):<32} Non-null: {non_null:5d}, Non-zero: {numeric_nonzero:5d}")
                
            except Exception as e:
                print(f"[{i:2d}] Column analysis error: {e}")
        
        # Show sample data for a material we know (1500900)
        print("\n=== SAMPLE DATA FOR MATERIAL 1500900 ===")
        mask = df.astype(str).apply(lambda x: x.str.contains('1500900', na=False)).any(axis=1)
        sample_rows = df[mask].head(2)
        
        if not sample_rows.empty:
            for row_idx, (_, row) in enumerate(sample_rows.iterrows()):
                print(f"\nRow {row_idx} (Material 1500900):")
                for i, val in enumerate(row):
                    if i < 16:  # First 16 columns
                        try:
                            # Clean up the display
                            if pd.isna(val):
                                display_val = "NaN"
                            elif isinstance(val, str):
                                display_val = f"'{val.strip()}'" if val.strip() else "''"
                            else:
                                display_val = str(val)
                            print(f"  [{i:2d}]: {display_val}")
                        except:
                            print(f"  [{i:2d}]: [unprintable]")
        
        # Look for patterns that might indicate usage columns
        print("\n=== IDENTIFYING USAGE COLUMNS ===")
        
        # Check which columns have significant variation (likely usage data)
        numeric_cols = []
        for i in range(df.shape[1]):
            try:
                col_data = pd.to_numeric(df.iloc[:, i], errors='coerce')
                if col_data.notna().sum() > 100:  # Has enough data
                    std_dev = col_data.std()
                    mean_val = col_data.mean()
                    max_val = col_data.max()
                    min_val = col_data.min()
                    
                    if std_dev > 0 and max_val > 100:  # Has variation and significant values
                        numeric_cols.append({
                            'column': i,
                            'mean': mean_val,
                            'std': std_dev,
                            'max': max_val,
                            'min': min_val,
                            'non_zero_count': (col_data != 0).sum()
                        })
            except:
                continue
        
        print("Columns with significant numeric variation (likely usage data):")
        for col_info in sorted(numeric_cols, key=lambda x: x['std'], reverse=True)[:8]:
            print(f"  Column {col_info['column']:2d}: Mean={col_info['mean']:8.2f}, "
                  f"Std={col_info['std']:8.2f}, Max={col_info['max']:8.2f}, "
                  f"NonZero={col_info['non_zero_count']:4d}")
        
        return df, numeric_cols
        
    except Exception as e:
        print(f"Error analyzing mb5b file: {e}")
        import traceback
        traceback.print_exc()
        return None, []

def check_suspicious_materials(df, numeric_cols):
    """Check if materials with database corruption have non-zero values in any columns"""
    
    print("\n=== CHECKING SUSPICIOUS MATERIALS ===")
    
    # Materials we know have wrong database values
    suspicious_materials = ['1500900', '1500968', '1000233']
    
    for material_num in suspicious_materials:
        print(f"\nMaterial {material_num}:")
        
        # Find CA01 row for this material
        mask = (df.astype(str).apply(lambda x: x.str.contains(material_num, na=False)).any(axis=1) & 
                df.astype(str).apply(lambda x: x.str.contains('CA01', na=False)).any(axis=1))
        
        rows = df[mask]
        if not rows.empty:
            row = rows.iloc[0]
            
            # Check the high-variation columns
            print("  Values in high-variation columns:")
            for col_info in numeric_cols[:6]:  # Top 6 columns
                col_idx = col_info['column']
                val = row.iloc[col_idx]
                try:
                    numeric_val = float(val) if pd.notna(val) else 0
                    print(f"    Column {col_idx:2d}: {numeric_val:10.2f}")
                except:
                    print(f"    Column {col_idx:2d}: {repr(val)}")

if __name__ == "__main__":
    df, numeric_cols = analyze_mb5b_structure()
    if df is not None:
        check_suspicious_materials(df, numeric_cols)