#!/usr/bin/env python3
"""
Final Fix with Corrections

This script applies the calculation sheet data and then fixes known issues like
incorrect beer serving sizes.
"""

import pandas as pd
import sys
from pathlib import Path
import shutil

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def final_fix_with_corrections():
    """Apply calculation sheet data and fix known issues"""
    
    # File paths
    # The original file is in data/dishes_related
    original_file = "data/dishes_related/inventory_calculation_data_manual_extracted.xlsx"
    calc_data_file = "calculation_sheets_extraction.xlsx"  # From the extraction script
    output_file = "output/inventory_calculation_data_final_corrected.xlsx"
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Read the original file
    print("Reading original file...")
    df = pd.read_excel(original_file)
    print(f"Original file has {len(df)} rows")
    
    # Read the calculation sheet data
    print("\nReading calculation sheet data...")
    calc_df = pd.read_excel(calc_data_file)
    print(f"Calculation data has {len(calc_df)} rows")
    
    # Create mapping from calculation data
    print("\nCreating mapping from calculation sheets...")
    mapping_dict = {}
    
    for _, row in calc_df.iterrows():
        # Create multiple keys for better matching
        if all(col in row.index for col in ['门店名称', '菜品名称', '物料号']):
            if pd.notna(row['物料号']):
                key1 = (row['门店名称'], row['菜品名称'], str(row['物料号']).replace('.0', ''))
                mapping_dict[key1] = {
                    '损耗': row.get('损耗', 1.0) if pd.notna(row.get('损耗')) else 1.0,
                    '物料单位': row.get('物料单位', 1.0) if pd.notna(row.get('物料单位')) else 1.0,
                    '出品分量': row.get('出品分量', pd.NA) if pd.notna(row.get('出品分量')) else pd.NA
                }
    
    print(f"Created {len(mapping_dict)} mappings")
    
    # Apply mappings
    print("\nApplying mappings...")
    matched_count = 0
    
    for idx in df.index:
        row = df.loc[idx]
        key = (row['门店名称'], row['菜品名称'], str(row['物料号']))
        
        if key in mapping_dict:
            mapping = mapping_dict[key]
            df.at[idx, '损耗'] = mapping['损耗']
            df.at[idx, '物料单位'] = mapping['物料单位']
            
            # Also update 出品分量 if available and different
            if pd.notna(mapping['出品分量']) and pd.notna(df.at[idx, '出品分量(kg)']):
                # Only update if significantly different (allows for some rounding differences)
                if abs(float(df.at[idx, '出品分量(kg)']) - float(mapping['出品分量'])) > 0.01:
                    print(f"  Updating 出品分量 for {row['菜品名称']}: {df.at[idx, '出品分量(kg)']} -> {mapping['出品分量']}")
                    df.at[idx, '出品分量(kg)'] = mapping['出品分量']
            
            matched_count += 1
        else:
            # Use defaults
            df.at[idx, '损耗'] = 1.0
            df.at[idx, '物料单位'] = 1.0
    
    print(f"Matched {matched_count} rows from calculation sheets")
    
    # Now fix known issues
    print("\n\n=== FIXING KNOWN ISSUES ===")
    
    # Fix beer serving sizes
    print("\nFixing beer serving sizes...")
    beer_fixes = 0
    
    # Define correct serving sizes for beverages
    beverage_serving_sizes = {
        '330ml': 0.33,
        '330毫升': 0.33,
        '355ml': 0.355,
        '473ml': 0.473,
        '500ml': 0.50,
        '500毫升': 0.50,
        '650ml': 0.65,
        '1.25l': 1.25,
        '1250ml': 1.25,
        '250ml': 0.25
    }
    
    # Find beverage items
    beverage_keywords = ['啤酒', 'beer', '朝日', '青岛', '百威', '科罗娜', 'smirnoff', 
                        '可乐', '雪碧', '芬达', '王老吉', '茶', '汁', 'coke', 'sprite']
    
    for idx in df.index:
        row = df.loc[idx]
        dish_name = str(row['菜品名称']).lower()
        spec = str(row.get('规格', '')).lower()
        combined_text = f"{dish_name} {spec}"
        
        # Check if it's a beverage
        is_beverage = any(keyword in combined_text for keyword in beverage_keywords)
        
        if is_beverage:
            current_serving = row['出品分量(kg)']
            
            # Find the correct serving size
            for volume_key, correct_size in beverage_serving_sizes.items():
                if volume_key in combined_text:
                    # Only fix if the current value is way off (e.g., 1.0 instead of 0.33)
                    if abs(current_serving - correct_size) > 0.1:
                        print(f"  Fixing {row['菜品名称']} ({row.get('规格', '')}): {current_serving} -> {correct_size}")
                        df.at[idx, '出品分量(kg)'] = correct_size
                        beer_fixes += 1
                    break
    
    print(f"Fixed {beer_fixes} beverage serving sizes")
    
    # Save the corrected file
    print(f"\n\nSaving corrected file to: {output_file}")
    df.to_excel(output_file, index=False)
    
    # Show specific examples for Store 5 beers
    print("\n\n=== VERIFICATION: Store 5 Beer Items ===")
    store5_beers = df[
        (df['门店名称'] == '加拿大五店') & 
        (df['菜品名称'].str.contains('朝日|青岛|啤酒', na=False, case=False))
    ]
    
    if len(store5_beers) > 0:
        print(f"Found {len(store5_beers)} beer items in Store 5:")
        display_cols = ['菜品名称', '规格', '出品分量(kg)', '损耗', '物料单位']
        for col in display_cols:
            if col in store5_beers.columns:
                print(f"\n{col}:")
                print(store5_beers[col].tolist()[:10])
    
    # Show summary statistics
    print("\n\n=== SUMMARY STATISTICS ===")
    print(f"Total rows: {len(df)}")
    print(f"损耗 non-null: {df['损耗'].notna().sum()}")
    print(f"物料单位 non-null: {df['物料单位'].notna().sum()}")
    print(f"出品分量(kg) non-null: {df['出品分量(kg)'].notna().sum()}")
    
    print("\n出品分量(kg) distribution for beverages:")
    beverage_mask = df['菜品名称'].str.contains('|'.join(beverage_keywords), na=False, case=False)
    beverage_serving_dist = df[beverage_mask]['出品分量(kg)'].value_counts().head(10)
    print(beverage_serving_dist)


if __name__ == "__main__":
    final_fix_with_corrections()