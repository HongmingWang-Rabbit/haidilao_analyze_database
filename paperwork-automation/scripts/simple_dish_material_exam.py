#!/usr/bin/env python3
"""
Simple examination of calculated dish material usage files
Avoids Unicode issues by not printing Chinese text
"""

import pandas as pd
from pathlib import Path

def examine_file():
    """Simple examination avoiding Unicode issues"""
    
    print("EXAMINING CALCULATED DISH MATERIAL FILE")
    print("=" * 40)
    
    file_path = Path("history_files/monthly_report_inputs/2025-06/calculated_dish_material_usage/material_usage.xls")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return False
    
    try:
        # Read file with xlrd engine
        df = pd.read_excel(file_path, engine='xlrd', nrows=20)
        
        print(f"File shape: {df.shape}")
        print(f"Columns count: {len(df.columns)}")
        
        # Count potential dish-material relationship indicators
        dish_related = 0
        material_related = 0
        quantity_related = 0
        
        for col in df.columns:
            col_str = str(col).lower()
            if 'code' in col_str or '编码' in col_str:
                dish_related += 1
            if 'material' in col_str or '物料' in col_str:
                material_related += 1
            if 'quantity' in col_str or '用量' in col_str or '数量' in col_str:
                quantity_related += 1
        
        print(f"Dish-related columns: {dish_related}")
        print(f"Material-related columns: {material_related}")
        print(f"Quantity-related columns: {quantity_related}")
        
        # Show numeric data only (avoid Chinese text)
        numeric_cols = df.select_dtypes(include=['number']).columns
        print(f"Numeric columns: {len(numeric_cols)}")
        
        if len(numeric_cols) > 0:
            print("Sample numeric data:")
            print(df[numeric_cols[:3]].head(3).to_string())
        
        # Check if this looks like dish-material data
        has_relationships = dish_related > 0 and material_related > 0
        print(f"\nLikely contains dish-material relationships: {has_relationships}")
        
        return has_relationships
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    examine_file()