#!/usr/bin/env python3
"""
Analyze and Extract Dish Material Data

This script analyzes the dish-material data and extracts the required information:
- 出品分量(kg)
- 损耗
- 物料单位
"""

import pandas as pd
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_dish_material_data():
    """Analyze and extract dish material data"""
    
    file_path = "Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx"
    
    try:
        # Read the Excel file
        print(f"Reading file: {file_path}")
        df = pd.read_excel(file_path, sheet_name='Sheet1')
        
        print(f"\nData shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Check data types and null values
        print("\nColumn info:")
        for col in ['出品分量(kg)', '损耗', '物料单位']:
            print(f"\n{col}:")
            print(f"  - Non-null count: {df[col].notna().sum()}")
            print(f"  - Unique values: {df[col].nunique()}")
            if df[col].notna().any():
                print(f"  - Sample values: {df[col].dropna().unique()[:5]}")
            else:
                print("  - All values are null")
        
        # Check if there are other columns that might contain the data
        print("\n\nChecking other columns that might contain the data:")
        
        # Look for columns with quantity/amount/unit information
        potential_columns = []
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in ['量', '数量', '单位', '规格', 'unit', 'quantity', 'amount']):
                potential_columns.append(col)
        
        print(f"Potential columns: {potential_columns}")
        
        for col in potential_columns:
            print(f"\n{col}:")
            print(f"  - Non-null count: {df[col].notna().sum()}")
            print(f"  - Sample values: {df[col].dropna().head(10).tolist()}")
        
        # Group by dish to see unique combinations
        print("\n\nAnalyzing dish-material combinations:")
        dish_material_df = df[['菜品编码', '菜品名称', '物料号', '物料描述', '出品分量(kg)', '损耗', '物料单位']].copy()
        
        # Count unique dishes and materials
        print(f"Unique dishes: {df['菜品编码'].nunique()}")
        print(f"Unique materials: {df['物料号'].nunique()}")
        
        # Show sample data for specific dishes
        print("\n\nSample dish-material mappings:")
        sample_dishes = df['菜品编码'].unique()[:5]
        for dish_code in sample_dishes:
            dish_data = df[df['菜品编码'] == dish_code]
            print(f"\nDish: {dish_data.iloc[0]['菜品名称']} (Code: {dish_code})")
            print(f"Materials used: {len(dish_data)}")
            for _, row in dish_data.iterrows():
                print(f"  - {row['物料描述']} (物料号: {row['物料号']})")
                
        # Save a summary file
        summary_file = "dish_material_summary.xlsx"
        with pd.ExcelWriter(summary_file, engine='openpyxl') as writer:
            # Sheet 1: Full data
            df.to_excel(writer, sheet_name='Full_Data', index=False)
            
            # Sheet 2: Unique dish-material combinations
            unique_combinations = df[['菜品编码', '菜品名称', '物料号', '物料描述', '出品分量(kg)', '损耗', '物料单位']].drop_duplicates()
            unique_combinations.to_excel(writer, sheet_name='Unique_Combinations', index=False)
            
            # Sheet 3: Summary statistics
            summary_stats = pd.DataFrame({
                'Metric': ['Total Rows', 'Unique Dishes', 'Unique Materials', 'Avg Materials per Dish'],
                'Value': [
                    len(df),
                    df['菜品编码'].nunique(),
                    df['物料号'].nunique(),
                    len(df) / df['菜品编码'].nunique()
                ]
            })
            summary_stats.to_excel(writer, sheet_name='Summary', index=False)
            
        print(f"\n\nSummary file saved to: {summary_file}")
        
        # Check if we need to look elsewhere for the actual values
        if df['出品分量(kg)'].isna().all() and df['损耗'].isna().all() and df['物料单位'].isna().all():
            print("\n\n⚠️  WARNING: The columns 出品分量(kg), 损耗, and 物料单位 are all empty!")
            print("These values might need to be extracted from:")
            print("1. The dish_material table in the database")
            print("2. Other Excel files in the material_detail folders")
            print("3. A separate configuration or mapping file")
            
    except Exception as e:
        print(f"Error analyzing file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_dish_material_data()