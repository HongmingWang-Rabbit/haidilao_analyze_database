#!/usr/bin/env python3
"""
Extract materials with proper type classifications - fixed for store-specific schema
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def extract_material_types_from_excel(file_path):
    """Extract material types and child types from Excel file"""
    
    try:
        df = pd.read_excel(file_path, dtype={'物料': str})
        print(f"Loaded {len(df)} rows from {file_path}")
        
        # Find classification columns
        type_col = None
        child_type_col = None
        
        for col in df.columns:
            col_str = str(col)
            if '一级分类' in col_str or '187-一级分类' in col_str:
                type_col = col
                print(f"Found material type column: {col}")
            elif '二级分类' in col_str or '187-二级分类' in col_str:
                child_type_col = col
                print(f"Found child type column: {col}")
        
        if not type_col:
            print("No material type classification column found!")
            return [], []
            
        # Extract unique material types
        material_types = []
        if type_col:
            unique_types = df[type_col].dropna().unique()
            for i, type_name in enumerate(unique_types):
                material_types.append({
                    'name': str(type_name).strip(),
                    'description': f'Material type: {type_name}',
                    'sort_order': i + 1,
                    'is_active': True
                })
            print(f"Extracted {len(material_types)} material types")
        
        # Extract unique child types with parent relationships
        child_types = []
        if child_type_col and type_col:
            # Group by type to get child types for each parent
            for _, row in df.iterrows():
                parent_type = row.get(type_col)
                child_type = row.get(child_type_col)
                
                if pd.notna(parent_type) and pd.notna(child_type):
                    parent_name = str(parent_type).strip()
                    child_name = str(child_type).strip()
                    
                    # Check if we already have this combination
                    key = (parent_name, child_name)
                    if not any(ct['parent_type_name'] == parent_name and ct['name'] == child_name for ct in child_types):
                        child_types.append({
                            'name': child_name,
                            'parent_type_name': parent_name,
                            'description': f'Material child type: {child_name}',
                            'sort_order': len(child_types) + 1,
                            'is_active': True
                        })
            print(f"Extracted {len(child_types)} child types")
        
        return material_types, child_types
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return [], []

def insert_material_types_to_db(material_types, child_types):
    """Insert material types and child types to database"""
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Inserting material types...")
        
        # Insert material types
        type_id_mapping = {}
        for mat_type in material_types:
            try:
                cursor.execute("""
                    INSERT INTO material_type (name, description, sort_order, is_active)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        description = EXCLUDED.description,
                        sort_order = EXCLUDED.sort_order,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (mat_type['name'], mat_type['description'], mat_type['sort_order'], mat_type['is_active']))
                
                result = cursor.fetchone()
                type_id_mapping[mat_type['name']] = result['id']
                print(f"  Inserted/updated type: {mat_type['name']} (ID: {result['id']})")
                
            except Exception as e:
                print(f"  Error inserting type {mat_type['name']}: {e}")
                continue
        
        print(f"   Processed {len(type_id_mapping)} material types")
        
        print("2. Inserting child types...")
        
        # Insert child types
        child_type_id_mapping = {}
        for child_type in child_types:
            parent_id = type_id_mapping.get(child_type['parent_type_name'])
            if not parent_id:
                print(f"  Warning: Parent type not found for {child_type['name']}")
                continue
                
            try:
                cursor.execute("""
                    INSERT INTO material_child_type (name, material_type_id, description, sort_order, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (material_type_id, name) DO UPDATE SET
                        description = EXCLUDED.description,
                        sort_order = EXCLUDED.sort_order,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (child_type['name'], parent_id, child_type['description'], child_type['sort_order'], child_type['is_active']))
                
                result = cursor.fetchone()
                key = (child_type['parent_type_name'], child_type['name'])
                child_type_id_mapping[key] = result['id']
                print(f"  Inserted/updated child type: {child_type['name']} (ID: {result['id']})")
                
            except Exception as e:
                print(f"  Error inserting child type {child_type['name']}: {e}")
                continue
        
        print(f"   Processed {len(child_type_id_mapping)} child types")
        
        conn.commit()
        return type_id_mapping, child_type_id_mapping

def update_materials_with_types():
    """Update existing materials with type associations"""
    
    print("3. Updating materials with type associations...")
    
    # Process each store's material file
    material_detail_path = Path("history_files/monthly_report_inputs/2025-05/material_detail")
    
    if not material_detail_path.exists():
        print(f"Material detail path not found: {material_detail_path}")
        return False
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    # Get type mappings first
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all material types
        cursor.execute("SELECT id, name FROM material_type")
        type_mapping = {row['name']: row['id'] for row in cursor.fetchall()}
        
        # Get all child types
        cursor.execute("SELECT id, name, material_type_id FROM material_child_type")
        child_type_rows = cursor.fetchall()
        
        # Build child type mapping by finding parent type name
        cursor.execute("""
            SELECT ct.id, ct.name as child_name, mt.name as parent_name 
            FROM material_child_type ct 
            JOIN material_type mt ON ct.material_type_id = mt.id
        """)
        child_type_mapping = {}
        for row in cursor.fetchall():
            key = (row['parent_name'], row['child_name'])
            child_type_mapping[key] = row['id']
    
    updated_count = 0
    
    # Process each store folder
    for store_folder in sorted(material_detail_path.iterdir()):
        if not store_folder.is_dir():
            continue
            
        store_id = int(store_folder.name)
        print(f"  Processing store {store_id}...")
        
        # Find Excel files in store folder
        excel_files = list(store_folder.glob("*.xlsx")) + list(store_folder.glob("*.XLSX"))
        
        for excel_file in excel_files:
            try:
                df = pd.read_excel(excel_file, dtype={'物料': str})
                
                # Find classification columns
                type_col = None
                child_type_col = None
                
                for col in df.columns:
                    col_str = str(col)
                    if '一级分类' in col_str or '187-一级分类' in col_str:
                        type_col = col
                    elif '二级分类' in col_str or '187-二级分类' in col_str:
                        child_type_col = col
                
                if not type_col:
                    print(f"    No type column in {excel_file}")
                    continue
                
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for _, row in df.iterrows():
                        material_number = row.get('物料')
                        if pd.isna(material_number):
                            continue
                            
                        # Clean material number - remove leading zeros
                        material_number = str(material_number).strip()
                        if material_number.endswith('.0'):
                            material_number = material_number[:-2]
                        material_number = material_number.lstrip('0')
                        if not material_number:
                            material_number = '0'
                        
                        if len(material_number) < 6:
                            continue
                        
                        # Get type information
                        parent_type_name = row.get(type_col)
                        child_type_name = row.get(child_type_col) if child_type_col else None
                        
                        if pd.isna(parent_type_name):
                            continue
                            
                        parent_type_name = str(parent_type_name).strip()
                        material_type_id = type_mapping.get(parent_type_name)
                        
                        if not material_type_id:
                            print(f"    Warning: Type not found: {parent_type_name}")
                            continue
                        
                        # Get child type ID if available
                        material_child_type_id = None
                        if child_type_name and pd.notna(child_type_name):
                            child_type_name = str(child_type_name).strip()
                            key = (parent_type_name, child_type_name)
                            material_child_type_id = child_type_mapping.get(key)
                        
                        # Update material with type associations
                        try:
                            cursor.execute("""
                                UPDATE material 
                                SET material_type_id = %s, 
                                    material_child_type_id = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE store_id = %s AND material_number = %s
                            """, (material_type_id, material_child_type_id, store_id, material_number))
                            
                            if cursor.rowcount > 0:
                                updated_count += 1
                                
                        except Exception as e:
                            print(f"    Error updating material {material_number}: {e}")
                            continue
                    
                    conn.commit()
                    
            except Exception as e:
                print(f"    Error processing {excel_file}: {e}")
                continue
    
    print(f"   Updated {updated_count} materials with type associations")
    return updated_count > 0

def main():
    """Main function"""
    
    print("EXTRACTING MATERIALS WITH PROPER TYPE CLASSIFICATIONS")
    print("=" * 55)
    
    # Use first store's file to extract type classifications
    sample_file = Path("history_files/monthly_report_inputs/2025-05/material_detail/1/ca01-202505.XLSX")
    
    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return False
    
    # Step 1: Extract material types and child types from Excel
    material_types, child_types = extract_material_types_from_excel(sample_file)
    
    if not material_types:
        print("No material types found!")
        return False
    
    # Step 2: Insert types to database
    type_mapping, child_type_mapping = insert_material_types_to_db(material_types, child_types)
    
    # Step 3: Update existing materials with type associations
    success = update_materials_with_types()
    
    # Step 4: Verify results
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM material WHERE material_type_id IS NOT NULL")
        materials_with_types = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM material")
        total_materials = cursor.fetchone()['count']
        
        print(f"\nResults:")
        print(f"  Material types: {len(material_types)}")
        print(f"  Child types: {len(child_types)}")
        print(f"  Materials with types: {materials_with_types}/{total_materials}")
    
    return success

if __name__ == "__main__":
    main()