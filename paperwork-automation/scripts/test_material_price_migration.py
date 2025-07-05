#!/usr/bin/env python3
"""
Test script to verify material price history migration from district_id to store_id.
This script validates the database structure changes and tests the updated queries.
"""

from utils.database import DatabaseManager, DatabaseConfig
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


def test_material_price_history_structure():
    """Test that material_price_history table has the new structure."""
    print("🔍 Testing material_price_history table structure...")

    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'material_price_history'
                    ORDER BY ordinal_position
                """)

                columns = cursor.fetchall()
                print("📋 Current table structure:")
                for col in columns:
                    print(
                        f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")

                # Check if store_id column exists
                store_id_exists = any(
                    col['column_name'] == 'store_id' for col in columns)
                district_id_exists = any(
                    col['column_name'] == 'district_id' for col in columns)

                print(f"\n📊 Migration status:")
                print(
                    f"  - store_id column exists: {'✅' if store_id_exists else '❌'}")
                print(
                    f"  - district_id column exists: {'❌' if not district_id_exists else '⚠️ (should be removed)'}")

                # Check unique constraints
                cursor.execute("""
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_name = 'material_price_history'
                    AND constraint_type = 'UNIQUE'
                """)

                constraints = cursor.fetchall()
                print(f"\n📋 Unique constraints:")
                for constraint in constraints:
                    print(
                        f"  - {constraint['constraint_name']}: {constraint['constraint_type']}")

                # Check indexes
                cursor.execute("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = 'material_price_history'
                """)

                indexes = cursor.fetchall()
                print(f"\n📋 Indexes:")
                for index in indexes:
                    print(f"  - {index['indexname']}")

                if store_id_exists and not district_id_exists:
                    print("\n✅ Migration appears successful!")
                    return True
                else:
                    print("\n❌ Migration not complete or structure is incorrect")
                    return False

    except Exception as e:
        print(f"❌ Error testing table structure: {e}")
        return False


def test_material_price_queries():
    """Test that queries using material_price_history work correctly."""
    print("\n🔍 Testing material price queries...")

    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Test query from material_usage_summary_worksheet.py
                print("📋 Testing material usage summary query...")
                cursor.execute("""
                    SELECT 
                        s.id as store_id,
                        s.name as store_name,
                        COUNT(mph.id) as price_records
                    FROM store s
                    LEFT JOIN material_price_history mph ON mph.store_id = s.id
                        AND mph.is_active = TRUE
                    WHERE s.is_active = TRUE
                    GROUP BY s.id, s.name
                    ORDER BY s.id
                """)

                results = cursor.fetchall()
                print("🏪 Store price records:")
                for result in results:
                    print(
                        f"  - Store {result['store_id']} ({result['store_name']}): {result['price_records']} price records")

                # Test query from detailed_material_spending_worksheet.py
                print("\n📋 Testing detailed material spending query...")
                cursor.execute("""
                    SELECT 
                        m.material_number,
                        m.name as material_name,
                        mph.price,
                        mph.store_id
                    FROM material m
                    LEFT JOIN material_price_history mph ON m.id = mph.material_id 
                        AND mph.is_active = TRUE
                        AND mph.store_id = 1
                    WHERE m.is_active = TRUE
                    LIMIT 5
                """)

                results = cursor.fetchall()
                print("📊 Sample material prices for store 1:")
                for result in results:
                    price = result['price'] if result['price'] else 'No price'
                    print(
                        f"  - {result['material_number']} ({result['material_name']}): {price}")

                print("✅ Queries executed successfully!")
                return True

    except Exception as e:
        print(f"❌ Error testing queries: {e}")
        return False


def test_sample_data_insertion():
    """Test inserting sample material price data."""
    print("\n🔍 Testing sample data insertion...")

    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Insert sample data
                sample_data = [
                    ('3000001', 1, 5.50, 'CAD'),
                    ('3000001', 2, 5.75, 'CAD'),
                    ('3000002', 1, 12.30, 'CAD'),
                ]

                inserted_count = 0

                for material_number, store_id, price, currency in sample_data:
                    try:
                        cursor.execute("""
                            INSERT INTO material_price_history (
                                material_id, store_id, price, currency, effective_date, is_active
                            )
                            SELECT m.id, %s, %s, %s, CURRENT_DATE, TRUE
                            FROM material m
                            WHERE m.material_number = %s
                            ON CONFLICT (material_id, store_id, effective_date) 
                            DO UPDATE SET
                                price = EXCLUDED.price,
                                currency = EXCLUDED.currency,
                                is_active = EXCLUDED.is_active
                        """, (store_id, price, currency, material_number))

                        if cursor.rowcount > 0:
                            inserted_count += 1
                            print(
                                f"✅ Sample price for material {material_number} store {store_id}: {price} {currency}")
                        else:
                            print(
                                f"⚠️ Material {material_number} not found in database")

                    except Exception as e:
                        print(
                            f"❌ Error inserting sample data for {material_number}: {e}")

                conn.commit()
                print(f"\n📊 Inserted {inserted_count} sample price records")

                # Verify insertion
                cursor.execute("""
                    SELECT COUNT(*) as total_prices
                    FROM material_price_history
                    WHERE is_active = TRUE
                """)

                result = cursor.fetchone()
                print(
                    f"📊 Total active price records in database: {result['total_prices']}")

                return True

    except Exception as e:
        print(f"❌ Error testing sample data insertion: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 MATERIAL PRICE HISTORY MIGRATION TEST")
    print("=" * 50)

    tests = [
        ("Table Structure", test_material_price_history_structure),
        ("Query Compatibility", test_material_price_queries),
        ("Sample Data Insertion", test_sample_data_insertion),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))

    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)

    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False

    print("="*50)
    if all_passed:
        print("🎉 All tests passed! Migration appears successful.")
        return True
    else:
        print("❌ Some tests failed. Please check the migration.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
