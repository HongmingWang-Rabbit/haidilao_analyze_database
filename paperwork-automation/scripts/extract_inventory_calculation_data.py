#!/usr/bin/env python3
"""
Extract dish material usage data from calculated_dish_material_usage files.

This script processes Excel files from history_files/monthly_report_inputs/YYYY-MM/calculated_dish_material_usage/
and extracts dish-material relationships with standard portion sizes from the "计算" sheet.
"""

import os
import sys
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_inventory_files():
    """Find all inventory checking result files from ALL historical months and current month"""
    inventory_files = []
    
    # First, check current month inventory files
    current_base = Path("Input/monthly_report/inventory_checking_result")
    if current_base.exists():
        for store_id in range(1, 8):
            store_folder = current_base / str(store_id)
            if store_folder.exists():
                excel_files = list(store_folder.glob("*.xls*"))
                if excel_files:
                    inventory_files.append((f"current-store-{store_id}", excel_files[0], store_id))
                    logger.info(f"Found current inventory file for store {store_id}: {excel_files[0].name}")
    
    # Then, check ALL historical months
    hist_base = Path("history_files/monthly_report_inputs")
    if hist_base.exists():
        for month_folder in hist_base.iterdir():
            if month_folder.is_dir():
                inv_folder = month_folder / "inventory_checking_result"
                if inv_folder.exists():
                    for store_id in range(1, 8):
                        store_folder = inv_folder / str(store_id)
                        if store_folder.exists():
                            excel_files = list(store_folder.glob("*.xls*"))
                            if excel_files:
                                file_key = f"{month_folder.name}-store-{store_id}"
                                inventory_files.append((file_key, excel_files[0], store_id))
                                logger.info(f"Found historical inventory file: {month_folder.name} store {store_id}")
    
    logger.info(f"Total inventory files found: {len(inventory_files)}")
    return inventory_files

def get_store_name(store_id):
    """Get store name based on store ID"""
    store_names = {
        1: "加拿大一店",
        2: "加拿大二店", 
        3: "加拿大三店",
        4: "加拿大四店",
        5: "加拿大五店",
        6: "加拿大六店",
        7: "加拿大七店"
    }
    return store_names.get(store_id, f"Store {store_id}")

def extract_calculation_data(file_path, store_id):
    """Extract data from the 计算 sheet of an inventory file (with CORRECT column mapping)"""
    try:
        # Read all sheet names first
        xl_file = pd.ExcelFile(file_path)
        sheet_names = xl_file.sheet_names
        logger.info(f"Store {store_id} sheets: {sheet_names}")
        
        # Look for the "计算" sheet (or similar variations)
        calculation_sheet = None
        for sheet in sheet_names:
            if "计算" in sheet or "计" in sheet or "calc" in sheet.lower():
                calculation_sheet = sheet
                break
        
        if not calculation_sheet:
            logger.error(f"No calculation sheet found in {file_path}. Available sheets: {sheet_names}")
            return pd.DataFrame()
        
        logger.info(f"Using sheet '{calculation_sheet}' for store {store_id}")
        
        # Read the calculation sheet
        df = pd.read_excel(file_path, sheet_name=calculation_sheet)
        
        # Define the target columns we want to extract
        target_columns = [
            "门店名称", "大类名称", "子类名称", "菜品编码", "菜品短编码", 
            "菜品名称", "规格", "出品分量", "损耗", "物料单位", 
            "物料号", "物料描述", "单位"
        ]
        
        # Show available columns for debugging
        logger.info(f"Available columns in {calculation_sheet}: {list(df.columns)}")
        
        # Try to find matching columns with CORRECT mapping (avoid 实收数量!)
        available_columns = list(df.columns)
        column_mapping = {}
        
        for target_col in target_columns:
            found = False
            # Try exact match first
            if target_col in available_columns:
                column_mapping[target_col] = target_col
                found = True
            else:
                # Special handling for quantity-related columns - AVOID 实收数量
                if target_col == "出品分量":
                    # Look for CORRECT portion size columns, NOT inventory quantities
                    portion_patterns = ["出品分量", "分量"]  # Removed "实收数量", "数量" 
                    for available_col in available_columns:
                        col_str = str(available_col).lower()
                        # Only match exact portion-related columns, NOT inventory
                        if any(pattern in col_str for pattern in portion_patterns) and "实收" not in col_str:
                            column_mapping[target_col] = available_col
                            logger.info(f"Mapped '{target_col}' to '{available_col}' for store {store_id}")
                            found = True
                            break
                
                # General case insensitive matching for other columns
                if not found:
                    for available_col in available_columns:
                        if (target_col.lower() in str(available_col).lower() or 
                            str(available_col).lower() in target_col.lower()):
                            column_mapping[target_col] = available_col
                            found = True
                            break
            
            if not found:
                logger.warning(f"Column '{target_col}' not found in store {store_id}")
        
        # Extract available columns
        extracted_data = pd.DataFrame()
        store_name = get_store_name(store_id)
        
        for target_col, source_col in column_mapping.items():
            if source_col in df.columns:
                # Rename to match expected output format
                output_col = target_col
                if target_col == "出品分量":
                    output_col = "出品分量(kg)"
                extracted_data[output_col] = df[source_col]
        
        # Add store name if not present
        if "门店名称" not in extracted_data.columns or extracted_data["门店名称"].isna().all():
            extracted_data["门店名称"] = store_name
        
        # Add store ID for reference
        extracted_data["store_id"] = store_id
        
        # Clean material numbers and dish codes to remove .0 suffixes
        if "物料号" in extracted_data.columns:
            extracted_data["物料号"] = extracted_data["物料号"].astype(str).str.replace('.0', '', regex=False)
        
        if "菜品编码" in extracted_data.columns:
            extracted_data["菜品编码"] = extracted_data["菜品编码"].astype(str).str.replace('.0', '', regex=False)
        
        logger.info(f"Extracted {len(extracted_data)} rows from store {store_id}")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return pd.DataFrame()

