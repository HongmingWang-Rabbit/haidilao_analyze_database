#!/usr/bin/env python3
"""
Investigate data loss issue in the database
"""

from datetime import datetime
from utils.database import DatabaseManager, DatabaseConfig
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def investigate_database():
    """Investigate what happened to the database data"""
    print("🔍 INVESTIGATING DATA LOSS")
    print("=" * 60)

    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            print("📊 CURRENT DATABASE STATUS")
            print("-" * 30)

            # Check all table counts
            tables = [
                'store', 'dish_type', 'dish_child_type', 'dish',
                'material', 'dish_price_history', 'material_price_history',
                'dish_monthly_sale', 'material_monthly_usage'
            ]

            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table:<25}: {count:>6} records")
                except Exception as e:
                    print(f"  {table:<25}: ERROR - {e}")

            print(f"\n📅 DATE RANGE ANALYSIS")
            print("-" * 30)

            # Check dish_monthly_sale date ranges
            cursor.execute("""
                SELECT 
                    MIN(year) as min_year, 
                    MAX(year) as max_year,
                    COUNT(DISTINCT year) as year_count,
                    COUNT(*) as total_records
                FROM dish_monthly_sale
            """)
            result = cursor.fetchone()
            if result and result[0]:
                print(
                    f"  Years: {result[0]} - {result[1]} ({result[2]} different years)")
                print(f"  Total monthly sales records: {result[3]}")
            else:
                print("  No data in dish_monthly_sale table")

            # Check 2024 specifically
            cursor.execute(
                "SELECT COUNT(*) FROM dish_monthly_sale WHERE year = 2024")
            count_2024 = cursor.fetchone()[0]
            print(f"  2024 records: {count_2024}")

            # Check other years
            cursor.execute("""
                SELECT year, COUNT(*) as count
                FROM dish_monthly_sale 
                GROUP BY year 
                ORDER BY year
            """)
            year_counts = cursor.fetchall()
            if year_counts:
                print(f"  Year breakdown:")
                for year, count in year_counts:
                    print(f"    {year}: {count} records")

            print(f"\n🔍 RECENT DATA ANALYSIS")
            print("-" * 30)

            # Check when data was last updated
            cursor.execute("""
                SELECT 
                    MAX(created_at) as last_created,
                    MAX(updated_at) as last_updated
                FROM dish_monthly_sale
            """)
            result = cursor.fetchone()
            if result and result[0]:
                print(f"  Last created: {result[0]}")
                print(f"  Last updated: {result[1]}")

            # Check for any dishes created recently
            cursor.execute("""
                SELECT COUNT(*), MAX(created_at)
                FROM dish 
                WHERE created_at > CURRENT_DATE - INTERVAL '1 day'
            """)
            result = cursor.fetchone()
            if result:
                print(f"  Dishes created in last 24 hours: {result[0]}")
                if result[1]:
                    print(f"  Most recent dish creation: {result[1]}")

            print(f"\n⚠️ POTENTIAL ISSUES")
            print("-" * 30)

            # Check for data consistency issues

            # 1. Check if there are dishes without monthly sales
            cursor.execute("""
                SELECT COUNT(DISTINCT d.id) as dishes_total,
                       COUNT(DISTINCT dms.dish_id) as dishes_with_sales
                FROM dish d
                LEFT JOIN dish_monthly_sale dms ON d.id = dms.dish_id
            """)
            result = cursor.fetchone()
            if result:
                print(f"  Total dishes: {result[0]}")
                print(f"  Dishes with sales data: {result[1]}")
                if result[0] > result[1]:
                    print(
                        f"  ⚠️ {result[0] - result[1]} dishes have no sales data")

            # 2. Check if the row limit is affecting data
            if count_2024 == 0:
                print(f"  ❌ NO 2024 DATA FOUND")
                print(f"  🔍 Checking if this is a historical extraction issue...")

                # Check if we have the source data
                historical_file = Path(
                    "history_files/monthly_report_inputs/2024-05/monthly_dish_sale/海外菜品销售报表_20250706_1147.xlsx")
                if historical_file.exists():
                    print(
                        f"  ✅ Historical file exists: {historical_file.name}")

                    import pandas as pd
                    try:
                        df = pd.read_excel(historical_file, nrows=10)
                        print(f"  📊 File has {len(df)} rows (sample)")
                        print(f"  📋 Columns: {list(df.columns)}")
                    except Exception as e:
                        print(f"  ❌ Error reading file: {e}")
                else:
                    print(f"  ❌ Historical file not found")

            print(f"\n🎯 DIAGNOSIS")
            print("-" * 30)

            if count_2024 == 0:
                print("❌ PRIMARY ISSUE: No 2024 data in database")
                print("   This suggests historical extraction failed")

            total_records = result[3] if result and result[3] else 0
            if total_records == 1000:
                print("⚠️ SUSPICIOUS: Exactly 1000 records suggests row limit issue")
            elif total_records < 1000:
                print("⚠️ DATA LOSS: Fewer records than expected")

            return True

    except Exception as e:
        print(f"❌ Error investigating database: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_backup_options():
    """Check if there are any backup or recovery options"""
    print(f"\n💾 BACKUP/RECOVERY OPTIONS")
    print("-" * 30)

    # Check if there are any SQL dump files
    sql_files = list(Path(".").glob("**/*.sql"))
    if sql_files:
        print("📁 Found SQL files:")
        for sql_file in sql_files:
            print(f"  - {sql_file}")

    # Check if there are recent database exports
    output_files = list(Path("output").glob("*.xlsx")
                        ) if Path("output").exists() else []
    if output_files:
        print("📊 Recent output files:")
        for output_file in sorted(output_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            mtime = datetime.fromtimestamp(output_file.stat().st_mtime)
            print(f"  - {output_file.name} (modified: {mtime})")


def suggest_recovery_steps():
    """Suggest steps to recover from data loss"""
    print(f"\n🔧 RECOVERY SUGGESTIONS")
    print("-" * 30)
    print("1. 🛑 STOP running any more extraction scripts until we understand the issue")
    print("2. 📋 Check if you have a database backup from before running the script")
    print("3. 🔍 Check if the data is in a different database (test vs production)")
    print("4. 🔄 Re-run current data extraction to restore non-historical data:")
    print("   - python scripts/extract-dishes.py [current_file] --direct-db")
    print(
        "   - python scripts/extract-materials.py [current_file] --direct-db")
    print("5. 🕐 THEN carefully re-run historical extraction with debugging enabled")


def main():
    print("🚨 DATABASE DATA LOSS INVESTIGATION")
    print("=" * 80)

    investigate_database()
    check_backup_options()
    suggest_recovery_steps()

    print(f"\n⚠️ IMPORTANT: DO NOT run any more extraction scripts until we understand what happened!")


if __name__ == "__main__":
    main()
