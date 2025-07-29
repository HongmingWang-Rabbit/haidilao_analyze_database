#!/usr/bin/env python3
"""
Test the store gross profit query method directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.database_queries import ReportDataProvider
from utils.database import DatabaseManager, DatabaseConfig

def test_store_gross_direct():
    """Test store gross profit method directly"""
    
    try:
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        queries = ReportDataProvider(db_manager)
        print("Testing get_store_gross_profit_data method...")
        
        # Test with May 2025 data
        result = queries.get_store_gross_profit_data("2025-05-01")
        
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)}")
        
        if result:
            print("First few records:")
            for i, record in enumerate(result[:3]):
                print(f"  Record {i+1}: Store {record.get('store_id', 'N/A')}, Revenue ${record.get('current_revenue', 0):,.0f}")
        else:
            print("No results returned")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_store_gross_direct()