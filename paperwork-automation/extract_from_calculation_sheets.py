#!/usr/bin/env python3
"""
Extract from Calculation Sheets

This script extracts 损耗 and 物料单位 data from the "计算" sheets 
in inventory checking result files for each store.
"""

import pandas as pd
import sys
from pathlib import Path
import shutil

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_calculation_data():
    """Extract data from all calculation sheets"""
    
    base_path = Path("Input/monthly_report/inventory_checking_result")
    all_data = []
    
    # Process each store
    for store_num in range(1, 8):
        store_path = base_path / str(store_num)
        inventory_files = list(store_path.glob("*.xls*"))
        
        if inventory_files:
            file_path = inventory_files[0]
            print(f"\nProcessing Store {store_num}: {file_path.name}")
            
            try:
                # Read the 计算 sheet
                df = pd.read_excel(file_path, sheet_name='计算')
                
                # Standardize column names (different stores use slightly different names)
                column_mapping = {
                    '出品分量(kg)': '出品分量',
                    '出品分量': '出品分量',
                    '出品份量': '出品分量'
                }
                
                # Rename columns if they exist
                for old_name, new_name in column_mapping.items():
                    if old_name in df.columns:
                        df = df.rename(columns={old_name: new_name})
                
                # Extract relevant columns
                relevant_cols = ['门店名称', '菜品名称', '规格', '物料号', '物料描述', '出品分量', '损耗', '物料单位']
                
                # Only keep columns that exist
                existing_cols = [col for col in relevant_cols if col in df.columns]
                extracted_df = df[existing_cols].copy()
                
                # Add store number if not present
                if '门店名称' not in extracted_df.columns:
                    extracted_df['门店名称'] = f'加拿大{["一", "二", "三", "四", "五", "六", "七"][store_num-1]}店'
                
                # Convert material number to string to avoid float conversion
                if '物料号' in extracted_df.columns:
                    extracted_df['物料号'] = extracted_df['物料号'].astype(str).str.replace('.0$', '', regex=True)
                
                # Remove rows where all key values are null
                key_cols = ['出品分量', '损耗', '物料单位']
                existing_key_cols = [col for col in key_cols if col in extracted_df.columns]
                if existing_key_cols:
                    extracted_df = extracted_df.dropna(subset=existing_key_cols, how='all')
                
                print(f"  Extracted {len(extracted_df)} rows with data")
                print(f"  损耗 non-null: {extracted_df['损耗'].notna().sum() if '损耗' in extracted_df.columns else 0}")
                print(f"  物料单位 non-null: {extracted_df['物料单位'].notna().sum() if '物料单位' in extracted_df.columns else 0}")
                
                all_data.append(extracted_df)
                
            except Exception as e:
                print(f"  Error processing store {store_num}: {e}")
    
    # Combine all data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"\n\nTotal combined data: {len(combined_df)} rows")
        
        # Save combined extraction
        extraction_file = "calculation_sheets_extraction.xlsx"
        combined_df.to_excel(extraction_file, index=False)
        print(f"Saved extraction to: {extraction_file}")
        
        # Now merge with the original file
        merge_with_original(combined_df)
        
    else:
        print("No data extracted from calculation sheets")


def merge_with_original(calc_data):
    """Merge calculation data with the original file"""
    
    # File paths
    input_file = "Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx"
    output_file = "output/inventory_calculation_data_from_calc_sheets.xlsx"
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Copy the file
    print(f"\n\nCopying {input_file} to {output_file}")
    shutil.copy2(input_file, output_file)
    
    # Read the file
    print("Reading file to update...")
    df = pd.read_excel(output_file, sheet_name='Sheet1')
    
    # Create mapping dictionary from calculation data
    print("\nCreating mapping from calculation sheets...")
    mapping_dict = {}
    
    for _, row in calc_data.iterrows():
        # Try multiple key combinations
        # Key 1: Store + Dish + Material Number
        if all(col in row.index for col in ['门店名称', '菜品名称', '物料号']):
            if pd.notna(row['物料号']):
                key1 = (row['门店名称'], row['菜品名称'], str(row['物料号']))
                mapping_dict[key1] = {
                    '损耗': row.get('损耗', 1.0) if pd.notna(row.get('损耗')) else 1.0,
                    '物料单位': row.get('物料单位', 1.0) if pd.notna(row.get('物料单位')) else 1.0
                }
        
        # Key 2: Store + Dish + Spec (for cases without material number)
        if all(col in row.index for col in ['门店名称', '菜品名称', '规格']):
            key2 = (row['门店名称'], row['菜品名称'], row.get('规格', ''))
            if key2 not in mapping_dict:  # Don't override if we already have a material-based match
                mapping_dict[key2] = {
                    '损耗': row.get('损耗', 1.0) if pd.notna(row.get('损耗')) else 1.0,
                    '物料单位': row.get('物料单位', 1.0) if pd.notna(row.get('物料单位')) else 1.0
                }
    
    print(f"Created {len(mapping_dict)} mappings from calculation sheets")
    
    # Apply mappings
    print("\nApplying mappings...")
    matched_count = 0
    defaulted_count = 0
    
    for idx in df.index:
        row = df.loc[idx]
        
        # Try to match with material number first
        key1 = (row['门店名称'], row['菜品名称'], str(row['物料号']))
        # Try to match with spec as fallback
        key2 = (row['门店名称'], row['菜品名称'], row.get('规格', ''))
        
        matched = False
        if key1 in mapping_dict:
            mapping = mapping_dict[key1]
            df.at[idx, '损耗'] = mapping['损耗']
            df.at[idx, '物料单位'] = mapping['物料单位']
            matched_count += 1
            matched = True
        elif key2 in mapping_dict:
            mapping = mapping_dict[key2]
            df.at[idx, '损耗'] = mapping['损耗']
            df.at[idx, '物料单位'] = mapping['物料单位']
            matched_count += 1
            matched = True
        
        if not matched:
            # Use default values
            df.at[idx, '损耗'] = 1.0
            df.at[idx, '物料单位'] = 1.0
            defaulted_count += 1
    
    print(f"\nUpdate complete:")
    print(f"  - Matched from calculation sheets: {matched_count} rows ({matched_count/len(df)*100:.1f}%)")
    print(f"  - Used default values: {defaulted_count} rows ({defaulted_count/len(df)*100:.1f}%)")
    
    # Save the updated file
    print(f"\nSaving updated file...")
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    
    print(f"\n✅ File successfully updated: {output_file}")
    
    # Show sample of updated data
    print("\nSample of updated data:")
    sample_cols = ['菜品名称', '物料描述', '出品分量(kg)', '损耗', '物料单位']
    print(df[sample_cols].head(10).to_string())
    
    # Value distribution
    print("\n损耗 value distribution:")
    print(df['损耗'].value_counts().head(10))
    
    print("\n物料单位 value distribution:")
    print(df['物料单位'].value_counts().head(10))


if __name__ == "__main__":
    extract_calculation_data()