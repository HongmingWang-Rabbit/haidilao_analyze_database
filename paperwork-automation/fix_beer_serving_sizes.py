#!/usr/bin/env python3
"""
Fix Beer Serving Sizes

This script fixes incorrect beer serving sizes in the calculation data.
Beer serving sizes should be based on volume:
- 330ml beer ≈ 0.33 kg
- 500ml beer ≈ 0.50 kg
"""

import pandas as pd
import sys
from pathlib import Path
import re

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def fix_beer_serving_sizes():
    """Fix incorrect beer serving sizes"""
    
    # Read the merged file  
    # First check where the file actually is
    if Path("output/inventory_calculation_data_from_calc_sheets.xlsx").exists():
        input_file = "output/inventory_calculation_data_from_calc_sheets.xlsx"
    else:
        # Use the file created by the extraction script
        input_file = "output/inventory_calculation_data_from_calc_sheets.xlsx"
        # If not found, create it from the extraction
        if not Path(input_file).exists():
            print("File not found. Re-running extraction...")
            # Use the file that was created by extraction script
            import shutil
            original = "Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx"
            input_file = "output/inventory_calculation_data_manual_extracted_fixed.xlsx"
            Path("output").mkdir(exist_ok=True)
            shutil.copy2(original, input_file)
            
    output_file = "output/inventory_calculation_data_fixed_beer.xlsx"
    
    # Create output directory if needed
    Path("output").mkdir(exist_ok=True)
    
    print(f"Reading file: {input_file}")
    df = pd.read_excel(input_file)
    
    print(f"Total rows: {len(df)}")
    
    # Find beer items with incorrect serving sizes
    beer_mask = df['菜品名称'].str.contains('啤酒|beer|朝日|青岛|百威|科罗娜|smirnoff', case=False, na=False)
    beer_items = df[beer_mask].copy()
    
    print(f"\nFound {len(beer_items)} beer items")
    
    # Show current state
    print("\nCurrent beer items with serving sizes > 1:")
    large_serving_beers = beer_items[beer_items['出品分量(kg)'] > 1]
    if len(large_serving_beers) > 0:
        display_cols = ['门店名称', '菜品名称', '规格', '出品分量(kg)', '损耗', '物料单位']
        print(large_serving_beers[display_cols].to_string())
    
    # Fix serving sizes based on volume
    fixes_applied = 0
    
    for idx in beer_items.index:
        row = df.loc[idx]
        dish_name = row['菜品名称']
        spec = row.get('规格', '')
        current_serving = row['出品分量(kg)']
        
        # Determine correct serving size based on volume
        correct_serving = None
        
        # Check dish name and spec for volume
        combined_text = f"{dish_name} {spec}".lower()
        
        if '330ml' in combined_text or '330毫升' in combined_text:
            correct_serving = 0.33
        elif '500ml' in combined_text or '500毫升' in combined_text:
            correct_serving = 0.50
        elif '355ml' in combined_text or '355毫升' in combined_text:
            correct_serving = 0.355
        elif '473ml' in combined_text or '473毫升' in combined_text:
            correct_serving = 0.473
        elif '650ml' in combined_text or '650毫升' in combined_text:
            correct_serving = 0.65
        
        # Apply fix if needed
        if correct_serving and abs(current_serving - correct_serving) > 0.1:
            print(f"\nFixing: {dish_name} ({spec})")
            print(f"  Current serving: {current_serving} kg")
            print(f"  Correct serving: {correct_serving} kg")
            
            df.at[idx, '出品分量(kg)'] = correct_serving
            fixes_applied += 1
    
    print(f"\n\nTotal fixes applied: {fixes_applied}")
    
    # Also fix other beverages if needed
    print("\n\nChecking other beverages...")
    
    # Find other beverages
    beverage_keywords = ['可乐', '雪碧', '芬达', '王老吉', '茶', '汁', '饮料', 'coke', 'sprite', 'juice']
    beverage_mask = False
    for keyword in beverage_keywords:
        beverage_mask = beverage_mask | df['菜品名称'].str.contains(keyword, case=False, na=False)
    
    # Exclude already processed beer items
    beverage_mask = beverage_mask & ~beer_mask
    other_beverages = df[beverage_mask].copy()
    
    print(f"Found {len(other_beverages)} other beverage items")
    
    # Check for incorrect serving sizes
    large_serving_beverages = other_beverages[other_beverages['出品分量(kg)'] > 2]
    if len(large_serving_beverages) > 0:
        print("\nOther beverages with serving sizes > 2 kg:")
        display_cols = ['门店名称', '菜品名称', '规格', '出品分量(kg)']
        print(large_serving_beverages[display_cols].head(20).to_string())
        
        # Fix common beverage sizes
        for idx in large_serving_beverages.index:
            row = df.loc[idx]
            dish_name = row['菜品名称']
            spec = row.get('规格', '')
            
            combined_text = f"{dish_name} {spec}".lower()
            
            # Common beverage sizes
            if '330ml' in combined_text:
                df.at[idx, '出品分量(kg)'] = 0.33
                fixes_applied += 1
            elif '500ml' in combined_text:
                df.at[idx, '出品分量(kg)'] = 0.50
                fixes_applied += 1
            elif '355ml' in combined_text:
                df.at[idx, '出品分量(kg)'] = 0.355
                fixes_applied += 1
            elif '250ml' in combined_text:
                df.at[idx, '出品分量(kg)'] = 0.25
                fixes_applied += 1
            elif '1.25l' in combined_text or '1250ml' in combined_text:
                df.at[idx, '出品分量(kg)'] = 1.25
                fixes_applied += 1
    
    # Save the fixed file
    print(f"\n\nSaving fixed file to: {output_file}")
    df.to_excel(output_file, index=False)
    
    # Show summary of changes
    print("\n\n=== SUMMARY ===")
    print(f"Total fixes applied: {fixes_applied}")
    
    # Verify the fixes
    fixed_beers = df[beer_mask]
    print(f"\nBeer serving sizes after fix:")
    print(fixed_beers['出品分量(kg)'].value_counts().head(10))
    
    # Show specific Store 5 beer items
    store5_beers = df[
        (df['门店名称'] == '加拿大五店') & 
        (df['菜品名称'].str.contains('朝日|啤酒', na=False))
    ]
    
    if len(store5_beers) > 0:
        print(f"\n\nStore 5 beer items after fix:")
        display_cols = ['菜品名称', '规格', '出品分量(kg)', '损耗', '物料单位']
        print(store5_beers[display_cols].to_string())


if __name__ == "__main__":
    fix_beer_serving_sizes()