#!/usr/bin/env python3
"""
Test the method exactly as it's called
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.database_queries import ReportDataProvider
from utils.database import DatabaseManager, DatabaseConfig

def test_method_exactly():
    """Test the exact method call"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    data_provider = ReportDataProvider(db_manager)
    
    try:
        print("Calling get_store_gross_profit_data method exactly...")
        result = data_provider.get_store_gross_profit_data("2025-05-01")
        
        print(f"Method returned: {type(result)}")
        print(f"Length: {len(result)}")
        
        if result:
            print("Data returned:")
            for item in result[:2]:
                print(f"  Store {item['store_id']}: Revenue ${item['current_revenue']:,.0f}")
        else:
            print("Empty result returned")
            
    except Exception as e:
        print(f"Error in method call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_method_exactly()