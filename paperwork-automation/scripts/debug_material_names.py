#!/usr/bin/env python3
"""
Debug why material names are still generic instead of real names
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def debug_material_names():
    """Debug the material name extraction issue"""
    
    print("DEBUGGING MATERIAL NAME EXTRACTION")
    print("=" * 40)
    
    # First check what's in the database
    print("1. Checking database contents:")
    db_manager = DatabaseManager(DatabaseConfig(is_test=True))
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM material")
        total = cursor.fetchone()['count']
        print(f"   Total materials in DB: {total}")
        
        # Check for generic vs real names
        cursor.execute("SELECT material_number, name FROM material LIMIT 10")
        samples = cursor.fetchall()
        print("   Sample material names:")
        for sample in samples:
            name = sample['name'][:50]  # Truncate to avoid Unicode issues
            print(f"     #{sample['material_number']}: {name}")
    
    # Now check what's actually in the Excel file
    print("\n2. Checking Excel file structure:")
    test_file = Path("history_files/monthly_report_inputs/2025-05/material_detail/1/ca01-202505.XLSX")
    
    if test_file.exists():
        try:
            df = pd.read_excel(test_file, engine='openpyxl', nrows=10)
            print(f"   File shape: {df.shape}")
            print(f"   Number of columns: {len(df.columns)}")
            
            # Check specific columns we're using
            print("\n   Column analysis:")
            for i in range(min(10, len(df.columns))):
                col_name = f"Column {i+1}"
                sample_values = df.iloc[:3, i].dropna().tolist()
                print(f"     {col_name}: {sample_values}")
                
                # Check if column 6 (index 5) has material names
                if i == 5:  # Column 6 (0-indexed as 5)
                    print(f"     ** This is our material NAME column **")
                    non_null_count = df.iloc[:, i].notna().sum()
                    print(f"     Non-null values in this column: {non_null_count}")
                    
        except Exception as e:
            print(f"   Error reading Excel: {e}")
    else:
        print(f"   Test file not found: {test_file}")
    
    # Test the extraction logic step by step
    print("\n3. Testing extraction logic:")
    if test_file.exists():
        try:
            df = pd.read_excel(test_file, engine='openpyxl', dtype={'物料': str}, nrows=5)
            
            # Extract the columns we're using
            material_numbers = df.iloc[:, 4]  # Column 5 (0-indexed as 4)
            material_names = df.iloc[:, 5]    # Column 6 (0-indexed as 5) 
            material_units = df.iloc[:, 6]    # Column 7 (0-indexed as 6)
            
            print("   Testing first 5 rows:")
            for i in range(min(5, len(df))):
                material_number = material_numbers.iloc[i]
                material_name = material_names.iloc[i]
                material_unit = material_units.iloc[i]
                
                print(f"   Row {i+1}:")
                print(f"     Material Number: {material_number}")
                print(f"     Material Name: {material_name}")
                print(f"     Material Unit: {material_unit}")
                
                # Test our logic
                if pd.isna(material_number) or not str(material_number).strip():
                    print("     -> SKIP: Invalid material number")
                    continue
                    
                material_number = str(material_number).strip()
                if not material_number.isdigit() or len(material_number) < 6:
                    print("     -> SKIP: Material number too short or not digits")
                    continue
                
                # Test name logic
                if pd.notna(material_name) and str(material_name).strip():
                    name = str(material_name).strip()
                    print(f"     -> USING REAL NAME: {name[:30]}...")
                else:
                    name = f"Material_{material_number}"
                    print(f"     -> USING FALLBACK NAME: {name}")
                
                print()
                
        except Exception as e:
            print(f"   Error testing extraction: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_material_names()