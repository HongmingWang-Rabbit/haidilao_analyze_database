#!/usr/bin/env python3
"""
Database utilities for Haidilao paperwork automation system.
Handles PostgreSQL connections, schema setup, and data operations.
"""

import os
import sys
import psycopg2
import psycopg2.extras
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self, is_test: bool = False):
        self.is_test = is_test
        prefix = "TEST_" if is_test else ""
        
        self.host = os.getenv(f"{prefix}PG_HOST", "localhost")
        self.port = int(os.getenv(f"{prefix}PG_PORT", "5432"))
        self.user = os.getenv(f"{prefix}PG_USER", "postgres")
        self.password = os.getenv(f"{prefix}PG_PASSWORD", "")
        self.database = os.getenv(f"{prefix}PG_DATABASE", "haidilao")
        
        # Validate required fields
        if not all([self.host, self.user, self.password, self.database]):
            missing = []
            if not self.host: missing.append(f"{prefix}PG_HOST")
            if not self.user: missing.append(f"{prefix}PG_USER")
            if not self.password: missing.append(f"{prefix}PG_PASSWORD")
            if not self.database: missing.append(f"{prefix}PG_DATABASE")
            
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def __str__(self) -> str:
        return f"DatabaseConfig(host={self.host}, port={self.port}, user={self.user}, database={self.database}, is_test={self.is_test})"

class DatabaseManager:
    """Database connection and operation manager"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    return result is not None and result['test'] == 1  # type: ignore
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_sql_file(self, file_path: str) -> bool:
        """Execute SQL file"""
        try:
            sql_path = Path(file_path)
            if not sql_path.exists():
                logger.error(f"SQL file not found: {file_path}")
                return False
            
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Split by semicolon and execute each statement
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    
                    for statement in statements:
                        if statement:
                            cursor.execute(statement)
                    
                    conn.commit()
                    logger.info(f"Successfully executed SQL file: {file_path}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to execute SQL file {file_path}: {e}")
            return False
    
    def execute_sql(self, sql: str, params: Optional[Tuple] = None) -> bool:
        """Execute SQL statement"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    logger.info("SQL executed successfully")
                    return True
        except Exception as e:
            logger.error(f"Failed to execute SQL: {e}")
            return False
    
    def fetch_all(self, sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all results from SQL query"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    results = cursor.fetchall()
                    return list(results) if results else []  # type: ignore
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return []
    
    def fetch_one(self, sql: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch one result from SQL query"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    result = cursor.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return None

class DatabaseSetup:
    """Database setup and initialization"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.sql_dir = Path(__file__).parent.parent / "haidilao-database-querys"
    
    def setup_test_database(self) -> bool:
        """Setup test database with schema and initial data"""
        logger.info("🔄 Setting up test database...")
        
        try:
            # 1. Reset database schema
            reset_sql = self.sql_dir / "reset-db.sql"
            if not self.db_manager.execute_sql_file(str(reset_sql)):
                logger.error("Failed to reset database schema")
                return False
            logger.info("✅ Database schema reset completed")
            
            # 2. Insert constant data (stores and time segments)
            const_sql = self.sql_dir / "insert_const_data.sql"
            if not self.db_manager.execute_sql_file(str(const_sql)):
                logger.error("Failed to insert constant data")
                return False
            logger.info("✅ Constant data inserted")
            
            # 3. Insert monthly targets
            target_sql = self.sql_dir / "insert_monthly_target.sql"
            if not self.db_manager.execute_sql_file(str(target_sql)):
                logger.error("Failed to insert monthly targets")
                return False
            logger.info("✅ Monthly targets inserted")
            
            logger.info("🎉 Test database setup completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False
    
    def verify_database_structure(self) -> bool:
        """Verify database has required tables and data"""
        required_tables = ['store', 'time_segment', 'daily_report', 'store_time_report', 'store_monthly_target']
        
        try:
            for table in required_tables:
                result = self.db_manager.fetch_one(
                    "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = %s",
                    (table,)
                )
                if not result or result['count'] == 0:
                    logger.error(f"Required table '{table}' not found")
                    return False
            
            # Check if stores are populated
            stores = self.db_manager.fetch_all("SELECT COUNT(*) as count FROM store")
            if not stores or stores[0]['count'] < 7:
                logger.error("Store data not properly populated")
                return False
            
            # Check if time segments are populated
            time_segments = self.db_manager.fetch_all("SELECT COUNT(*) as count FROM time_segment")
            if not time_segments or time_segments[0]['count'] < 4:
                logger.error("Time segment data not properly populated")
                return False
            
            logger.info("✅ Database structure verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False

def get_database_manager(is_test: bool = False) -> DatabaseManager:
    """Get configured database manager"""
    config = DatabaseConfig(is_test=is_test)
    return DatabaseManager(config)

def setup_database_for_tests() -> bool:
    """Setup database for testing"""
    try:
        db_manager = get_database_manager(is_test=True)
        setup = DatabaseSetup(db_manager)
        return setup.setup_test_database()
    except Exception as e:
        logger.error(f"Failed to setup test database: {e}")
        return False

def verify_database_connection(is_test: bool = False) -> bool:
    """Verify database connection"""
    try:
        db_manager = get_database_manager(is_test=is_test)
        return db_manager.test_connection()
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        return False

if __name__ == "__main__":
    # Command line interface for database operations
    import argparse
    
    parser = argparse.ArgumentParser(description="Database utilities for Haidilao system")
    parser.add_argument("--test", action="store_true", help="Use test database")
    parser.add_argument("--setup", action="store_true", help="Setup database")
    parser.add_argument("--verify", action="store_true", help="Verify database connection")
    parser.add_argument("--check-structure", action="store_true", help="Check database structure")
    
    args = parser.parse_args()
    
    if args.setup:
        success = setup_database_for_tests() if args.test else False
        if not args.test:
            print("❌ Setup only available for test database. Use --test flag.")
        sys.exit(0 if success else 1)
    
    if args.verify:
        success = verify_database_connection(is_test=args.test)
        env_type = "test" if args.test else "production"
        if success:
            print(f"✅ {env_type.title()} database connection successful")
        else:
            print(f"❌ {env_type.title()} database connection failed")
        sys.exit(0 if success else 1)
    
    if args.check_structure:
        db_manager = get_database_manager(is_test=args.test)
        setup = DatabaseSetup(db_manager)
        success = setup.verify_database_structure()
        env_type = "test" if args.test else "production"
        if success:
            print(f"✅ {env_type.title()} database structure is valid")
        else:
            print(f"❌ {env_type.title()} database structure is invalid")
        sys.exit(0 if success else 1)
    
    # Default: show help
    parser.print_help() 