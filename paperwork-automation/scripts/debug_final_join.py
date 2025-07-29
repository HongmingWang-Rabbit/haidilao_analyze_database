#!/usr/bin/env python3
"""
Debug the final previous cost join
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def debug_final_join():
    """Debug the final previous cost join"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Test the previous cost subquery alone first
        print("1. Testing previous cost subquery alone:")
        prev_cost_alone_sql = """
        SELECT 
            store_id,
            ROUND(SUM(revenue_tax_not_included) * 0.65, 2) as previous_cost
        FROM daily_report
        WHERE EXTRACT(YEAR FROM date) = %s 
            AND EXTRACT(MONTH FROM date) = %s
        GROUP BY store_id
        ORDER BY store_id
        """
        prev_cost_alone = db_manager.fetch_all(prev_cost_alone_sql, (2025, 4))
        print(f"   {len(prev_cost_alone)} stores with previous cost")
        if prev_cost_alone:
            for row in prev_cost_alone[:3]:
                print(f"     Store {row['store_id']}: Previous Cost=${row['previous_cost']:,.2f}")
        
        # Now test the full query with the final join
        print("\\n2. Testing full query with all joins:")
        full_sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            COALESCE(cr.current_revenue, 0) as current_revenue,
            COALESCE(cc.current_cost, 0) as current_cost,
            COALESCE(pr.previous_revenue, 0) as previous_revenue,
            COALESCE(pc.previous_cost, 0) as previous_cost
        FROM store s
        LEFT JOIN (
            SELECT 
                store_id,
                SUM(sale_amount) as current_revenue
            FROM dish_monthly_sale
            WHERE year = %s AND month = %s
            GROUP BY store_id
        ) cr ON s.id = cr.store_id
        LEFT JOIN (
            SELECT 
                mmu.store_id,
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
        ) cc ON s.id = cc.store_id
        LEFT JOIN (
            SELECT 
                store_id,
                SUM(revenue_tax_not_included) as previous_revenue
            FROM daily_report
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
            GROUP BY store_id
        ) pr ON s.id = pr.store_id
        LEFT JOIN (
            SELECT 
                store_id,
                ROUND(SUM(revenue_tax_not_included) * 0.65, 2) as previous_cost
            FROM daily_report
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
            GROUP BY store_id
        ) pc ON s.id = pc.store_id
        WHERE s.id BETWEEN 1 AND 7
        ORDER BY s.id
        """
        
        params = (2025, 5, 2025, 5, 2025, 5, 2025, 4, 2025, 4)
        print(f"Parameters: {params}")
        
        full_result = db_manager.fetch_all(full_sql, params)
        print(f"   Full query returned {len(full_result)} stores")
        
        if full_result:
            print("   Sample data:")
            for row in full_result[:2]:
                print(f"     Store {row['store_id']}: Current Rev=${row['current_revenue']:,.0f}, Cost=${row['current_cost']:,.0f}, Prev Rev=${row['previous_revenue']:,.0f}, Prev Cost=${row['previous_cost']:,.2f}")
        else:
            print("   No results - this is the problem!")
        
    except Exception as e:
        print(f"Error: {e}")  
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_final_join()