#!/usr/bin/env python3
"""
Fix monthly_combo_dish_sale table schema - add missing combo_id column
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def fix_monthly_combo_dish_sale_schema():
    """Add missing combo_id column and correct constraints"""
    
    print("FIXING MONTHLY_COMBO_DISH_SALE SCHEMA")
    print("=" * 40)
    
    config = DatabaseConfig(is_test=False)  # Production database
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Checking current schema...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'monthly_combo_dish_sale'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("   Current columns:")
        for c in columns:
            print(f"     {c['column_name']} ({c['data_type']}) - nullable: {c['is_nullable']}")
        
        # Check if combo_id column exists
        has_combo_id = any(c['column_name'] == 'combo_id' for c in columns)
        
        if not has_combo_id:
            print("2. Adding missing combo_id column...")
            cursor.execute("""
                ALTER TABLE monthly_combo_dish_sale 
                ADD COLUMN combo_id INTEGER
            """)
            
            print("3. Adding foreign key constraint for combo_id...")
            cursor.execute("""
                ALTER TABLE monthly_combo_dish_sale 
                ADD CONSTRAINT monthly_combo_dish_sale_combo_id_fkey 
                FOREIGN KEY (combo_id) REFERENCES combo(id)
            """)
            
            print("4. Dropping old unique constraint...")
            cursor.execute("""
                ALTER TABLE monthly_combo_dish_sale 
                DROP CONSTRAINT IF EXISTS monthly_combo_dish_sale_dish_id_store_id_year_month_key
            """)
            
            print("5. Adding correct unique constraint with combo_id...")
            cursor.execute("""
                ALTER TABLE monthly_combo_dish_sale 
                ADD CONSTRAINT monthly_combo_dish_sale_combo_id_dish_id_store_id_year_month_key 
                UNIQUE (combo_id, dish_id, store_id, year, month)
            """)
            
            print("6. Adding updated_at column if missing...")
            cursor.execute("""
                ALTER TABLE monthly_combo_dish_sale 
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            
            conn.commit()
            print("✅ Schema fixes applied successfully!")
        else:
            print("✅ combo_id column already exists, no changes needed")
        
        # Verify final schema
        print("7. Verifying final schema...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'monthly_combo_dish_sale'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("   Final columns:")
        for c in columns:
            print(f"     {c['column_name']} ({c['data_type']}) - nullable: {c['is_nullable']}")
        
        # Show constraints
        cursor.execute("""
            SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'monthly_combo_dish_sale'
            ORDER BY tc.constraint_type, tc.constraint_name, kcu.ordinal_position
        """)
        constraints = cursor.fetchall()
        print("   Final constraints:")
        current_constraint = None
        columns_in_constraint = []
        for c in constraints:
            if c['constraint_name'] != current_constraint:
                if current_constraint:
                    print(f"     {constraint_type}: {current_constraint} on ({', '.join(columns_in_constraint)})")
                current_constraint = c['constraint_name']
                constraint_type = c['constraint_type']
                columns_in_constraint = [c['column_name']]
            else:
                columns_in_constraint.append(c['column_name'])
        
        # Print last constraint
        if current_constraint:
            print(f"     {constraint_type}: {current_constraint} on ({', '.join(columns_in_constraint)})")
        
        return True

def main():
    """Main function"""
    
    success = fix_monthly_combo_dish_sale_schema()
    
    if success:
        print("\nSchema fix completed successfully!")
    else:
        print("\nSchema fix failed!")
    
    return success

if __name__ == "__main__":
    main()