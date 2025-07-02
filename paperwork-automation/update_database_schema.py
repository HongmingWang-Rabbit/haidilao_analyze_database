#!/usr/bin/env python3
"""
Update database schema to include monthly performance tracking tables.
Run this script to add the new tables: dish_monthly_sale and material_monthly_usage
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.database import DatabaseManager, DatabaseConfig
except ImportError:
    print("❌ Database utilities not available")
    sys.exit(1)


def update_database_schema():
    """Update database with new monthly performance tables"""

    print("🗄️  Updating database schema with monthly performance tables...")

    try:
        # Connect to database
        db_manager = DatabaseManager(DatabaseConfig(is_test=False))

        # Check if tables already exist
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check for existing tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('dish_monthly_sale', 'material_monthly_usage')
                """)
                existing_tables = [row['table_name']
                                   for row in cursor.fetchall()]

                if 'dish_monthly_sale' in existing_tables and 'material_monthly_usage' in existing_tables:
                    print("✅ Monthly performance tables already exist!")
                    return True

                # Read and execute the migration script (safe for existing databases)
        print("📊 Reading migration script...")
        migration_file = Path(
            "haidilao-database-querys/add_monthly_performance_tables.sql")

        if not migration_file.exists():
            print(
                "❌ Migration file not found: haidilao-database-querys/add_monthly_performance_tables.sql")
            return False

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Execute migration (safe - only adds new tables)
        print("🔄 Executing database migration (safe for existing data)...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(migration_sql)
                conn.commit()

        print("✅ Database schema updated successfully!")
        print()
        print("📊 New tables added:")
        print("   🍽️  dish_monthly_sale - Tracks monthly sales performance per dish")
        print("       - sale_amount, return_amount, free_meal_amount, gift_amount")
        print("   🧪 material_monthly_usage - Tracks monthly material consumption")
        print("       - material_used, opening_stock, closing_stock")
        print()
        print("📈 Enhanced capabilities:")
        print("   ✅ Monthly sales performance tracking")
        print("   ✅ Material consumption analysis")
        print("   ✅ Inventory movement tracking")
        print("   ✅ Enhanced monthly dishes reports")
        print()
        print("🚀 You can now use:")
        print("   - scripts/extract_dish_monthly_sales.py")
        print("   - scripts/extract_material_monthly_usage.py")
        print("   - Enhanced monthly dishes worksheet with performance data")

        return True

    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🍲 HAIDILAO DATABASE SCHEMA UPDATE")
    print("=" * 50)

    success = update_database_schema()

    if success:
        print("\n🎉 Database update completed successfully!")
        print("\nNext steps:")
        print("1. Extract your existing data using the automation menu")
        print("2. Extract monthly performance data with new scripts")
        print("3. Generate enhanced monthly dishes reports")
    else:
        print("\n❌ Database update failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
