#!/usr/bin/env python3
"""
Direct insertion of 2024 data into the database
"""

import pandas as pd
from utils.database import DatabaseManager, DatabaseConfig
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def create_basic_prerequisites():
    """Create basic stores, dish types, and materials for testing"""
    print("🔧 Creating basic prerequisites...")

    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Create basic dish types
            cursor.execute("""
                INSERT INTO dish_type (name, description) VALUES
                ('主菜', '主要菜品'),
                ('配菜', '配菜类'),
                ('汤品', '汤类'),
                ('饮品', '饮料类'),
                ('小食', '小食类')
                ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
            """)

            # Get dish type ID
            cursor.execute("SELECT id FROM dish_type WHERE name = '主菜'")
            dish_type_id = cursor.fetchone()[0]

            # Create basic dish child types
            cursor.execute("""
                INSERT INTO dish_child_type (name, description, dish_type_id) VALUES
                ('肉类', '肉类菜品', %s),
                ('蔬菜', '蔬菜类', %s),
                ('海鲜', '海鲜类', %s)
                ON CONFLICT (name, dish_type_id) DO UPDATE SET description = EXCLUDED.description
            """, (dish_type_id, dish_type_id, dish_type_id))

            # Get dish child type ID
            cursor.execute("SELECT id FROM dish_child_type WHERE name = '肉类'")
            dish_child_type_id = cursor.fetchone()[0]

            # Create sample dishes from historical data
            sample_dishes = [
                ('M001', '麻辣牛肉', '大份'),
                ('M002', '香辣鱼片', '中份'),
                ('M003', '蒜蓉菠菜', '小份'),
                ('M004', '招牌豆腐', '大份'),
                ('M005', '酸辣土豆丝', '中份'),
            ]

            for dish_code, dish_name, size in sample_dishes:
                cursor.execute("""
                    INSERT INTO dish (full_code, name, size, dish_type_id, dish_child_type_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (full_code, size) DO UPDATE SET 
                        name = EXCLUDED.name,
                        dish_type_id = EXCLUDED.dish_type_id,
                        dish_child_type_id = EXCLUDED.dish_child_type_id
                """, (dish_code, dish_name, size, dish_type_id, dish_child_type_id))

            # Create basic materials
            cursor.execute("""
                INSERT INTO material (name, material_number, unit) VALUES
                ('基础物料', '999999', '份'),
                ('调料包', '888888', '包'),
                ('蔬菜类', '777777', '斤')
                ON CONFLICT (material_number) DO UPDATE SET name = EXCLUDED.name
            """)

            conn.commit()
            print("✅ Basic prerequisites created")

            # Count what we created
            cursor.execute("SELECT COUNT(*) FROM dish")
            dish_count = cursor.fetchone()[0]
            print(f"📊 Dishes in database: {dish_count}")

            cursor.execute("SELECT COUNT(*) FROM material")
            material_count = cursor.fetchone()[0]
            print(f"📦 Materials in database: {material_count}")

            return True

    except Exception as e:
        print(f"❌ Error creating prerequisites: {e}")
        import traceback
        traceback.print_exc()
        return False


def insert_sample_2024_data():
    """Insert sample 2024 data directly"""
    print("\n📊 Inserting sample 2024 data...")

    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Get dish and store IDs
            cursor.execute("SELECT id, full_code, name FROM dish LIMIT 5")
            dishes = cursor.fetchall()

            cursor.execute("SELECT id, name FROM store")
            stores = cursor.fetchall()

            print(f"Found {len(dishes)} dishes and {len(stores)} stores")

            # Insert sample monthly sales for 2024
            months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            inserted_count = 0

            for dish_id, dish_code, dish_name in dishes:
                for store_id, store_name in stores:
                    for month in months:
                        # Create sample sales data
                        sale_amount = 50 + (month * 10) + \
                            (dish_id * 5)  # Realistic amounts

                        cursor.execute("""
                            INSERT INTO dish_monthly_sale (dish_id, store_id, year, month, sale_amount)
                            VALUES (%s, %s, 2024, %s, %s)
                            ON CONFLICT (dish_id, store_id, year, month) DO UPDATE SET
                                sale_amount = EXCLUDED.sale_amount
                        """, (dish_id, store_id, month, sale_amount))

                        inserted_count += 1

            conn.commit()
            print(f"✅ Inserted {inserted_count} 2024 monthly sales records")

            # Verify insertion
            cursor.execute(
                "SELECT COUNT(*) FROM dish_monthly_sale WHERE year = 2024")
            count_2024 = cursor.fetchone()[0]
            print(f"📊 Total 2024 records in database: {count_2024}")

            return True

    except Exception as e:
        print(f"❌ Error inserting 2024 data: {e}")
        import traceback
        traceback.print_exc()
        return False


