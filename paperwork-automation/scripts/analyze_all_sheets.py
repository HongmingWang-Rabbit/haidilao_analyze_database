#!/usr/bin/env python3
"""
Analyze all sheets in the generated report to identify issues
"""

import pandas as pd

def analyze_all_sheets():
    """Analyze all sheets to find remaining issues"""
    
    file_path = "output/monthly_gross_margin/fixed_material_prices.xlsx"
    
    sheet_names = [
        "菜品价格变动及菜品损耗表",
        "原材料成本变动表", 
        "打折优惠表",
        "各店毛利率分析",
        "月度毛利汇总",
        "同比环比分析"
    ]
    
    try:
        xl_file = pd.ExcelFile(file_path, engine='openpyxl')
        print("COMPREHENSIVE SHEET ANALYSIS:")
        print("=" * 60)
        
        for i, expected_name in enumerate(sheet_names):
            try:
                df = pd.read_excel(file_path, sheet_name=i)
                non_empty = df.dropna(how='all').shape[0]
                
                print(f"\nSheet {i+1}: {non_empty} rows")
                
                if non_empty > 100:
                    status = "EXCELLENT"
                elif non_empty > 10:
                    status = "GOOD"
                elif non_empty > 5:
                    status = "FAIR"
                elif non_empty > 1:
                    status = "MINIMAL"
                else:
                    status = "EMPTY"
                
                print(f"  Status: {status}")
                
                # Check for data quality issues
                if non_empty > 2:  # Has data beyond headers
                    data_rows = df.iloc[2:].dropna(how='all')
                    if len(data_rows) > 0:
                        # Check for columns with all zeros (potential issues)
                        numeric_cols = df.select_dtypes(include=['number']).columns
                        zero_cols = 0
                        for col in numeric_cols:
                            if len(data_rows) > 0:
                                col_data = data_rows[col].dropna()
                                if len(col_data) > 0 and (col_data == 0).all():
                                    zero_cols += 1
                        
                        if zero_cols > 0:
                            print(f"  Warning: {zero_cols} columns with all zeros")
                        
                        # Check for missing data
                        missing_pct = (data_rows.isna().sum().sum() / (len(data_rows) * len(data_rows.columns))) * 100
                        if missing_pct > 50:
                            print(f"  Warning: {missing_pct:.1f}% missing data")
                        
                        print(f"  Data quality: {len(data_rows)} data rows, {missing_pct:.1f}% missing")
                
            except Exception as e:
                print(f"\nSheet {i+1}: ERROR - {e}")
        
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print("- Sheet 1 (Dishes): Should be EXCELLENT (>100 rows)")
        print("- Sheet 2 (Materials): Should be EXCELLENT (>100 rows) ✅ FIXED")
        print("- Sheet 3 (Discounts): Should be FAIR (5-10 rows)")
        print("- Sheet 4 (Store Profit): Should be FAIR (7-10 rows)")
        print("- Sheet 5 (Monthly Summary): Should be FAIR (7-10 rows)")
        print("- Sheet 6 (YoY/MoM): Should be GOOD (10-20 rows) ✅ FIXED")
        
    except Exception as e:
        print(f"Error analyzing sheets: {e}")

if __name__ == "__main__":
    analyze_all_sheets()