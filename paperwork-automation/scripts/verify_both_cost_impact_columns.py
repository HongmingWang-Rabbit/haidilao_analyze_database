#!/usr/bin/env python3
"""
Verify both 环比成本影响金额 and 同比成本影响金额 columns are working correctly
"""

import pandas as pd

def verify_both_cost_impact_columns():
    """Check both MoM and YoY cost impact calculations"""
    
    file_path = r"output\monthly_gross_margin\毛利相关分析指标-202505.xlsx"
    
    try:
        # Read the material cost changes sheet (index 1)
        df = pd.read_excel(file_path, sheet_name=1, header=None)
        
        print("=== DUAL COST IMPACT VERIFICATION ===")
        print(f"Total rows in sheet: {len(df)}")
        
        # Check headers
        print("\nColumn Headers:")
        if len(df) >= 2:
            for i, header in enumerate(df.iloc[1]):
                if pd.notna(header):
                    print(f"  Column {i+1}: {header}")
        
        # Data starts from row 3 (index 2)
        data_rows = df.iloc[2:].dropna(how='all')
        print(f"\nData rows: {len(data_rows)}")
        
        # Cost impact columns should be 12 (环比) and 13 (同比)
        mom_cost_impact_col = 11  # Column 12 (0-indexed)
        yoy_cost_impact_col = 12  # Column 13 (0-indexed)
        
        sample_count = 0
        mom_valid = 0
        yoy_valid = 0
        
        print("\nSample Cost Impact Calculations:")
        
        for idx, row in data_rows.iterrows():
            if len(row) > yoy_cost_impact_col and sample_count < 5:
                try:
                    # Get the values
                    material_num = str(row.iloc[1]).replace('.0', '') if pd.notna(row.iloc[1]) else 'Unknown'
                    current_price = float(row.iloc[5]) if pd.notna(row.iloc[5]) else 0
                    prev_price = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0
                    last_year_price = float(row.iloc[7]) if pd.notna(row.iloc[7]) else 0
                    usage = float(row.iloc[10]) if pd.notna(row.iloc[10]) else 0
                    
                    mom_cost_impact = float(row.iloc[mom_cost_impact_col]) if pd.notna(row.iloc[mom_cost_impact_col]) else 0
                    yoy_cost_impact = float(row.iloc[yoy_cost_impact_col]) if pd.notna(row.iloc[yoy_cost_impact_col]) else 0
                    
                    # Calculate expected values
                    expected_mom = usage * (prev_price - current_price)
                    expected_yoy = usage * (last_year_price - current_price)
                    
                    print(f"\nMaterial {material_num}:")
                    print(f"  Usage: {usage}")
                    print(f"  Current Price: ${current_price:.4f}")
                    print(f"  Previous Price: ${prev_price:.4f}")
                    print(f"  Last Year Price: ${last_year_price:.4f}")
                    
                    print(f"  环比成本影响金额:")
                    print(f"    Calculated: ${mom_cost_impact:.4f}")
                    print(f"    Expected: ${expected_mom:.4f}")
                    mom_correct = abs(mom_cost_impact - expected_mom) < 0.01
                    print(f"    Result: {'✅' if mom_correct else '❌'}")
                    if mom_correct:
                        mom_valid += 1
                    
                    print(f"  同比成本影响金额:")
                    print(f"    Calculated: ${yoy_cost_impact:.4f}")
                    print(f"    Expected: ${expected_yoy:.4f}")
                    yoy_correct = abs(yoy_cost_impact - expected_yoy) < 0.01
                    print(f"    Result: {'✅' if yoy_correct else '❌'}")
                    if yoy_correct:
                        yoy_valid += 1
                    
                    sample_count += 1
                    
                except (ValueError, TypeError, IndexError) as e:
                    print(f"Error processing row {idx}: {e}")
                    continue
        
        # Summary statistics
        print(f"\n=== COLUMN STATISTICS ===")
        
        # Count non-zero values in each column
        mom_nonzero = 0
        yoy_nonzero = 0
        
        for idx, row in data_rows.iterrows():
            if len(row) > yoy_cost_impact_col:
                try:
                    mom_val = float(row.iloc[mom_cost_impact_col]) if pd.notna(row.iloc[mom_cost_impact_col]) else 0
                    yoy_val = float(row.iloc[yoy_cost_impact_col]) if pd.notna(row.iloc[yoy_cost_impact_col]) else 0
                    
                    if mom_val != 0:
                        mom_nonzero += 1
                    if yoy_val != 0:
                        yoy_nonzero += 1
                        
                except (ValueError, TypeError):
                    continue
        
        print(f"环比成本影响金额 non-zero values: {mom_nonzero}/{len(data_rows)}")
        print(f"同比成本影响金额 non-zero values: {yoy_nonzero}/{len(data_rows)}")
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"环比 Calculation Accuracy: {mom_valid}/{sample_count}")
        print(f"同比 Calculation Accuracy: {yoy_valid}/{sample_count}")
        
        if mom_valid == sample_count and yoy_valid == sample_count and sample_count > 0:
            print("✅ SUCCESS: Both cost impact columns are working correctly!")
            print("✅ 环比成本影响金额: Month-over-month cost impact")
            print("✅ 同比成本影响金额: Year-over-year cost impact")
            return True
        else:
            print("❌ ISSUE: Cost impact calculations need review")
            return False
            
    except Exception as e:
        print(f"Error in verification: {e}")
        return False

if __name__ == "__main__":
    verify_both_cost_impact_columns()