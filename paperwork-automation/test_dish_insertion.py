#!/usr/bin/env python3
"""
Test dish insertion with fixed schema
"""

from utils.database import DatabaseManager, DatabaseConfig
import os
import sys
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for database connection
os.environ['PG_HOST'] = 'localhost'
os.environ['PG_PORT'] = '5432'
os.environ['PG_USER'] = 'hongming'
os.environ['PG_PASSWORD'] = '8894'
os.environ['PG_DATABASE'] = 'haidilao-paperwork'


def test_dish_insertion():
    """Test inserting a single dish with the corrected schema."""
    print("🧪 TESTING DISH INSERTION")
    print("=" * 50)

    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)

        # First, let's read some real data from the Excel file
        file_path = Path(
            "history_files/monthly_report_inputs/2024-05/monthly_dish_sale/海外菜品销售报表_20250706_1147.xlsx")

        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return

        # Read a small sample
        df = pd.read_excel(file_path, engine='openpyxl', nrows=5)
        print(f"📊 Loaded {len(df)} sample rows")

        # Test with the first row of real data
        row = df.iloc[0]
        print(f"📋 Testing with first row:")
        print(f"  菜品名称: {row['菜品名称(门店pad显示名称)']}")
        print(f"  菜品编码: {row['菜品编码']}")
        print(f"  大类名称: {row['大类名称']}")
        print(f"  子类名称: {row['子类名称']}")
        print(f"  规格: {row['规格'] if '规格' in row else 'N/A'}")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Clean the dish code
            full_code = str(row['菜品编码']).strip()
            if full_code.endswith('.0'):
                full_code = full_code[:-2]

            size = str(row['规格']) if '规格' in row and pd.notna(
                row['规格']) else ''
            dish_name = str(row['菜品名称(门店pad显示名称)']).strip()

            print(f"\n🔄 Cleaned data:")
            print(f"  full_code: {full_code}")
            print(f"  size: {size}")
            print(f"  dish_name: {dish_name}")

            # Get dish_type_id
            dish_type_id = None
            if pd.notna(row['大类名称']):
                cursor.execute(
                    "SELECT id FROM dish_type WHERE name = %s", (row['大类名称'],))
                result = cursor.fetchone()
                if result:
                    dish_type_id = result['id']
                    print(f"  dish_type_id: {dish_type_id}")
                else:
                    print(f"  ❌ dish_type not found: {row['大类名称']}")

            # Get dish_child_type_id
            dish_child_type_id = None
            if pd.notna(row['子类名称']) and dish_type_id:
                cursor.execute("SELECT id FROM dish_child_type WHERE name = %s AND dish_type_id = %s",
                               (row['子类名称'], dish_type_id))
                result = cursor.fetchone()
                if result:
                    dish_child_type_id = result['id']
                    print(f"  dish_child_type_id: {dish_child_type_id}")
                else:
                    print(f"  ❌ dish_child_type not found: {row['子类名称']}")

            # Try to insert the dish
            print(f"\n🔄 Attempting to insert dish...")
            try:
                cursor.execute("""
                    INSERT INTO dish (
                        full_code, size, name, dish_child_type_id
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (full_code, size) DO UPDATE SET
                        name = EXCLUDED.name,
                        dish_child_type_id = EXCLUDED.dish_child_type_id,
                        updated_at = CURRENT_TIMESTAMP
                """, (full_code, size, dish_name, dish_child_type_id))

                if cursor.rowcount > 0:
                    print(f"  ✅ Successfully inserted/updated dish")
                    conn.commit()
                else:
                    print(f"  ⚠️ No rows affected")

            except Exception as e:
                print(f"  ❌ Error inserting dish: {e}")
                conn.rollback()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_dish_insertion()
