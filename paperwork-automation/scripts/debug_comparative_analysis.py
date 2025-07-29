#!/usr/bin/env python3
"""
Debug the comparative analysis query for YoY/MoM sheet
"""

import sys
import os
from datetime import datetime, timedelta
import calendar

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_database_manager

def debug_comparative_analysis():
    """Debug the comparative analysis query step by step"""
    
    # Setup dates like in the main script
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
    
    print("Debugging comparative analysis query...")
    print(f"Current month: {month_start} to {month_end}")
    print(f"Previous month: {prev_month_start} to {prev_month_end}")
    print(f"Last year month: {last_year_month_start} to {last_year_month_end}")
    
    db = get_database_manager()
    
    # Test the simplified query first
    print("\n=== Test 1: Simple store revenue check ===")
    query1 = """
    SELECT s.id, s.name, COUNT(dr.id) as report_count
    FROM store s
    LEFT JOIN daily_report dr ON s.id = dr.store_id 
        AND dr.date >= %s AND dr.date <= %s
    GROUP BY s.id, s.name
    ORDER BY s.id
    """
    try:
        result1 = db.fetch_all(query1, (month_start, month_end))
        print("Store report counts for current month:")
        for row in result1:
            print(f"  Store {row['id']}: {row['report_count']} reports")
    except Exception as e:
        print(f"Error in simple query: {e}")
    
    # Test the full comparative query
    print("\n=== Test 2: Full comparative query ===")
    query2 = """
    WITH current_month AS (
        SELECT 
            s.id as store_id,
            s.name as store_name,
            COALESCE(SUM(dr.revenue_tax_not_included), 0) as revenue,
            COALESCE(SUM(dr.material_cost), 0) as material_cost,
            COUNT(DISTINCT dr.date) as days_open,
            COALESCE(SUM(dr.transaction_count), 0) as transaction_count,
            COALESCE(AVG(dr.average_ticket_size), 0) as avg_ticket
        FROM store s
        LEFT JOIN daily_report dr ON s.id = dr.store_id 
            AND dr.date >= %s AND dr.date <= %s
        GROUP BY s.id, s.name
    ),
    prev_month AS (
        SELECT 
            s.id as store_id,
            COALESCE(SUM(dr.revenue_tax_not_included), 0) as revenue
        FROM store s
        LEFT JOIN daily_report dr ON s.id = dr.store_id 
            AND dr.date >= %s AND dr.date <= %s
        GROUP BY s.id
    ),
    last_year AS (
        SELECT 
            s.id as store_id,
            COALESCE(SUM(dr.revenue_tax_not_included), 0) as revenue
        FROM store s
        LEFT JOIN daily_report dr ON s.id = dr.store_id 
            AND dr.date >= %s AND dr.date <= %s
        GROUP BY s.id
    )
    SELECT 
        cm.store_name,
        cm.revenue as current_revenue,
        COALESCE(pm.revenue, 0) as prev_revenue,
        COALESCE(ly.revenue, 0) as last_year_revenue,
        cm.material_cost as current_cost,
        cm.days_open,
        cm.transaction_count,
        cm.avg_ticket
    FROM current_month cm
    LEFT JOIN prev_month pm ON cm.store_id = pm.store_id
    LEFT JOIN last_year ly ON cm.store_id = ly.store_id
    ORDER BY cm.store_name
    """
    try:
        result2 = db.fetch_all(query2, (
            month_start, month_end,  # current
            prev_month_start, prev_month_end,  # prev
            last_year_month_start, last_year_month_end  # last year
        ))
        print(f"Comparative query returned {len(result2)} rows")
        print("Sample results:")
        for i, row in enumerate(result2[:3]):
            print(f"  Row {i}: Store revenue=${row.get('current_revenue', 0)}, days={row.get('days_open', 0)}")
            
        # Check if any row has data
        has_data = any(row.get('current_revenue', 0) > 0 for row in result2)
        print(f"Has meaningful data: {has_data}")
        
    except Exception as e:
        print(f"Error in comparative query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_comparative_analysis()