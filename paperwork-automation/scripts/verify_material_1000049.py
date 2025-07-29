#!/usr/bin/env python3
"""
Verify that material 1000049 now shows the correct historical price
"""

import pandas as pd

def verify_material_1000049():
    """Check if material 1000049 shows $2.35 for previous month"""
    
    file_path = "output/monthly_gross_margin/fixed_historical_prices.xlsx"
    
    try:
        # Read sheet 2 (Material Cost Changes) - index 1
        df = pd.read_excel(file_path, sheet_name=1)
        
        # Look for material 1000049 in store 1 (assuming store names start with 加拿大一店)
        # Material number should be in column 2 (index 1)
        # Previous month price should be in column 7 (index 6)
        
        data_rows = df.iloc[2:].dropna(how='all')  # Skip headers
        
        # Find material 1000049
        material_found = False
        for idx, row in data_rows.iterrows():
            if len(row) > 1:  # Has material number column
                material_num = str(row.iloc[1]).replace('.0', '')  # Remove .0 if present
                if material_num == '1000049':
                    material_found = True
                    current_price = row.iloc[5] if len(row) > 5 else 0  # Column 6 (本月均价)
                    prev_price = row.iloc[6] if len(row) > 6 else 0     # Column 7 (上月均价)
                    last_year_price = row.iloc[7] if len(row) > 7 else 0 # Column 8 (去年同期均价)
                    
                    print(f"Material 1000049 found:")
                    print(f"  Store: Store 1")
                    print(f"  Current month price: ${current_price:.4f}")
                    print(f"  Previous month price: ${prev_price:.4f}")
                    print(f"  Last year price: ${last_year_price:.4f}")
                    
                    if abs(prev_price - 2.35) < 0.01:  # Allow small floating point differences
                        print("  SUCCESS: Previous month price is $2.35 as expected!")
                        return True
                    else:
                        print(f"  ISSUE: Expected $2.35, got ${prev_price:.4f}")
                        return False
        
        if not material_found:
            print("Material 1000049 not found in the report")
            return False
            
    except Exception as e:
        print(f"Error verifying material: {e}")
        return False

if __name__ == "__main__":
    verify_material_1000049()