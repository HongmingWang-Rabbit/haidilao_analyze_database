#!/usr/bin/env python3
"""
Analyze Unmatched Rows

This script analyzes why some rows didn't match between the files.
"""

import pandas as pd
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_unmatched_rows():
    """Analyze why rows didn't match"""
    
    try:
        # Read both files
        existing_df = pd.read_excel("Input/monthly_report/calculated_dish_material_usage/inventory_calculation_data_manual_extracted.xlsx")
        db_df = pd.read_excel("dish_material_data_from_database.xlsx", sheet_name='Full_Data')
        
        # Get unique values from each file
        print("=== ANALYSIS OF UNMATCHED ROWS ===\n")
        
        # Store names
        existing_stores = set(existing_df['门店名称'].unique())
        db_stores = set(db_df['store_name'].unique())
        
        print("1. STORE COMPARISON:")
        print(f"   Stores in existing file: {existing_stores}")
        print(f"   Stores in database: {db_stores}")
        print(f"   Stores only in existing file: {existing_stores - db_stores}")
        print(f"   Stores only in database: {db_stores - existing_stores}")
        
        # Dish names
        existing_dishes = set(existing_df['菜品名称'].unique())
        db_dishes = set(db_df['dish_name'].unique())
        
        print(f"\n2. DISH COMPARISON:")
        print(f"   Total unique dishes in existing file: {len(existing_dishes)}")
        print(f"   Total unique dishes in database: {len(db_dishes)}")
        print(f"   Dishes only in existing file: {len(existing_dishes - db_dishes)}")
        print(f"   Dishes only in database: {len(db_dishes - existing_dishes)}")
        
        # Show some examples of dishes only in existing file
        only_in_existing = list(existing_dishes - db_dishes)[:10]
        print(f"   Examples of dishes only in existing file:")
        for dish in only_in_existing:
            print(f"     - {dish}")
        
        # Material numbers
        existing_materials = set(existing_df['物料号'].astype(str).unique())
        db_materials = set(db_df['material_number'].astype(str).unique())
        
        print(f"\n3. MATERIAL COMPARISON:")
        print(f"   Total unique materials in existing file: {len(existing_materials)}")
        print(f"   Total unique materials in database: {len(db_materials)}")
        print(f"   Materials only in existing file: {len(existing_materials - db_materials)}")
        print(f"   Materials only in database: {len(db_materials - existing_materials)}")
        
        # Analyze specific unmatched cases
        print(f"\n4. SPECIFIC UNMATCHED ANALYSIS:")
        
        # Find rows where dish exists in DB but combination doesn't match
        unmatched_with_dish_in_db = []
        for _, row in existing_df.iterrows():
            dish_name = row['菜品名称']
            if dish_name in db_dishes:
                # Check if this specific combination exists
                db_match = db_df[
                    (db_df['store_name'] == row['门店名称']) &
                    (db_df['dish_name'] == dish_name) &
                    (db_df['material_number'].astype(str) == str(row['物料号']))
                ]
                if db_match.empty:
                    unmatched_with_dish_in_db.append({
                        'store': row['门店名称'],
                        'dish': dish_name,
                        'material': row['物料号'],
                        'material_desc': row['物料描述']
                    })
        
        print(f"   Found {len(unmatched_with_dish_in_db)} cases where dish exists but combination doesn't")
        print("   First 5 examples:")
        for item in unmatched_with_dish_in_db[:5]:
            print(f"     - {item['dish']} + {item['material_desc']} in {item['store']}")
        
        # Save detailed analysis
        output_file = "unmatched_analysis.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Dishes only in existing
            pd.DataFrame({'Dishes_Only_In_Existing': list(existing_dishes - db_dishes)}).to_excel(
                writer, sheet_name='Dishes_Only_Existing', index=False)
            
            # Materials only in existing
            pd.DataFrame({'Materials_Only_In_Existing': list(existing_materials - db_materials)}).to_excel(
                writer, sheet_name='Materials_Only_Existing', index=False)
            
            # Unmatched combinations
            if unmatched_with_dish_in_db:
                pd.DataFrame(unmatched_with_dish_in_db).to_excel(
                    writer, sheet_name='Unmatched_Combinations', index=False)
        
        print(f"\nDetailed analysis saved to: {output_file}")
        
    except Exception as e:
        print(f"Error analyzing unmatched rows: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_unmatched_rows()