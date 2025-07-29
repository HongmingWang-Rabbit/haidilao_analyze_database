#!/usr/bin/env python3
"""
Verify the inventory extraction results and show a summary
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_extraction():
    """Verify the latest extraction results"""
    
    # Find the most recent extraction file
    extraction_dir = Path("output/inventory_extraction")
    if not extraction_dir.exists():
        logger.error("No extraction directory found!")
        return
    
    excel_files = list(extraction_dir.glob("inventory_calculation_data_*.xlsx"))
    if not excel_files:
        logger.error("No extraction files found!")
        return
    
    # Get the most recent file
    latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
    logger.info(f"Verifying file: {latest_file}")
    
    # Read the data
    df = pd.read_excel(latest_file)
    
    print("\\n" + "="*80)
    print("INVENTORY EXTRACTION VERIFICATION")
    print("="*80)
    
    print(f"File: {latest_file.name}")
    print(f"Total records: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    print("\\nColumns extracted:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\\nRecords by store:")
    if "store_id" in df.columns:
        store_counts = df["store_id"].value_counts().sort_index()
        store_names = {
            1: "加拿大一店", 2: "加拿大二店", 3: "加拿大三店", 4: "加拿大四店",
            5: "加拿大五店", 6: "加拿大六店", 7: "加拿大七店"
        }
        for store_id, count in store_counts.items():
            store_name = store_names.get(store_id, f"Store {store_id}")
            print(f"  Store {store_id} ({store_name}): {count} records")
    
    print("\\nSample data (first 3 records):")
    print("-" * 80)
    
    # Show first few records with key columns
    key_columns = ["门店名称", "菜品编码", "菜品名称", "物料号", "物料描述"]
    available_key_cols = [col for col in key_columns if col in df.columns]
    
    if available_key_cols:
        sample_data = df[available_key_cols].head(3)
        for idx, row in sample_data.iterrows():
            print(f"Record {idx+1}:")
            for col in available_key_cols:
                try:
                    value = str(row[col])[:50] + "..." if len(str(row[col])) > 50 else str(row[col])
                    print(f"  {col}: {value}")
                except UnicodeEncodeError:
                    print(f"  {col}: <Unicode display error>")
            print()
    
    # Check for missing requested columns
    requested_columns = [
        "门店名称", "大类名称", "子类名称", "菜品编码", "菜品短编码", 
        "菜品名称", "规格", "出品分量(kg)", "损耗", "物料单位", 
        "物料号", "物料描述", "单位"
    ]
    
    missing_columns = [col for col in requested_columns if col not in df.columns]
    if missing_columns:
        print("\\nMissing requested columns:")
        for col in missing_columns:
            print(f"  - {col}")
    else:
        print("\\n✅ All requested columns found!")
    
    print("="*80)

if __name__ == "__main__":
    verify_extraction()