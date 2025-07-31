#!/usr/bin/env python3
"""
Merge Dish Material Data

This script merges the dish-material data from the database with your existing file
to add the missing columns: 出品分量(kg), 损耗, and 物料单位
"""

import pandas as pd
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def merge_dish_material_data():
    """Merge database data with existing file"""
    
    try:
        # Read the existing file with empty columns
        existing_file = "Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx"
        print(f"Reading existing file: {existing_file}")
        existing_df = pd.read_excel(existing_file, sheet_name='Sheet1')
        print(f"Existing data shape: {existing_df.shape}")
        
        # Read the database extract
        db_file = "dish_material_data_from_database.xlsx"
        print(f"\nReading database extract: {db_file}")
        db_df = pd.read_excel(db_file, sheet_name='Full_Data')
        print(f"Database data shape: {db_df.shape}")
        
        # Prepare for merging
        # Create a mapping dictionary for each dish-material combination
        print("\nCreating mapping dictionary...")
        
        # Group by dish name and material number to get unique values
        mapping_dict = {}
        for _, row in db_df.iterrows():
            key = (row['store_name'], row['dish_name'], row['material_number'])
            mapping_dict[key] = {
                'standard_quantity': row['standard_quantity'],
                'loss_rate': row['loss_rate'],
                'unit_conversion_rate': row['unit_conversion_rate']
            }
        
        print(f"Created {len(mapping_dict)} unique mappings")
        
        # Apply mapping to existing data
        print("\nApplying mappings to existing data...")
        
        # Initialize the columns with current values (should be NaN)
        existing_df['出品分量(kg)_new'] = pd.NA
        existing_df['损耗_new'] = pd.NA
        existing_df['物料单位_new'] = pd.NA
        
        # Track matches
        matched_count = 0
        unmatched_rows = []
        
        for idx, row in existing_df.iterrows():
            key = (row['门店名称'], row['菜品名称'], row['物料号'])
            
            if key in mapping_dict:
                mapping = mapping_dict[key]
                existing_df.at[idx, '出品分量(kg)_new'] = mapping['standard_quantity']
                existing_df.at[idx, '损耗_new'] = mapping['loss_rate']
                existing_df.at[idx, '物料单位_new'] = mapping['unit_conversion_rate']
                matched_count += 1
            else:
                unmatched_rows.append({
                    'row': idx + 2,  # Excel row number (1-indexed + header)
                    'store': row['门店名称'],
                    'dish': row['菜品名称'],
                    'material': row['物料号']
                })
        
        print(f"\nMatched {matched_count} out of {len(existing_df)} rows ({matched_count/len(existing_df)*100:.1f}%)")
        
        # Replace original columns with new values
        existing_df['出品分量(kg)'] = existing_df['出品分量(kg)_new']
        existing_df['损耗'] = existing_df['损耗_new']
        existing_df['物料单位'] = existing_df['物料单位_new']
        
        # Drop temporary columns
        existing_df = existing_df.drop(columns=['出品分量(kg)_new', '损耗_new', '物料单位_new'])
        
        # Save the merged data
        output_file = "inventory_calculation_data_with_values.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main data
            existing_df.to_excel(writer, sheet_name='Merged_Data', index=False)
            
            # Summary statistics
            summary_df = pd.DataFrame({
                'Metric': ['Total Rows', 'Matched Rows', 'Unmatched Rows', 'Match Rate'],
                'Value': [
                    len(existing_df),
                    matched_count,
                    len(existing_df) - matched_count,
                    f"{matched_count/len(existing_df)*100:.1f}%"
                ]
            })
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Unmatched rows report
            if unmatched_rows:
                unmatched_df = pd.DataFrame(unmatched_rows[:100])  # First 100 unmatched
                unmatched_df.to_excel(writer, sheet_name='Unmatched_Rows', index=False)
        
        print(f"\nMerged data saved to: {output_file}")
        
        # Show sample of merged data
        print("\nSample of merged data (rows with values):")
        sample_with_values = existing_df[existing_df['出品分量(kg)'].notna()].head(10)
        if len(sample_with_values) > 0:
            for col in ['菜品名称', '物料描述', '出品分量(kg)', '损耗', '物料单位']:
                print(f"\n{col}:")
                print(sample_with_values[col].tolist())
        
        # Report on unmatched rows
        if unmatched_rows:
            print(f"\n\nFound {len(unmatched_rows)} unmatched rows")
            print("First 10 unmatched rows:")
            for row_info in unmatched_rows[:10]:
                print(f"  Row {row_info['row']}: {row_info['dish']} - {row_info['material']}")
                
    except Exception as e:
        print(f"Error merging data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    merge_dish_material_data()