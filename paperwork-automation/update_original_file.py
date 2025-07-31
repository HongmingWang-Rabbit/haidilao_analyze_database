#!/usr/bin/env python3
"""
Update Original File

This script copies the original input file and updates it with 损耗 and 物料单位 values.
"""

import pandas as pd
import shutil
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def update_original_file():
    """Update the original file with merged values"""
    
    try:
        # File paths
        input_file = "Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx"
        output_file = "output/inventory_calculation_data_manual_extracted_updated.xlsx"
        
        # Create output directory if it doesn't exist
        Path("output").mkdir(exist_ok=True)
        
        # First, copy the file to output
        print(f"Copying {input_file} to {output_file}")
        shutil.copy2(input_file, output_file)
        
        # Read the file
        print(f"\nReading file to update...")
        df = pd.read_excel(output_file, sheet_name='Sheet1')
        print(f"Data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Check current state of target columns
        print("\nCurrent state of target columns:")
        print(f"损耗 - Non-null values: {df['损耗'].notna().sum()}")
        print(f"物料单位 - Non-null values: {df['物料单位'].notna().sum()}")
        
        # Read the database extract
        db_file = "dish_material_data_from_database.xlsx"
        print(f"\nReading database extract: {db_file}")
        db_df = pd.read_excel(db_file, sheet_name='Full_Data')
        
        # Create mapping dictionary
        print("\nCreating mapping dictionary...")
        mapping_dict = {}
        for _, row in db_df.iterrows():
            key = (row['store_name'], row['dish_name'], str(row['material_number']))
            mapping_dict[key] = {
                'loss_rate': row['loss_rate'],
                'unit_conversion_rate': row['unit_conversion_rate']
            }
        
        print(f"Created {len(mapping_dict)} unique mappings")
        
        # Apply mappings with defaults
        print("\nUpdating values...")
        
        matched_count = 0
        defaulted_count = 0
        
        # Update each row
        for idx in df.index:
            row = df.loc[idx]
            key = (row['门店名称'], row['菜品名称'], str(row['物料号']))
            
            if key in mapping_dict:
                # Use values from database
                mapping = mapping_dict[key]
                df.at[idx, '损耗'] = mapping['loss_rate']
                df.at[idx, '物料单位'] = mapping['unit_conversion_rate']
                matched_count += 1
            else:
                # Use default values
                df.at[idx, '损耗'] = 1.0
                df.at[idx, '物料单位'] = 1.0
                defaulted_count += 1
        
        print(f"\nUpdate complete:")
        print(f"  - Matched from database: {matched_count} rows")
        print(f"  - Used default values: {defaulted_count} rows")
        
        # Verify the update
        print("\nAfter update:")
        print(f"损耗 - Non-null values: {df['损耗'].notna().sum()}")
        print(f"物料单位 - Non-null values: {df['物料单位'].notna().sum()}")
        
        # Save the updated file
        print(f"\nSaving updated file to: {output_file}")
        with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False)
        
        print("\n✅ File successfully updated!")
        
        # Show sample of updated data
        print("\nSample of updated data (first 10 rows):")
        sample_cols = ['菜品名称', '物料描述', '出品分量(kg)', '损耗', '物料单位']
        print(df[sample_cols].head(10).to_string())
        
        # Value distribution
        print("\n损耗 value distribution:")
        print(df['损耗'].value_counts().head())
        
        print("\n物料单位 value distribution:")
        print(df['物料单位'].value_counts().head())
        
    except Exception as e:
        print(f"Error updating file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_original_file()