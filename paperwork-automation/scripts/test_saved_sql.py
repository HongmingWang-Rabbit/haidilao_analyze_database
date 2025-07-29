#!/usr/bin/env python3
"""
Test the exact SQL that was saved from the method
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def test_saved_sql():
    """Test the saved SQL file"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Read the exact SQL from the saved file
        with open("debug_sql_output.sql", "r", encoding="utf-8") as f:
            sql = f.read()
        
        print(f"SQL length: {len(sql)}")
        print(f"SQL placeholders: {sql.count('%s')}")
        
        # Test parameters
        params = (2025, 5, 2025, 5, 2025, 5, 2025, 4, 2025, 4)
        print(f"Parameters: {params}")
        print(f"Parameter count: {len(params)}")
        
        print("\\nTesting the saved SQL...")
        results = db_manager.fetch_all(sql, params)
        
        print(f"Results: {len(results)} rows")
        if results:
            print("Sample data:")
            for row in results[:2]:
                print(f"  Store {row['store_id']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_saved_sql()