def main():
    """Main function to extract inventory calculation data with CORRECTED column mapping"""
    logger.info("Starting inventory calculation data extraction...")
    
    # Find all inventory files
    inventory_files = find_inventory_files()
    
    if not inventory_files:
        logger.error("No inventory files found!")
        return
    
    # Extract data from all files
    all_data = []
    
    for file_key, file_path, store_id in inventory_files:
        logger.info(f"Processing {file_key}: {file_path}")
        data = extract_calculation_data(file_path, store_id)
        if not data.empty:
            # Add month/source information
            data['data_source'] = file_key
            all_data.append(data)
    
    if not all_data:
        logger.error("No data extracted from any files!")
        return
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Reorder columns to match the original format (include data_source for tracking)
    desired_order = [
        "门店名称", "大类名称", "子类名称", "菜品编码", "菜品短编码", 
        "菜品名称", "规格", "出品分量(kg)", "损耗", "物料单位", 
        "物料号", "物料描述", "单位", "store_id", "data_source"
    ]
    
    # Only include columns that exist in the data
    available_columns = [col for col in desired_order if col in combined_data.columns]
    combined_data = combined_data[available_columns]
    
    # Create output directory if it doesn't exist
    output_dir = Path("output/inventory_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"inventory_calculation_data_{timestamp}.xlsx"
    
    # Save to Excel (this will overwrite the problematic file)
    combined_data.to_excel(output_file, index=False, engine='openpyxl')
    
    logger.info(f"✅ Extraction completed!")
    logger.info(f"📄 Total records extracted: {len(combined_data)}")
    logger.info(f"🏪 Stores processed: {len(inventory_files)}")
    logger.info(f"📁 Output saved to: {output_file}")
    
    # Show summary by store
    print("\\n" + "="*80)
    print("CORRECTED EXTRACTION SUMMARY")
    print("="*80)
    if "store_id" in combined_data.columns:
        store_counts = combined_data["store_id"].value_counts().sort_index()
        for store_id, count in store_counts.items():
            store_name = get_store_name(store_id)
            try:
                print(f"  {store_name}: {count} records")
            except UnicodeEncodeError:
                print(f"  Store {store_id}: {count} records")
    
    # Show sample portion sizes to verify reasonableness
    if "出品分量(kg)" in combined_data.columns:
        try:
            print(f"\\nPortion size statistics (CORRECTED):")
            # Convert to numeric to avoid data type issues
            numeric_portions = pd.to_numeric(combined_data["出品分量(kg)"], errors='coerce').dropna()
            if len(numeric_portions) > 0:
                print(f"  Min: {numeric_portions.min()} kg")
                print(f"  Max: {numeric_portions.max()} kg")
                print(f"  Mean: {numeric_portions.mean():.3f} kg")
                print(f"  Count of values > 1000kg: {len(numeric_portions[numeric_portions > 1000])}")
            else:
                print("  No valid numeric portion sizes found")
        except Exception as e:
            print(f"  Could not calculate portion statistics: {e}")
    
    print(f"\\nTotal records: {len(combined_data)}")
    print(f"Output file: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()