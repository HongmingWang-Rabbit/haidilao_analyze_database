#!/usr/bin/env python3
"""
Diagnostic script to check unit_conversion_rate migration status.
This script helps diagnose the "无可用数据" issue in material variance analysis.
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


def check_unit_conversion_rate_status():
    """Check if unit_conversion_rate column exists and provide guidance"""
    print("🔍 UNIT CONVERSION RATE MIGRATION STATUS CHECK")
    print("=" * 60)

    try:
        # Connect to database
        db_manager = DatabaseManager(DatabaseConfig(is_test=False))
        print("✅ Connected to production database")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check if unit_conversion_rate column exists
            cursor.execute("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'dish_material' 
                AND column_name = 'unit_conversion_rate'
            """)

            column_info = cursor.fetchone()

            if column_info:
                print("✅ unit_conversion_rate column EXISTS")
                print(f"   Data type: {column_info['data_type']}")
                print(f"   Default: {column_info['column_default']}")
                print(f"   Nullable: {column_info['is_nullable']}")

                # Check if there are any records with conversion rates != 1.0
                cursor.execute("""
                    SELECT COUNT(*) as total_records,
                           COUNT(CASE WHEN unit_conversion_rate != 1.0 THEN 1 END) as non_default_rates,
                           MIN(unit_conversion_rate) as min_rate,
                           MAX(unit_conversion_rate) as max_rate,
                           AVG(unit_conversion_rate) as avg_rate
                    FROM dish_material
                    WHERE unit_conversion_rate IS NOT NULL
                """)

                stats = cursor.fetchone()
                if stats and stats['total_records'] > 0:
                    print(f"\n📊 CONVERSION RATE STATISTICS:")
                    print(
                        f"   Total dish-material records: {stats['total_records']}")
                    print(
                        f"   Records with non-default rates: {stats['non_default_rates']}")
                    print(f"   Min conversion rate: {stats['min_rate']}")
                    print(f"   Max conversion rate: {stats['max_rate']}")
                    print(
                        f"   Average conversion rate: {stats['avg_rate']:.4f}")

                    if stats['non_default_rates'] > 0:
                        print("✅ Migration complete and data populated!")
                    else:
                        print(
                            "⚠️  Migration complete but no conversion rates extracted yet")
                        print(
                            "💡 Run dish-material extraction to populate conversion rates")
                else:
                    print("⚠️  No dish-material records found")

                print("\n🎯 NEXT STEPS:")
                print("   ✅ Migration is complete")
                print("   📊 Material variance analysis should work now")
                print("   🔄 Run monthly automation to populate conversion rates")

            else:
                print("❌ unit_conversion_rate column DOES NOT EXIST")
                print("\n🔧 REQUIRED ACTION:")
                print("   1. Run the database migration to add the column")
                print("   2. Use automation menu: Database Management → Option 7")
                print("   3. Or run manually:")
                print("      psql -h localhost -U hongming -d haidilao-paperwork -f haidilao-database-querys/add_unit_conversion_rate_column.sql")
                print(
                    "\n💡 This will fix the '无可用数据' issue in material variance analysis")

            # Check dish_material table status
            cursor.execute("""
                SELECT COUNT(*) as total_relationships,
                       COUNT(DISTINCT dish_id) as unique_dishes,
                       COUNT(DISTINCT material_id) as unique_materials
                FROM dish_material
            """)

            relationships = cursor.fetchone()
            if relationships:
                print(f"\n📋 DISH-MATERIAL RELATIONSHIPS:")
                print(
                    f"   Total relationships: {relationships['total_relationships']}")
                print(f"   Unique dishes: {relationships['unique_dishes']}")
                print(
                    f"   Unique materials: {relationships['unique_materials']}")

                if relationships['total_relationships'] == 0:
                    print("⚠️  No dish-material relationships found!")
                    print(
                        "💡 Run dish-material extraction first: option 'q' in automation menu")

            # Check sample data for debugging
            if column_info:
                cursor.execute("""
                    SELECT d.full_code, m.material_number, dm.standard_quantity, dm.unit_conversion_rate
                    FROM dish_material dm
                    JOIN dish d ON dm.dish_id = d.id
                    JOIN material m ON dm.material_id = m.id
                    WHERE d.full_code = '1060062' AND m.material_number = '1500882'
                    LIMIT 1
                """)

                sample = cursor.fetchone()
                if sample:
                    print(f"\n🎯 SAMPLE DATA (dish 1060062 + material 1500882):")
                    print(
                        f"   Standard quantity: {sample['standard_quantity']}")
                    print(
                        f"   Unit conversion rate: {sample['unit_conversion_rate']}")
                else:
                    print("\n⚠️  Sample dish 1060062 + material 1500882 not found")
                    print("💡 This relationship may not be extracted yet")

    except Exception as e:
        print(f"❌ Error checking migration status: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    return True


if __name__ == "__main__":
    print("🍲 Haidilao Unit Conversion Rate Migration Checker")
    print()

    if check_unit_conversion_rate_status():
        print("✅ Check completed successfully")
    else:
        print("❌ Check failed")
        sys.exit(1)
