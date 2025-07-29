#!/usr/bin/env python3
"""
Simple analysis of material files without Unicode display issues
"""

import pandas as pd
from pathlib import Path

def analyze_material_files():
    """Simple analysis avoiding Unicode issues"""
    
    print("MATERIAL FILE ANALYSIS")
    print("=" * 30)
    
    # Test MB5B file
    mb5b_file = Path("history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls")
    print(f"MB5B File: {mb5b_file.exists()}")
    
    if mb5b_file.exists():
        df_mb5b = pd.read_csv(mb5b_file, sep='\t', encoding='utf-16', dtype={'物料': str}, nrows=5)
        print(f"MB5B shape: {df_mb5b.shape}")
        print(f"MB5B has {len(df_mb5b.columns)} columns")
        
        # Show material numbers and units
        for i, col in enumerate(df_mb5b.columns):
            if i == 2:  # Material number column
                print(f"Material numbers: {df_mb5b.iloc[:3, i].tolist()}")
            elif i == 9:  # Unit column  
                print(f"Units: {df_mb5b.iloc[:3, i].tolist()}")
    
    # Test material detail file
    detail_file = Path("history_files/monthly_report_inputs/2025-05/material_detail/1/ca01-202505.XLSX")
    print(f"\nDetail File: {detail_file.exists()}")
    
    if detail_file.exists():
        df_detail = pd.read_excel(detail_file, engine='openpyxl', nrows=5)
        print(f"Detail shape: {df_detail.shape}")
        print(f"Detail has {len(df_detail.columns)} columns")
        
        # Look for key columns by checking sample data
        for i, col in enumerate(df_detail.columns):
            sample_data = df_detail.iloc[:3, i].dropna().tolist()
            if len(sample_data) > 0:
                # Check if looks like material numbers (7-digit numbers)
                if any(str(val).isdigit() and len(str(val)) == 7 for val in sample_data):
                    print(f"Column {i+1} - Material numbers: {sample_data}")
                # Check if looks like material names (Chinese text)
                elif any(len(str(val)) > 10 and not str(val).isdigit() for val in sample_data):
                    print(f"Column {i+1} - Material names: {len(sample_data)} items")
                # Check if looks like units
                elif any(str(val) in ['KG', 'L', 'PCS', 'BOX'] for val in sample_data):
                    print(f"Column {i+1} - Units: {sample_data}")

if __name__ == "__main__":
    analyze_material_files()