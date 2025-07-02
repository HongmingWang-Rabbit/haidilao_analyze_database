#!/usr/bin/env python3
"""
Script to migrate database by adding loss_rate column to dish_material table.
"""

from utils.database import DatabaseManager, DatabaseConfig
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the database migration to add loss_rate column."""
    try:
        # Use production database by default
        db_manager = DatabaseManager(DatabaseConfig(is_test=False))

        # Read migration script
        migration_file = Path(__file__).parent.parent / \
            "haidilao-database-querys" / "add_loss_rate_column.sql"

        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        logger.info("🔧 Running database migration to add loss_rate column...")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Split the SQL into individual statements and execute them
            statements = [stmt.strip()
                          for stmt in migration_sql.split(';') if stmt.strip()]

            for statement in statements:
                if statement.strip():
                    # Skip SELECT statements (they're for verification)
                    if statement.strip().upper().startswith('SELECT'):
                        logger.info("Verifying migration...")
                        cursor.execute(statement)
                        results = cursor.fetchall()
                        for row in results:
                            logger.info(f"Column info: {row}")
                    else:
                        cursor.execute(statement)

            conn.commit()

        logger.info("✅ Database migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
