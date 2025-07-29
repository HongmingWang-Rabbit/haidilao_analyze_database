#!/usr/bin/env python3
"""
Simple verification of both cost impact columns
"""

import pandas as pd

def simple_dual_cost_check():
    """Simple check of both cost impact columns"""
    
    file_path = r"output\monthly_gross_margin\毛利相关分析指标-202505.xlsx"
    
    try:
        # Read the material cost changes sheet (index 1)
        df = pd.read_excel(file_path, sheet_name=1, header=None)
        
        print("Dual Cost Impact Column Check")
        print(f"Total sheet rows: {len(df)}")
        
        # Data starts from row 3 (index 2)
        data_rows = df.iloc[2:].dropna(how='all')
        print(f"Data rows: {len(data_rows)}")
        
        # Check column count - should be 13 columns now
        if len(data_rows) > 0:
            max_cols = max(len(row) for idx, row in data_rows.iterrows())
            print(f"Maximum columns in data: {max_cols}")
        
        # Count non-zero values in both cost impact columns
        mom_col = 11  # Column 12 (环比成本影响金额)  
        yoy_col = 12  # Column 13 (同比成本影响金额)
        
        mom_nonzero = 0
        yoy_nonzero = 0
        total_checked = 0
        
        print("\nSample calculations (first 3 materials):")
        sample_count = 0
        
        for idx, row in data_rows.iterrows():
            if len(row) > yoy_col:
                try:
                    material_num = str(row.iloc[1]).replace('.0', '') if pd.notna(row.iloc[1]) else 'Unknown'
                    usage = float(row.iloc[10]) if pd.notna(row.iloc[10]) else 0
                    current_price = float(row.iloc[5]) if pd.notna(row.iloc[5]) else 0
                    prev_price = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0
                    last_year_price = float(row.iloc[7]) if pd.notna(row.iloc[7]) else 0
                    
                    mom_impact = float(row.iloc[mom_col]) if pd.notna(row.iloc[mom_col]) else 0
                    yoy_impact = float(row.iloc[yoy_col]) if pd.notna(row.iloc[yoy_col]) else 0
                    
                    # Count non-zero impacts
                    if mom_impact != 0:
                        mom_nonzero += 1
                    if yoy_impact != 0:
                        yoy_nonzero += 1
                    
                    total_checked += 1
                    
                    # Show first 3 samples
                    if sample_count < 3:
                        expected_mom = usage * (prev_price - current_price)
                        expected_yoy = usage * (last_year_price - current_price)
                        
                        print(f"Material {material_num}:")
                        print(f"  MoM: ${mom_impact:.2f} (expected: ${expected_mom:.2f})")
                        print(f"  YoY: ${yoy_impact:.2f} (expected: ${expected_yoy:.2f})")
                        sample_count += 1
                        
                except (ValueError, TypeError):
                    continue
        
        print(f"\nResults Summary:")
        print(f"Total materials checked: {total_checked}")
        print(f"MoM cost impacts (non-zero): {mom_nonzero}")
        print(f"YoY cost impacts (non-zero): {yoy_nonzero}")
        
        if total_checked > 0:
            mom_percentage = (mom_nonzero / total_checked) * 100
            yoy_percentage = (yoy_nonzero / total_checked) * 100
            print(f"MoM coverage: {mom_percentage:.1f}%")
            print(f"YoY coverage: {yoy_percentage:.1f}%")
        
        # Success criteria
        if total_checked > 3000 and mom_nonzero > 1000 and yoy_nonzero > 1000:
            print("\nSUCCESS: Both cost impact columns contain data!")
            print("- Column 12: 环比成本影响金额 (Month-over-Month)")
            print("- Column 13: 同比成本影响金额 (Year-over-Year)")
            return True
        else:
            print("\nISSUE: Insufficient data in cost impact columns")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    simple_dual_cost_check()