#!/usr/bin/env python3
"""Check Coca Cola material in database"""

from utils.database import DatabaseConfig, get_database_manager
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))


def check_coca_cola_in_database():
    """Check if Coca Cola material is properly imported with type info"""

    try:
        print("=== CHECKING COCA COLA IN DATABASE ===")

        # Use test database
        config = DatabaseConfig(is_test=True)
        db_manager = get_database_manager(is_test=True)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:

                # Search for material 000000000001500902
                print("1. Searching for material 000000000001500902:")
                cursor.execute("""
                    SELECT m.id, m.material_number, m.name, m.description, 
                           mt.name as material_type_name, mct.name as material_child_type_name
                    FROM material m
                    LEFT JOIN material_type mt ON m.material_type_id = mt.id
                    LEFT JOIN material_child_type mct ON m.material_child_type_id = mct.id
                    WHERE m.material_number = %s
                """, ('000000000001500902',))

                results = cursor.fetchall()
                if results:
                    print(f"   ✅ Found material 000000000001500902!")
                    for row in results:
                        print(f"   ID: {row['id']}")
                        print(f"   Material Number: {row['material_number']}")
                        print(f"   Name: {row['name']}")
                        print(f"   Description: {row['description']}")
                        print(f"   Type: {row['material_type_name']}")
                        print(
                            f"   Child Type: {row['material_child_type_name']}")
                        print()
                else:
                    print("   ❌ Material 000000000001500902 not found")

                # Search for all beverage materials
                print("2. Searching for materials with '成本-酒水类' type:")
                cursor.execute("""
                    SELECT m.id, m.material_number, m.name, 
                           mt.name as material_type_name
                    FROM material m
                    JOIN material_type mt ON m.material_type_id = mt.id
                    WHERE mt.name = %s
                    ORDER BY m.name
                """, ('成本-酒水类',))

                beverage_results = cursor.fetchall()
                if beverage_results:
                    print(
                        f"   ✅ Found {len(beverage_results)} beverage materials:")
                    for row in beverage_results[:10]:  # Show first 10
                        print(f"   - {row['material_number']}: {row['name']}")
                    if len(beverage_results) > 10:
                        print(f"   ... and {len(beverage_results) - 10} more")
                else:
                    print("   ❌ No beverage materials found")

                # Check all material types
                print(f"\n3. All material types in database:")
                cursor.execute(
                    "SELECT id, name, description FROM material_type ORDER BY name")
                type_results = cursor.fetchall()
                for row in type_results:
                    print(f"   - {row['name']} (ID: {row['id']})")

                # Check material counts by type
                print(f"\n4. Material counts by type:")
                cursor.execute("""
                    SELECT mt.name, COUNT(m.id) as material_count
                    FROM material_type mt
                    LEFT JOIN material m ON m.material_type_id = mt.id
                    GROUP BY mt.id, mt.name
                    ORDER BY material_count DESC
                """)
                count_results = cursor.fetchall()
                for row in count_results:
                    print(
                        f"   - {row['name']}: {row['material_count']} materials")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_coca_cola_in_database()
