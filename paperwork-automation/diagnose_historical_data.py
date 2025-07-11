#!/usr/bin/env python3
"""
Diagnostic script to check what's missing in the database for historical data extraction
"""

from utils.database import DatabaseManager, DatabaseConfig
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def check_database_status():
    """Check what data exists in the database"""
    print("🔍 CHECKING DATABASE STATUS")
    print("=" * 50)

    try:
        config = DatabaseConfig(is_test=False)  # Use production database
        db_manager = DatabaseManager(config)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check stores
            cursor.execute("SELECT COUNT(*) FROM store")
            store_count = cursor.fetchone()[0]
            print(f"🏪 Stores: {store_count}")

            if store_count > 0:
                cursor.execute("SELECT id, name FROM store LIMIT 5")
                stores = cursor.fetchall()
                for store_id, name in stores:
                    print(f"   - {store_id}: {name}")

            # Check dish types
            cursor.execute("SELECT COUNT(*) FROM dish_type")
            dish_type_count = cursor.fetchone()[0]
            print(f"🍽️ Dish types: {dish_type_count}")

            # Check dish child types
            cursor.execute("SELECT COUNT(*) FROM dish_child_type")
            dish_child_type_count = cursor.fetchone()[0]
            print(f"🍽️ Dish child types: {dish_child_type_count}")

            # Check dishes
            cursor.execute("SELECT COUNT(*) FROM dish")
            dish_count = cursor.fetchone()[0]
            print(f"🍽️ Dishes: {dish_count}")

            if dish_count > 0:
                cursor.execute("SELECT id, full_code, name FROM dish LIMIT 5")
                dishes = cursor.fetchall()
                for dish_id, code, name in dishes:
                    print(f"   - {dish_id}: {code} - {name[:30]}...")

            # Check materials
            cursor.execute("SELECT COUNT(*) FROM material")
            material_count = cursor.fetchone()[0]
            print(f"📦 Materials: {material_count}")

            # Check dish price history
            cursor.execute("SELECT COUNT(*) FROM dish_price_history")
            dish_price_count = cursor.fetchone()[0]
            print(f"💰 Dish price history: {dish_price_count}")

            # Check material price history
            cursor.execute("SELECT COUNT(*) FROM material_price_history")
            material_price_count = cursor.fetchone()[0]
            print(f"💰 Material price history: {material_price_count}")

            # Check dish monthly sales (the main issue)
            cursor.execute("SELECT COUNT(*) FROM dish_monthly_sale")
            monthly_sale_count = cursor.fetchone()[0]
            print(f"📊 Dish monthly sales: {monthly_sale_count}")

            print("\n" + "=" * 50)
            print("🎯 DIAGNOSIS")
            print("=" * 50)

            if store_count == 0:
                print("❌ No stores found - need to run basic setup first")
            else:
                print("✅ Stores exist")

            if dish_type_count == 0:
                print(
                    "❌ No dish types - historical extraction needs to create these first")
            else:
                print("✅ Dish types exist")

            if dish_count == 0:
                print("❌ No dishes - can't create dish_monthly_sale without dishes")
            else:
                print("✅ Dishes exist")

            if material_count == 0:
                print("❌ No materials - can't create material price history")
            else:
                print("✅ Materials exist")

            if monthly_sale_count == 0:
                print("❌ No dish monthly sales - this is what we need to fix!")
            else:
                print("✅ Dish monthly sales exist")

            # Check for sample historical data to see what columns are available
            print("\n" + "=" * 50)
            print("📋 SAMPLE DATA CHECK")
            print("=" * 50)

            import pandas as pd

            # Check a sample dish file
            sample_dish_file = Path(
                "history_files/monthly_report_inputs/2024-05/monthly_dish_sale/海外菜品销售报表_20250706_1147.xlsx")
            if sample_dish_file.exists():
                print(f"📋 Reading sample dish file: {sample_dish_file.name}")
                df = pd.read_excel(sample_dish_file, nrows=5)
                print(f"   Columns: {list(df.columns)}")

                # Check if we have quantity/revenue columns for monthly sales
                has_quantity = any('数量' in col for col in df.columns)
                has_revenue = any(
                    '销售额' in col or '金额' in col for col in df.columns)
                print(f"   Has quantity columns: {has_quantity}")
                print(f"   Has revenue columns: {has_revenue}")

                if has_quantity and has_revenue:
                    print("✅ Can extract monthly sales data")
                else:
                    print("❌ Missing quantity/revenue data for monthly sales")

    except Exception as e:
        print(f"❌ Error checking database: {e}")


def check_missing_insertion_code():
    """Check what's missing in the extraction script"""
    print("\n" + "=" * 50)
    print("🔍 CHECKING EXTRACTION SCRIPT")
    print("=" * 50)

    script_path = Path("scripts/extract_historical_data_batch.py")
    if not script_path.exists():
        print("❌ Extraction script not found")
        return

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for dish_monthly_sale insertion
    has_monthly_sale_insert = "INSERT INTO dish_monthly_sale" in content
    print(f"📊 Has dish_monthly_sale insertion: {has_monthly_sale_insert}")

    # Check for dish type processing
    has_dish_type_process = "process_dish_types" in content
    print(f"🍽️ Has dish type processing: {has_dish_type_process}")

    # Check for proper transaction handling
    has_transaction_handling = "with self.db_manager.get_connection()" in content
    print(f"🔄 Has transaction handling: {has_transaction_handling}")

    if not has_monthly_sale_insert:
        print("❌ CRITICAL: Missing dish_monthly_sale insertion code!")
        print("   This is why dish_monthly_sale table is empty")

    print("\n" + "=" * 50)
    print("💡 RECOMMENDATIONS")
    print("=" * 50)
    print("1. Add dish_monthly_sale insertion code to the extraction script")
    print("2. Fix dish type insertion to ensure dishes can reference them")
    print("3. Process data in correct order: stores → dish types → dishes → prices → monthly sales")
    print("4. Add extraction of quantity/revenue data from historical files")


if __name__ == "__main__":
    check_database_status()
    check_missing_insertion_code()
