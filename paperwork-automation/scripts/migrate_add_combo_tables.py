#!/usr/bin/env python3
"""
Combo Tables Migration Runner
===========================================

This script executes the combo tables migration SQL script to add:
- combo table
- monthly_combo_dish_sale table
- related indexes and triggers

Usage:
    python scripts/migrate_add_combo_tables.py

The script will:
1. Connect to the database
2. Execute the migration SQL script
3. Show progress and results
4. Provide next steps

Generated: 2025-07-03
"""

from utils.database import DatabaseManager, DatabaseConfig
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_logging():
    """Setup logging for the migration process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def load_migration_sql() -> str:
    """Load the migration SQL script."""
    sql_file = Path(__file__).parent.parent / \
        "haidilao-database-querys" / "migrate_add_combo_tables.sql"

    if not sql_file.exists():
        raise FileNotFoundError(f"Migration SQL file not found: {sql_file}")

    with open(sql_file, 'r', encoding='utf-8') as f:
        return f.read()


def execute_migration(logger: logging.Logger) -> bool:
    """Execute the combo tables migration."""
    try:
        # Load migration SQL
        logger.info("Loading migration SQL script...")
        migration_sql = load_migration_sql()

        # Connect to database
        logger.info("Connecting to database...")
        db_config = DatabaseConfig(is_test=False)  # Production database
        db_manager = DatabaseManager(db_config)

        # Execute migration
        logger.info("Executing migration script...")
        logger.info("=" * 50)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Execute the migration SQL
                cur.execute(migration_sql)

                # Commit the changes
                conn.commit()

                # Get all notices (PostgreSQL RAISE NOTICE messages)
                notices = conn.notices
                for notice in notices:
                    # Clean up the notice format
                    notice_text = notice.strip()
                    if notice_text.startswith('NOTICE:'):
                        notice_text = notice_text[7:].strip()
                    logger.info(notice_text)

        logger.info("=" * 50)
        logger.info("SUCCESS: Migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"ERROR: Migration failed: {str(e)}")
        return False


def show_next_steps(logger: logging.Logger):
    """Show the next steps after migration."""
    logger.info("")
    logger.info("NEXT STEPS:")
    logger.info("1. Extract combo data:")
    logger.info("   python scripts/extract_combo_monthly_sales.py Input/monthly_report/monthly_combo_sale/海外套餐销售明细_20250703_1848.xlsx --direct-db")
    logger.info("")
    logger.info("2. Generate monthly material reports:")
    logger.info(
        "   The reports will now automatically include combo usage in calculations")
    logger.info("")
    logger.info("3. Test the system:")
    logger.info(
        "   Run the automation menu option 2 (Complete Monthly Automation) to verify")
    logger.info("")


def main():
    """Main migration runner function."""
    logger = setup_logging()

    logger.info("HAIDILAO COMBO TABLES MIGRATION")
    logger.info("=" * 50)

    # Ask for confirmation
    print(
        "\n[WARNING] This migration will add combo tables to your production database.")
    print("   The migration is safe and will not affect existing data.")
    print("   Tables will only be created if they don't already exist.")
    print("")

    confirm = input(
        "Do you want to proceed with the migration? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        logger.info("CANCELLED: Migration cancelled by user.")
        return

    # Execute migration
    success = execute_migration(logger)

    if success:
        show_next_steps(logger)
    else:
        logger.info("")
        logger.info(
            "ERROR: Migration failed. Please check the error messages above.")
        logger.info(
            "   You may need to check your database connection or permissions.")


if __name__ == "__main__":
    main()
