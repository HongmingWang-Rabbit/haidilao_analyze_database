#!/usr/bin/env python3
"""
Check store gross profit data to understand why previous month amounts are low
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def check_store_gross_profit_data():
    """Check store gross profit data sources"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        print("=== STORE GROSS PROFIT DATA INVESTIGATION ===")
        
        # Check current month data (May 2025)
        print("\n1. CURRENT MONTH REVENUE (May 2025):")
        current_revenue_sql = """
        SELECT 
            store_id,
            SUM(sale_amount) as current_revenue,
            COUNT(*) as record_count
        FROM dish_monthly_sale
        WHERE year = 2025 AND month = 5
        GROUP BY store_id
        ORDER BY store_id
        """
        
        current_revenue = db_manager.fetch_all(current_revenue_sql)
        if current_revenue:
            for row in current_revenue:
                print(f"  Store {row['store_id']}: ${row['current_revenue']:,.2f} ({row['record_count']} records)")
        else:
            print("  No current month revenue data found")
        
        # Check previous month data (April 2025)
        print("\n2. PREVIOUS MONTH REVENUE (April 2025):")
        prev_revenue_sql = """
        SELECT 
            store_id,
            SUM(sale_amount) as previous_revenue,
            COUNT(*) as record_count
        FROM dish_monthly_sale
        WHERE year = 2025 AND month = 4
        GROUP BY store_id
        ORDER BY store_id
        """
        
        prev_revenue = db_manager.fetch_all(prev_revenue_sql)
        if prev_revenue:
            for row in prev_revenue:
                print(f"  Store {row['store_id']}: ${row['previous_revenue']:,.2f} ({row['record_count']} records)")
        else:
            print("  No previous month revenue data found")
        
        # Check current month cost data
        print("\n3. CURRENT MONTH COST (May 2025):")
        current_cost_sql = """
        SELECT 
            mmu.store_id,
            SUM(mmu.material_used * COALESCE(mph.price, 0)) as current_cost,
            COUNT(*) as record_count
        FROM material_monthly_usage mmu
        LEFT JOIN LATERAL (
            SELECT price 
            FROM material_price_history 
            WHERE material_id = mmu.material_id 
                AND store_id = mmu.store_id 
                AND is_active = true
                AND effective_date <= '2025-05-31'
            ORDER BY effective_date DESC
            LIMIT 1
        ) mph ON true
        WHERE mmu.year = 2025 AND mmu.month = 5
        GROUP BY mmu.store_id
        ORDER BY mmu.store_id
        """
        
        current_cost = db_manager.fetch_all(current_cost_sql)
        if current_cost:
            for row in current_cost:
                print(f"  Store {row['store_id']}: ${row['current_cost']:,.2f} ({row['record_count']} records)")
        else:
            print("  No current month cost data found")
        
        # Check previous month cost data
        print("\n4. PREVIOUS MONTH COST (April 2025):")
        prev_cost_sql = """
        SELECT 
            mmu.store_id,
            SUM(mmu.material_used * COALESCE(mph.price, 0)) as previous_cost,
            COUNT(*) as record_count
        FROM material_monthly_usage mmu
        LEFT JOIN LATERAL (
            SELECT price 
            FROM material_price_history 
            WHERE material_id = mmu.material_id 
                AND store_id = mmu.store_id 
                AND is_active = true
                AND effective_date <= '2025-04-30'
            ORDER BY effective_date DESC
            LIMIT 1
        ) mph ON true
        WHERE mmu.year = 2025 AND mmu.month = 4
        GROUP BY mmu.store_id
        ORDER BY mmu.store_id
        """
        
        prev_cost = db_manager.fetch_all(prev_cost_sql)
        if prev_cost:
            for row in prev_cost:
                print(f"  Store {row['store_id']}: ${row['previous_cost']:,.2f} ({row['record_count']} records)")
        else:
            print("  No previous month cost data found")
        
        # Check if we have any data at all for April 2025
        print("\n5. APRIL 2025 DATA AVAILABILITY CHECK:")
        april_check_sql = """
        SELECT 
            'dish_monthly_sale' as table_name,
            COUNT(*) as record_count,
            SUM(sale_amount) as total_amount
        FROM dish_monthly_sale 
        WHERE year = 2025 AND month = 4
        UNION ALL
        SELECT 
            'material_monthly_usage' as table_name,
            COUNT(*) as record_count,
            SUM(material_used) as total_amount
        FROM material_monthly_usage 
        WHERE year = 2025 AND month = 4
        """
        
        april_data = db_manager.fetch_all(april_check_sql)
        for row in april_data:
            print(f"  {row['table_name']}: {row['record_count']} records, total: {row['total_amount'] or 0:.2f}")
        
        # Check daily_report for previous month as alternative source
        print("\n6. DAILY_REPORT ALTERNATIVE (April 2025):")
        daily_report_sql = """
        SELECT 
            store_id,
            COUNT(*) as days,
            SUM(revenue_tax_not_included) as total_revenue
        FROM daily_report
        WHERE EXTRACT(YEAR FROM date) = 2025 
            AND EXTRACT(MONTH FROM date) = 4
        GROUP BY store_id
        ORDER BY store_id
        """
        
        daily_data = db_manager.fetch_all(daily_report_sql)
        if daily_data:
            print("Alternative revenue source from daily_report:")
            for row in daily_data:
                print(f"  Store {row['store_id']}: ${row['total_revenue']:,.2f} over {row['days']} days")
        else:
            print("  No daily_report data found for April 2025")
        
    except Exception as e:
        print(f"Error checking store gross profit data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_store_gross_profit_data()