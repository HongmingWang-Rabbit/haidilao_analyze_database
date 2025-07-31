#!/usr/bin/env python3
"""
Apply Calculation Sheet Data Only

This script applies the calculation sheet data WITHOUT any "corrections" or "fixes".
It respects the actual values from the calculation sheets, including 出品分量 = 1.0 for beers.
"""

import pandas as pd
import sys
from pathlib import Path
import shutil

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def apply_calculation_sheet_data_only():
    """Apply calculation sheet data without any modifications"""
    
    # File paths
    original_file = "data/dishes_related/inventory_calculation_data_manual_extracted.xlsx"
    calc_data_file = "calculation_sheets_extraction.xlsx"  # From the extraction script
    output_file = "output/inventory_calculation_data_from_sheets_only.xlsx"
    
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
    
    # Apply mappings WITHOUT any "fixes"
    print("\nApplying mappings (NO CORRECTIONS)...")
    matched_count = 0
    updated_serving_count = 0
    
    for idx in df.index:
        row = df.loc[idx]
        key = (row['门店名称'], row['菜品名称'], str(row['物料号']))
        
        if key in mapping_dict:
            mapping = mapping_dict[key]
            df.at[idx, '损耗'] = mapping['损耗']
            df.at[idx, '物料单位'] = mapping['物料单位']
            
            # Update 出品分量(kg) from calculation sheet if available
            if pd.notna(mapping['出品分量']):
                original_serving = df.at[idx, '出品分量(kg)']
                new_serving = float(mapping['出品分量'])
                
                # Always use the value from calculation sheet, no "corrections"
                if pd.notna(original_serving) and abs(float(original_serving) - new_serving) > 0.001:
                    print(f"  Updating 出品分量 for {row['菜品名称']}: {original_serving} -> {new_serving}")
                    updated_serving_count += 1
                
                df.at[idx, '出品分量(kg)'] = new_serving
            
            matched_count += 1
        else:
            # Use defaults for unmatched rows
            df.at[idx, '损耗'] = 1.0
            df.at[idx, '物料单位'] = 1.0
    
    print(f"Matched {matched_count} rows from calculation sheets")
    print(f"Updated {updated_serving_count} serving sizes from calculation sheets")
    
    # Save the file WITHOUT any beverage "fixes"
    print(f"\n\nSaving file to: {output_file}")
    df.to_excel(output_file, index=False)
    
    # Show specific examples for Store 5 beers to verify
    print("\n\n=== VERIFICATION: Store 5 Beer Items ===")
    store5_beers = df[
        (df['门店名称'] == '加拿大五店') & 
        (df['菜品名称'].str.contains('朝日|青岛|啤酒', na=False, case=False))
    ]
    
    if len(store5_beers) > 0:
        print(f"Found {len(store5_beers)} beer items in Store 5:")
        display_cols = ['菜品名称', '规格', '出品分量(kg)', '损耗', '物料单位']
        
        print("\nStore 5 beer serving sizes (AS-IS from calculation sheets):")
        for _, row in store5_beers.iterrows():
            dish_name = row['菜品名称']
            spec = row.get('规格', '')
            serving = row['出品分量(kg)']
            print(f"  {dish_name} {spec}: 出品分量 = {serving} kg")
    
    # Show summary statistics
    print("\n\n=== SUMMARY STATISTICS ===")
    print(f"Total rows: {len(df)}")
    print(f"损耗 non-null: {df['损耗'].notna().sum()}")
    print(f"物料单位 non-null: {df['物料单位'].notna().sum()}")
    print(f"出品分量(kg) non-null: {df['出品分量(kg)'].notna().sum()}")
    
    # Show the distribution of 出品分量 values for beers
    print("\n出品分量(kg) distribution for beer items:")
    beer_keywords = ['啤酒', 'beer', '朝日', '青岛', '百威', '科罗娜']
    beer_mask = df['菜品名称'].str.contains('|'.join(beer_keywords), na=False, case=False)
    beer_serving_dist = df[beer_mask]['出品分量(kg)'].value_counts().head(10)
    print(beer_serving_dist)
    
    print("\n✅ Applied calculation sheet data WITHOUT any corrections or fixes!")
    print("The file now contains the exact values from the calculation sheets.")


if __name__ == "__main__":
    apply_calculation_sheet_data_only()