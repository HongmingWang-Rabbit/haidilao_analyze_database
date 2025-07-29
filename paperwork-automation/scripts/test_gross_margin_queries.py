#!/usr/bin/env python3
"""
Test the queries used in gross margin report generation
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
from lib.database_queries import DataProvider

def test_queries():
    """Test the queries that generate gross margin report data"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    data_provider = DataProvider(db_manager)
    
    print("TESTING GROSS MARGIN REPORT QUERIES")
    print("=" * 60)
    
    # Test parameters
    year = 2025
    month = 5
    
    print(f"\nTesting for: {year}-{month:02d}")
    
    try:
        # 1. Test dish price data query
        print("\n1. Testing Dish Price Changes Query...")
        query = """
        SELECT COUNT(*) as count
        FROM dish_monthly_sale
        WHERE year = %s AND month = %s
        """
        result = data_provider.execute_query(query, (year, month))
        print(f"   Dish sales records for May 2025: {result[0][0] if result else 0}")
        
        # 2. Test material cost data query
        print("\n2. Testing Material Cost Query...")
        query = """
        SELECT COUNT(*) as count
        FROM material_monthly_usage
        WHERE year = %s AND month = %s
        """
        result = data_provider.execute_query(query, (year, month))
        print(f"   Material usage records for May 2025: {result[0][0] if result else 0}")
        
        # 3. Test price history
        print("\n3. Testing Material Price History...")
        query = """
        SELECT COUNT(*) as count
        FROM material_price_history
        WHERE effective_date <= '2025-05-31'
            AND is_active = true
        """
        result = data_provider.execute_query(query)
        print(f"   Active material prices: {result[0][0] if result else 0}")
        
        # 4. Test the store gross profit data
        print("\n4. Testing Store Gross Profit Query...")
        try:
            from lib.database_queries import StoreGrossProfitDataProvider
            gross_profit_provider = StoreGrossProfitDataProvider(db_manager)
            data = gross_profit_provider.get_store_gross_profit_data('2025-05-31')
            print(f"   Store gross profit records: {len(data)}")
            if data:
                print("   Sample data for first store:")
                store = data[0]
                print(f"     Store: {store['store_name']}")
                print(f"     Revenue: ${store.get('revenue', 0):,.2f}")
                print(f"     Cost: ${store.get('cost', 0):,.2f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 5. Test monthly summary data
        print("\n5. Testing Monthly Summary Query...")
        query = """
        WITH monthly_data AS (
            SELECT 
                s.name as store_name,
                COALESCE(SUM(dms.sale_amount), 0) as revenue
            FROM store s
            LEFT JOIN dish_monthly_sale dms ON s.id = dms.store_id
                AND dms.year = %s AND dms.month = %s
            WHERE s.id BETWEEN 1 AND 7
            GROUP BY s.id, s.name
        )
        SELECT store_name, revenue
        FROM monthly_data
        ORDER BY store_name
        """
        result = data_provider.execute_query(query, (year, month))
        print(f"   Monthly summary records: {len(result) if result else 0}")
        if result:
            for row in result:
                print(f"     {row[0]}: ${row[1]:,.2f}")
        
        print("\n" + "=" * 60)
        print("SUMMARY:")
        
        # Check if data exists
        has_dish_sales = data_provider.execute_query(
            "SELECT EXISTS(SELECT 1 FROM dish_monthly_sale WHERE year = %s AND month = %s)", 
            (year, month)
        )[0][0]
        
        has_material_usage = data_provider.execute_query(
            "SELECT EXISTS(SELECT 1 FROM material_monthly_usage WHERE year = %s AND month = %s)", 
            (year, month)
        )[0][0]
        
        has_prices = data_provider.execute_query(
            "SELECT EXISTS(SELECT 1 FROM material_price_history WHERE effective_date <= '2025-05-31')"
        )[0][0]
        
        if has_dish_sales and has_material_usage and has_prices:
            print("✅ All required data exists")
            print("\n⚠️  If sheets are still empty, the issue might be:")
            print("   1. Data joins not matching (check material_id, store_id relationships)")
            print("   2. Price effective dates not covering May 2025")
            print("   3. Query logic issues in the report generator")
        else:
            print("❌ Missing required data:")
            if not has_dish_sales:
                print("   - No dish sales for May 2025")
            if not has_material_usage:
                print("   - No material usage for May 2025")
            if not has_prices:
                print("   - No material prices")
            print("\n📋 You need to run historical data extraction first!")
            
    except Exception as e:
        print(f"\n❌ Error testing queries: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_queries()