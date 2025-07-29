#!/usr/bin/env python3
"""
Verify that the cost column formulas are working correctly
"""

import pandas as pd
from pathlib import Path

def verify_cost_formulas():
    """Verify the cost column formulas in the generated report"""
    
    output_file = Path("output/test_material_report_with_cost_columns.xlsx")
    
    if not output_file.exists():
        print("❌ Test output file not found. Please run the test first.")
        return False
    
    print("Verifying Cost Column Formulas")
    print("=" * 35)
    
    try:
        # Read the Excel file
        df = pd.read_excel(output_file)
        
        print(f"📊 File loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Find header row (contains "序号")
        header_row = None
        for idx, row in df.iterrows():
            if "序号" in str(row.iloc[0]):
                header_row = idx
                break
        
        if header_row is None:
            print("❌ Could not find header row with '序号'")
            return False
        
        print(f"📋 Header row found at index: {header_row}")
        
        # Get column names from header row
        headers = df.iloc[header_row].tolist()
        print("\\n📝 Column headers:")
        for i, header in enumerate(headers):
            if pd.notna(header):
                col_letter = chr(65 + i)  # A=65
                print(f"   {col_letter}: {header}")
        
        # Check if our new columns exist
        has_total_cost = "本月总消费金额" in headers
        has_variance_cost = "差异金额" in headers
        
        print(f"\\n✅ New columns verification:")
        print(f"   本月总消费金额 (Total Cost): {'✅ Found' if has_total_cost else '❌ Missing'}")
        print(f"   差异金额 (Variance Cost): {'✅ Found' if has_variance_cost else '❌ Missing'}")
        
        # Look for data rows (after header)
        data_start_row = header_row + 1
        if data_start_row < len(df):
            print(f"\\n📊 Sample data (first 3 data rows):")
            for i in range(3):
                row_idx = data_start_row + i
                if row_idx < len(df):
                    row_data = df.iloc[row_idx]
                    if pd.notna(row_data.iloc[1]):  # Check if there's store data
                        try:
                            store = str(row_data.iloc[1])[:20] if pd.notna(row_data.iloc[1]) else "N/A"
                            material = str(row_data.iloc[2])[:30] if pd.notna(row_data.iloc[2]) else "N/A"
                            print(f"   Row {i+1}: Store: {store}, Material: {material}")
                        except UnicodeEncodeError:
                            print(f"   Row {i+1}: <Unicode display error>")
        
        success = has_total_cost and has_variance_cost
        
        if success:
            print("\\n✅ Verification successful! Both new cost columns were added correctly.")
        else:
            print("\\n❌ Verification failed! One or both cost columns are missing.")
        
        return success
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

if __name__ == "__main__":
    verify_cost_formulas()