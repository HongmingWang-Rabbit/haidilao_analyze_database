#!/usr/bin/env python3
"""
Extract Dish Material Data from Database

This script extracts dish-material relationship data including:
- standard_quantity (出品分量)
- loss_rate (损耗)
- unit_conversion_rate (物料单位)
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from utils.database import DatabaseConfig, DatabaseManager
import pandas as pd

def extract_dish_material_data():
    """Extract dish-material data from database"""
    
    try:
        # Setup database connection
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, check the structure of dish_material table
            print("Checking dish_material table structure...")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'dish_material'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print("\nColumns in dish_material table:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
            
            # First check dish table structure
            print("\n\nChecking dish table structure...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'dish'
                ORDER BY ordinal_position
            """)
            dish_cols = cursor.fetchall()
            print("Dish table columns:", [col['column_name'] for col in dish_cols])
            
            # Query dish-material relationships with all relevant data
            print("\n\nExtracting dish-material relationships...")
            
            query = """
                SELECT 
                    d.store_id,
                    s.name as store_name,
                    d.id as dish_id,
                    d.name as dish_name,
                    d.size as dish_size,
                    m.id as material_id,
                    m.material_number,
                    m.name as material_name,
                    m.unit as material_unit,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate,
                    dm.created_at,
                    dm.updated_at
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id
                JOIN material m ON dm.material_id = m.id
                JOIN store s ON d.store_id = s.id
                WHERE d.is_active = TRUE
                AND m.is_active = TRUE
                ORDER BY s.name, d.name, m.material_number
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            print(f"\nExtracted {len(df)} dish-material relationships")
            
            # Show sample data
            if len(df) > 0:
                print("\nSample data:")
                print(df.head(10))
                
                # Check for null values in key columns
                print("\n\nNull value counts:")
                for col in ['standard_quantity', 'loss_rate', 'unit_conversion_rate']:
                    null_count = df[col].isna().sum()
                    print(f"  {col}: {null_count} nulls ({null_count/len(df)*100:.1f}%)")
                
                # Show unique values for unit_conversion_rate
                print("\n\nUnique unit_conversion_rate values (top 20):")
                unique_rates = df['unit_conversion_rate'].value_counts().head(20)
                for rate, count in unique_rates.items():
                    print(f"  {rate}: {count} occurrences")
            
            # Save to Excel file
            output_file = "dish_material_data_from_database.xlsx"
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Full data
                df.to_excel(writer, sheet_name='Full_Data', index=False)
                
                # Summary by store
                store_summary = df.groupby('store_name').agg({
                    'dish_name': 'count',
                    'standard_quantity': ['mean', 'min', 'max'],
                    'loss_rate': ['mean', 'min', 'max'],
                    'unit_conversion_rate': ['mean', 'min', 'max']
                }).round(4)
                store_summary.columns = ['dish_count', 'std_qty_mean', 'std_qty_min', 'std_qty_max', 
                                        'loss_rate_mean', 'loss_rate_min', 'loss_rate_max',
                                        'conversion_rate_mean', 'conversion_rate_min', 'conversion_rate_max']
                store_summary.to_excel(writer, sheet_name='Store_Summary')
                
                # Materials with unit conversion rates
                materials_with_rates = df[df['unit_conversion_rate'].notna()][
                    ['material_number', 'material_name', 'material_unit', 'unit_conversion_rate']
                ].drop_duplicates().sort_values('material_number')
                materials_with_rates.to_excel(writer, sheet_name='Material_Conversion_Rates', index=False)
                
            print(f"\n\nData saved to: {output_file}")
            
            # Also create a CSV file for easy merging
            csv_file = "dish_material_for_merge.csv"
            merge_df = df[['dish_name', 'material_number', 'standard_quantity', 'loss_rate', 'unit_conversion_rate']]
            merge_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"Merge-ready data saved to: {csv_file}")
            
            return df
            
    except Exception as e:
        print(f"Error extracting data: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    extract_dish_material_data()