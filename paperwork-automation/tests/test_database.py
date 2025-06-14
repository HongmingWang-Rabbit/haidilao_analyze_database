#!/usr/bin/env python3
"""
Database integration tests for Haidilao paperwork automation system.
Tests database connections, schema setup, and data operations.
"""

import unittest
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import (
    DatabaseConfig, DatabaseManager, DatabaseSetup,
    get_database_manager, setup_database_for_tests,
    verify_database_connection
)

class TestDatabaseConfig(unittest.TestCase):
    """Test database configuration management"""
    
    def setUp(self):
        # Store original environment variables
        self.original_env = {}
        env_vars = [
            'PG_HOST', 'PG_PORT', 'PG_USER', 'PG_PASSWORD', 'PG_DATABASE',
            'TEST_PG_HOST', 'TEST_PG_PORT', 'TEST_PG_USER', 'TEST_PG_PASSWORD', 'TEST_PG_DATABASE'
        ]
        for var in env_vars:
            self.original_env[var] = os.getenv(var)
    
    def tearDown(self):
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
    
    def test_production_config_creation(self):
        """Test production database configuration creation"""
        # Set test environment variables
        os.environ['PG_HOST'] = 'localhost'
        os.environ['PG_PORT'] = '5432'
        os.environ['PG_USER'] = 'testuser'
        os.environ['PG_PASSWORD'] = 'testpass'
        os.environ['PG_DATABASE'] = 'testdb'
        
        config = DatabaseConfig(is_test=False)
        
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.user, 'testuser')
        self.assertEqual(config.password, 'testpass')
        self.assertEqual(config.database, 'testdb')
        self.assertFalse(config.is_test)
    
    def test_test_config_creation(self):
        """Test test database configuration creation"""
        # Set test environment variables
        os.environ['TEST_PG_HOST'] = 'test-localhost'
        os.environ['TEST_PG_PORT'] = '5433'
        os.environ['TEST_PG_USER'] = 'testuser'
        os.environ['TEST_PG_PASSWORD'] = 'testpass'
        os.environ['TEST_PG_DATABASE'] = 'testdb'
        
        config = DatabaseConfig(is_test=True)
        
        self.assertEqual(config.host, 'test-localhost')
        self.assertEqual(config.port, 5433)
        self.assertEqual(config.user, 'testuser')
        self.assertEqual(config.password, 'testpass')
        self.assertEqual(config.database, 'testdb')
        self.assertTrue(config.is_test)
    
    def test_missing_required_config(self):
        """Test error handling for missing required configuration"""
        # Clear all database environment variables
        for var in ['PG_HOST', 'PG_USER', 'PG_PASSWORD', 'PG_DATABASE']:
            os.environ.pop(var, None)
        
        with self.assertRaises(ValueError) as context:
            DatabaseConfig(is_test=False)
        
        self.assertIn("Missing required environment variables", str(context.exception))
    
    def test_connection_string_generation(self):
        """Test PostgreSQL connection string generation"""
        os.environ['PG_HOST'] = 'localhost'
        os.environ['PG_PORT'] = '5432'
        os.environ['PG_USER'] = 'testuser'
        os.environ['PG_PASSWORD'] = 'testpass'
        os.environ['PG_DATABASE'] = 'testdb'
        
        config = DatabaseConfig(is_test=False)
        expected = "postgresql://testuser:testpass@localhost:5432/testdb"
        
        self.assertEqual(config.connection_string, expected)

class TestDatabaseManager(unittest.TestCase):
    """Test database manager functionality"""
    
    def setUp(self):
        # Mock database configuration
        self.mock_config = MagicMock()
        self.mock_config.host = 'localhost'
        self.mock_config.port = 5432
        self.mock_config.user = 'testuser'
        self.mock_config.password = 'testpass'
        self.mock_config.database = 'testdb'
        
        self.db_manager = DatabaseManager(self.mock_config)
    
    @patch('utils.database.psycopg2.connect')
    def test_successful_connection(self, mock_connect):
        """Test successful database connection"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        with self.db_manager.get_connection() as conn:
            self.assertEqual(conn, mock_conn)
        
        mock_connect.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('utils.database.psycopg2.connect')
    def test_connection_test_success(self, mock_connect):
        """Test successful connection test"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = self.db_manager.test_connection()
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_with("SELECT 1")
    
    @patch('utils.database.psycopg2.connect')
    def test_connection_test_failure(self, mock_connect):
        """Test connection test failure"""
        mock_connect.side_effect = Exception("Connection failed")
        
        result = self.db_manager.test_connection()
        
        self.assertFalse(result)
    
    @patch('utils.database.psycopg2.connect')
    def test_execute_sql_success(self, mock_connect):
        """Test successful SQL execution"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = self.db_manager.execute_sql("INSERT INTO test VALUES (1)")
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_with("INSERT INTO test VALUES (1)", None)
        mock_conn.commit.assert_called_once()
    
    @patch('utils.database.psycopg2.connect')
    def test_fetch_all_success(self, mock_connect):
        """Test successful data fetching"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = self.db_manager.fetch_all("SELECT * FROM test")
        
        self.assertEqual(result, [{'id': 1, 'name': 'test'}])
        mock_cursor.execute.assert_called_with("SELECT * FROM test", None)

