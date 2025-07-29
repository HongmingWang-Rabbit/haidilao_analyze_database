#!/usr/bin/env python3
"""
Simple check for dish loss cost data
"""

import pandas as pd

def simple_dish_loss_check():
    """Simple check of dish loss cost columns"""
    
    file_path = r"output\monthly_gross_margin\毛利相关分析指标-202505.xlsx"
    
    try:
        # Read the dish price changes sheet (index 0)
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        
        print("Dish Loss Cost Check")
        print(f"Total sheet rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")
        
        # Data starts around row 4
        data_rows = df.iloc[3:].dropna(how='all')
        print(f"Data rows: {len(data_rows)}")
        
        if len(data_rows) == 0:
            print("No data found")
            return False
        
        # Check last 5 columns for loss cost data (columns should be around 24-28)
        max_cols = len(df.columns)
        loss_cols = list(range(max(0, max_cols-5), max_cols))
        
        print(f"Checking loss cost columns: {loss_cols}")
        
        # Count non-zero values in loss cost columns
        non_zero_counts = {}
        total_checked = 0
        
        print("\nSample values from loss cost columns:")
        sample_count = 0
        
        for idx, row in data_rows.iterrows():
            if sample_count < 3:  # Check first 3 rows
                dish_info = str(row.iloc[2])[:10] if len(row) > 2 else 'Unknown'
                print(f"Row {idx}, Dish: {dish_info}")
                
                for col in loss_cols:
                    if col < len(row):
                        value = row.iloc[col]
                        if pd.notna(value) and str(value).replace('.', '').replace('-', '').isdigit():
                            try:
                                float_val = float(value)
                                print(f"  Col {col}: {float_val}")
                            except:
                                print(f"  Col {col}: {value}")
                        else:
                            print(f"  Col {col}: Empty/Non-numeric")
                print()
                sample_count += 1
            
            # Count all non-zero values
            for col in loss_cols:
                if col not in non_zero_counts:
                    non_zero_counts[col] = 0
                    
                if col < len(row):
                    try:
                        value = row.iloc[col]
                        if pd.notna(value):
                            float_val = float(value)
                            if float_val != 0:
                                non_zero_counts[col] += 1
                    except:
                        pass
            
            total_checked += 1
        
        print(f"Results Summary:")
        print(f"Total dishes checked: {total_checked}")
        
        total_non_zero = 0
        for col, count in non_zero_counts.items():
            print(f"Column {col}: {count} non-zero values")
            total_non_zero += count
        
        if total_non_zero > 0:
            print(f"\nSUCCESS: Found {total_non_zero} non-zero loss cost values!")
            print("Loss cost calculations are working!")
            return True
        else:
            print("\nISSUE: No loss cost data found")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    simple_dish_loss_check()