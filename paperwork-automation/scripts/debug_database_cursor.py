#!/usr/bin/env python3
"""
Debug what the database cursor is actually returning
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def debug_cursor_format():
    """Debug what format the cursor returns"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Test simple query first
        simple_sql = "SELECT id, name FROM store WHERE id = 1"
        print("1. Testing simple query:")
        result = db_manager.fetch_all(simple_sql)
        print(f"   Result type: {type(result)}")
        if result:
            print(f"   First row type: {type(result[0])}")
            try:
                print(f"   First row content: {dict(result[0])}")
            except UnicodeEncodeError:
                print("   First row content: <Unicode encoding error - Chinese characters>")
            print(f"   Keys available: {list(result[0].keys()) if hasattr(result[0], 'keys') else 'No keys method'}")
        else:
            print("   No results returned")
            
        # Test if it's accessing as dict
        print("\n2. Testing dictionary access:")
        if result:
            try:
                store_id = result[0]['id']
                store_name = result[0]['name']
                print(f"   Dictionary access works: id={store_id}, name={store_name}")
            except Exception as e:
                print(f"   Dictionary access failed: {e}")
                # Try tuple access
                try:
                    store_id = result[0][0]
                    store_name = result[0][1]
                    print(f"   Tuple access works: id={store_id}, name={store_name}")
                except Exception as e2:
                    print(f"   Tuple access also failed: {e2}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_cursor_format()