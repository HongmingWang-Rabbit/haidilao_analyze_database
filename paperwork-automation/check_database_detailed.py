#!/usr/bin/env python3
"""
Detailed database check to identify missing prerequisite data
"""

from utils.database import DatabaseManager, DatabaseConfig
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for database connection
os.environ['PG_HOST'] = 'localhost'
os.environ['PG_PORT'] = '5432'
os.environ['PG_USER'] = 'hongming'
os.environ['PG_PASSWORD'] = '8894'
os.environ['PG_DATABASE'] = 'haidilao-paperwork'


def check_database_detailed():
    print("🔍 DETAILED DATABASE CHECK")
    print("=" * 50)

    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check all table counts
            tables = [
                'store', 'dish_type', 'dish_child_type', 'dish',
                'material', 'dish_monthly_sale', 'dish_price_history',
                'material_price_history'
            ]

            print("📊 TABLE COUNTS:")
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    print(f"  {table:<20}: {count}")
                except Exception as e:
                    print(f"  {table:<20}: ERROR - {e}")

            # Check dish_type specifically
            print("\n🍽️ DISH TYPE DETAILS:")
            cursor.execute("SELECT COUNT(*) as count FROM dish_type")
            dish_type_count = cursor.fetchone()['count']

            if dish_type_count > 0:
                cursor.execute("SELECT id, name FROM dish_type LIMIT 5")
                dish_types = cursor.fetchall()
                for dt in dish_types:
                    print(f"  ID {dt['id']}: {dt['name']}")
            else:
                print("  ❌ NO DISH TYPES FOUND!")

            # Check dish_child_type specifically
            print("\n🍽️ DISH CHILD TYPE DETAILS:")
            cursor.execute("SELECT COUNT(*) as count FROM dish_child_type")
            child_type_count = cursor.fetchone()['count']

            if child_type_count > 0:
                cursor.execute("SELECT id, name FROM dish_child_type LIMIT 5")
                child_types = cursor.fetchall()
                for ct in child_types:
                    print(f"  ID {ct['id']}: {ct['name']}")
            else:
                print("  ❌ NO DISH CHILD TYPES FOUND!")

            # Check if dishes exist
            print("\n🍽️ DISH DETAILS:")
            cursor.execute("SELECT COUNT(*) as count FROM dish")
            dish_count = cursor.fetchone()['count']

            if dish_count > 0:
                cursor.execute(
                    "SELECT id, full_code, name, dish_type_id, dish_child_type_id FROM dish LIMIT 5")
                dishes = cursor.fetchall()
                for dish in dishes:
                    print(
                        f"  ID {dish['id']}: {dish['full_code']} - {dish['name']} (type: {dish['dish_type_id']}, child: {dish['dish_child_type_id']})")
            else:
                print("  ❌ NO DISHES FOUND!")

            # Check stores
            print("\n🏪 STORE DETAILS:")
            cursor.execute("SELECT id, name FROM store ORDER BY id")
            stores = cursor.fetchall()
            for store in stores:
                print(f"  ID {store['id']}: {store['name']}")

            # Check for any constraint violations
            print("\n🔍 CONSTRAINT ANALYSIS:")

            # Check if there are dishes without valid foreign keys
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM dish 
                WHERE dish_type_id IS NULL OR dish_child_type_id IS NULL
            """)
            invalid_dishes = cursor.fetchone()['count']

            if invalid_dishes > 0:
                print(
                    f"  ❌ Found {invalid_dishes} dishes with NULL foreign keys")
            else:
                print("  ✅ All dishes have valid foreign keys")

            # Check foreign key constraints
            print("\n🔗 FOREIGN KEY CONSTRAINTS:")
            cursor.execute("""
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name IN ('dish', 'dish_monthly_sale', 'dish_price_history')
            """)

            constraints = cursor.fetchall()
            for constraint in constraints:
                print(
                    f"  {constraint['table_name']}.{constraint['column_name']} -> {constraint['foreign_table_name']}.{constraint['foreign_column_name']}")

    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_database_detailed()
