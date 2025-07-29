#!/usr/bin/env python3
"""
Migrate existing discount_total data from daily_report to daily_discount_detail table
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
from datetime import datetime
import psycopg2

def migrate_discount_data():
    """Migrate existing discount data from daily_report to daily_discount_detail"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            print("Starting discount data migration...")
            print("=" * 60)
            
            # First, ensure the discount analysis tables exist
            print("\n1. Creating discount analysis tables...")
            sql_file = Path(__file__).parent.parent / "haidilao-database-querys" / "add_discount_analysis_tables.sql"
            if sql_file.exists():
                # Read with UTF-8 encoding to handle Chinese characters
                sql_content = sql_file.read_text(encoding='utf-8')
                cursor.execute(sql_content)
                conn.commit()
                print("✅ Discount analysis tables created successfully")
            else:
                print("❌ SQL file not found, please run add_discount_analysis_tables.sql manually")
                return
            
            # Get the ID for "其他优惠" (Other promotions) discount type
            cursor.execute("SELECT id FROM discount_type WHERE name = '其他优惠'")
            result = cursor.fetchone()
            if result:
                other_discount_type_id = result['id']
            else:
                print("❌ Discount type '其他优惠' not found")
                return
            
            # Migrate existing discount_total data
            print(f"\n2. Migrating existing discount data (using type ID {other_discount_type_id} for '其他优惠')...")
            
            # Count existing records
            cursor.execute("SELECT COUNT(*) FROM daily_report WHERE discount_total > 0")
            total_records = cursor.fetchone()['count']
            print(f"   Found {total_records} records with discount data")
            
            # Migrate data
            migrate_query = """
                INSERT INTO daily_discount_detail (store_id, date, discount_type_id, discount_amount, discount_count)
                SELECT 
                    store_id,
                    date,
                    %s as discount_type_id,  -- Use '其他优惠' for all existing data
                    discount_total as discount_amount,
                    1 as discount_count  -- Assume 1 since we don't have detailed count
                FROM daily_report
                WHERE discount_total > 0
                ON CONFLICT (store_id, date, discount_type_id) DO UPDATE
                SET 
                    discount_amount = EXCLUDED.discount_amount,
                    discount_count = EXCLUDED.discount_count,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(migrate_query, (other_discount_type_id,))
            migrated_count = cursor.rowcount
            
            print(f"✅ Migrated {migrated_count} discount records")
            
            # Verify migration
            print("\n3. Verifying migration...")
            
            # Check daily_discount_detail
            cursor.execute("SELECT COUNT(*) FROM daily_discount_detail")
            detail_count = cursor.fetchone()['count']
            print(f"   Daily discount detail records: {detail_count}")
            
            # Check monthly_discount_summary (should be populated by trigger)
            cursor.execute("SELECT COUNT(*) FROM monthly_discount_summary")
            summary_count = cursor.fetchone()['count']
            print(f"   Monthly discount summary records: {summary_count}")
            
            # Show sample data
            print("\n4. Sample migrated data:")
            cursor.execute("""
                SELECT 
                    s.name as store_name,
                    dd.date,
                    dt.name as discount_type,
                    dd.discount_amount,
                    dd.discount_count
                FROM daily_discount_detail dd
                JOIN store s ON dd.store_id = s.id
                JOIN discount_type dt ON dd.discount_type_id = dt.id
                ORDER BY dd.date DESC
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            print(f"\n   {'Store':<15} {'Date':<12} {'Type':<15} {'Amount':>10} {'Count':>6}")
            print("   " + "-" * 60)
            for row in results:
                print(f"   {row['store_name']:<15} {row['date']} {row['discount_type']:<15} {row['discount_amount']:>10.2f} {row['discount_count']:>6}")
            
            # Show monthly summary
            print("\n5. Monthly summary for May 2025:")
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
                WHERE ms.year = 2025 AND ms.month = 5
                ORDER BY s.id, dt.id
            """)
            
            results = cursor.fetchall()
            if results:
                print(f"\n   {'Store':<15} {'Year':<5} {'Month':<5} {'Type':<15} {'Total':>12} {'Count':>6} {'Avg':>10}")
                print("   " + "-" * 75)
                for row in results:
                    print(f"   {row['store_name']:<15} {row['year']:<5} {row['month']:<5} {row['discount_type']:<15} {row['total_discount_amount']:>12.2f} {row['total_discount_count']:>6} {row['avg_discount_per_use']:>10.2f}")
            else:
                print("   No data found for May 2025")
            
            conn.commit()
            print("\n✅ Discount data migration completed successfully!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_discount_data()