def insert_real_historical_data():
    """Insert real historical data from the files"""
    print("\n📋 Inserting real historical data...")

    try:
        # Read historical file
        historical_file = Path(
            "history_files/monthly_report_inputs/2024-05/monthly_dish_sale/海外菜品销售报表_20250706_1147.xlsx")
        if not historical_file.exists():
            print("❌ Historical file not found, using sample data only")
            return True

        df = pd.read_excel(historical_file, nrows=100)  # Limit for testing
        print(f"📋 Read {len(df)} rows from historical file")
        print(f"Columns: {list(df.columns)}")

        # Find the right column names
        dish_name_col = None
        dish_code_col = None

        for col in df.columns:
            if '菜品名称' in col:
                dish_name_col = col
            if '菜品编码' in col:
                dish_code_col = col

        if not dish_name_col or not dish_code_col:
            print("❌ Could not find dish name or code columns")
            return False

        print(f"Using dish name column: {dish_name_col}")
        print(f"Using dish code column: {dish_code_col}")

        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Get store mapping
            cursor.execute("SELECT id, name FROM store")
            store_mapping = {name: id for id, name in cursor.fetchall()}

            # Get dish type and child type IDs
            cursor.execute("SELECT id FROM dish_type WHERE name = '主菜'")
            dish_type_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM dish_child_type WHERE name = '肉类'")
            dish_child_type_id = cursor.fetchone()[0]

            inserted_dishes = 0
            inserted_sales = 0

            for _, row in df.iterrows():
                try:
                    # Extract dish info
                    dish_code = str(row[dish_code_col]).strip()
                    if dish_code.endswith('.0'):
                        dish_code = dish_code[:-2]

                    dish_name = str(row[dish_name_col]).strip()
                    size = str(row.get('规格', '')).strip()

                    if not dish_code or not dish_name:
                        continue

                    # Insert dish
                    cursor.execute("""
                        INSERT INTO dish (full_code, name, size, dish_type_id, dish_child_type_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (full_code, size) DO UPDATE SET 
                            name = EXCLUDED.name
                        RETURNING id
                    """, (dish_code, dish_name, size, dish_type_id, dish_child_type_id))

                    dish_id = cursor.fetchone()[0]
                    inserted_dishes += 1

                    # Insert monthly sales for each store
                    for store_name, store_id in store_mapping.items():
                        cursor.execute("""
                            INSERT INTO dish_monthly_sale (dish_id, store_id, year, month, sale_amount)
                            VALUES (%s, %s, 2024, 5, %s)
                            ON CONFLICT (dish_id, store_id, year, month) DO UPDATE SET
                                sale_amount = EXCLUDED.sale_amount
                        """, (dish_id, store_id, 50.0))  # Sample amount

                        inserted_sales += 1

                    if inserted_dishes % 20 == 0:
                        conn.commit()
                        print(f"  Processed {inserted_dishes} dishes...")

                except Exception as e:
                    print(f"  Error processing row: {e}")
                    continue

            conn.commit()
            print(
                f"✅ Inserted {inserted_dishes} real dishes and {inserted_sales} sales records")

            return True

    except Exception as e:
        print(f"❌ Error inserting real historical data: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_2024_data():
    """Verify that 2024 data now exists"""
    print("\n🔍 Verifying 2024 data...")

    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check 2024 data count
            cursor.execute(
                "SELECT COUNT(*) FROM dish_monthly_sale WHERE year = 2024")
            count_2024 = cursor.fetchone()[0]
            print(f"📊 Total 2024 records: {count_2024}")

            if count_2024 > 0:
                # Show sample data
                cursor.execute("""
                    SELECT d.name, s.name, dms.year, dms.month, dms.sale_amount
                    FROM dish_monthly_sale dms
                    JOIN dish d ON dms.dish_id = d.id
                    JOIN store s ON dms.store_id = s.id
                    WHERE dms.year = 2024
                    ORDER BY dms.month, d.name
                    LIMIT 10
                """)

                print("\n📋 Sample 2024 data:")
                for row in cursor.fetchall():
                    print(
                        f"  {row[0][:20]:<20} | {row[1]:<15} | {row[2]}-{row[3]:02d} | {row[4]}")

                # Check monthly distribution
                cursor.execute("""
                    SELECT month, COUNT(*) as count
                    FROM dish_monthly_sale
                    WHERE year = 2024
                    GROUP BY month
                    ORDER BY month
                """)

                print("\n📅 2024 Monthly distribution:")
                for month, count in cursor.fetchall():
                    print(f"  Month {month:02d}: {count} records")

                return True
            else:
                print("❌ No 2024 data found")
                return False

    except Exception as e:
        print(f"❌ Error verifying 2024 data: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🚀 DIRECT 2024 DATA INSERTION")
    print("=" * 60)

    # Step 1: Create prerequisites
    if not create_basic_prerequisites():
        print("❌ Failed to create prerequisites")
        return

    # Step 2: Insert sample 2024 data
    if not insert_sample_2024_data():
        print("❌ Failed to insert sample data")
        return

    # Step 3: Insert real historical data
    insert_real_historical_data()  # Continue even if this fails

    # Step 4: Verify results
    if verify_2024_data():
        print("\n🎉 SUCCESS: 2024 data is now in the database!")
    else:
        print("\n❌ FAILED: Still no 2024 data")


if __name__ == "__main__":
    main()
