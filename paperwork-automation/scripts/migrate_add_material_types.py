#!/usr/bin/env python3
"""
Migration script to add material type tables and update material table structure.
This adds material classification similar to dish classification for better organization.
"""

from utils.database import DatabaseManager, DatabaseConfig
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path FIRST, before importing local modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import local modules after path is set


def safe_print(message):
    """Print message safely, handling Unicode encoding errors on Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Remove emojis and special Unicode characters for Windows console
        import re
        clean_message = re.sub(r'[^\x00-\x7F]+', '', message)
        print(clean_message)


def safe_log(logger_func, message):
    """Log message safely, handling Unicode encoding errors on Windows"""
    try:
        logger_func(message)
    except UnicodeEncodeError:
        # Remove emojis and special Unicode characters for Windows console
        import re
        clean_message = re.sub(r'[^\x00-\x7F]+', '', message)
        logger_func(clean_message)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_material_type_migration(is_test: bool = False):
    """
    Run the material type migration on the database.

    Args:
        is_test: Whether to run on test database
    """

    try:
        # Initialize database connection
        config = DatabaseConfig(is_test=is_test)
        db_manager = DatabaseManager(config)

        db_type = "test" if is_test else "production"
        safe_log(logger.info,
                 f"🔧 Starting material type migration on {db_type} database")

        # Read migration SQL file
        migration_file = project_root / "haidilao-database-querys" / \
            "add_material_type_tables.sql"

        if not migration_file.exists():
            safe_log(logger.error,
                     f"❌ Migration file not found: {migration_file}")
            return False

        safe_log(logger.info, f"📄 Reading migration script: {migration_file}")

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Execute migration
        safe_log(logger.info, "🚀 Executing material type migration...")

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute the entire SQL script as one statement
                # This handles multi-line dollar-quoted strings properly
                safe_log(
                    logger.info, "⚙️  Executing material type migration script...")
                cursor.execute(migration_sql)

                # Commit the transaction
                conn.commit()
                safe_log(logger.info, "✅ Migration committed successfully")

        # Verify migration results
        safe_log(logger.info, "🔍 Verifying migration results...")

        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check material_type table
                    cursor.execute("SELECT COUNT(*) FROM material_type")
                    result = cursor.fetchone()
                    material_type_count = result[0] if result else 0
                    safe_log(
                        logger.info, f"📋 Material types: {material_type_count}")

                    # Check material_child_type table
                    cursor.execute("SELECT COUNT(*) FROM material_child_type")
                    result = cursor.fetchone()
                    material_child_type_count = result[0] if result else 0
                    safe_log(logger.info,
                             f"📋 Material child types: {material_child_type_count}")

                    # Check if material table has new columns
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'material' 
                        AND column_name IN ('material_type_id', 'material_child_type_id')
                        ORDER BY column_name
                    """)
                    new_columns = [row[0] for row in cursor.fetchall()]
                    safe_log(
                        logger.info, f"🔗 New material columns: {new_columns}")

                    if len(new_columns) == 2:
                        safe_log(logger.info,
                                 "✅ All expected columns added to material table")
                    else:
                        safe_log(logger.warning,
                                 "⚠️  Some expected columns may be missing")

        except Exception as verification_error:
            safe_log(logger.warning,
                     f"⚠️  Verification failed: {verification_error}")
            # Don't fail the migration for verification errors

        safe_log(logger.info, "🎉 Material type migration completed successfully!")
        return True

    except Exception as e:
        safe_log(logger.error, f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for the migration script"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Add material type tables and update material table structure"
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run migration on test database instead of production'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt (for automation)'
    )

    args = parser.parse_args()

    db_type = "test" if args.test else "production"

    print("=" * 60)
    safe_print("🔧 MATERIAL TYPE TABLES MIGRATION")
    print("=" * 60)
    print("This migration will:")
    safe_print("✅ Create material_type table (11 types)")
    safe_print("✅ Create material_child_type table (6 child types)")
    safe_print("✅ Add material_type_id column to material table")
    safe_print("✅ Add material_child_type_id column to material table")
    safe_print("✅ Create appropriate indexes and triggers")
    safe_print("✅ Insert initial material type data")
    print()
    safe_print(f"🗄️  Target database: {db_type}")
    print("=" * 60)

    if not args.confirm:
        confirm = input("Proceed with migration? (y/N): ").lower().strip()
        if confirm != 'y':
            safe_print("❌ Migration cancelled")
            return

    # Run migration
    success = run_material_type_migration(is_test=args.test)

    if success:
        safe_print("\n✅ Migration completed successfully!")
        safe_print("📌 Next steps:")
        print("   1. Use complete monthly automation to extract material types from material_detail files")
        print("   2. Run material extraction to populate material_type_id and material_child_type_id")
        print("   3. Verify data with: SELECT COUNT(*) FROM material WHERE material_type_id IS NOT NULL")
    else:
        safe_print("\n❌ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
