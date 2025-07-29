#!/usr/bin/env python3
"""
Debug the store query joins one by one
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def debug_joins():
    """Debug each join individually"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Test 1: Just stores
        print("1. Testing just stores:")
        stores_sql = "SELECT id as store_id, name as store_name FROM store WHERE id BETWEEN 1 AND 7 ORDER BY id"
        stores = db_manager.fetch_all(stores_sql)
        print(f"   {len(stores)} stores found")
        
        # Test 2: Stores + current revenue
        print("2. Testing stores + current revenue:")
        stores_rev_sql = """
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
        stores_rev = db_manager.fetch_all(stores_rev_sql, (2025, 5))
        print(f"   {len(stores_rev)} stores with revenue")
        
        # Test 3: Stores + current revenue + current cost
        print("3. Testing stores + current revenue + current cost:")
        stores_cost_sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            COALESCE(cr.current_revenue, 0) as current_revenue,
            COALESCE(cc.current_cost, 0) as current_cost
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
        WHERE s.id BETWEEN 1 AND 7
        ORDER BY s.id
        """
        stores_cost = db_manager.fetch_all(stores_cost_sql, (2025, 5, 2025, 5, 2025, 5))
        print(f"   {len(stores_cost)} stores with revenue and cost")
        
        # Test 4: Add previous revenue
        print("4. Testing + previous revenue:")
        prev_rev_sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            COALESCE(cr.current_revenue, 0) as current_revenue,
            COALESCE(cc.current_cost, 0) as current_cost,
            COALESCE(pr.previous_revenue, 0) as previous_revenue
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
        WHERE s.id BETWEEN 1 AND 7
        ORDER BY s.id
        """
        prev_rev = db_manager.fetch_all(prev_rev_sql, (2025, 5, 2025, 5, 2025, 5, 2025, 4))
        print(f"   {len(prev_rev)} stores with revenue, cost, and previous revenue")
        
        if prev_rev:
            print("   Sample data:")
            for row in prev_rev[:2]:
                print(f"     Store {row['store_id']}: Current Rev=${row['current_revenue']:,.0f}, Cost=${row['current_cost']:,.0f}, Prev Rev=${row['previous_revenue']:,.0f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_joins()