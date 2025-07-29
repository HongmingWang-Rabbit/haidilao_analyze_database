#!/usr/bin/env python3
"""
Simple fix for material types - add default material type for all materials
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def create_default_material_type():
    """Create a default material type for all materials"""
    
    print("CREATING DEFAULT MATERIAL TYPE")
    print("=" * 30)
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Creating default material type...")
        
        # Insert default material type
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
            """, ('General Materials', 'Default material type for all materials', 1, True))
            
            result = cursor.fetchone()
            default_type_id = result['id']
            print(f"   Created/updated default material type (ID: {default_type_id})")
            
        except Exception as e:
            print(f"   Error creating default type: {e}")
            return False
        
        print("2. Updating all materials with default type...")
        
        # Update all materials without a type to use the default type
        try:
            cursor.execute("""
                UPDATE material 
                SET material_type_id = %s, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE material_type_id IS NULL
            """, (default_type_id,))
            
            updated_count = cursor.rowcount
            print(f"   Updated {updated_count} materials with default type")
            
        except Exception as e:
            print(f"   Error updating materials: {e}")
            return False
        
        conn.commit()
        
        print("3. Verifying results...")
        
        # Check final counts
        cursor.execute("SELECT COUNT(*) as count FROM material WHERE material_type_id IS NULL")
        null_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM material WHERE material_type_id IS NOT NULL")
        with_type_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM material")
        total_count = cursor.fetchone()['count']
        
        print(f"   Materials with null type_id: {null_count}")
        print(f"   Materials with type_id: {with_type_count}")
        print(f"   Total materials: {total_count}")
        
        if null_count == 0:
            print("   SUCCESS: All materials now have a material_type_id!")
            return True
        else:
            print(f"   WARNING: {null_count} materials still have null type_id")
            return False

def main():
    """Main function"""
    
    success = create_default_material_type()
    
    if success:
        print("\nMaterial type assignment completed successfully!")
    else:
        print("\nMaterial type assignment failed!")
    
    return success

if __name__ == "__main__":
    main()