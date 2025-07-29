#!/usr/bin/env python3
"""
Verify that the dish loss cost columns are properly populated
"""

import pandas as pd

def verify_dish_loss_costs():
    """Check if dish loss cost columns contain data"""
    
    file_path = r"output\monthly_gross_margin\毛利相关分析指标-202505.xlsx"
    
    try:
        # Read the dish price changes sheet (index 0)
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        
        print("=== DISH LOSS COST VERIFICATION ===")
        print(f"Total rows in sheet: {len(df)}")
        
        # Skip title rows and find data start (usually around row 4-5)
        data_start = None
        for i in range(10):
            if i < len(df):
                # Look for row that starts with store data
                first_col = df.iloc[i, 0] if len(df.columns) > 0 else None
                if pd.notna(first_col) and ('加拿大' in str(first_col) or '店' in str(first_col)):
                    data_start = i
                    break
        
        if data_start is None:
            print("Could not find data start in sheet")
            return False
            
        print(f"Data starts at row: {data_start + 1}")
        
        # Get column count 
        max_cols = len(df.columns)
        print(f"Total columns: {max_cols}")
        
        # Data rows
        data_rows = df.iloc[data_start:].dropna(how='all')
        print(f"Data rows: {len(data_rows)}")
        
        if len(data_rows) == 0:
            print("No data found")
            return False
        
        # The loss cost columns should be in the last 5 columns based on the worksheet structure:
        # Column positions for loss analysis (approximate):
        # - 本月损耗影响成本金额: around column 25-29
        # - 上月损耗影响成本金额: around column 26-30
        # - 损耗环比变动金额: around column 27-31
        # - 可比期间损耗影响成本金额: around column 28-32
        # - 损耗同比变动金额: around column 29-33
        
        loss_cols_start = max_cols - 5  # Last 5 columns
        
        print(f"\nChecking loss cost columns (columns {loss_cols_start} to {max_cols-1}):")
        
        sample_count = 0
        loss_data_found = False
        
        print("\nSample loss cost values (first 5 dishes):")
        
        for idx, row in data_rows.iterrows():
            if sample_count >= 5:
                break
                
            # Get dish info
            dish_code = row.iloc[2] if len(row) > 2 else 'Unknown'
            dish_name = row.iloc[4] if len(row) > 4 else 'Unknown'
            
            print(f"Dish {dish_code} ({dish_name}):")
            
            # Check last 5 columns for loss cost data
            has_loss_data = False
            for col_idx in range(max(0, loss_cols_start), min(max_cols, loss_cols_start + 5)):
                if col_idx < len(row):
                    value = row.iloc[col_idx]
                    if pd.notna(value) and value != 0:
                        has_loss_data = True
                        loss_data_found = True
                        print(f"  Column {col_idx}: {value}")
            
            if not has_loss_data:
                print("  No loss cost data found")
            
            sample_count += 1
        
        # Count non-zero values in loss cost columns
        total_loss_values = 0
        non_zero_loss_values = 0
        
        for idx, row in data_rows.iterrows():
            for col_idx in range(max(0, loss_cols_start), min(max_cols, loss_cols_start + 5)):
                if col_idx < len(row):
                    value = row.iloc[col_idx]
                    total_loss_values += 1
                    if pd.notna(value) and value != 0:
                        non_zero_loss_values += 1
        
        print(f"\n=== LOSS COST STATISTICS ===")
        print(f"Total loss cost fields: {total_loss_values}")
        print(f"Non-zero loss cost values: {non_zero_loss_values}")
        
        if total_loss_values > 0:
            coverage = (non_zero_loss_values / total_loss_values) * 100
            print(f"Loss cost coverage: {coverage:.1f}%")
        
        if loss_data_found:
            print("\n✅ SUCCESS: Dish loss cost columns contain data!")
            print("✅ Loss cost calculations are working!")
            return True
        else:
            print("\n❌ ISSUE: No loss cost data found in expected columns")
            return False
            
    except Exception as e:
        print(f"Error verifying dish loss costs: {e}")
        return False

if __name__ == "__main__":
    verify_dish_loss_costs()