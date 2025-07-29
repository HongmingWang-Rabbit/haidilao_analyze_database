#!/usr/bin/env python3
"""
Find alternative cost data sources for previous month
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def find_cost_data_source():
    """Find cost data sources"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        print("=== COST DATA SOURCE INVESTIGATION ===")
        
        # Check if daily_cost_detail or similar table exists
        print("\n1. Looking for cost-related tables:")
        cost_tables_sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%cost%' OR table_name LIKE '%expense%')
        """
        
        cost_tables = db_manager.fetch_all(cost_tables_sql)
        if cost_tables:
            for table in cost_tables:
                print(f"  - {table['table_name']}")
        else:
            print("  No cost-related tables found")
        
        # Check material-related tables for historical data
        print("\n2. Material-related tables:")
        material_tables_sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%material%'
        """
        
        material_tables = db_manager.fetch_all(material_tables_sql)
        for table in material_tables:
            print(f"  - {table['table_name']}")
        
        # Check if we have daily material usage data
        print("\n3. Checking for daily material usage:")
        daily_material_sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%daily%' AND table_name LIKE '%material%')
        """
        
        daily_material_tables = db_manager.fetch_all(daily_material_sql)
        if daily_material_tables:
            for table in daily_material_tables:
                print(f"  Found: {table['table_name']}")
        else:
            print("  No daily material tables found")
        
        # Check material_price_history for April 2025 prices
        print("\n4. Material prices available for April 2025:")
        april_prices_sql = """
        SELECT 
            store_id,
            COUNT(DISTINCT material_id) as material_count,
            MIN(effective_date) as earliest_date,
            MAX(effective_date) as latest_date
        FROM material_price_history 
        WHERE effective_date >= '2025-04-01' 
            AND effective_date <= '2025-04-30'
        GROUP BY store_id
        ORDER BY store_id
        """
        
        april_prices = db_manager.fetch_all(april_prices_sql)
        if april_prices:
            print("Material prices available for April 2025:")
            for row in april_prices:
                print(f"  Store {row['store_id']}: {row['material_count']} materials ({row['earliest_date']} to {row['latest_date']})")
        else:
            print("  No material prices found for April 2025")
        
        # Alternative: Calculate estimated cost using current usage pattern
        print("\n5. ALTERNATIVE APPROACH:")
        print("Since April material usage data is missing, options are:")
        print("  A) Use current month usage pattern with April prices")
        print("  B) Use a fixed cost-to-revenue ratio estimate")
        print("  C) Set previous month cost to 0 until data is available")
        print("  D) Use May usage data with April prices as estimate")
        
        # Check the cost-to-revenue ratio from current month for estimation
        current_ratio_sql = """
        SELECT 
            s.id as store_id,
            COALESCE(SUM(dms.sale_amount), 0) as revenue,
            COALESCE(SUM(mmu.material_used * mph.price), 0) as cost,
            CASE 
                WHEN SUM(dms.sale_amount) > 0 
                THEN SUM(mmu.material_used * mph.price) / SUM(dms.sale_amount) * 100
                ELSE 0 
            END as cost_ratio_percent
        FROM store s
        LEFT JOIN dish_monthly_sale dms ON s.id = dms.store_id 
            AND dms.year = 2025 AND dms.month = 5
        LEFT JOIN material_monthly_usage mmu ON s.id = mmu.store_id 
            AND mmu.year = 2025 AND mmu.month = 5
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
        WHERE s.id BETWEEN 1 AND 7
        GROUP BY s.id
        ORDER BY s.id
        """
        
        ratios = db_manager.fetch_all(current_ratio_sql)
        if ratios:
            print("\nCurrent month cost-to-revenue ratios (for estimation):")
            for row in ratios:
                print(f"  Store {row['store_id']}: {row['cost_ratio_percent']:.1f}% (Cost/Revenue)")
        
    except Exception as e:
        print(f"Error finding cost data source: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_cost_data_source()