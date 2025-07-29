#!/usr/bin/env python3
"""
Debug the query step by step to find the issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def debug_query_step_by_step():
    """Debug query step by step"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Test 1: Simple store query
        print("1. Testing basic store query:")
        simple_sql = "SELECT id, name FROM store WHERE id BETWEEN 1 AND 7 ORDER BY id"
        stores = db_manager.fetch_all(simple_sql)
        print(f"   Found {len(stores)} stores")
        
        # Test 2: Current revenue
        print("\n2. Testing current revenue:")
        current_rev_sql = """
        SELECT 
            store_id,
            SUM(sale_amount) as current_revenue
        FROM dish_monthly_sale
        WHERE year = %s AND month = %s
        GROUP BY store_id
        ORDER BY store_id
        """
        current_rev = db_manager.fetch_all(current_rev_sql, (2025, 5))
        print(f"   Found revenue for {len(current_rev)} stores")
        
        # Test 3: Previous revenue  
        print("\n3. Testing previous revenue:")
        prev_rev_sql = """
        SELECT 
            store_id,
            SUM(revenue_tax_not_included) as previous_revenue
        FROM daily_report
        WHERE EXTRACT(YEAR FROM date) = %s 
            AND EXTRACT(MONTH FROM date) = %s
        GROUP BY store_id
        ORDER BY store_id
        """
        prev_rev = db_manager.fetch_all(prev_rev_sql, (2025, 4))
        print(f"   Found previous revenue for {len(prev_rev)} stores")
        
        # Test 4: Current cost (simplified)
        print("\n4. Testing current cost (simplified):")
        current_cost_sql = """
        SELECT 
            mmu.store_id,
            COUNT(*) as material_count,
            SUM(mmu.material_used) as total_usage
        FROM material_monthly_usage mmu
        WHERE mmu.year = %s AND mmu.month = %s
        GROUP BY mmu.store_id
        ORDER BY mmu.store_id
        """
        current_cost = db_manager.fetch_all(current_cost_sql, (2025, 5))
        print(f"   Found cost data for {len(current_cost)} stores")
        
        # Test 5: The problematic LATERAL join
        print("\n5. Testing LATERAL join (this might be the issue):")
        lateral_sql = """
        SELECT 
            mmu.store_id,
            mmu.material_id,
            mmu.material_used,
            mph.price
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
            AND mmu.store_id = 1
        LIMIT 5
        """
        
        try:
            lateral_test = db_manager.fetch_all(lateral_sql, (2025, 5, 2025, 5))
            print(f"   LATERAL join works - found {len(lateral_test)} records")
        except Exception as e:
            print(f"   LATERAL join failed: {e}")
            
            # Try without LATERAL
            print("   Trying without LATERAL:")
            no_lateral_sql = """
            SELECT 
                mmu.store_id,
                COUNT(*) as records
            FROM material_monthly_usage mmu
            WHERE mmu.year = %s AND mmu.month = %s
                AND mmu.store_id = 1
            GROUP BY mmu.store_id
            """
            no_lateral = db_manager.fetch_all(no_lateral_sql, (2025, 5))
            print(f"   Without LATERAL: {len(no_lateral)} stores")
        
    except Exception as e:
        print(f"Error in step-by-step debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_query_step_by_step()