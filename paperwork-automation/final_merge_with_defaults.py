#!/usr/bin/env python3
"""
Final Merge with Defaults

This script merges the dish-material data and sets default values for unmatched rows:
- 损耗: 1 (default)
- 物料单位: 1 (default)
"""

import pandas as pd
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def final_merge_with_defaults():
    """Merge data with defaults for unmatched rows"""
    
    try:
        # Read the existing file
        existing_file = "Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx"
        print(f"Reading existing file: {existing_file}")
        existing_df = pd.read_excel(existing_file, sheet_name='Sheet1')
        print(f"Existing data shape: {existing_df.shape}")
        
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
        print("\nApplying mappings with defaults...")
        
        # Initialize counters
        matched_count = 0
        defaulted_count = 0
        
        # Process each row
        loss_rate_values = []
        unit_conversion_values = []
        
        for idx, row in existing_df.iterrows():
            key = (row['门店名称'], row['菜品名称'], str(row['物料号']))
            
            if key in mapping_dict:
                # Use values from database
                mapping = mapping_dict[key]
                loss_rate_values.append(mapping['loss_rate'])
                unit_conversion_values.append(mapping['unit_conversion_rate'])
                matched_count += 1
            else:
                # Use default values
                loss_rate_values.append(1.0)
                unit_conversion_values.append(1.0)
                defaulted_count += 1
        
        # Update the dataframe
        existing_df['损耗'] = loss_rate_values
        existing_df['物料单位'] = unit_conversion_values
        
        print(f"\nProcessing complete:")
        print(f"  - Matched from database: {matched_count} rows ({matched_count/len(existing_df)*100:.1f}%)")
        print(f"  - Used default values: {defaulted_count} rows ({defaulted_count/len(existing_df)*100:.1f}%)")
        
        # Save the final result
        output_file = "inventory_calculation_data_final.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main data
            existing_df.to_excel(writer, sheet_name='Final_Data', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Rows',
                    'Matched from Database',
                    'Used Default Values',
                    'Match Rate',
                    'Default Rate'
                ],
                'Value': [
                    len(existing_df),
                    matched_count,
                    defaulted_count,
                    f"{matched_count/len(existing_df)*100:.1f}%",
                    f"{defaulted_count/len(existing_df)*100:.1f}%"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Value distribution
            value_dist_data = {
                '损耗_Value': existing_df['损耗'].value_counts().index.tolist()[:20],
                '损耗_Count': existing_df['损耗'].value_counts().values.tolist()[:20],
                '物料单位_Value': existing_df['物料单位'].value_counts().index.tolist()[:20],
                '物料单位_Count': existing_df['物料单位'].value_counts().values.tolist()[:20]
            }
            # Pad shorter columns with None
            max_len = max(len(v) for v in value_dist_data.values())
            for key, values in value_dist_data.items():
                value_dist_data[key] = values + [None] * (max_len - len(values))
            
            value_dist_df = pd.DataFrame(value_dist_data)
            value_dist_df.to_excel(writer, sheet_name='Value_Distribution', index=False)
        
        print(f"\nFinal data saved to: {output_file}")
        
        # Show summary of values
        print("\n损耗 value distribution (top 5):")
        for value, count in existing_df['损耗'].value_counts().head().items():
            print(f"  {value}: {count} occurrences")
        
        print("\n物料单位 value distribution (top 5):")
        for value, count in existing_df['物料单位'].value_counts().head().items():
            print(f"  {value}: {count} occurrences")
        
        # Also save as CSV for easy use
        csv_file = "inventory_calculation_data_final.csv"
        existing_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"\nAlso saved as CSV: {csv_file}")
        
    except Exception as e:
        print(f"Error in final merge: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    final_merge_with_defaults()