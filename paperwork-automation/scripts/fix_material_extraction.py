#!/usr/bin/env python3
"""
Fix material extraction to get proper names, descriptions, units from material detail files
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def extract_proper_materials():
    """Extract materials with proper names and descriptions from material detail files"""
    
    print("FIXING MATERIAL EXTRACTION")
    print("=" * 30)
    
    # Clear existing materials first
    print("Clearing existing materials...")
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM material")
        conn.commit()
        print("Existing materials cleared")
    
    # Extract from material detail files for 2025-05
    material_detail_folder = Path("history_files/monthly_report_inputs/2025-05/material_detail")
    
    if not material_detail_folder.exists():
        print(f"Material detail folder not found: {material_detail_folder}")
        return False
    
    store_folders = [f for f in material_detail_folder.iterdir() if f.is_dir()]
    store_folders.sort()
    
    total_materials = 0
    
    for store_folder in store_folders:
        store_id = int(store_folder.name)
        print(f"Processing store {store_id}...")
        
        excel_files = list(store_folder.glob("*.xlsx")) + list(store_folder.glob("*.XLSX"))
        
        for excel_file in excel_files:
            try:
                print(f"  Reading {excel_file.name}...")
                df = pd.read_excel(excel_file, engine='openpyxl', dtype={'物料': str})
                
                print(f"  Shape: {df.shape}")
                
                # Based on analysis: Column 5 = material numbers, Column 6 = material names, Column 7 = units
                if df.shape[1] >= 7:
                    material_numbers = df.iloc[:, 4]  # Column 5 (0-indexed)
                    material_names = df.iloc[:, 5]    # Column 6 (0-indexed) 
                    material_units = df.iloc[:, 6]    # Column 7 (0-indexed)
                    
                    materials_added = 0
                    
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        for i in range(len(df)):
                            material_number = material_numbers.iloc[i]
                            material_name = material_names.iloc[i]
                            material_unit = material_units.iloc[i]
                            
                            # Skip if material number is invalid
                            if pd.isna(material_number) or not str(material_number).strip():
                                continue
                                
                            material_number = str(material_number).strip()
                            
                            # Remove leading zeros (material numbers have many leading zeros)
                            material_number = material_number.lstrip('0')
                            if not material_number:
                                material_number = '0'
                            
                            if not material_number.isdigit() or len(material_number) < 6:
                                continue
                            
                            # Use material name or fallback to generic name
                            if pd.notna(material_name) and str(material_name).strip():
                                name = str(material_name).strip()
                            else:
                                name = f"Material_{material_number}"
                            
                            # Use unit or default to empty
                            if pd.notna(material_unit) and str(material_unit).strip():
                                unit = str(material_unit).strip()
                            else:
                                unit = ''
                            
                            try:
                                # Insert material with store-specific data
                                cursor.execute("""
                                    INSERT INTO material (
                                        store_id, material_number, name, unit, is_active
                                    )
                                    VALUES (%s, %s, %s, %s, %s)
                                    ON CONFLICT (store_id, material_number) DO UPDATE SET
                                        name = EXCLUDED.name,
                                        unit = EXCLUDED.unit,
                                        updated_at = CURRENT_TIMESTAMP
                                """, (store_id, material_number, name, unit, True))
                                
                                materials_added += 1
                                
                            except Exception as e:
                                print(f"    Error inserting material {material_number}: {e}")
                                continue
                        
                        conn.commit()
                    
                    print(f"    Added {materials_added} materials for store {store_id}")
                    total_materials += materials_added
                
            except Exception as e:
                print(f"    Error processing {excel_file}: {e}")
                continue
    
    print(f"\nTotal materials extracted: {total_materials}")
    
    # Verify results
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM material")
        db_count = cursor.fetchone()['count']
        print(f"Materials in database: {db_count}")
        
        # Show sample materials
        cursor.execute("""
            SELECT store_id, material_number, name, unit 
            FROM material 
            WHERE name != 'Material_' || material_number
            LIMIT 5
        """)
        samples = cursor.fetchall()
        print("\nSample materials with proper names:")
        for sample in samples:
            print(f"  Store {sample['store_id']}: #{sample['material_number']} - {sample['name']} ({sample['unit']})")
    
    return total_materials > 0

if __name__ == "__main__":
    extract_proper_materials()