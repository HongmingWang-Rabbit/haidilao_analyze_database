#!/usr/bin/env python3
"""
Check the material cost sheet for non-zero historical prices
"""

import pandas as pd

def check_material_sheet():
    """Check if material cost sheet has historical price data"""
    
    file_path = "output/monthly_gross_margin/fixed_historical_prices.xlsx"
    
    try:
        # Read sheet 2 (Material Cost Changes) - index 1
        df = pd.read_excel(file_path, sheet_name=1)
        non_empty = df.dropna(how='all').shape[0]
        print(f'Sheet 2 Material Cost Changes: {non_empty} non-empty rows')
        
        if non_empty > 2:  # Skip headers
            data_rows = df.iloc[2:].dropna(how='all')  # Skip first 2 header rows
            if len(data_rows) > 0:
                prev_month_nonzero = 0
                last_year_nonzero = 0
                
                for idx, row in data_rows.iterrows():
                    if len(row) > 6:  # Has previous month price column
                        prev_val = row.iloc[6]  # Column 7 (上月均价)
                        if pd.notna(prev_val) and prev_val != 0:
                            prev_month_nonzero += 1
                    if len(row) > 7:  # Has last year price column  
                        last_year_val = row.iloc[7]  # Column 8 (去年同期均价)
                        if pd.notna(last_year_val) and last_year_val != 0:
                            last_year_nonzero += 1
                
                print(f'Data rows: {len(data_rows)}')
                print(f'Non-zero previous month prices: {prev_month_nonzero} out of {len(data_rows)}')
                print(f'Non-zero last year prices: {last_year_nonzero} out of {len(data_rows)}')
                
                if prev_month_nonzero > 0 or last_year_nonzero > 0:
                    print('SUCCESS: Historical price data is now showing!')
                else:
                    print('ISSUE: Still no historical price data')
            else:
                print('No data rows found')
        else:
            print('Not enough rows (likely just headers)')
            
    except Exception as e:
        print(f'Error checking sheet: {e}')

if __name__ == "__main__":
    check_material_sheet()