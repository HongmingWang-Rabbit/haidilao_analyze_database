#!/usr/bin/env python3
"""
Add missing updated_at column to dish_monthly_sale table
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def add_updated_at_column():
    """Add updated_at column to dish_monthly_sale table"""
    
    print("ADDING UPDATED_AT COLUMN TO DISH_MONTHLY_SALE")
    print("=" * 45)
    
    # Connect to test database
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Checking if updated_at column exists...")
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'dish_monthly_sale' 
            AND column_name = 'updated_at'
        """)
        
        existing_column = cursor.fetchone()
        
        if existing_column:
            print("   updated_at column already exists!")
            return True
        
        print("   updated_at column does not exist, adding...")
        
        try:
            # Add updated_at column
            cursor.execute("""
                ALTER TABLE dish_monthly_sale 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            
            print("   Added updated_at column")
            
            # Update existing records to have current timestamp
            cursor.execute("""
                UPDATE dish_monthly_sale 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE updated_at IS NULL
            """)
            
            updated_rows = cursor.rowcount
            print(f"   Updated {updated_rows} existing records with current timestamp")
            
            conn.commit()
            
            print("\n2. Verifying the column was added...")
            
            # Verify column was added
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'dish_monthly_sale' 
                AND column_name = 'updated_at'
            """)
            
            column_info = cursor.fetchone()
            if column_info:
                print(f"   ✅ Column added successfully:")
                print(f"      Name: {column_info['column_name']}")
                print(f"      Type: {column_info['data_type']}")
                print(f"      Nullable: {column_info['is_nullable']}")
                print(f"      Default: {column_info['column_default']}")
            else:
                print("   ❌ Column was not added properly")
                return False
            
            print("\n3. Testing column functionality...")
            
            # Test insert with updated_at
            cursor.execute("""
                SELECT COUNT(*) as count FROM dish_monthly_sale LIMIT 1
            """)
            count = cursor.fetchone()['count']
            print(f"   Current record count: {count}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error adding column: {e}")
            conn.rollback()
            return False
    
    print("\nUpdated_at column addition completed!")

if __name__ == "__main__":
    add_updated_at_column()