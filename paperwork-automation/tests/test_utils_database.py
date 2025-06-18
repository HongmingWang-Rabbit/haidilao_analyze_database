#!/usr/bin/env python3
"""
Comprehensive tests for utils/database.py module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
from pathlib import Path
import os
import psycopg2
from psycopg2 import sql

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import DatabaseConfig, DatabaseManager, DatabaseSetup
from utils.database import get_database_manager, setup_database_for_tests, verify_database_connection


class TestDatabaseConfig(unittest.TestCase):
    """Test cases for DatabaseConfig class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Store original environment variables
        self.original_env = {}
        env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 
                   'TEST_DB_HOST', 'TEST_DB_PORT', 'TEST_DB_NAME', 'TEST_DB_USER', 'TEST_DB_PASSWORD']
        
        for var in env_vars:
            self.original_env[var] = os.environ.get(var)

    def tearDown(self):
        """Clean up after tests"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value

    def test_production_config_initialization(self):
        """Test production configuration initialization"""
        # Set up production environment variables
        os.environ.update({
            'DB_HOST': 'prod-host',
            'DB_PORT': '5432',
            'DB_NAME': 'prod_db',
            'DB_USER': 'prod_user',
            'DB_PASSWORD': 'prod_pass'
        })
        
        config = DatabaseConfig(is_test=False)
        
        self.assertEqual(config.host, 'prod-host')
        self.assertEqual(config.port, '5432')
        self.assertEqual(config.database, 'prod_db')
        self.assertEqual(config.user, 'prod_user')
        self.assertEqual(config.password, 'prod_pass')
        self.assertFalse(config.is_test)

    def test_test_config_initialization(self):
        """Test test configuration initialization"""
        # Set up test environment variables
        os.environ.update({
            'TEST_DB_HOST': 'test-host',
            'TEST_DB_PORT': '5433',
            'TEST_DB_NAME': 'test_db',
            'TEST_DB_USER': 'test_user',
            'TEST_DB_PASSWORD': 'test_pass'
        })
        
        config = DatabaseConfig(is_test=True)
        
        self.assertEqual(config.host, 'test-host')
        self.assertEqual(config.port, '5433')
        self.assertEqual(config.database, 'test_db')
        self.assertEqual(config.user, 'test_user')
        self.assertEqual(config.password, 'test_pass')
        self.assertTrue(config.is_test)

    def test_default_values(self):
        """Test default values when environment variables are not set"""
        # Clear environment variables
        for var in ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']:
            os.environ.pop(var, None)
        
        config = DatabaseConfig(is_test=False)
        
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, '5432')
        self.assertEqual(config.database, 'haidilao_db')
        self.assertEqual(config.user, 'postgres')
        self.assertEqual(config.password, '')

    def test_connection_string(self):
        """Test connection string generation"""
        os.environ.update({
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_pass'
        })
        
        config = DatabaseConfig(is_test=False)
        conn_str = config.connection_string()
        
        expected = "host=localhost port=5432 dbname=test_db user=test_user password=test_pass"
        self.assertEqual(conn_str, expected)

    def test_connection_string_with_empty_password(self):
        """Test connection string with empty password"""
        os.environ.update({
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': ''
        })
        
        config = DatabaseConfig(is_test=False)
        conn_str = config.connection_string()
        
        expected = "host=localhost port=5432 dbname=test_db user=test_user password="
        self.assertEqual(conn_str, expected)

    def test_str_representation(self):
        """Test string representation"""
        os.environ.update({
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'secret'
        })
        
        config = DatabaseConfig(is_test=False)
        str_repr = str(config)
        
        self.assertIn('localhost:5432/test_db', str_repr)
        self.assertIn('test_user', str_repr)
        self.assertNotIn('secret', str_repr)  # Password should be masked

    def test_test_config_fallback_to_production(self):
        """Test test config fallback to production values"""
        # Set only production environment variables
        os.environ.update({
            'DB_HOST': 'prod-host',
            'DB_PORT': '5432',
            'DB_NAME': 'prod_db',
            'DB_USER': 'prod_user',
            'DB_PASSWORD': 'prod_pass'
        })
        
        # Clear test environment variables
        for var in ['TEST_DB_HOST', 'TEST_DB_PORT', 'TEST_DB_NAME', 'TEST_DB_USER', 'TEST_DB_PASSWORD']:
            os.environ.pop(var, None)
        
        config = DatabaseConfig(is_test=True)
        
        # Should use production values as fallback
        self.assertEqual(config.host, 'prod-host')
        self.assertEqual(config.port, '5432')
        self.assertEqual(config.database, 'prod_db')
        self.assertEqual(config.user, 'prod_user')
        self.assertEqual(config.password, 'prod_pass')


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = DatabaseConfig(is_test=True)
        self.db_manager = DatabaseManager(self.config)

    def test_initialization(self):
        """Test DatabaseManager initialization"""
        self.assertEqual(self.db_manager.config, self.config)
        self.assertIsNone(self.db_manager._connection)

    @patch('utils.database.psycopg2.connect')
    def test_get_connection_success(self, mock_connect):
        """Test successful database connection"""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        connection = self.db_manager.get_connection()
        
        self.assertEqual(connection, mock_connection)
        mock_connect.assert_called_once_with(self.config.connection_string())

    @patch('utils.database.psycopg2.connect')
    def test_get_connection_failure(self, mock_connect):
        """Test database connection failure"""
        mock_connect.side_effect = psycopg2.Error("Connection failed")
        
        with self.assertRaises(psycopg2.Error):
            self.db_manager.get_connection()

    @patch('utils.database.psycopg2.connect')
    def test_get_connection_reuse(self, mock_connect):
        """Test connection reuse"""
        mock_connection = MagicMock()
        mock_connection.closed = 0  # Connection is open
        mock_connect.return_value = mock_connection
        
        # First call
        connection1 = self.db_manager.get_connection()
        
        # Second call should reuse the same connection
        connection2 = self.db_manager.get_connection()
        
        self.assertEqual(connection1, connection2)
        mock_connect.assert_called_once()  # Should only be called once

    @patch('utils.database.psycopg2.connect')
    def test_get_connection_recreate_closed(self, mock_connect):
        """Test connection recreation when closed"""
        mock_connection1 = MagicMock()
        mock_connection1.closed = 1  # Connection is closed
        mock_connection2 = MagicMock()
        mock_connection2.closed = 0  # Connection is open
        mock_connect.side_effect = [mock_connection1, mock_connection2]
        
        # First call
        connection1 = self.db_manager.get_connection()
        
        # Second call should create new connection since first is closed
        connection2 = self.db_manager.get_connection()
        
        self.assertEqual(connection1, mock_connection1)
        self.assertEqual(connection2, mock_connection2)
        self.assertEqual(mock_connect.call_count, 2)

    @patch('utils.database.psycopg2.connect')
    def test_test_connection_success(self, mock_connect):
        """Test successful connection test"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.test_connection()
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch('utils.database.psycopg2.connect')
    def test_test_connection_failure(self, mock_connect):
        """Test connection test failure"""
        mock_connect.side_effect = psycopg2.Error("Connection failed")
        
        result = self.db_manager.test_connection()
        
        self.assertFalse(result)

    @patch('utils.database.psycopg2.connect')
    @patch('builtins.open', new_callable=mock_open, read_data="SELECT 1; CREATE TABLE test();")
    @patch('os.path.exists')
    def test_execute_sql_file_success(self, mock_exists, mock_file, mock_connect):
        """Test successful SQL file execution"""
        mock_exists.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.execute_sql_file("test.sql")
        
        self.assertTrue(result)
        mock_file.assert_called_once_with("test.sql", 'r', encoding='utf-8')
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called_once()

    @patch('os.path.exists')
    def test_execute_sql_file_not_found(self, mock_exists):
        """Test SQL file execution with non-existent file"""
        mock_exists.return_value = False
        
        result = self.db_manager.execute_sql_file("nonexistent.sql")
        
        self.assertFalse(result)

    @patch('utils.database.psycopg2.connect')
    @patch('builtins.open', new_callable=mock_open, read_data="INVALID SQL;")
    @patch('os.path.exists')
    def test_execute_sql_file_sql_error(self, mock_exists, mock_file, mock_connect):
        """Test SQL file execution with SQL error"""
        mock_exists.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("SQL error")
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.execute_sql_file("test.sql")
        
        self.assertFalse(result)
        mock_connection.rollback.assert_called_once()

    @patch('utils.database.psycopg2.connect')
    def test_execute_sql_success(self, mock_connect):
        """Test successful SQL execution"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.execute_sql("SELECT 1", (1, 2))
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with("SELECT 1", (1, 2))
        mock_connection.commit.assert_called_once()

    @patch('utils.database.psycopg2.connect')
    def test_execute_sql_error(self, mock_connect):
        """Test SQL execution error"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("SQL error")
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.execute_sql("INVALID SQL")
        
        self.assertFalse(result)
        mock_connection.rollback.assert_called_once()

    @patch('utils.database.psycopg2.connect')
    def test_fetch_all_success(self, mock_connect):
        """Test successful fetch all"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.fetch_all("SELECT * FROM test", (1,))
        
        self.assertEqual(result, [{'id': 1, 'name': 'test'}])
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test", (1,))

    @patch('utils.database.psycopg2.connect')
    def test_fetch_all_error(self, mock_connect):
        """Test fetch all error"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("SQL error")
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.fetch_all("INVALID SQL")
        
        self.assertEqual(result, [])

    @patch('utils.database.psycopg2.connect')
    def test_fetch_one_success(self, mock_connect):
        """Test successful fetch one"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1, 'name': 'test'}
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.fetch_one("SELECT * FROM test WHERE id = %s", (1,))
        
        self.assertEqual(result, {'id': 1, 'name': 'test'})
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test WHERE id = %s", (1,))

    @patch('utils.database.psycopg2.connect')
    def test_fetch_one_error(self, mock_connect):
        """Test fetch one error"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("SQL error")
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.fetch_one("INVALID SQL")
        
        self.assertIsNone(result)

    @patch('utils.database.psycopg2.connect')
    def test_fetch_one_no_result(self, mock_connect):
        """Test fetch one with no result"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.fetch_one("SELECT * FROM test WHERE id = %s", (999,))
        
        self.assertIsNone(result)


class TestDatabaseSetup(unittest.TestCase):
    """Test cases for DatabaseSetup class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.setup = DatabaseSetup(self.mock_db_manager)

    def test_initialization(self):
        """Test DatabaseSetup initialization"""
        self.assertEqual(self.setup.db_manager, self.mock_db_manager)

    @patch('utils.database.Path.glob')
    def test_setup_test_database_success(self, mock_glob):
        """Test successful test database setup"""
        # Mock SQL files
        mock_files = [
            Mock(name='001_create_tables.sql'),
            Mock(name='002_insert_data.sql')
        ]
        mock_glob.return_value = mock_files
        
        # Mock successful execution
        self.mock_db_manager.execute_sql_file.return_value = True
        
        result = self.setup.setup_test_database()
        
        self.assertTrue(result)
        self.assertEqual(self.mock_db_manager.execute_sql_file.call_count, 2)

    @patch('utils.database.Path.glob')
    def test_setup_test_database_file_error(self, mock_glob):
        """Test test database setup with file execution error"""
        mock_files = [Mock(name='001_create_tables.sql')]
        mock_glob.return_value = mock_files
        
        # Mock failed execution
        self.mock_db_manager.execute_sql_file.return_value = False
        
        result = self.setup.setup_test_database()
        
        self.assertFalse(result)

    @patch('utils.database.Path.glob')
    def test_setup_test_database_no_files(self, mock_glob):
        """Test test database setup with no SQL files"""
        mock_glob.return_value = []
        
        result = self.setup.setup_test_database()
        
        self.assertTrue(result)  # Should succeed if no files to execute
        self.mock_db_manager.execute_sql_file.assert_not_called()

    @patch('utils.database.Path.glob')
    def test_setup_test_database_exception(self, mock_glob):
        """Test test database setup with exception"""
        mock_glob.side_effect = Exception("File system error")
        
        result = self.setup.setup_test_database()
        
        self.assertFalse(result)

    def test_verify_database_structure_success(self):
        """Test successful database structure verification"""
        # Mock table existence checks
        self.mock_db_manager.fetch_one.side_effect = [
            {'exists': True},  # stores table
            {'exists': True},  # daily_report table
            {'exists': True},  # time_segment_report table
            {'exists': True}   # monthly_targets table
        ]
        
        result = self.setup.verify_database_structure()
        
        self.assertTrue(result)
        self.assertEqual(self.mock_db_manager.fetch_one.call_count, 4)

    def test_verify_database_structure_missing_table(self):
        """Test database structure verification with missing table"""
        # Mock missing table
        self.mock_db_manager.fetch_one.side_effect = [
            {'exists': True},   # stores table
            {'exists': False},  # daily_report table missing
            {'exists': True},   # time_segment_report table
            {'exists': True}    # monthly_targets table
        ]
        
        result = self.setup.verify_database_structure()
        
        self.assertFalse(result)

    def test_verify_database_structure_error(self):
        """Test database structure verification with error"""
        self.mock_db_manager.fetch_one.side_effect = Exception("Database error")
        
        result = self.setup.verify_database_structure()
        
        self.assertFalse(result)

    def test_verify_database_structure_none_result(self):
        """Test database structure verification with None result"""
        self.mock_db_manager.fetch_one.return_value = None
        
        result = self.setup.verify_database_structure()
        
        self.assertFalse(result)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions"""
    
    @patch('utils.database.DatabaseManager')
    @patch('utils.database.DatabaseConfig')
    def test_get_database_manager(self, mock_config_class, mock_manager_class):
        """Test get_database_manager function"""
        mock_config = Mock()
        mock_manager = Mock()
        mock_config_class.return_value = mock_config
        mock_manager_class.return_value = mock_manager
        
        # Test production
        result = get_database_manager(is_test=False)
        
        self.assertEqual(result, mock_manager)
        mock_config_class.assert_called_once_with(is_test=False)
        mock_manager_class.assert_called_once_with(mock_config)
        
        # Reset mocks
        mock_config_class.reset_mock()
        mock_manager_class.reset_mock()
        
        # Test with test database
        result = get_database_manager(is_test=True)
        
        self.assertEqual(result, mock_manager)
        mock_config_class.assert_called_once_with(is_test=True)
        mock_manager_class.assert_called_once_with(mock_config)

    @patch('utils.database.DatabaseSetup')
    @patch('utils.database.get_database_manager')
    def test_setup_database_for_tests_success(self, mock_get_manager, mock_setup_class):
        """Test successful setup_database_for_tests"""
        mock_manager = Mock()
        mock_setup = Mock()
        mock_get_manager.return_value = mock_manager
        mock_setup_class.return_value = mock_setup
        mock_setup.setup_test_database.return_value = True
        
        result = setup_database_for_tests()
        
        self.assertTrue(result)
        mock_get_manager.assert_called_once_with(is_test=True)
        mock_setup_class.assert_called_once_with(mock_manager)
        mock_setup.setup_test_database.assert_called_once()

    @patch('utils.database.DatabaseSetup')
    @patch('utils.database.get_database_manager')
    def test_setup_database_for_tests_failure(self, mock_get_manager, mock_setup_class):
        """Test failed setup_database_for_tests"""
        mock_manager = Mock()
        mock_setup = Mock()
        mock_get_manager.return_value = mock_manager
        mock_setup_class.return_value = mock_setup
        mock_setup.setup_test_database.return_value = False
        
        result = setup_database_for_tests()
        
        self.assertFalse(result)

    @patch('utils.database.DatabaseSetup')
    @patch('utils.database.get_database_manager')
    def test_setup_database_for_tests_exception(self, mock_get_manager, mock_setup_class):
        """Test setup_database_for_tests with exception"""
        mock_get_manager.side_effect = Exception("Setup error")
        
        result = setup_database_for_tests()
        
        self.assertFalse(result)

    @patch('utils.database.get_database_manager')
    def test_verify_database_connection_success(self, mock_get_manager):
        """Test successful verify_database_connection"""
        mock_manager = Mock()
        mock_manager.test_connection.return_value = True
        mock_get_manager.return_value = mock_manager
        
        result = verify_database_connection(is_test=False)
        
        self.assertTrue(result)
        mock_get_manager.assert_called_once_with(is_test=False)
        mock_manager.test_connection.assert_called_once()

    @patch('utils.database.get_database_manager')
    def test_verify_database_connection_failure(self, mock_get_manager):
        """Test failed verify_database_connection"""
        mock_manager = Mock()
        mock_manager.test_connection.return_value = False
        mock_get_manager.return_value = mock_manager
        
        result = verify_database_connection(is_test=True)
        
        self.assertFalse(result)
        mock_get_manager.assert_called_once_with(is_test=True)

    @patch('utils.database.get_database_manager')
    def test_verify_database_connection_exception(self, mock_get_manager):
        """Test verify_database_connection with exception"""
        mock_get_manager.side_effect = Exception("Connection error")
        
        result = verify_database_connection()
        
        self.assertFalse(result)


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for database components"""
    
    def test_full_workflow_with_mocks(self):
        """Test complete workflow with mocked components"""
        # Create config
        with patch.dict(os.environ, {
            'TEST_DB_HOST': 'localhost',
            'TEST_DB_PORT': '5432',
            'TEST_DB_NAME': 'test_db',
            'TEST_DB_USER': 'test_user',
            'TEST_DB_PASSWORD': 'test_pass'
        }):
            config = DatabaseConfig(is_test=True)
            
            # Create manager with mocked connection
            with patch('utils.database.psycopg2.connect') as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_connection.cursor.return_value = mock_cursor
                mock_connect.return_value = mock_connection
                
                manager = DatabaseManager(config)
                
                # Test connection
                self.assertTrue(manager.test_connection())
                
                # Test SQL execution
                self.assertTrue(manager.execute_sql("SELECT 1"))
                
                # Test data fetching
                mock_cursor.fetchall.return_value = [{'id': 1}]
                result = manager.fetch_all("SELECT * FROM test")
                self.assertEqual(result, [{'id': 1}])

    def test_error_handling_chain(self):
        """Test error handling through the entire chain"""
        config = DatabaseConfig(is_test=True)
        
        # Test with connection that fails
        with patch('utils.database.psycopg2.connect') as mock_connect:
            mock_connect.side_effect = psycopg2.Error("Connection failed")
            
            manager = DatabaseManager(config)
            
            # All operations should handle the error gracefully
            self.assertFalse(manager.test_connection())
            self.assertFalse(manager.execute_sql("SELECT 1"))
            self.assertEqual(manager.fetch_all("SELECT 1"), [])
            self.assertIsNone(manager.fetch_one("SELECT 1"))

    def test_configuration_variations(self):
        """Test different configuration scenarios"""
        # Test with minimal environment
        with patch.dict(os.environ, {}, clear=True):
            config = DatabaseConfig(is_test=False)
            self.assertEqual(config.host, 'localhost')
            self.assertEqual(config.database, 'haidilao_db')
        
        # Test with partial environment
        with patch.dict(os.environ, {'DB_HOST': 'custom-host'}, clear=True):
            config = DatabaseConfig(is_test=False)
            self.assertEqual(config.host, 'custom-host')
            self.assertEqual(config.database, 'haidilao_db')  # Default


if __name__ == '__main__':
    unittest.main() 