class TestDatabaseSetup(unittest.TestCase):
    """Test database setup functionality"""
    
    def setUp(self):
        self.mock_db_manager = MagicMock()
        self.db_setup = DatabaseSetup(self.mock_db_manager)
    
    def test_setup_test_database_success(self):
        """Test successful test database setup"""
        self.mock_db_manager.execute_sql_file.return_value = True
        
        result = self.db_setup.setup_test_database()
        
        self.assertTrue(result)
        # Should call execute_sql_file 3 times (reset, const data, monthly targets)
        self.assertEqual(self.mock_db_manager.execute_sql_file.call_count, 3)
    
    def test_setup_test_database_failure(self):
        """Test test database setup failure"""
        self.mock_db_manager.execute_sql_file.return_value = False
        
        result = self.db_setup.setup_test_database()
        
        self.assertFalse(result)
    
    def test_verify_database_structure_success(self):
        """Test successful database structure verification"""
        # Mock table existence checks
        self.mock_db_manager.fetch_one.side_effect = [
            {'count': 1},  # store table exists
            {'count': 1},  # time_segment table exists
            {'count': 1},  # daily_report table exists
            {'count': 1},  # store_time_report table exists
            {'count': 1},  # store_monthly_target table exists
        ]
        
        # Mock data population checks
        self.mock_db_manager.fetch_all.side_effect = [
            [{'count': 7}],  # 7 stores
            [{'count': 4}],  # 4 time segments
        ]
        
        result = self.db_setup.verify_database_structure()
        
        self.assertTrue(result)
    
    def test_verify_database_structure_missing_table(self):
        """Test database structure verification with missing table"""
        # Mock missing table
        self.mock_db_manager.fetch_one.side_effect = [
            {'count': 0},  # store table missing
        ]
        
        result = self.db_setup.verify_database_structure()
        
        self.assertFalse(result)

class TestDatabaseIntegration(unittest.TestCase):
    """Test database integration functions"""
    
    @patch('utils.database.DatabaseManager')
    @patch('utils.database.DatabaseConfig')
    def test_get_database_manager(self, mock_config_class, mock_manager_class):
        """Test database manager creation"""
        mock_config = MagicMock()
        mock_manager = MagicMock()
        mock_config_class.return_value = mock_config
        mock_manager_class.return_value = mock_manager
        
        result = get_database_manager(is_test=True)
        
        self.assertEqual(result, mock_manager)
        mock_config_class.assert_called_with(is_test=True)
        mock_manager_class.assert_called_with(mock_config)
    
    @patch('utils.database.DatabaseSetup')
    @patch('utils.database.get_database_manager')
    def test_setup_database_for_tests_success(self, mock_get_manager, mock_setup_class):
        """Test successful test database setup"""
        mock_manager = MagicMock()
        mock_setup = MagicMock()
        mock_setup.setup_test_database.return_value = True
        mock_get_manager.return_value = mock_manager
        mock_setup_class.return_value = mock_setup
        
        result = setup_database_for_tests()
        
        self.assertTrue(result)
        mock_get_manager.assert_called_with(is_test=True)
        mock_setup_class.assert_called_with(mock_manager)
    
    @patch('utils.database.get_database_manager')
    def test_verify_database_connection_success(self, mock_get_manager):
        """Test successful database connection verification"""
        mock_manager = MagicMock()
        mock_manager.test_connection.return_value = True
        mock_get_manager.return_value = mock_manager
        
        result = verify_database_connection(is_test=False)
        
        self.assertTrue(result)
        mock_get_manager.assert_called_with(is_test=False)

class TestDatabaseScriptIntegration(unittest.TestCase):
    """Test database integration with processing scripts"""
    
    def setUp(self):
        # Create sample Excel data for testing
        self.sample_daily_data = pd.DataFrame({
            '门店名称': ['加拿大一店', '加拿大二店'],
            '日期': [20250610, 20250610],
            '节假日': ['工作日', '工作日'],
            '营业桌数': [100, 80],
            '营业桌数(考核)': [95, 75],
            '翻台率(考核)': [4.2, 3.8],
            '营业收入(不含税)': [15000.50, 12000.25],
            '营业桌数(考核)(外卖)': [5, 3],
            '就餐人数': [380, 285],
            '优惠总金额(不含税)': [500.00, 300.00]
        })
        
        self.sample_time_data = pd.DataFrame({
            '门店名称': ['加拿大一店', '加拿大一店'],
            '日期': [20250610, 20250610],
            '分时段': ['08:00-13:59', '14:00-16:59'],
            '节假日': ['工作日', '工作日'],
            '营业桌数(考核)': [25, 20],
            '翻台率(考核)': [1.2, 0.8]
        })
    
    def test_daily_data_transformation(self):
        """Test daily data transformation for database insertion"""
        # This would test the transform_excel_data function from insert-data.py
        # Import would be done here in a real test
        pass
    
    def test_time_segment_data_transformation(self):
        """Test time segment data transformation for database insertion"""
        # This would test the transform_time_segment_data function from extract-time-segments.py
        # Import would be done here in a real test
        pass

if __name__ == '__main__':
    # Set up test environment variables if not already set
    test_env_vars = {
        'TEST_PG_HOST': 'localhost',
        'TEST_PG_PORT': '5432',
        'TEST_PG_USER': 'testuser',
        'TEST_PG_PASSWORD': 'testpass',
        'TEST_PG_DATABASE': 'testdb'
    }
    
    for var, value in test_env_vars.items():
        if not os.getenv(var):
            os.environ[var] = value
    
    unittest.main() 