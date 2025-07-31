#!/usr/bin/env python3
"""
Diagnose Beer Serving Size Issue

The user reports seeing:
朝日啤酒 330ml 冰镇 sale-331.00 出品分量(kg)-331.0000 损耗-1.0000 物料单位-1.000000 materials_use-109561.0000

This suggests that 出品分量(kg) is showing the sales quantity (331) instead of the serving size (1.0).
Let's diagnose where this is happening.
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def diagnose_beer_serving_issue():
    """Diagnose where the beer serving size issue is coming from"""
    
    print("=== DIAGNOSING BEER SERVING SIZE ISSUE ===\n")
    
    # Step 1: Check the calculation sheet data
    print("Step 1: Checking Store 5 calculation sheet data...")
    store5_file = "Input/monthly_report/inventory_checking_result/5/CA05-盘点结果 -2505.xls"
    
    try:
        calc_df = pd.read_excel(store5_file, sheet_name='计算')
        
        # Find 朝日啤酒 items
        asahi_items = calc_df[calc_df['菜品名称'].str.contains('朝日', na=False)]
        
        if len(asahi_items) > 0:
            print(f"Found {len(asahi_items)} 朝日啤酒 items in calculation sheet:")
            for idx, row in asahi_items.iterrows():
                dish_name = row.get('菜品名称', '')
                spec = row.get('规格', '')
                quantity_sold = row.get('实收数量', 0)
                serving_size = row.get('出品份量', 0)  # Note: 份量 not 分量
                
                print(f"  {dish_name} {spec}:")
                print(f"    实收数量 (quantity sold): {quantity_sold}")
                print(f"    出品份量 (serving size): {serving_size}")
                
                if abs(serving_size - quantity_sold) < 1:
                    print(f"    ⚠️  WARNING: Serving size equals quantity sold!")
        else:
            print("  No 朝日啤酒 items found in calculation sheet")
            
    except Exception as e:
        print(f"  Error reading calculation sheet: {e}")
    
    print("\n" + "-"*60 + "\n")
    
    # Step 2: Check our extracted data file
    print("Step 2: Checking extracted data file...")
    extracted_file = "output/inventory_calculation_data_from_sheets_only.xlsx"
    
    if Path(extracted_file).exists():
        try:
            df = pd.read_excel(extracted_file)
            
            # Filter for Store 5 朝日啤酒
            store5_asahi = df[
                (df['门店名称'] == '加拿大五店') & 
                (df['菜品名称'].str.contains('朝日', na=False))
            ]
            
            if len(store5_asahi) > 0:
                print(f"Found {len(store5_asahi)} 朝日啤酒 items in extracted data:")
                for idx, row in store5_asahi.iterrows():
                    dish_name = row['菜品名称']
                    spec = row.get('规格', '')
                    serving = row['出品分量(kg)']
                    loss = row['损耗']
                    unit_conv = row['物料单位']
                    
                    print(f"  {dish_name} {spec}:")
                    print(f"    出品分量(kg): {serving}")
                    print(f"    损耗: {loss}")
                    print(f"    物料单位: {unit_conv}")
            else:
                print("  No Store 5 朝日啤酒 items found in extracted data")
                
        except Exception as e:
            print(f"  Error reading extracted data: {e}")
    else:
        print(f"  File not found: {extracted_file}")
    
    print("\n" + "-"*60 + "\n")
    
    # Step 3: Check if there's a materials_use file being generated
    print("Step 3: Checking for materials_use files...")
    materials_use_dir = Path("output/materials_use_with_division")
    
    if materials_use_dir.exists():
        files = list(materials_use_dir.glob("*.xlsx"))
        if files:
            latest_file = max(files, key=lambda x: x.stat().st_mtime)
            print(f"Found materials_use file: {latest_file.name}")
            
            try:
                df = pd.read_excel(latest_file)
                
                # Filter for Store 5 朝日啤酒
                store5_asahi = df[
                    (df['门店名称'] == '加拿大五店') & 
                    (df['菜品名称'].str.contains('朝日', na=False))
                ]
                
                if len(store5_asahi) > 0:
                    print(f"\nFound {len(store5_asahi)} 朝日啤酒 items in materials_use file:")
                    print("\nThis might be where the user is seeing the output:")
                    
                    for idx, row in store5_asahi.iterrows():
                        dish_name = row['菜品名称']
                        spec = row.get('规格', '')
                        sale = row.get('sale_amount', 0)
                        serving = row.get('出品分量(kg)', 0)
                        loss = row.get('损耗', 1)
                        unit_conv = row.get('物料单位', 1)
                        materials_use = row.get('materials_use', 0)
                        
                        # This might be the format the user is seeing
                        print(f"\n  {dish_name} {spec} sale-{sale:.2f} 出品分量(kg)-{serving:.4f} 损耗-{loss:.4f} 物料单位-{unit_conv:.6f} materials_use-{materials_use:.4f}")
                        
                        # Check if serving size equals sale amount
                        if abs(serving - sale) < 1:
                            print(f"  ⚠️  FOUND THE ISSUE: 出品分量(kg) = {serving} equals sale_amount = {sale}!")
                            print(f"  This explains why the user sees 出品分量(kg) = 331 instead of 1.0")
                else:
                    print("  No Store 5 朝日啤酒 items found in materials_use file")
                    
            except Exception as e:
                print(f"  Error reading materials_use file: {e}")
        else:
            print("  No materials_use files found")
    else:
        print("  materials_use_with_division directory not found")
    
    print("\n" + "="*60 + "\n")
    print("DIAGNOSIS SUMMARY:")
    print("The issue appears to be that somewhere in the report generation,")
    print("the sale_amount column is being used instead of the serving_size column")
    print("for the 出品分量(kg) field in the output.")


if __name__ == "__main__":
    diagnose_beer_serving_issue()