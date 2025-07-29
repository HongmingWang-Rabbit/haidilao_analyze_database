#!/usr/bin/env python3
"""
Test the comparative analysis query directly
"""

import sys
import os
from datetime import datetime, timedelta
import calendar

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_database_manager

def test_comparative_query():
    """Test the comparative analysis query that's used in YoY/MoM sheet"""
    
    # Setup dates
    target_dt = datetime.strptime('2025-05-31', '%Y-%m-%d')
    month_start = target_dt.replace(day=1)
    month_end = target_dt
    
    # Previous month
    if month_start.month == 1:
        prev_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        prev_month_start = month_start.replace(month=month_start.month - 1)
    prev_month_end = prev_month_start + timedelta(days=calendar.monthrange(prev_month_start.year, prev_month_start.month)[1] - 1)
    
    # Last year same month
    last_year_month_start = month_start.replace(year=month_start.year - 1)
    last_year_month_end = last_year_month_start + timedelta(days=calendar.monthrange(last_year_month_start.year, last_year_month_start.month)[1] - 1)
    
    print("Date parameters:")
    print(f"Current: {month_start} to {month_end}")
    print(f"Previous: {prev_month_start} to {prev_month_end}")  
    print(f"Last year: {last_year_month_start} to {last_year_month_end}")
    print(f"Current year/month: {target_dt.year}/{target_dt.month}")
    print(f"Previous year/month: {prev_month_start.year}/{prev_month_start.month}")
    print(f"Last year year/month: {last_year_month_start.year}/{last_year_month_start.month}")
    
    db = get_database_manager()
    
    # Test the exact query from the script
    query = """
    WITH current_month AS (
        SELECT 
            s.id as store_id,
            s.name as store_name,
            SUM(dr.revenue_tax_not_included) as revenue,
            COUNT(DISTINCT dr.date) as days_open,
            COALESCE(SUM(dr.customers), 0) as total_customers,
            COALESCE(AVG(dr.revenue_tax_not_included / NULLIF(dr.customers, 0)), 0) as avg_ticket
        FROM daily_report dr
        JOIN store s ON dr.store_id = s.id
        WHERE dr.date BETWEEN %s AND %s
        GROUP BY s.id, s.name
    ),
    prev_month AS (
        SELECT 
            store_id,
            SUM(revenue_tax_not_included) as revenue
        FROM daily_report
        WHERE date BETWEEN %s AND %s
        GROUP BY store_id
    ),
    last_year AS (
        SELECT 
            store_id,
            SUM(revenue_tax_not_included) as revenue
        FROM daily_report
        WHERE date BETWEEN %s AND %s
        GROUP BY store_id
    )
    SELECT 
        cm.store_name,
        cm.revenue as current_revenue,
        COALESCE(pm.revenue, 0) as prev_revenue,
        COALESCE(ly.revenue, 0) as last_year_revenue,
        cm.days_open,
        cm.total_customers,
        cm.avg_ticket
    FROM current_month cm
    LEFT JOIN prev_month pm ON cm.store_id = pm.store_id
    LEFT JOIN last_year ly ON cm.store_id = ly.store_id
    ORDER BY cm.store_name
    """
    
    try:
        result = db.fetch_all(query, (
            month_start, month_end,  # current month revenue
            prev_month_start, prev_month_end,  # prev month revenue
            last_year_month_start, last_year_month_end  # last year revenue
        ))
        
        print(f"\nQuery returned {len(result)} rows")
        
        if result:
            print("Sample results:")
            for i, row in enumerate(result[:3]):
                # Avoid Chinese characters in output
                store_id = i + 1  # Just use index instead of name
                current_rev = row.get('current_revenue', 0) or 0
                prev_rev = row.get('prev_revenue', 0) or 0  
                last_year_rev = row.get('last_year_revenue', 0) or 0
                days = row.get('days_open', 0) or 0
                
                print(f"  Store {store_id}: Current=${current_rev:.2f}, Prev=${prev_rev:.2f}, LastYear=${last_year_rev:.2f}, Days={days}")
                
            # Check if there's meaningful data
            has_current_data = any((row.get('current_revenue', 0) or 0) > 0 for row in result)
            has_prev_data = any((row.get('prev_revenue', 0) or 0) > 0 for row in result)
            has_last_year_data = any((row.get('last_year_revenue', 0) or 0) > 0 for row in result)
            
            print(f"\nData availability:")
            print(f"  Current month revenue: {'YES' if has_current_data else 'NO'}")
            print(f"  Previous month revenue: {'YES' if has_prev_data else 'NO'}")
            print(f"  Last year revenue: {'YES' if has_last_year_data else 'NO'}")
            
        else:
            print("NO RESULTS returned from query")
            
    except Exception as e:
        print(f"Query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comparative_query()