#!/usr/bin/env python3
"""
Simple script to check database contents
"""

from utils.database import DatabaseManager, DatabaseConfig
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def check_database():
    print("🔍 CHECKING DATABASE CONTENTS")
    print("=" * 50)

    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check basic counts
            cursor.execute("SELECT COUNT(*) as count FROM store")
            store_count = cursor.fetchone()['count']
            print(f"🏪 Stores: {store_count}")

            cursor.execute("SELECT COUNT(*) as count FROM dish")
            dish_count = cursor.fetchone()['count']
            print(f"🍽️ Dishes: {dish_count}")

            cursor.execute("SELECT COUNT(*) as count FROM material")
            material_count = cursor.fetchone()['count']
            print(f"📦 Materials: {material_count}")

            cursor.execute("SELECT COUNT(*) as count FROM dish_monthly_sale")
            monthly_sale_count = cursor.fetchone()['count']
            print(f"📊 Dish monthly sales: {monthly_sale_count}")

            # Check if we have any 2024 data
            cursor.execute(
                "SELECT COUNT(*) as count FROM dish_monthly_sale WHERE year = 2024")
            sales_2024 = cursor.fetchone()['count']
            print(f"📊 2024 monthly sales: {sales_2024}")

            # Check date range in dish_monthly_sale
            cursor.execute(
                "SELECT MIN(year) as min_year, MAX(year) as max_year FROM dish_monthly_sale")
            result = cursor.fetchone()
            if result['min_year'] is not None:
                print(
                    f"📅 Date range: {result['min_year']} - {result['max_year']}")
            else:
                print("📅 No date data in dish_monthly_sale")

            print("\n" + "=" * 50)
            print("🎯 ANALYSIS")
            print("=" * 50)

            if store_count == 0:
                print("❌ No stores - need to run database reset first")
            elif dish_count == 0:
                print("❌ No dishes - need to extract dishes first")
            elif material_count == 0:
                print("❌ No materials - need to extract materials first")
            elif monthly_sale_count == 0:
                print("❌ No monthly sales - historical extraction failed")
            elif sales_2024 == 0:
                print("❌ No 2024 data - historical extraction didn't insert 2024 data")
            else:
                print("✅ Database looks good")

    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_database()
