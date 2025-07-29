#!/usr/bin/env python3
"""
Test material price queries for current/previous/last year
"""

import sys
import os
from datetime import datetime, timedelta
import calendar

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_database_manager

def test_material_price_queries():
    """Test material price queries for different time periods"""
    
    # Setup dates like in the script
    target_dt = datetime.strptime('2025-05-31', '%Y-%m-%d')
    month_start = target_dt.replace(day=1)
    
    if month_start.month == 1:
        prev_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        prev_month_start = month_start.replace(month=month_start.month - 1)
    prev_month_end = prev_month_start + timedelta(days=calendar.monthrange(prev_month_start.year, prev_month_start.month)[1] - 1)
    
    last_year_month_start = month_start.replace(year=month_start.year - 1)
    last_year_month_end = last_year_month_start + timedelta(days=calendar.monthrange(last_year_month_start.year, last_year_month_start.month)[1] - 1)
    
    print("Testing material price availability for different periods:")
    print(f"Current month: {target_dt.strftime('%Y-%m-%d')}")
    print(f"Previous month: {prev_month_end.strftime('%Y-%m-%d')}")
    print(f"Last year: {last_year_month_end.strftime('%Y-%m-%d')}")
    
    db = get_database_manager()
    
    # Test query similar to what's used in the script
    query = """
    SELECT 
        s.name as store_name,
        m.material_number,
        m.name as material_name,
        -- Current month average price
        (SELECT AVG(price) FROM material_price_history 
         WHERE material_id = m.id AND store_id = s.id 
         AND is_active = true AND effective_date = %s) as current_price,
        -- Previous month average price  
        (SELECT AVG(price) FROM material_price_history 
         WHERE material_id = m.id AND store_id = s.id 
         AND is_active = true AND effective_date = %s) as prev_price,
        -- Last year average price
        (SELECT AVG(price) FROM material_price_history 
         WHERE material_id = m.id AND store_id = s.id 
         AND is_active = true AND effective_date = %s) as last_year_price
    FROM material m
    CROSS JOIN store s
    WHERE m.id IN (
        SELECT DISTINCT material_id FROM material_monthly_usage 
        WHERE year = %s AND month = %s
    )
    AND s.id = 1  -- Just test store 1
    LIMIT 5
    """
    
    try:
        result = db.fetch_all(query, (
            target_dt.strftime('%Y-%m-%d'),  # current
            prev_month_end.strftime('%Y-%m-%d'),  # previous
            last_year_month_end.strftime('%Y-%m-%d'),  # last year
            target_dt.year, target_dt.month
        ))
        
        print(f"\nQuery returned {len(result)} sample materials for Store 1:")
        for row in result:
            current = row.get('current_price', 0) or 0
            prev = row.get('prev_price', 0) or 0
            last_year = row.get('last_year_price', 0) or 0
            
            print(f"Material {row['material_number']}:")
            print(f"  Current: ${current:.4f}")
            print(f"  Previous: ${prev:.4f}")
            print(f"  Last year: ${last_year:.4f}")
            print()
        
        # Summary
        has_current = any((row.get('current_price', 0) or 0) > 0 for row in result)
        has_prev = any((row.get('prev_price', 0) or 0) > 0 for row in result)
        has_last_year = any((row.get('last_year_price', 0) or 0) > 0 for row in result)
        
        print("Price data availability:")
        print(f"  Current month (2025-05): {'✅ HAS DATA' if has_current else '❌ NO DATA'}")
        print(f"  Previous month (2025-04): {'✅ HAS DATA' if has_prev else '❌ NO DATA'}")
        print(f"  Last year (2024-05): {'✅ HAS DATA' if has_last_year else '❌ NO DATA'}")
        
    except Exception as e:
        print(f"Query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_material_price_queries()