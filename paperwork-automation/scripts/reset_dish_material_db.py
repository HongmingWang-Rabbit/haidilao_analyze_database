#!/usr/bin/env python3
"""
Python script to reset dish-material related tables only
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def reset_dish_material_tables():
    """Reset only dish-material related tables while preserving other data"""
    
    print("RESETTING DISH-MATERIAL RELATED TABLES")
    print("=" * 40)
    
    # Connect to test database
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Checking current table counts...")
        
        # Check current counts
        tables_to_check = [
            'dish_type', 'dish_child_type', 'dish', 'material',
            'dish_material', 'dish_price_history', 'dish_monthly_sale', 
            'material_price_history'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"   {table}: {count} records")
            except Exception as e:
                print(f"   {table}: Error - {e}")
        
        print("\n2. Clearing dish-material related tables...")
        
        # Clear tables in proper order (respecting foreign keys)
        clear_commands = [
            "DELETE FROM dish_material",
            "DELETE FROM dish_monthly_sale", 
            "DELETE FROM dish_price_history",
            "DELETE FROM material_price_history",
            "DELETE FROM material",
            "DELETE FROM dish",
            "DELETE FROM dish_child_type",
            "DELETE FROM dish_type"
        ]
        
        for command in clear_commands:
            try:
                cursor.execute(command)
                table_name = command.split()[-1]
                print(f"   Cleared {table_name}")
            except Exception as e:
                print(f"   Error clearing {command}: {e}")
        
        # Reset sequences if they exist
        print("\n3. Resetting ID sequences...")
        
        sequence_resets = [
            "SELECT setval(pg_get_serial_sequence('dish_type', 'id'), 1, false)",
            "SELECT setval(pg_get_serial_sequence('dish_child_type', 'id'), 1, false)", 
            "SELECT setval(pg_get_serial_sequence('dish', 'id'), 1, false)",
            "SELECT setval(pg_get_serial_sequence('material', 'id'), 1, false)"
        ]
        
        for reset_cmd in sequence_resets:
            try:
                cursor.execute(reset_cmd)
                print(f"   Reset sequence for {reset_cmd.split("'")[1]}")
            except Exception as e:
                print(f"   Sequence reset failed: {e}")
        
        # Commit all changes
        conn.commit()
        
        print("\n4. Verifying cleanup...")
        
        # Verify all tables are empty
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"   {table}: {count} records (should be 0)")
            except Exception as e:
                print(f"   {table}: Error - {e}")
        
        # Check that store data is preserved
        print("\n5. Verifying store data is preserved...")
        try:
            cursor.execute("SELECT COUNT(*) as count FROM store")
            store_count = cursor.fetchone()['count']
            print(f"   Stores preserved: {store_count} records")
        except Exception as e:
            print(f"   Store check failed: {e}")
    
    print("\nDish-material tables reset completed!")
    print("Store data and other tables remain intact.")

if __name__ == "__main__":
    reset_dish_material_tables()