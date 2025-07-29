#!/usr/bin/env python3
"""
Debug the material cost analysis query that's failing
"""

import sys
import os
from datetime import datetime, timedelta
import calendar

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_database_manager

def test_material_cost_query():
    """Test the material cost analysis query step by step"""
    
    # Setup dates like in the main script
    target_dt = datetime.strptime('2025-05-31', '%Y-%m-%d')
    month_start = target_dt.replace(day=1)
    
    if month_start.month == 1:
        prev_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        prev_month_start = month_start.replace(month=month_start.month - 1)
    
    prev_month_end = prev_month_start + timedelta(days=calendar.monthrange(prev_month_start.year, prev_month_start.month)[1] - 1)
    
    last_year_month_start = month_start.replace(year=month_start.year - 1)
    last_year_month_end = last_year_month_start + timedelta(days=calendar.monthrange(last_year_month_start.year, last_year_month_start.month)[1] - 1)
    
    print("Date calculations:")
    print(f"  Current month: {target_dt.year}-{target_dt.month}")
    print(f"  Previous month: {prev_month_start.year}-{prev_month_start.month}")
    print(f"  Last year month: {last_year_month_start.year}-{last_year_month_start.month}")
    print(f"  prev_month_end: {prev_month_end}")
    print(f"  last_year_month_end: {last_year_month_end}")
    
    db = get_database_manager()
    
    # Test 1: Check if we have basic material usage data
    print("\n=== Test 1: Basic Material Usage Data ===")
    query1 = """
    SELECT COUNT(*) as count 
    FROM material_monthly_usage mmu
    WHERE mmu.year = %s AND mmu.month = %s
    """
    result1 = db.fetch_all(query1, (target_dt.year, target_dt.month))
    print(f"Material usage records for {target_dt.year}-{target_dt.month}: {result1[0]['count']}")
    
    # Test 2: Check material price data
    print("\n=== Test 2: Material Price Data ===")
    query2 = """
    SELECT COUNT(*) as count 
    FROM material_price_history mph
    WHERE mph.effective_date = %s AND mph.is_active = true
    """
    result2 = db.fetch_all(query2, (target_dt.strftime('%Y-%m-%d'),))
    print(f"Active material prices for {target_dt.strftime('%Y-%m-%d')}: {result2[0]['count']}")
    
    # Test 3: Check material table structure
    print("\n=== Test 3: Material Table Structure ===")
    query3 = """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'material' 
    ORDER BY ordinal_position
    """
    result3 = db.fetch_all(query3)
    print("Material table columns:")
    for row in result3:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    # Test 4: Simple material query without date issues
    print("\n=== Test 4: Simple Material Query ===")
    query4 = """
    SELECT 
        s.name as store_name,
        m.material_number,
        m.name as material_name,
        mmu.material_used as total_usage
    FROM material_monthly_usage mmu
    JOIN material m ON mmu.material_id = m.id
    JOIN store s ON mmu.store_id = s.id
    WHERE mmu.year = %s AND mmu.month = %s
    LIMIT 5
    """
    try:
        result4 = db.fetch_all(query4, (target_dt.year, target_dt.month))
        print(f"Sample material usage data:")
        for row in result4:
            print(f"  {row['store_name']}: {row['material_name']} - {row['total_usage']}")
    except Exception as e:
        print(f"Error in simple query: {e}")

if __name__ == "__main__":
    test_material_cost_query()