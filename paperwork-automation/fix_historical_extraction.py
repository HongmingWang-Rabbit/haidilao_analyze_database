#!/usr/bin/env python3
"""
Fix historical extraction by ensuring prerequisites exist first
"""

import logging
import pandas as pd
from utils.database import DatabaseManager, DatabaseConfig
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_basic_data_exists():
    """Ensure stores, dish types, and materials exist before historical extraction"""
    print("🔧 ENSURING PREREQUISITE DATA EXISTS")
    print("=" * 50)

    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check if stores exist
            cursor.execute("SELECT COUNT(*) FROM store")
            store_count = cursor.fetchone()[0]
            print(f"🏪 Stores: {store_count}")

            if store_count == 0:
                print("❌ No stores found - need to run database reset first")
                return False

            # Check if dish types exist
            cursor.execute("SELECT COUNT(*) FROM dish_type")
            dish_type_count = cursor.fetchone()[0]
            print(f"🍽️ Dish types: {dish_type_count}")

            if dish_type_count == 0:
                print("⚠️ No dish types - creating basic dish types...")
                # Create basic dish types
                cursor.execute("""
                    INSERT INTO dish_type (name, description) VALUES
                    ('主菜', '主要菜品'),
                    ('配菜', '配菜类'),
                    ('汤品', '汤类'),
                    ('饮品', '饮料类'),
                    ('小食', '小食类')
                    ON CONFLICT (name) DO NOTHING
                """)
                conn.commit()
                print("✅ Basic dish types created")

            # Check if materials exist
            cursor.execute("SELECT COUNT(*) FROM material")
            material_count = cursor.fetchone()[0]
            print(f"📦 Materials: {material_count}")

            if material_count == 0:
                print("⚠️ No materials - creating basic materials...")
                # Create basic materials
                cursor.execute("""
                    INSERT INTO material (name, material_number, unit) VALUES
                    ('基础物料', '999999', '份')
                    ON CONFLICT (material_number) DO NOTHING
                """)
                conn.commit()
                print("✅ Basic materials created")

            return True

    except Exception as e:
        print(f"❌ Error ensuring basic data: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_historical_insertion():
    """Test inserting one historical record manually"""
    print("\n🧪 TESTING HISTORICAL INSERTION")
    print("=" * 50)

    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Get a sample dish and store
            cursor.execute("SELECT id FROM dish LIMIT 1")
            dish_result = cursor.fetchone()
            if not dish_result:
                print("❌ No dishes found - need to extract dishes first")
                return False

            dish_id = dish_result[0]

            cursor.execute("SELECT id FROM store LIMIT 1")
            store_result = cursor.fetchone()
            if not store_result:
                print("❌ No stores found")
                return False

            store_id = store_result[0]

            # Try to insert a test 2024 record
            cursor.execute("""
                INSERT INTO dish_monthly_sale (dish_id, store_id, year, month, sale_amount)
                VALUES (%s, %s, 2024, 5, 100.0)
                ON CONFLICT (dish_id, store_id, year, month) DO UPDATE SET
                    sale_amount = EXCLUDED.sale_amount
            """, (dish_id, store_id))

            conn.commit()

            # Check if it was inserted
            cursor.execute(
                "SELECT COUNT(*) FROM dish_monthly_sale WHERE year = 2024")
            count_2024 = cursor.fetchone()[0]
            print(
                f"✅ Successfully inserted test 2024 record. Total 2024 records: {count_2024}")

            return True

    except Exception as e:
        print(f"❌ Error testing historical insertion: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_current_extraction_first():
    """Run current month extraction to ensure basic data exists"""
    print("\n🔄 RUNNING CURRENT EXTRACTION FIRST")
    print("=" * 50)

    try:
        # Import and run current extraction scripts
        import subprocess

        # Run dish extraction
        result = subprocess.run([
            'python', '-m', 'scripts.extract-dishes'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Dishes extracted successfully")
        else:
            print(f"⚠️ Dish extraction issues: {result.stderr}")

        # Run material extraction
        result = subprocess.run([
            'python', '-m', 'scripts.extract-materials'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Materials extracted successfully")
        else:
            print(f"⚠️ Material extraction issues: {result.stderr}")

        return True

    except Exception as e:
        print(f"❌ Error running current extraction: {e}")
        return False


def main():
    print("🚀 FIXING HISTORICAL EXTRACTION")
    print("=" * 60)

    # Step 1: Ensure basic data exists
    if not ensure_basic_data_exists():
        print("❌ Failed to ensure basic data exists")
        return False

    # Step 2: Run current extraction to populate dishes/materials
    print("\n⚠️ Running current extraction to populate basic data...")
    run_current_extraction_first()

    # Step 3: Test historical insertion
    if not test_historical_insertion():
        print("❌ Historical insertion test failed")
        return False

    # Step 4: Run historical extraction
    print("\n🔄 RUNNING HISTORICAL EXTRACTION")
    print("=" * 50)

    import subprocess
    result = subprocess.run([
        'python', '-m', 'scripts.extract_historical_data_batch',
        '--month', '2024-05'
    ], capture_output=True, text=True)

    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    if result.returncode == 0:
        print("✅ Historical extraction completed")
    else:
        print(
            f"❌ Historical extraction failed with return code: {result.returncode}")

    # Step 5: Check final results
    print("\n🔍 FINAL CHECK")
    print("=" * 50)

    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM dish_monthly_sale WHERE year = 2024")
            count_2024 = cursor.fetchone()[0]
            print(f"📊 2024 monthly sales records: {count_2024}")

            if count_2024 > 0:
                print("✅ SUCCESS: 2024 data now exists in database!")

                # Show sample data
                cursor.execute("""
                    SELECT d.name, s.name, dms.year, dms.month, dms.sale_amount
                    FROM dish_monthly_sale dms
                    JOIN dish d ON dms.dish_id = d.id
                    JOIN store s ON dms.store_id = s.id
                    WHERE dms.year = 2024
                    LIMIT 5
                """)

                print("\nSample 2024 data:")
                for row in cursor.fetchall():
                    print(
                        f"  {row[0]} | {row[1]} | {row[2]}-{row[3]:02d} | {row[4]}")

            else:
                print("❌ Still no 2024 data - something is wrong")

    except Exception as e:
        print(f"❌ Error in final check: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
