#!/usr/bin/env python3
"""
Show a simple summary of the inventory extraction
"""

import pandas as pd
from pathlib import Path

def show_summary():
    """Show extraction summary"""
    
    # Find the most recent extraction file
    extraction_dir = Path("output/inventory_extraction")
    excel_files = list(extraction_dir.glob("inventory_calculation_data_*.xlsx"))
    latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
    
    # Read the data
    df = pd.read_excel(latest_file)
    
    print("INVENTORY EXTRACTION SUMMARY")
    print("=" * 50)
    print(f"File: {latest_file.name}")
    print(f"Total records extracted: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print()
    
    print("Records by store:")
    if "store_id" in df.columns:
        store_counts = df["store_id"].value_counts().sort_index()
        for store_id, count in store_counts.items():
            print(f"  Store {store_id}: {count} records")
    print()
    
    print("Column mapping success:")
    requested_columns = [
        "门店名称", "大类名称", "子类名称", "菜品编码", "菜品短编码", 
        "菜品名称", "规格", "出品分量(kg)", "损耗", "物料单位", 
        "物料号", "物料描述", "单位"
    ]
    
    found_count = 0
    for col in requested_columns:
        if col in df.columns:
            print(f"  ✅ {col}")
            found_count += 1
        else:
            print(f"  ❌ {col} (not found)")
    
    print(f"\\nSuccess rate: {found_count}/{len(requested_columns)} columns ({found_count/len(requested_columns)*100:.1f}%)")
    print("=" * 50)

if __name__ == "__main__":
    show_summary()