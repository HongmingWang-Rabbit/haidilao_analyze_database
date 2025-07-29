#!/usr/bin/env python3
"""
Extract material prices from inventory checking result files
"""

import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def safe_float(value):
    """Safely convert value to float"""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def clean_material_number(material_number):
    """Clean material number by removing leading zeros"""
    if pd.isna(material_number):
        return None
    
    material_str = str(material_number)
    if material_str.endswith('.0'):
        material_str = material_str[:-2]
    
    try:
        cleaned_number = str(int(material_str))
        return cleaned_number
    except (ValueError, TypeError):
        return material_str

def extract_material_prices_from_inventory():
    """Extract material prices from inventory checking result files"""
    
    print("EXTRACTING MATERIAL PRICES FROM INVENTORY FILES")
    print("=" * 50)
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    inventory_path = Path("history_files/monthly_report_inputs/2025-05/inventory_checking_result")
    
    if not inventory_path.exists():
        print(f"Inventory path not found: {inventory_path}")
        return False
    
    total_prices_extracted = 0
    
    # Process each store's inventory file
    for store_folder in sorted(inventory_path.iterdir()):
        if not store_folder.is_dir():
            continue
            
        store_id = int(store_folder.name)
        print(f"Processing store {store_id}...")
        
        # Find inventory files
        inventory_files = list(store_folder.glob("*.xls")) + list(store_folder.glob("*.xlsx"))
        
        for inv_file in inventory_files:
            try:
                print(f"  Reading {inv_file.name}...")
                
                # Try reading with different engines
                df = None
                try:
                    df = pd.read_excel(inv_file, engine='xlrd')
                except:
                    try:
                        df = pd.read_excel(inv_file, engine='openpyxl')
                    except Exception as e:
                        print(f"    Could not read file: {e}")
                        continue
                
                if df is None:
                    continue
                
                print(f"    Loaded {len(df)} rows")
                
                # Look for columns that might contain material numbers and prices
                material_col = None
                price_col = None
                unit_price_col = None
                
                for col in df.columns:
                    col_str = str(col).lower()
                    if '物料' in col_str or 'material' in col_str:
                        material_col = col
                        print(f"    Found material column: {col}")
                    elif '单价' in col_str or 'price' in col_str or '价格' in col_str:
                        if not price_col:  # Take first price column
                            price_col = col
                            print(f"    Found price column: {col}")
                    elif '金额' in col_str or 'amount' in col_str:
                        if not unit_price_col:
                            unit_price_col = col
                            print(f"    Found amount column: {col}")
                
                if not material_col:
                    print("    No material column found, skipping")
                    continue
                
                # Use price_col or unit_price_col
                target_price_col = price_col or unit_price_col
                if not target_price_col:
                    print("    No price column found, skipping")
                    continue
                
                print(f"    Using price column: {target_price_col}")
                
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    store_prices_extracted = 0
                    
                    for _, row in df.iterrows():
                        material_number = clean_material_number(row.get(material_col))
                        price = safe_float(row.get(target_price_col))
                        
                        if not material_number or price is None or price <= 0:
                            continue
                        
                        if len(material_number) < 6:  # Skip very short material numbers
                            continue
                        
                        # Check if material exists in our database
                        cursor.execute("""
                            SELECT id FROM material 
                            WHERE store_id = %s AND material_number = %s
                        """, (store_id, material_number))
                        
                        material_result = cursor.fetchone()
                        if not material_result:
                            continue  # Material not found in our database
                        
                        material_id = material_result['id']
                        
                        # Insert material price history
                        try:
                            cursor.execute("""
                                INSERT INTO material_price_history (
                                    material_id, store_id, price, effective_date, is_active
                                )
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (material_id, store_id, effective_date) DO UPDATE SET
                                    price = EXCLUDED.price,
                                    is_active = EXCLUDED.is_active,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (material_id, store_id, price, '2025-05-01', True))
                            
                            store_prices_extracted += 1
                            
                        except Exception as e:
                            print(f"      Error inserting price for material {material_number}: {e}")
                            continue
                    
                    conn.commit()
                    print(f"    Extracted {store_prices_extracted} material prices for store {store_id}")
                    total_prices_extracted += store_prices_extracted
                    
            except Exception as e:
                print(f"    Error processing {inv_file}: {e}")
                continue
    
    print(f"\nTotal material prices extracted: {total_prices_extracted}")
    
    # Verify results
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM material_price_history")
        db_count = cursor.fetchone()['count']
        print(f"Material prices in database: {db_count}")
        
        if db_count > 0:
            cursor.execute("""
                SELECT store_id, COUNT(*) as count 
                FROM material_price_history 
                GROUP BY store_id 
                ORDER BY store_id
            """)
            store_distribution = cursor.fetchall()
            print("Price distribution by store:")
            for row in store_distribution:
                print(f"  Store {row['store_id']}: {row['count']} prices")
    
    return total_prices_extracted > 0

def main():
    """Main function"""
    
    success = extract_material_prices_from_inventory()
    
    if success:
        print("\nMaterial price extraction completed successfully!")
    else:
        print("\nMaterial price extraction failed!")
    
    return success

if __name__ == "__main__":
    main()