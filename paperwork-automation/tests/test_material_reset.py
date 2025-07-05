#!/usr/bin/env python3
"""
Material Reset Helper Script

This script executes the reset_materials_only.sql script to reset
material-related tables for development/testing purposes.

Usage:
    python -m tests.test_material_reset [--test-db]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from utils.database import DatabaseManager, DatabaseConfig
except ImportError:
    print("❌ Error: Could not import database utilities")
    print("Make sure you are running from the project root directory")
    sys.exit(1)


def execute_material_reset(use_test_db: bool = True):
    """Execute the material reset SQL script"""

    # Load the SQL script
    sql_file = project_root / "haidilao-database-querys" / \
        "tests" / "reset_materials_only.sql"

    if not sql_file.exists():
        print(f"❌ Error: SQL script not found: {sql_file}")
        return False

    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        return False

    # Set up database connection
    try:
        config = DatabaseConfig(is_test=use_test_db)
        db_manager = DatabaseManager(config)

        print(
            f"🗄️  Connecting to {'test' if use_test_db else 'production'} database...")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            print("🔄 Executing material reset script...")

            # Execute the SQL script
            cursor.execute(sql_content)
            conn.commit()

            print("✅ Material reset completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Reset material tables using reset_materials_only.sql'
    )
    parser.add_argument(
        '--test-db',
        action='store_true',
        default=True,
        help='Use test database (default)'
    )
    parser.add_argument(
        '--production-db',
        action='store_true',
        help='Use production database (WARNING: dangerous!)'
    )

    args = parser.parse_args()

    # Default to test database for safety
    use_test_db = not args.production_db

    print("🧪 MATERIAL TABLES RESET")
    print("=" * 35)

    db_type = "test" if use_test_db else "production"
    print(f"Database: {db_type}")

    success = execute_material_reset(use_test_db=use_test_db)

    if success:
        print("🎉 Material reset finished successfully!")
        sys.exit(0)
    else:
        print("❌ Material reset failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
