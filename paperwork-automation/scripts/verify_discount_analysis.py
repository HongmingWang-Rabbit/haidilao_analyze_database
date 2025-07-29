#!/usr/bin/env python3
"""
Verify discount analysis implementation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix encoding issues on Windows
import locale
import codecs
if sys.platform.startswith('win'):
    # Set UTF-8 encoding for Windows console
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from utils.database import DatabaseConfig, DatabaseManager
import psycopg2

def verify_discount_analysis():
    """Verify discount analysis tables and data"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            print("DISCOUNT ANALYSIS VERIFICATION")
            print("=" * 60)
            
            # 1. Check if tables exist
            print("\n1. Checking discount tables...")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('discount_type', 'daily_discount_detail', 'monthly_discount_summary')
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            print(f"   Found {len(tables)} discount tables:")
            for table in tables:
                print(f"   ✅ {table['table_name']}")
            
            if len(tables) < 3:
                print("   ❌ Missing discount tables. Run setup_discount_analysis.py first.")
                return
            
            # 2. Check discount types
            print("\n2. Discount types:")
            cursor.execute("SELECT id, name, description FROM discount_type ORDER BY id")
            types = cursor.fetchall()
            
            for dt in types:
                print(f"   {dt['id']:2d}. {dt['name']:<15} - {dt['description'] or 'No description'}")
            
            # 3. Check daily discount data
            print("\n3. Daily discount data summary:")
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT store_id) as stores,
                    COUNT(DISTINCT date) as days,
                    COUNT(*) as total_records,
                    SUM(discount_amount) as total_discount,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM daily_discount_detail
            """)
            
            result = cursor.fetchone()
            if result and result['stores'] > 0:
                print(f"   Stores with discounts: {result['stores']}")
                print(f"   Days with discounts: {result['days']}")
                print(f"   Total records: {result['total_records']}")
                print(f"   Total discount amount: ${result['total_discount']:,.2f}")
                print(f"   Date range: {result['earliest_date']} to {result['latest_date']}")
            else:
                print("   ❌ No discount data found")
            
            # 4. Check monthly summary
            print("\n4. Monthly discount summary (Last 3 months):")
            cursor.execute("""
                SELECT 
                    s.name as store_name,
                    ms.year,
                    ms.month,
                    dt.name as discount_type,
                    ms.total_discount_amount,
                    ms.total_discount_count,
                    ms.avg_discount_per_use
                FROM monthly_discount_summary ms
                JOIN store s ON ms.store_id = s.id
                JOIN discount_type dt ON ms.discount_type_id = dt.id
                WHERE (ms.year, ms.month) IN (
                    SELECT DISTINCT year, month 
                    FROM monthly_discount_summary 
                    ORDER BY year DESC, month DESC 
                    LIMIT 3
                )
                ORDER BY ms.year DESC, ms.month DESC, s.id, dt.id
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            if results:
                print(f"\n   {'Store':<15} {'Date':<8} {'Type':<15} {'Amount':>10} {'Count':>6} {'Avg':>8}")
                print("   " + "-" * 70)
                for row in results:
                    date_str = f"{row['year']}-{row['month']:02d}"
                    print(f"   {row['store_name']:<15} {date_str:<8} {row['discount_type']:<15} ${row['total_discount_amount']:>9.2f} {row['total_discount_count']:>6} ${row['avg_discount_per_use']:>7.2f}")
                
                if len(results) == 10:
                    print("   ... (showing first 10 records)")
            else:
                print("   ❌ No monthly summary data found")
            
            # 5. Check if discount data matches daily_report totals
            print("\n5. Data consistency check (May 2025):")
            cursor.execute("""
                WITH daily_totals AS (
                    SELECT 
                        store_id,
                        SUM(discount_total) as report_total
                    FROM daily_report
                    WHERE date BETWEEN '2025-05-01' AND '2025-05-31'
                        AND discount_total > 0
                    GROUP BY store_id
                ),
                detail_totals AS (
                    SELECT 
                        store_id,
                        SUM(discount_amount) as detail_total
                    FROM daily_discount_detail
                    WHERE date BETWEEN '2025-05-01' AND '2025-05-31'
                    GROUP BY store_id
                )
                SELECT 
                    s.name as store_name,
                    COALESCE(dt.report_total, 0) as daily_report_total,
                    COALESCE(dd.detail_total, 0) as discount_detail_total,
                    COALESCE(dt.report_total, 0) - COALESCE(dd.detail_total, 0) as difference
                FROM store s
                LEFT JOIN daily_totals dt ON s.id = dt.store_id
                LEFT JOIN detail_totals dd ON s.id = dd.store_id
                WHERE s.id BETWEEN 1 AND 7
                    AND (dt.report_total IS NOT NULL OR dd.detail_total IS NOT NULL)
                ORDER BY s.id
            """)
            
            results = cursor.fetchall()
            if results:
                print(f"\n   {'Store':<15} {'Daily Report':>15} {'Discount Detail':>15} {'Difference':>12}")
                print("   " + "-" * 60)
                for row in results:
                    diff_flag = "✅" if abs(row['difference']) < 0.01 else "⚠️"
                    print(f"   {row['store_name']:<15} ${row['daily_report_total']:>14.2f} ${row['discount_detail_total']:>14.2f} ${row['difference']:>11.2f} {diff_flag}")
            else:
                print("   No data for May 2025")
            
            # 6. Test discount analysis query
            print("\n6. Testing discount analysis query (Sample):")
            cursor.execute("""
                SELECT 
                    store_name,
                    discount_type,
                    current_amount,
                    revenue_ratio
                FROM (
                    SELECT 
                        s.name as store_name,
                        dt.name as discount_type,
                        COALESCE(cm.total_discount_amount, 0) as current_amount,
                        CASE WHEN dr.revenue > 0 
                            THEN ROUND((COALESCE(cm.total_discount_amount, 0) / dr.revenue * 100), 2) 
                            ELSE 0 
                        END as revenue_ratio
                    FROM store s
                    CROSS JOIN discount_type dt
                    LEFT JOIN monthly_discount_summary cm ON s.id = cm.store_id 
                        AND cm.discount_type_id = dt.id
                        AND cm.year = 2025 AND cm.month = 5
                    LEFT JOIN (
                        SELECT store_id, SUM(revenue_tax_not_included) as revenue
                        FROM daily_report
                        WHERE EXTRACT(YEAR FROM date) = 2025 
                            AND EXTRACT(MONTH FROM date) = 5
                        GROUP BY store_id
                    ) dr ON s.id = dr.store_id
                    WHERE s.id = 1
                        AND cm.total_discount_amount > 0
                ) t
                ORDER BY store_name, discount_type
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            if results:
                print(f"\n   {'Store':<15} {'Discount Type':<20} {'Amount':>10} {'% of Rev':>10}")
                print("   " + "-" * 58)
                for row in results:
                    print(f"   {row['store_name']:<15} {row['discount_type']:<20} ${row['current_amount']:>9.2f} {row['revenue_ratio']:>9.2f}%")
            else:
                print("   No discount data for analysis")
            
            print("\n✅ Discount analysis verification completed!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_discount_analysis()