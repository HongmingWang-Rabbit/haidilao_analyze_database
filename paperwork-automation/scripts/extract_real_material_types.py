#!/usr/bin/env python3
"""
Extract real material types from Excel files by column position instead of names
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def safe_str(value):
    """Safely convert value to string"""
    if pd.isna(value):
        return None
    return str(value).strip()

def extract_material_types_by_position(file_path):
    """Extract material types from Excel file using column positions"""
    
    try:
        df = pd.read_excel(file_path, dtype={'物料': str})
        print(f"Loaded {len(df)} rows from Excel file")
        print(f"Excel has {len(df.columns)} columns")
        
        # Based on typical material detail file structure:
        # Column positions may vary, but let's check columns that might contain type info
        material_types = set()
        child_types = set()
        type_child_mapping = {}
        
        # Check each column for potential type data
        for col_idx in range(len(df.columns)):
            col = df.columns[col_idx]
            col_data = df.iloc[:, col_idx].dropna()
            
            # Check if this column contains type-like data
            unique_values = col_data.unique()
            if len(unique_values) > 1 and len(unique_values) < 50:  # Reasonable number of types
                print(f"Column {col_idx}: {len(unique_values)} unique values")
                
                # Sample some values to see if they look like types
                sample_values = unique_values[:5]
                print(f"  Sample values: {[safe_str(v) for v in sample_values if safe_str(v)]}")
                
                # If values look like material types (short strings), use this column
                valid_values = [safe_str(v) for v in unique_values if safe_str(v) and len(safe_str(v)) < 50]
                if len(valid_values) > 1:
                    if col_idx in [5, 6, 7, 8, 9, 10]:  # Likely positions for type columns
                        print(f"  Using column {col_idx} as material type column")
                        for val in valid_values:
                            material_types.add(val)
        
        # Try common column positions for material types (based on typical structure)
        # Usually type columns are after material number and description
        potential_type_columns = []
        
        for col_idx in range(min(len(df.columns), 15)):  # Check first 15 columns
            col_values = df.iloc[:, col_idx].dropna().unique()
            
            # Look for columns that have 3-20 unique values (typical for material types)
            if 3 <= len(col_values) <= 20:
                # Check if values are short strings (not numbers or long descriptions)
                string_values = [v for v in col_values if isinstance(v, str) and 2 <= len(v) <= 30]
                if len(string_values) >= 3:
                    potential_type_columns.append((col_idx, string_values))
                    print(f"Potential type column {col_idx}: {string_values[:3]}...")
        
        # Use the most promising columns
        if potential_type_columns:
            # Sort by number of unique values (prefer moderate numbers)
            potential_type_columns.sort(key=lambda x: len(x[1]))
            
            # Use first column as material type
            type_col_idx, type_values = potential_type_columns[0]
            material_types.update(type_values)
            print(f"Selected column {type_col_idx} as material type column")
            print(f"Material types: {sorted(material_types)}")
            
            # If we have a second potential column, use it as child types
            if len(potential_type_columns) > 1:
                child_col_idx, child_values = potential_type_columns[1]
                child_types.update(child_values)
                print(f"Selected column {child_col_idx} as child type column")
                print(f"Child types: {sorted(child_types)}")
                
                # Build parent-child mapping
                for _, row in df.iterrows():
                    parent_val = safe_str(row.iloc[type_col_idx])
                    child_val = safe_str(row.iloc[child_col_idx])
                    if parent_val and child_val:
                        type_child_mapping[(parent_val, child_val)] = True
        
        return list(material_types), list(child_types), type_child_mapping
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        import traceback
        traceback.print_exc()
        return [], [], {}

def insert_real_material_types(material_types, child_types, type_child_mapping):
    """Insert real material types to database"""
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Clearing existing material types...")
        
        # First, clear existing type assignments from materials
        cursor.execute("UPDATE material SET material_type_id = NULL, material_child_type_id = NULL")
        
        # Delete existing types (this will cascade if properly set up)
        cursor.execute("DELETE FROM material_child_type")
        cursor.execute("DELETE FROM material_type")
        
        print("2. Inserting real material types...")
        
        type_id_mapping = {}
        for i, type_name in enumerate(sorted(material_types)):
            try:
                cursor.execute("""
                    INSERT INTO material_type (name, description, sort_order, is_active)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (type_name, f'Material type: {type_name}', i + 1, True))
                
                result = cursor.fetchone()
                type_id_mapping[type_name] = result['id']
                print(f"  Inserted type: {type_name} (ID: {result['id']})")
                
            except Exception as e:
                print(f"  Error inserting type {type_name}: {e}")
                continue
        
        print(f"   Created {len(type_id_mapping)} material types")
        
        print("3. Inserting child types...")
        
        child_type_id_mapping = {}
        for i, child_name in enumerate(sorted(child_types)):
            # Find parent type for this child type
            parent_type = None
            for (parent, child) in type_child_mapping:
                if child == child_name:
                    parent_type = parent
                    break
            
            if not parent_type or parent_type not in type_id_mapping:
                print(f"  Warning: No parent found for child type {child_name}")
                continue
                
            try:
                cursor.execute("""
                    INSERT INTO material_child_type (name, material_type_id, description, sort_order, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (child_name, type_id_mapping[parent_type], f'Child type: {child_name}', i + 1, True))
                
                result = cursor.fetchone()
                child_type_id_mapping[(parent_type, child_name)] = result['id']
                print(f"  Inserted child type: {child_name} under {parent_type} (ID: {result['id']})")
                
            except Exception as e:
                print(f"  Error inserting child type {child_name}: {e}")
                continue
        
        print(f"   Created {len(child_type_id_mapping)} child types")
        
        conn.commit()
        return type_id_mapping, child_type_id_mapping

def update_materials_with_real_types(type_id_mapping, child_type_id_mapping, sample_file):
    """Update materials with real type associations based on Excel data"""
    
    print("4. Updating materials with real type associations...")
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    # First, analyze the sample file to determine column positions
    df = pd.read_excel(sample_file, dtype={'物料': str})
    
    # Find the type columns again
    potential_type_columns = []
    for col_idx in range(min(len(df.columns), 15)):
        col_values = df.iloc[:, col_idx].dropna().unique()
        if 3 <= len(col_values) <= 20:
            string_values = [v for v in col_values if isinstance(v, str) and 2 <= len(v) <= 30]
            if len(string_values) >= 3:
                potential_type_columns.append((col_idx, string_values))
    
    if not potential_type_columns:
        print("  No type columns found!")
        return False
    
    potential_type_columns.sort(key=lambda x: len(x[1]))
    type_col_idx = potential_type_columns[0][0]
    child_col_idx = potential_type_columns[1][0] if len(potential_type_columns) > 1 else None
    
    print(f"  Using column {type_col_idx} for material types")
    if child_col_idx:
        print(f"  Using column {child_col_idx} for child types")
    
    # Process each store's material file
    material_detail_path = Path("history_files/monthly_report_inputs/2025-05/material_detail")
    updated_count = 0
    
    for store_folder in sorted(material_detail_path.iterdir()):
        if not store_folder.is_dir():
            continue
            
        store_id = int(store_folder.name)
        print(f"  Processing store {store_id}...")
        
        excel_files = list(store_folder.glob("*.xlsx")) + list(store_folder.glob("*.XLSX"))
        
        for excel_file in excel_files:
            try:
                df = pd.read_excel(excel_file, dtype={'物料': str})
                
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for _, row in df.iterrows():
                        material_number = safe_str(row.get('物料'))
                        if not material_number:
                            continue
                            
                        # Clean material number
                        if material_number.endswith('.0'):
                            material_number = material_number[:-2]
                        material_number = material_number.lstrip('0')
                        if not material_number:
                            material_number = '0'
                        
                        if len(material_number) < 6:
                            continue
                        
                        # Get type from determined columns
                        parent_type = safe_str(row.iloc[type_col_idx]) if type_col_idx < len(row) else None
                        child_type = safe_str(row.iloc[child_col_idx]) if child_col_idx and child_col_idx < len(row) else None
                        
                        if not parent_type or parent_type not in type_id_mapping:
                            continue
                        
                        material_type_id = type_id_mapping[parent_type]
                        material_child_type_id = None
                        
                        if child_type:
                            key = (parent_type, child_type)
                            material_child_type_id = child_type_id_mapping.get(key)
                        
                        # Update material
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
    
    print(f"   Updated {updated_count} materials with real type associations")
    return updated_count > 0

def main():
    """Main function"""
    
    print("EXTRACTING REAL MATERIAL TYPES FROM EXCEL FILES")
    print("=" * 50)
    
    sample_file = Path("history_files/monthly_report_inputs/2025-05/material_detail/1/ca01-202505.XLSX")
    
    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return False
    
    # Step 1: Extract real material types from Excel
    material_types, child_types, type_child_mapping = extract_material_types_by_position(sample_file)
    
    if not material_types:
        print("No material types found!")
        return False
    
    print(f"\nFound {len(material_types)} material types and {len(child_types)} child types")
    
    # Step 2: Insert real types to database
    type_id_mapping, child_type_id_mapping = insert_real_material_types(material_types, child_types, type_child_mapping)
    
    # Step 3: Update materials with real type associations
    success = update_materials_with_real_types(type_id_mapping, child_type_id_mapping, sample_file)
    
    # Step 4: Verify results
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM material_type")
        type_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM material_child_type")
        child_type_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM material WHERE material_type_id IS NOT NULL")
        materials_with_types = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM material")
        total_materials = cursor.fetchone()['count']
        
        # Show type distribution
        cursor.execute("""
            SELECT mt.name, COUNT(m.id) as material_count 
            FROM material_type mt 
            LEFT JOIN material m ON mt.id = m.material_type_id 
            GROUP BY mt.id, mt.name 
            ORDER BY material_count DESC
        """)
        type_distribution = cursor.fetchall()
        
        print(f"\nResults:")
        print(f"  Material types created: {type_count}")
        print(f"  Child types created: {child_type_count}")
        print(f"  Materials with types: {materials_with_types}/{total_materials}")
        print(f"\nType distribution:")
        for row in type_distribution:
            print(f"  {row['name']}: {row['material_count']} materials")
    
    return success

if __name__ == "__main__":
    main()