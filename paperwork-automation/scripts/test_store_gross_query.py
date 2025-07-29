#!/usr/bin/env python3
"""
Test the store gross profit query directly to debug parameter issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig
from datetime import datetime

def test_store_gross_query():
    """Test store gross profit query directly"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    target_date = "2025-05-01"
    target_dt = datetime.strptime(target_date, '%Y-%m-%d')
    current_year = target_dt.year
    current_month = target_dt.month

    # Calculate previous month and year
    if current_month == 1:
        prev_month = 12
        prev_month_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_month_year = current_year
    
    sql = """
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
            -- Estimate previous month cost using previous month revenue * 65% (typical restaurant cost ratio)
            ROUND(SUM(revenue_tax_not_included) * 0.65, 2) as previous_cost
        FROM daily_report
        WHERE EXTRACT(YEAR FROM date) = %s 
            AND EXTRACT(MONTH FROM date) = %s
        GROUP BY store_id
    ) pc ON s.id = pc.store_id
    WHERE s.id BETWEEN 1 AND 7
    ORDER BY s.id
    """
    
    try:
        # Count placeholders in SQL
        placeholder_count = sql.count('%s')
        print(f"SQL placeholders: {placeholder_count}")
        
        params = (
            current_year, current_month,  # Current revenue
            current_year, current_month,  # Current cost price date (year, month for CAST)
            current_year, current_month,  # Current cost where clause
            prev_month_year, prev_month,  # Previous revenue (from daily_report)
            prev_month_year, prev_month   # Previous cost estimation (from daily_report with 65% ratio)
        )
        
        print(f"Parameters provided: {len(params)}")
        print(f"Parameters: {params}")
        
        if placeholder_count != len(params):
            print(f"ERROR: Mismatch - SQL has {placeholder_count} placeholders but {len(params)} parameters provided")
            return
        
        results = db_manager.fetch_all(sql, params)
        
        print(f"\nQuery Results:")
        if results:
            for row in results:
                print(f"Store {row['store_id']}: Current Rev=${row['current_revenue']:,.0f}, Cost=${row['current_cost']:,.0f}, Prev Rev=${row['previous_revenue']:,.0f}, Prev Cost=${row['previous_cost']:,.0f}")
        else:
            print("No results returned")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_store_gross_query()