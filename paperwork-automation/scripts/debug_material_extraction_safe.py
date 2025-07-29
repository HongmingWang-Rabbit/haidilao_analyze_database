#!/usr/bin/env python3
"""
Safe debugging of material name extraction without Unicode display issues
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def debug_material_extraction_safe():
    """Debug material extraction safely without Unicode issues"""
    
    print("DEBUGGING MATERIAL EXTRACTION (SAFE)")
    print("=" * 40)
    
    # Check the Excel file structure
    test_file = Path("history_files/monthly_report_inputs/2025-05/material_detail/1/ca01-202505.XLSX")
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return
    
    try:
        df = pd.read_excel(test_file, engine='openpyxl', dtype={'物料': str}, nrows=10)
        print(f"File shape: {df.shape}")
        
        # Test our column extraction logic
        print("\nTesting column extraction:")
        
        # Based on our previous analysis: Column 5 = material numbers, Column 6 = material names, Column 7 = units
        if df.shape[1] >= 7:
            material_numbers = df.iloc[:, 4]  # Column 5 (0-indexed as 4)
            material_names = df.iloc[:, 5]    # Column 6 (0-indexed as 5) 
            material_units = df.iloc[:, 6]    # Column 7 (0-indexed as 6)
            
            print("First 5 material numbers:")
            for i in range(min(5, len(material_numbers))):
                mat_num = material_numbers.iloc[i]
                print(f"  Row {i+1}: '{mat_num}' (type: {type(mat_num)})")
                
                # Test our cleaning logic
                if pd.notna(mat_num):
                    cleaned = str(mat_num).strip()
                    print(f"    After str().strip(): '{cleaned}'")
                    
                    # Test digit check
                    if cleaned.isdigit():
                        print(f"    Is digit: True, Length: {len(cleaned)}")
                        
                        # Remove leading zeros like in the fix
                        cleaned_no_zeros = cleaned.lstrip('0')
                        if not cleaned_no_zeros:
                            cleaned_no_zeros = '0'
                        print(f"    After removing leading zeros: '{cleaned_no_zeros}'")
                    else:
                        print(f"    Is digit: False")
                else:
                    print(f"    Is null/NaN")
            
            print("\nChecking material names (without displaying Chinese):")
            for i in range(min(5, len(material_names))):
                mat_name = material_names.iloc[i]
                if pd.notna(mat_name):
                    name_str = str(mat_name).strip()
                    print(f"  Row {i+1}: Has material name (length: {len(name_str)})")
                else:
                    print(f"  Row {i+1}: No material name (null/NaN)")
            
            print("\nChecking material units:")
            for i in range(min(5, len(material_units))):
                mat_unit = material_units.iloc[i]
                if pd.notna(mat_unit):
                    unit_str = str(mat_unit).strip()
                    print(f"  Row {i+1}: '{unit_str}'")
                else:
                    print(f"  Row {i+1}: No unit (null/NaN)")
        
        # Now identify the issue in our extraction logic
        print("\nTesting the extraction logic that should be used:")
        
        for i in range(min(3, len(df))):
            material_number = material_numbers.iloc[i]
            material_name = material_names.iloc[i]
            
            print(f"\nRow {i+1} processing:")
            
            # Skip if material number is invalid
            if pd.isna(material_number) or not str(material_number).strip():
                print("  SKIP: Invalid material number")
                continue
                
            material_number_clean = str(material_number).strip()
            print(f"  Original number: '{material_number_clean}'")
            
            # ISSUE: We need to remove leading zeros!
            material_number_clean = material_number_clean.lstrip('0')
            if not material_number_clean:
                material_number_clean = '0'
            print(f"  After removing leading zeros: '{material_number_clean}'")
            
            if not material_number_clean.isdigit() or len(material_number_clean) < 6:
                print(f"  SKIP: Material number too short or not digits (length: {len(material_number_clean)})")
                continue
            
            # Use material name or fallback to generic name
            if pd.notna(material_name) and str(material_name).strip():
                print("  REAL NAME AVAILABLE - would use actual material name")
                name_result = "REAL_NAME_FROM_FILE"
            else:
                print("  NO REAL NAME - would use generic fallback")
                name_result = f"Material_{material_number_clean}"
            
            print(f"  Final name decision: {name_result}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_material_extraction_safe()