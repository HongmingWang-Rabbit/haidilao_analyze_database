#!/usr/bin/env python3
"""
Verify that the SQL fix produces the correct yearly revenue values.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from utils.database import DatabaseConfig, DatabaseManager
from lib.database_queries import ReportDataProvider

def verify_sql_fix():
    """Verify the SQL fix results"""
    target_date = "2025-06-16"
    
    # Initialize database components
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    data_provider = ReportDataProvider(db_manager)
    
    print(f"🔍 Verifying SQL Fix for {target_date}")
    print("=" * 60)
    
    # Get processed data with the fix
    processed_data = data_provider.get_all_processed_data(target_date)
    yearly_previous = processed_data[6]  # yearly_previous is index 6
    
    # Expected values from manual calculation
    expected_values = {
        1: 56.29,  # 加拿大一店
        2: 28.62,  # 加拿大二店 
        7: 52.50,  # 加拿大七店
        3: 55.19,  # 加拿大三店
        4: 59.92,  # 加拿大四店
        5: 52.61,  # 加拿大五店
        6: 30.58,  # 加拿大六店
    }
    
    print(f"📊 Store-by-Store Comparison:")
    print(f"{'Store':<12} {'Expected':<12} {'Calculated':<12} {'Difference':<12} {'Match':<8}")
    print("-" * 64)
    
    total_expected = 335.71
    total_calculated = 0
    all_match = True
    
    for row in yearly_previous:
        store_id = row['store_id']
        store_name = f"Store {store_id}"
        
        calculated_revenue = float(row['total_revenue']) / 10000  # Convert to 万加元
        expected = expected_values.get(store_id, 0)
        total_calculated += calculated_revenue
        
        difference = calculated_revenue - expected
        is_close = abs(difference) < 0.05  # Within 0.05 万加元
        match_symbol = "✅" if is_close else "❌"
        
        if not is_close:
            all_match = False
        
        print(f"{store_name:<12} {expected:<12.2f} {calculated_revenue:<12.2f} {difference:<+12.2f} {match_symbol:<8}")
    
    print("-" * 64)
    total_difference = total_calculated - total_expected
    total_close = abs(total_difference) < 0.1
    total_symbol = "✅" if total_close else "❌"
    
    print(f"{'Total':<12} {total_expected:<12.2f} {total_calculated:<12.2f} {total_difference:<+12.2f} {total_symbol:<8}")
    
    print(f"\n🎯 Summary:")
    print(f"  Expected total: {total_expected:.2f} 万加元")
    print(f"  Calculated total: {total_calculated:.2f} 万加元")
    print(f"  Total difference: {total_difference:+.2f} 万加元")
    print(f"  Percentage difference: {(total_difference / total_expected) * 100:+.1f}%")
    
    if all_match and total_close:
        print(f"  ✅ SUCCESS: All values now match the manual calculation!")
    elif total_close:
        print(f"  ✅ GOOD: Total matches, minor individual differences")
    else:
        print(f"  ❌ Still some discrepancy - may need further investigation")
        
    # Show the date range being used
    print(f"\n📅 Date Range Analysis:")
    sample_store = yearly_previous[0] if yearly_previous else None
    if sample_store:
        # Get raw data to show date range
        all_data = data_provider.get_all_report_data(target_date)
        prev_year_records = [r for r in all_data if r['store_id'] == sample_store['store_id'] and r['period_type'] == 'prev_year_mtd']
        
        if prev_year_records:
            dates = [r['date'] for r in prev_year_records]
            print(f"  Previous year date range: {min(dates)} to {max(dates)} ({len(dates)} days)")
            print(f"  This should be June 1-15, 2024 (15 days) for June 16, 2025 target")

if __name__ == "__main__":
    verify_sql_fix() 