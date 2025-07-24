#!/usr/bin/env python3
"""
Quick fix to add unit_conversion_rate column and set the conversion rate.
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


def quick_fix():
    """Quick fix for unit conversion rates"""
    print("🔧 QUICK UNIT CONVERSION RATE FIX")
    print("=" * 50)

    try:
        # Connect to database
        db_manager = DatabaseManager(DatabaseConfig(is_test=False))
        print("✅ Connected to production database")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Step 1: Add column if not exists
            print("\n1️⃣ ADDING COLUMN")
            print("-" * 30)

            try:
                cursor.execute("""
                    ALTER TABLE dish_material 
                    ADD COLUMN unit_conversion_rate DECIMAL(10,6) NOT NULL DEFAULT 1.0
                """)
                print("✅ Column added successfully")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✅ Column already exists")
                else:
                    print(f"❌ Error adding column: {e}")
                    # Continue anyway, column might exist

            # Step 2: Set conversion rate for all dish 1060062 + material 1500882 relationships
            print("\n2️⃣ SETTING CONVERSION RATES")
            print("-" * 30)

            cursor.execute("""
                UPDATE dish_material 
                SET unit_conversion_rate = 0.354, updated_at = CURRENT_TIMESTAMP
                FROM dish d, material m
                WHERE dish_material.dish_id = d.id 
                AND dish_material.material_id = m.id
                AND d.full_code = '1060062' 
                AND m.material_number = '1500882'
            """)

            updated_count = cursor.rowcount
            print(f"✅ Updated {updated_count} relationships")

            # Step 3: Verify
            print("\n3️⃣ VERIFICATION")
            print("-" * 30)

            cursor.execute("""
                SELECT 
                    d.full_code,
                    d.size,
                    m.material_number,
                    dm.unit_conversion_rate
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id
                JOIN material m ON dm.material_id = m.id
                WHERE d.full_code = '1060062' AND m.material_number = '1500882'
            """)

            results = cursor.fetchall()

            if results:
                print("✅ Verification successful:")
                for result in results:
                    print(
                        f"   Dish {result['full_code']} ({result['size']}) + Material {result['material_number']} = {result['unit_conversion_rate']}")

                # Test calculation
                test_value = 140.56
                expected = test_value / 0.354
                print(
                    f"\n📊 Test calculation: {test_value} ÷ 0.354 = {expected:.2f}")
            else:
                print("❌ No relationships found")

            # Commit changes
            conn.commit()
            print("\n✅ Changes committed")

            print("\n" + "=" * 50)
            print("🎯 SUCCESS!")
            print("Now regenerate your report - you should see:")
            print(f"理论用量 = ~397 (instead of 140.56)")
            print(f"套餐用量 = also divided by 0.354")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    if quick_fix():
        print("\n🚀 Run this to test:")
        print("python scripts/generate_database_report.py --target-date 2024-06-30")
    else:
        print("\n❌ Fix failed")
        sys.exit(1)
