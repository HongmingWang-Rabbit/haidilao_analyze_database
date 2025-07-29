#!/usr/bin/env python3
"""
Test a minimal version of the store query to isolate the issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def test_minimal_query():
    """Test minimal store query"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Test minimal query that should return results
        print("Testing minimal store revenue query:")
        minimal_sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            COALESCE(cr.current_revenue, 0) as current_revenue
        FROM store s
        LEFT JOIN (
            SELECT 
                store_id,
                SUM(sale_amount) as current_revenue
            FROM dish_monthly_sale
            WHERE year = %s AND month = %s
            GROUP BY store_id
        ) cr ON s.id = cr.store_id
        WHERE s.id BETWEEN 1 AND 7
        ORDER BY s.id
        """
        
        print("Executing query...")
        results = db_manager.fetch_all(minimal_sql, (2025, 5))
        
        print(f"Query executed successfully!")
        print(f"Results type: {type(results)}")
        print(f"Results length: {len(results)}")
        
        if results:
            print("First few results:")
            for i, row in enumerate(results[:3]):
                try:
                    print(f"  Store {row['store_id']}: {row['store_name'][:20]}... Revenue: ${row['current_revenue']:,.0f}")
                except UnicodeEncodeError:
                    print(f"  Store {row['store_id']}: <Chinese name> Revenue: ${row['current_revenue']:,.0f}")
                except Exception as e:
                    print(f"  Row {i}: Error accessing data - {e}")
        else:
            print("No results returned")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_query()