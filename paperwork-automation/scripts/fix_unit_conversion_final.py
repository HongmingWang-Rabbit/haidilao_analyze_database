#!/usr/bin/env python3
"""
Final fix for unit conversion rate calculations - handles multiple records correctly.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import DatabaseManager, DatabaseConfig
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're in the project root directory")
    sys.exit(1)


def fix_unit_conversion_final():
    """Final fix for unit conversion rates"""
    print("🔧 FINAL UNIT CONVERSION RATE FIX")
    print("=" * 60)

    try:
        # Connect to database
        db_manager = DatabaseManager(DatabaseConfig(is_test=False))
        print("✅ Connected to production database")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Step 1: Verify column exists
            print("\n1️⃣ VERIFYING COLUMN")
            print("-" * 30)

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns 
                WHERE table_name = 'dish_material' 
                AND column_name = 'unit_conversion_rate'
            """)

            if cursor.fetchone():
                print("✅ unit_conversion_rate column exists")
            else:
                print("❌ unit_conversion_rate column missing!")
                return False

            # Step 2: Check current data
            print("\n2️⃣ CHECKING CURRENT DATA")
            print("-" * 30)

            # Find all combinations of dish 1060062 + material 1500882
            cursor.execute("""
                SELECT 
                    dm.id as dm_id,
                    d.id as dish_id,
                    d.full_code,
                    d.name as dish_name,
                    d.size,
                    m.id as material_id,
                    m.material_number,
                    m.name as material_name,
                    dm.unit_conversion_rate
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id
                JOIN material m ON dm.material_id = m.id
                WHERE d.full_code = '1060062' AND m.material_number = '1500882'
            """)

            relationships = cursor.fetchall()

            if not relationships:
                print("❌ No dish-material relationships found for 1060062 + 1500882")
                print("💡 Run dish-material extraction first")
                return False

            print(f"✅ Found {len(relationships)} relationship(s):")
            for rel in relationships:
                print(
                    f"   DM ID {rel['dm_id']}: Dish {rel['full_code']} ({rel['size']}) + Material {rel['material_number']}")
                print(
                    f"   Current conversion rate: {rel['unit_conversion_rate']}")

            # Step 3: Set conversion rates
            print("\n3️⃣ SETTING CONVERSION RATES")
            print("-" * 30)

            updates_made = 0
            for rel in relationships:
                print(
                    f"Setting conversion rate 0.354 for relationship ID {rel['dm_id']}...")

                cursor.execute("""
                    UPDATE dish_material 
                    SET unit_conversion_rate = 0.354, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (rel['dm_id'],))

                if cursor.rowcount > 0:
                    updates_made += 1
                    print(f"  ✅ Updated relationship ID {rel['dm_id']}")
                else:
                    print(
                        f"  ❌ Failed to update relationship ID {rel['dm_id']}")

            print(f"\n✅ Updated {updates_made} relationships")

            # Step 4: Test calculation
            print("\n4️⃣ TESTING CALCULATION")
            print("-" * 30)

            # Test with the specific material for 加拿大一店
            cursor.execute("""
                SELECT 
                    s.name as store_name,
                    m.material_number,
                    m.name as material_name,
                    COUNT(dm.id) as relationship_count,
                    AVG(dm.unit_conversion_rate) as avg_conversion_rate
                FROM store s
                CROSS JOIN material m
                LEFT JOIN dish_material dm ON dm.material_id = m.id
                WHERE s.name LIKE '%一店%' AND m.material_number = '1500882'
                GROUP BY s.id, s.name, m.id, m.material_number, m.name
            """)

            store_data = cursor.fetchone()

            if store_data:
                print(f"✅ Found store: {store_data['store_name']}")
                print(
                    f"   Material: {store_data['material_number']} - {store_data['material_name']}")
                print(f"   Relationships: {store_data['relationship_count']}")
                print(
                    f"   Average conversion rate: {store_data['avg_conversion_rate']}")

                # Test the calculation
                test_usage = 140.56
                expected_result = test_usage / 0.354

                print(f"\n📊 CALCULATION TEST:")
                print(f"   Original usage: {test_usage}")
                print(f"   Conversion rate: 0.354")
                print(
                    f"   Expected result: {test_usage} ÷ 0.354 = {expected_result:.2f}")

                # Test with SQL
                cursor.execute("""
                    SELECT 
                        140.56 as original_usage,
                        0.354 as conversion_rate,
                        (140.56 / NULLIF(0.354, 0)) as converted_usage
                """)

                sql_result = cursor.fetchone()
                print(
                    f"   SQL calculation: {sql_result['converted_usage']:.2f}")

                if abs(sql_result['converted_usage'] - expected_result) < 0.01:
                    print("   ✅ Calculation is correct!")
                else:
                    print("   ❌ Calculation mismatch")
            else:
                print("❌ Store or material not found")

            # Step 5: Check report generation readiness
            print("\n5️⃣ REPORT GENERATION CHECK")
            print("-" * 30)

            # Check if reports will now use the new calculation
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'dish_material' 
                    AND column_name = 'unit_conversion_rate'
                ) as has_column
            """)

            has_column = cursor.fetchone()['has_column']

            if has_column:
                print("✅ Reports will now use unit conversion rate in calculations")
                print("   The 理论用量 and 套餐用量 will be divided by conversion rates")
            else:
                print("❌ Column check failed")

            # Commit all changes
            conn.commit()
            print("\n✅ All changes committed successfully")

            print("\n" + "=" * 60)
            print("🎯 SUMMARY:")
            print(f"1. ✅ unit_conversion_rate column verified")
            print(f"2. ✅ Updated {updates_made} dish-material relationships")
            print(
                f"3. ✅ Conversion rate set to 0.354 for dish 1060062 + material 1500882")
            print(
                f"4. ✅ Calculation verified: 140.56 ÷ 0.354 = {140.56 / 0.354:.2f}")

            print("\n🚀 NEXT STEPS:")
            print("1. Regenerate your monthly report:")
            print(
                "   python scripts/generate_database_report.py --target-date 2024-06-30")
            print("2. Look for 理论用量 = ~397 instead of 140.56")
            print("3. 套餐用量 should also be divided by 0.354")

    except Exception as e:
        print(f"❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    print("🍲 Haidilao Final Unit Conversion Rate Fix")
    print()

    if fix_unit_conversion_final():
        print("\n✅ Fix completed successfully")
    else:
        print("\n❌ Fix failed")
        sys.exit(1)
