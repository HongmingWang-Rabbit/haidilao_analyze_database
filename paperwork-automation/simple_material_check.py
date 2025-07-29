#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.database import DatabaseManager, DatabaseConfig

def simple_check():
    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Simple test
            cursor.execute("SELECT COUNT(*) FROM material")
            total = cursor.fetchone()
            print(f"Total materials: {total}")
            
            # Check for 4515229
            cursor.execute("SELECT COUNT(*) FROM material WHERE material_number = %s", ("4515229",))
            count_4515229 = cursor.fetchone()
            print(f"Materials with number 4515229: {count_4515229}")
            
            # Check Store 3 specifically
            cursor.execute("SELECT COUNT(*) FROM material WHERE material_number = %s AND store_id = %s", ("4515229", 3))
            store3_count = cursor.fetchone()
            print(f"Store 3 materials with number 4515229: {store3_count}")
            
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error: {e}")

if __name__ == "__main__":
    simple_check()