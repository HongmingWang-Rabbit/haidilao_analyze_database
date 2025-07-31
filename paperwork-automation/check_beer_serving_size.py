#!/usr/bin/env python3
"""
Check Beer Serving Size

This script checks the serving size (出品分量) for beer items in Store 5's calculation sheet
to understand why they show incorrect values like 331 kg for a 330ml beer.
"""

import pandas as pd
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_beer_serving_sizes():
    """Check beer serving sizes in Store 5 calculation sheet"""
    
    # Store 5 file path
    store5_file = "Input/monthly_report/inventory_checking_result/5/CA05-盘点结果 -2505.xls"
    
    print(f"Checking Store 5 file: {store5_file}")
    
    try:
        # Read the calculation sheet
        calc_df = pd.read_excel(store5_file, sheet_name='计算')
        
        # Look for beer items
        print("\n=== SEARCHING FOR BEER ITEMS ===")
        
        # Search for items containing beer-related keywords
        beer_keywords = ['啤酒', '朝日', 'beer', 'asahi', '330ml', '500ml']
        
        beer_mask = False
        for keyword in beer_keywords:
            beer_mask = beer_mask | calc_df['菜品名称'].str.contains(keyword, case=False, na=False)
            if '物料描述' in calc_df.columns:
                beer_mask = beer_mask | calc_df['物料描述'].str.contains(keyword, case=False, na=False)
        
        beer_items = calc_df[beer_mask]
        
        if len(beer_items) > 0:
            print(f"\nFound {len(beer_items)} beer-related items:")
            
            # Show relevant columns
            display_cols = ['菜品名称', '规格', '实收数量', '出品份量', '损耗', '物料单位', '物料号', '物料描述']
            existing_cols = [col for col in display_cols if col in beer_items.columns]
            
            print("\nBeer items data:")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            print(beer_items[existing_cols].to_string())
            
            # Check if the issue is with the actual data
            print("\n\n=== ANALYSIS ===")
            for idx, row in beer_items.iterrows():
                dish_name = row.get('菜品名称', '')
                serving_size = row.get('出品份量', 0)
                quantity = row.get('实收数量', 0)
                
                print(f"\nDish: {dish_name}")
                print(f"  实收数量 (quantity sold): {quantity}")
                print(f"  出品份量 (serving size): {serving_size}")
                
                # Check if serving size might be mistakenly the total quantity
                if abs(serving_size - quantity) < 1:
                    print(f"  ⚠️  WARNING: 出品份量 appears to be the same as 实收数量!")
                    print(f"  This suggests the serving size might be incorrectly set to the total quantity sold")
                    
                    # Calculate what the actual serving size should be
                    if '330ml' in str(dish_name).lower() or '330ml' in str(row.get('规格', '')).lower():
                        print(f"  Expected serving size for 330ml beer: ~0.33 kg")
                    elif '500ml' in str(dish_name).lower() or '500ml' in str(row.get('规格', '')).lower():
                        print(f"  Expected serving size for 500ml beer: ~0.50 kg")
        
        else:
            print("No beer items found in calculation sheet")
            
            # Let's also check the main sheet
            print("\n\nChecking main sheet for beer items...")
            main_df = pd.read_excel(store5_file, sheet_name=0)  # First sheet
            
            # Search in main sheet
            for col in main_df.columns:
                if any(keyword in str(col).lower() for keyword in ['物料', 'material', '描述']):
                    beer_in_main = main_df[main_df[col].str.contains('啤酒|beer', case=False, na=False)]
                    if len(beer_in_main) > 0:
                        print(f"\nFound beer items in main sheet column '{col}':")
                        print(beer_in_main[[col]].head(10))
                        break
        
        # Also check our merged file to see the final result
        print("\n\n=== CHECKING MERGED FILE ===")
        merged_file = "output/inventory_calculation_data_from_calc_sheets.xlsx"
        if Path(merged_file).exists():
            merged_df = pd.read_excel(merged_file)
            
            # Find beer items in merged file
            beer_in_merged = merged_df[
                (merged_df['菜品名称'].str.contains('啤酒|朝日|beer', case=False, na=False)) &
                (merged_df['门店名称'] == '加拿大五店')
            ]
            
            if len(beer_in_merged) > 0:
                print(f"\nBeer items in merged file for Store 5:")
                relevant_cols = ['菜品名称', '规格', '出品分量(kg)', '损耗', '物料单位']
                print(beer_in_merged[relevant_cols].to_string())
                
    except Exception as e:
        print(f"Error checking beer serving sizes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_beer_serving_sizes()