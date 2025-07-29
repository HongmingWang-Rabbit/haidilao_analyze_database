#!/usr/bin/env python3
"""
Check discount data in monthly_discount_summary table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def check_discount_data():
    """Check discount data aggregation"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Check if monthly_discount_summary table exists
        tables_sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%discount%'
        """
        
        tables = db_manager.fetch_all(tables_sql)
        print("Discount-related tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check monthly_discount_summary data for May 2025
        monthly_sql = """
        SELECT 
            store_id,
            discount_type_id,
            year,
            month,
            total_discount_amount,
            total_discount_count
        FROM monthly_discount_summary 
        WHERE year = 2025 AND month = 5
        ORDER BY store_id, discount_type_id
        LIMIT 10
        """
        
        monthly_data = db_manager.fetch_all(monthly_sql)
        print(f"\nMonthly discount summary (May 2025) - Sample:")
        if monthly_data:
            for row in monthly_data:
                print(f"  Store {row['store_id']}, Type {row['discount_type_id']}: ${row['total_discount_amount']:.2f} ({row['total_discount_count']} times)")
        else:
            print("  No data found in monthly_discount_summary for May 2025")
        
        # Check daily_discount_detail data for comparison
        daily_sql = """
        SELECT 
            store_id,
            discount_type_id,
            COUNT(*) as days_with_discounts,
            SUM(discount_amount) as total_amount,
            SUM(discount_count) as total_count
        FROM daily_discount_detail 
        WHERE EXTRACT(YEAR FROM date) = 2025 
        AND EXTRACT(MONTH FROM date) = 5
        GROUP BY store_id, discount_type_id
        ORDER BY store_id, discount_type_id
        LIMIT 10
        """
        
        daily_data = db_manager.fetch_all(daily_sql)
        print(f"\nDaily discount aggregation (May 2025) - Sample:")
        if daily_data:
            for row in daily_data:
                print(f"  Store {row['store_id']}, Type {row['discount_type_id']}: ${row['total_amount']:.2f} ({row['total_count']} times) over {row['days_with_discounts']} days")
        else:
            print("  No data found in daily_discount_detail for May 2025")
        
        # Compare monthly vs daily aggregation
        if monthly_data and daily_data:
            print(f"\n=== COMPARISON ===")
            monthly_dict = {(r['store_id'], r['discount_type_id']): r['total_discount_amount'] for r in monthly_data}
            daily_dict = {(r['store_id'], r['discount_type_id']): r['total_amount'] for r in daily_data}
            
            for key in list(monthly_dict.keys())[:3]:  # Check first 3
                monthly_amt = monthly_dict.get(key, 0)
                daily_amt = daily_dict.get(key, 0)
                print(f"Store {key[0]}, Type {key[1]}: Monthly=${monthly_amt:.2f}, Daily_Agg=${daily_amt:.2f}")
                
                if abs(monthly_amt - daily_amt) > 0.01:
                    print(f"  ⚠️  MISMATCH: Difference of ${abs(monthly_amt - daily_amt):.2f}")
                else:
                    print(f"  ✅ MATCH")
        
        # Check if the amounts look reasonable for monthly totals
        print(f"\n=== REASONABLENESS CHECK ===")
        if monthly_data:
            amounts = [row['total_discount_amount'] for row in monthly_data if row['total_discount_amount'] > 0]
            if amounts:
                avg_amount = sum(amounts) / len(amounts)
                min_amount = min(amounts)
                max_amount = max(amounts)
                
                print(f"Monthly discount amounts:")
                print(f"  Average: ${avg_amount:.2f}")
                print(f"  Range: ${min_amount:.2f} - ${max_amount:.2f}")
                
                if avg_amount < 10000:
                    print(f"  ⚠️  WARNING: Average amount ${avg_amount:.2f} seems low for monthly total")
                    print(f"      Expected monthly discount for a restaurant: $20,000 - $100,000+")
                else:
                    print(f"  ✅ Amounts look reasonable for monthly totals")
            else:
                print("  No non-zero amounts found")
        
    except Exception as e:
        print(f"Error checking discount data: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.close()

if __name__ == "__main__":
    check_discount_data()