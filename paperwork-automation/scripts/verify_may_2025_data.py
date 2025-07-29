#!/usr/bin/env python3
"""
Verify May 2025 data availability in database
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix encoding issues on Windows
import codecs
if sys.platform.startswith('win'):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from utils.database import DatabaseConfig, DatabaseManager

def verify_may_data():
    """Check what May 2025 data is in the database"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            print("MAY 2025 DATA VERIFICATION")
            print("=" * 60)
            
            # Check dish monthly sales
            print("\n1. Dish Monthly Sales (May 2025):")
            cursor.execute("""
                SELECT COUNT(DISTINCT store_id) as stores, 
                       COUNT(DISTINCT dish_id) as dishes,
                       SUM(sale_amount) as total_revenue
                FROM dish_monthly_sale 
                WHERE year = 2025 AND month = 5
            """)
            result = cursor.fetchone()
            print(f"   Stores: {result['stores']}")
            print(f"   Dishes: {result['dishes']}")
            print(f"   Total Revenue: ${result['total_revenue']:,.2f}" if result['total_revenue'] else "   Total Revenue: $0.00")
            
            # Check material monthly usage
            print("\n2. Material Monthly Usage (May 2025):")
            cursor.execute("""
                SELECT COUNT(DISTINCT store_id) as stores,
                       COUNT(DISTINCT material_id) as materials,
                       SUM(material_used) as total_usage
                FROM material_monthly_usage 
                WHERE year = 2025 AND month = 5
            """)
            result = cursor.fetchone()
            print(f"   Stores: {result['stores']}")
            print(f"   Materials: {result['materials']}")
            print(f"   Total Usage: {result['total_usage']:,.2f}" if result['total_usage'] else "   Total Usage: 0.00")
            
            # Check material prices
            print("\n3. Material Prices (May 2025):")
            cursor.execute("""
                SELECT COUNT(DISTINCT store_id) as stores,
                       COUNT(DISTINCT material_id) as materials,
                       COUNT(*) as price_records
                FROM material_price_history 
                WHERE effective_date BETWEEN '2025-05-01' AND '2025-05-31'
            """)
            result = cursor.fetchone()
            print(f"   Stores: {result['stores']}")
            print(f"   Materials: {result['materials']}")
            print(f"   Price Records: {result['price_records']}")
            
            # Check daily reports
            print("\n4. Daily Reports (May 2025):")
            cursor.execute("""
                SELECT COUNT(DISTINCT store_id) as stores,
                       COUNT(*) as days,
                       SUM(revenue_tax_not_included) as total_revenue,
                       SUM(discount_total) as total_discounts
                FROM daily_report 
                WHERE date BETWEEN '2025-05-01' AND '2025-05-31'
            """)
            result = cursor.fetchone()
            print(f"   Stores: {result['stores']}")
            print(f"   Days: {result['days']}")
            print(f"   Total Revenue: ${result['total_revenue']:,.2f}" if result['total_revenue'] else "   Total Revenue: $0.00")
            print(f"   Total Discounts: ${result['total_discounts']:,.2f}" if result['total_discounts'] else "   Total Discounts: $0.00")
            
            # Check what months have data
            print("\n5. Available Months with Data:")
            cursor.execute("""
                SELECT DISTINCT year, month, COUNT(DISTINCT store_id) as stores
                FROM dish_monthly_sale
                GROUP BY year, month
                ORDER BY year DESC, month DESC
                LIMIT 6
            """)
            results = cursor.fetchall()
            for row in results:
                print(f"   {row['year']}-{row['month']:02d}: {row['stores']} stores")
            
            # Summary
            print("\n" + "=" * 60)
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM dish_monthly_sale WHERE year = 2025 AND month = 5) > 0 as has_dish_sales,
                    (SELECT COUNT(*) FROM material_monthly_usage WHERE year = 2025 AND month = 5) > 0 as has_material_usage,
                    (SELECT COUNT(*) FROM material_price_history WHERE effective_date BETWEEN '2025-05-01' AND '2025-05-31') > 0 as has_prices
            """)
            result = cursor.fetchone()
            
            if result['has_dish_sales'] and result['has_material_usage'] and result['has_prices']:
                print("✅ May 2025 data is available - ready to generate monthly gross margin report!")
            else:
                print("❌ May 2025 data is missing:")
                if not result['has_dish_sales']:
                    print("   - Missing dish sales data")
                if not result['has_material_usage']:
                    print("   - Missing material usage data")
                if not result['has_prices']:
                    print("   - Missing material price data")
                print("\n⚠️  You need to run historical data extraction first!")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_may_data()