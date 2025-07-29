#!/usr/bin/env python3
"""
Test the cost calculation part separately
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def test_cost_calculation():
    """Test cost calculation query"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        print("Testing cost calculation with LATERAL join:")
        cost_sql = """
        SELECT 
            mmu.store_id,
            COUNT(*) as material_count,
            SUM(mmu.material_used * COALESCE(mph.price, 0)) as current_cost
        FROM material_monthly_usage mmu
        LEFT JOIN LATERAL (
            SELECT price 
            FROM material_price_history 
            WHERE material_id = mmu.material_id 
                AND store_id = mmu.store_id 
                AND is_active = true
                AND effective_date <= (date_trunc('month', make_date(%s, %s, 1)) + interval '1 month - 1 day')::date
            ORDER BY effective_date DESC
            LIMIT 1
        ) mph ON true
        WHERE mmu.year = %s AND mmu.month = %s
        GROUP BY mmu.store_id
        ORDER BY mmu.store_id
        """
        
        print("Executing cost query...")
        results = db_manager.fetch_all(cost_sql, (2025, 5, 2025, 5))
        
        print(f"Cost query executed successfully!")
        print(f"Results length: {len(results)}")
        
        if results:
            print("Cost results:")
            for row in results:
                print(f"  Store {row['store_id']}: Materials: {row['material_count']}, Cost: ${row['current_cost']:,.0f}")
        else:
            print("No cost results returned")
            
    except Exception as e:
        print(f"Error in cost calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cost_calculation()