#!/usr/bin/env python3
"""
Fix material_type and material_child_type table schemas by adding missing columns
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def fix_material_type_schemas():
    """Add missing columns to material_type and material_child_type tables"""
    
    print("FIXING MATERIAL TYPE TABLE SCHEMAS")
    print("=" * 35)
    
    # Connect to test database
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Checking material_type table...")
        
        # Check existing columns in material_type
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'material_type'
        """)
        
        existing_cols = [row['column_name'] for row in cursor.fetchall()]
        print(f"   Existing columns: {existing_cols}")
        
        # Add missing columns to material_type
        missing_cols = []
        if 'sort_order' not in existing_cols:
            missing_cols.append(('sort_order', 'INTEGER DEFAULT 1'))
        if 'is_active' not in existing_cols:
            missing_cols.append(('is_active', 'BOOLEAN DEFAULT TRUE'))
            
        if missing_cols:
            print(f"   Adding missing columns: {[col[0] for col in missing_cols]}")
            for col_name, col_def in missing_cols:
                try:
                    cursor.execute(f"ALTER TABLE material_type ADD COLUMN {col_name} {col_def}")
                    print(f"   Added {col_name} column")
                except Exception as e:
                    print(f"   Error adding {col_name}: {e}")
        else:
            print("   All required columns exist")
            
        print("\n2. Checking material_child_type table...")
        
        # Check existing columns in material_child_type
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'material_child_type'
        """)
        
        existing_cols = [row['column_name'] for row in cursor.fetchall()]
        print(f"   Existing columns: {existing_cols}")
        
        # Add missing columns to material_child_type
        missing_cols = []
        if 'sort_order' not in existing_cols:
            missing_cols.append(('sort_order', 'INTEGER DEFAULT 1'))
        if 'is_active' not in existing_cols:
            missing_cols.append(('is_active', 'BOOLEAN DEFAULT TRUE'))
            
        if missing_cols:
            print(f"   Adding missing columns: {[col[0] for col in missing_cols]}")
            for col_name, col_def in missing_cols:
                try:
                    cursor.execute(f"ALTER TABLE material_child_type ADD COLUMN {col_name} {col_def}")
                    print(f"   Added {col_name} column")
                except Exception as e:
                    print(f"   Error adding {col_name}: {e}")
        else:
            print("   All required columns exist")
            
        conn.commit()
        
        print("\n3. Verifying schema fixes...")
        
        # Verify material_type schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'material_type' 
            ORDER BY ordinal_position
        """)
        
        print("   material_type final schema:")
        for col in cursor.fetchall():
            print(f"     {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")
        
        # Verify material_child_type schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'material_child_type' 
            ORDER BY ordinal_position
        """)
        
        print("   material_child_type final schema:")
        for col in cursor.fetchall():
            print(f"     {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")
            
        return True
    
    print("\nMaterial type schema fixes completed!")

if __name__ == "__main__":
    fix_material_type_schemas()