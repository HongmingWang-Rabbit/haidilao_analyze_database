#!/usr/bin/env python3
"""
Comprehensive tests for lib/database_utils.py
Tests database operations that were consolidated from 50+ files.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import pandas as pd
from datetime import datetime
from contextlib import contextmanager

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from lib.database_utils import DatabaseOperations, CommonQueries


class TestDatabaseOperations(unittest.TestCase):
    """Test DatabaseOperations class functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock()
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        
        # Setup mock connection chain
        self.mock_db_manager.get_connection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        
        self.db_ops = DatabaseOperations(self.mock_db_manager)
        
    def test_initialization(self):
        """Test DatabaseOperations initialization"""
        self.assertEqual(self.db_ops.db_manager, self.mock_db_manager)
        self.assertIsNotNone(self.db_ops.logger)
        
    def test_get_connection_context_manager_success(self):
        """Test get_connection context manager success path"""
        # Mock connection as context manager
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        with self.db_ops.get_connection() as conn:
            self.assertEqual(conn, self.mock_connection)
            
        # Verify connection was closed
        self.mock_connection.close.assert_called_once()
        
    def test_get_connection_context_manager_exception(self):
        """Test get_connection context manager with exception"""
        # Mock connection as context manager that raises exception
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        with self.assertRaises(RuntimeError):
            with self.db_ops.get_connection() as conn:
                raise RuntimeError("Test exception")
                
        # Verify rollback and close were called
        self.mock_connection.rollback.assert_called_once()
        self.mock_connection.close.assert_called_once()
        
    def test_safe_insert_with_conflict_handling_success(self):
        """Test successful upsert operation"""
        # Setup mock for context manager behavior
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        test_data = {
            'material_id': 1500680,
            'material_name': '锅底材料',
            'price': 15.50
        }
        
        conflict_columns = ['material_id']
        
        result = self.db_ops.safe_insert_with_conflict_handling(
            'materials', test_data, conflict_columns
        )
        
        self.assertTrue(result)
        
        # Verify SQL was executed
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()
        
        # Check SQL structure
        executed_sql = self.mock_cursor.execute.call_args[0][0]
        self.assertIn('INSERT INTO materials', executed_sql)
        self.assertIn('ON CONFLICT', executed_sql)
        self.assertIn('DO UPDATE SET', executed_sql)
        
    def test_safe_insert_with_conflict_handling_empty_data(self):
        """Test upsert with empty data"""
        result = self.db_ops.safe_insert_with_conflict_handling(
            'test_table', {}, ['id']
        )
        
        self.assertTrue(result)
        self.mock_cursor.execute.assert_not_called()
        
    def test_safe_insert_with_conflict_handling_exception(self):
        """Test upsert with database exception"""
        # Setup mock to raise exception
        self.mock_db_manager.get_connection.return_value.__enter__.side_effect = Exception("DB Error")
        
        test_data = {'id': 1, 'name': 'test'}
        
        result = self.db_ops.safe_insert_with_conflict_handling(
            'test_table', test_data, ['id']
        )
        
        self.assertFalse(result)
        
    def test_batch_upsert_success(self):
        """Test successful batch upsert"""
        # Setup mock for context manager behavior
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        test_data = [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'},
            {'id': 3, 'name': 'Item 3'}
        ]
        
        result = self.db_ops.batch_upsert(
            'test_items', test_data, ['id'], batch_size=2
        )
        
        self.assertEqual(result, 3)
        
        # Should have 2 batch calls (2 items + 1 item)
        self.assertEqual(self.mock_cursor.executemany.call_count, 2)
        self.assertEqual(self.mock_connection.commit.call_count, 2)
        
    def test_batch_upsert_empty_data(self):
        """Test batch upsert with empty data"""
        result = self.db_ops.batch_upsert('test_table', [], ['id'])
        
        self.assertEqual(result, 0)
        self.mock_cursor.executemany.assert_not_called()
        
    def test_batch_upsert_with_exception(self):
        """Test batch upsert with partial failure"""
        # Setup mock to fail on second batch
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        # First call succeeds, second fails
        self.mock_cursor.executemany.side_effect = [None, Exception("Batch failed")]
        
        test_data = [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'},
            {'id': 3, 'name': 'Item 3'},
            {'id': 4, 'name': 'Item 4'}
        ]
        
        result = self.db_ops.batch_upsert(
            'test_items', test_data, ['id'], batch_size=2
        )
        
        # Should process first batch successfully
        self.assertEqual(result, 2)
        
    def test_get_or_create_lookup_existing_record(self):
        """Test get_or_create_lookup with existing record"""
        # Setup mock for context manager and query result
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        # Mock existing record found
        self.mock_cursor.fetchone.return_value = [123]
        
        lookup_data = {'name': 'Test Store', 'location': 'Canada'}
        
        result = self.db_ops.get_or_create_lookup(
            'stores', lookup_data, 'id'
        )
        
        self.assertEqual(result, 123)
        
        # Should execute SELECT but not INSERT
        execute_calls = self.mock_cursor.execute.call_args_list
        self.assertEqual(len(execute_calls), 1)
        
        select_sql = execute_calls[0][0][0]
        self.assertIn('SELECT id FROM stores', select_sql)
        
    def test_get_or_create_lookup_new_record(self):
        """Test get_or_create_lookup with new record creation"""
        # Setup mock for context manager
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        # Mock no existing record, then return new ID
        self.mock_cursor.fetchone.side_effect = [None, [456]]
        
        lookup_data = {'name': 'New Store', 'location': 'Canada'}
        
        result = self.db_ops.get_or_create_lookup(
            'stores', lookup_data, 'id'
        )
        
        self.assertEqual(result, 456)
        
        # Should execute SELECT then INSERT
        execute_calls = self.mock_cursor.execute.call_args_list
        self.assertEqual(len(execute_calls), 2)
        
        select_sql = execute_calls[0][0][0]
        insert_sql = execute_calls[1][0][0]
        
        self.assertIn('SELECT id FROM stores', select_sql)
        self.assertIn('INSERT INTO stores', insert_sql)
        self.assertIn('RETURNING id', insert_sql)
        
    def test_execute_query_to_dataframe_success(self):
        """Test successful query to DataFrame conversion"""
        # Mock pandas.read_sql_query
        expected_df = pd.DataFrame({
            'store_id': [1, 2, 3],
            'store_name': ['店1', '店2', '店3'],
            'revenue': [1000, 2000, 1500]
        })
        
        with patch('pandas.read_sql_query', return_value=expected_df) as mock_read_sql:
            # Setup connection mock
            self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
            self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
            
            query = "SELECT store_id, store_name, revenue FROM daily_report"
            params = ['2025-01-15']
            
            result_df = self.db_ops.execute_query_to_dataframe(query, params)
            
            self.assertIsNotNone(result_df)
            self.assertEqual(len(result_df), 3)
            self.assertIn('store_name', result_df.columns)
            
            # Verify pandas.read_sql_query was called correctly
            mock_read_sql.assert_called_once_with(query, self.mock_connection, params=params)
            
    def test_execute_query_to_dataframe_exception(self):
        """Test query to DataFrame with exception"""
        with patch('pandas.read_sql_query', side_effect=Exception("Query failed")):
            self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
            self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
            
            result_df = self.db_ops.execute_query_to_dataframe("SELECT * FROM test")
            
            self.assertIsNone(result_df)
            
    def test_get_store_data_summary(self):
        """Test get_store_data_summary method"""
        # Mock successful DataFrame response
        mock_df = pd.DataFrame({
            'store_name': ['加拿大一店', '加拿大二店', '加拿大三店'],
            'record_count': [31, 28, 30]
        })
        
        self.db_ops.execute_query_to_dataframe = Mock(return_value=mock_df)
        
        target_date = '2025-01-15'
        result = self.db_ops.get_store_data_summary(target_date)
        
        expected_result = {
            '加拿大一店': 31,
            '加拿大二店': 28,
            '加拿大三店': 30
        }
        
        self.assertEqual(result, expected_result)
        
        # Verify query was called with correct parameters
        self.db_ops.execute_query_to_dataframe.assert_called_once()
        call_args = self.db_ops.execute_query_to_dataframe.call_args
        self.assertIn(target_date, call_args[0][1])
        
    def test_get_store_data_summary_exception(self):
        """Test get_store_data_summary with exception"""
        self.db_ops.execute_query_to_dataframe = Mock(return_value=None)
        
        result = self.db_ops.get_store_data_summary('2025-01-15')
        
        self.assertEqual(result, {})
        
    def test_deactivate_previous_records_success(self):
        """Test successful record deactivation"""
        # Setup mock for context manager
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        # Mock 3 rows affected
        self.mock_cursor.rowcount = 3
        
        filter_conditions = {'material_id': 1500680, 'store_id': 1}
        
        result = self.db_ops.deactivate_previous_records(
            'material_price_history', filter_conditions
        )
        
        self.assertEqual(result, 3)
        
        # Verify SQL was executed
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()
        
        executed_sql = self.mock_cursor.execute.call_args[0][0]
        self.assertIn('UPDATE material_price_history', executed_sql)
        self.assertIn('SET is_active = false', executed_sql)
        
    def test_deactivate_previous_records_no_matches(self):
        """Test deactivation with no matching records"""
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        # Mock 0 rows affected
        self.mock_cursor.rowcount = 0
        
        filter_conditions = {'material_id': 9999999}
        
        result = self.db_ops.deactivate_previous_records(
            'material_price_history', filter_conditions
        )
        
        self.assertEqual(result, 0)
        
    def test_get_max_effective_date_success(self):
        """Test get_max_effective_date with results"""
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        # Mock date result
        expected_date = datetime(2025, 1, 15)
        self.mock_cursor.fetchone.return_value = [expected_date]
        
        filter_conditions = {'material_id': 1500680}
        
        result = self.db_ops.get_max_effective_date(
            'material_price_history', filter_conditions
        )
        
        self.assertEqual(result, expected_date)
        
        # Verify SQL
        executed_sql = self.mock_cursor.execute.call_args[0][0]
        self.assertIn('SELECT MAX(effective_date)', executed_sql)
        
    def test_get_max_effective_date_no_results(self):
        """Test get_max_effective_date with no results"""
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        
        # Mock no result
        self.mock_cursor.fetchone.return_value = [None]
        
        filter_conditions = {'material_id': 9999999}
        
        result = self.db_ops.get_max_effective_date(
            'material_price_history', filter_conditions
        )
        
        self.assertIsNone(result)
        
    def test_validate_data_completeness_complete(self):
        """Test data completeness validation with complete data"""
        # Mock DataFrame with all required stores
        mock_df = pd.DataFrame({
            'store_id': [1, 2, 3, 4, 5]
        })
        
        self.db_ops.execute_query_to_dataframe = Mock(return_value=mock_df)
        
        required_stores = [1, 2, 3, 4, 5]
        target_date = '2025-01-15'
        
        is_complete, missing_stores = self.db_ops.validate_data_completeness(
            'daily_report', required_stores, target_date
        )
        
        self.assertTrue(is_complete)
        self.assertEqual(missing_stores, [])
        
    def test_validate_data_completeness_incomplete(self):
        """Test data completeness validation with missing data"""
        # Mock DataFrame with some missing stores
        mock_df = pd.DataFrame({
            'store_id': [1, 3, 5]  # Missing stores 2 and 4
        })
        
        self.db_ops.execute_query_to_dataframe = Mock(return_value=mock_df)
        
        required_stores = [1, 2, 3, 4, 5]
        target_date = '2025-01-15'
        
        is_complete, missing_stores = self.db_ops.validate_data_completeness(
            'daily_report', required_stores, target_date
        )
        
        self.assertFalse(is_complete)
        self.assertEqual(set(missing_stores), {2, 4})
        
    def test_validate_data_completeness_exception(self):
        """Test data completeness validation with exception"""
        self.db_ops.execute_query_to_dataframe = Mock(return_value=None)
        
        required_stores = [1, 2, 3]
        
        is_complete, missing_stores = self.db_ops.validate_data_completeness(
            'daily_report', required_stores, '2025-01-15'
        )
        
        self.assertFalse(is_complete)
        self.assertEqual(missing_stores, required_stores)


class TestCommonQueries(unittest.TestCase):
    """Test CommonQueries utility class"""
    
    def test_get_store_mapping_query(self):
        """Test store mapping query"""
        query = CommonQueries.get_store_mapping_query()
        
        self.assertIsInstance(query, str)
        self.assertIn('SELECT id, store_name', query)
        self.assertIn('FROM store', query)
        self.assertIn('ORDER BY id', query)
        
    def test_get_material_types_query(self):
        """Test material types query"""
        query = CommonQueries.get_material_types_query()
        
        self.assertIsInstance(query, str)
        self.assertIn('SELECT id, type_name', query)
        self.assertIn('FROM material_type', query)
        
    def test_get_active_prices_query(self):
        """Test active prices query"""
        target_date = '2025-01-15'
        query = CommonQueries.get_active_prices_query(target_date)
        
        self.assertIsInstance(query, str)
        self.assertIn('material_price_history', query)
        self.assertIn('effective_date <=', query)
        self.assertIn('is_active = true', query)
        self.assertIn(target_date, query)
        
    def test_get_monthly_summary_query(self):
        """Test monthly summary query"""
        year = 2025
        month = 6
        query = CommonQueries.get_monthly_summary_query(year, month)
        
        self.assertIsInstance(query, str)
        self.assertIn('daily_report', query)
        self.assertIn('EXTRACT(YEAR', query)
        self.assertIn('EXTRACT(MONTH', query)
        self.assertIn(str(year), query)
        self.assertIn(str(month), query)


class TestDatabaseOperationsIntegration(unittest.TestCase):
    """Test integration scenarios for database operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock()
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        
        # Setup mock connection chain
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_db_manager.get_connection.return_value.__exit__.return_value = None
        self.mock_connection.cursor.return_value = self.mock_cursor
        
        self.db_ops = DatabaseOperations(self.mock_db_manager)
        
    def test_material_price_update_workflow(self):
        """Test complete material price update workflow"""
        # Simulate material price update process
        material_id = 1500680
        store_id = 1
        new_price = 25.50
        
        # Step 1: Deactivate previous prices
        self.mock_cursor.rowcount = 2  # 2 previous prices deactivated
        
        deactivated_count = self.db_ops.deactivate_previous_records(
            'material_price_history',
            {'material_id': material_id, 'store_id': store_id}
        )
        
        self.assertEqual(deactivated_count, 2)
        
        # Step 2: Insert new price
        new_price_data = {
            'material_id': material_id,
            'store_id': store_id,
            'price': new_price,
            'effective_date': '2025-01-15',
            'is_active': True
        }
        
        insert_success = self.db_ops.safe_insert_with_conflict_handling(
            'material_price_history',
            new_price_data,
            ['material_id', 'store_id', 'effective_date']
        )
        
        self.assertTrue(insert_success)
        
        # Verify both operations were called
        self.assertEqual(self.mock_cursor.execute.call_count, 2)
        self.assertEqual(self.mock_connection.commit.call_count, 2)
        
    def test_store_data_validation_workflow(self):
        """Test store data validation workflow"""
        target_date = '2025-01-15'
        required_stores = [1, 2, 3, 4, 5, 6, 7]  # All 7 Canadian stores
        
        # Mock store data summary
        store_summary = {
            '加拿大一店': 1,
            '加拿大二店': 1, 
            '加拿大三店': 1,
            '加拿大四店': 1,
            '加拿大五店': 1,
            '加拿大六店': 0,  # Missing data for store 6
            '加拿大七店': 1
        }
        
        self.db_ops.get_store_data_summary = Mock(return_value=store_summary)
        
        # Mock data completeness check
        mock_df = pd.DataFrame({
            'store_id': [1, 2, 3, 4, 5, 7]  # Store 6 missing
        })
        self.db_ops.execute_query_to_dataframe = Mock(return_value=mock_df)
        
        # Validate completeness
        is_complete, missing_stores = self.db_ops.validate_data_completeness(
            'daily_report', required_stores, target_date
        )
        
        self.assertFalse(is_complete)
        self.assertEqual(missing_stores, [6])
        
        # Get summary for context
        summary = self.db_ops.get_store_data_summary(target_date)
        self.assertEqual(summary['加拿大六店'], 0)  # Confirms store 6 has no data
        
    def test_batch_material_insertion_workflow(self):
        """Test batch material insertion workflow"""
        # Simulate extracting and inserting material data
        materials_data = []
        
        # Generate test material data
        for i in range(1, 151):  # 150 materials
            materials_data.append({
                'material_number': f'15006{i:02d}',
                'material_name': f'材料{i}',
                'material_type_id': (i % 11) + 1,  # Rotate through 11 material types
                'is_active': True
            })
            
        # Test batch insertion
        result_count = self.db_ops.batch_upsert(
            'materials',
            materials_data,
            ['material_number'],
            batch_size=50  # Process in batches of 50
        )
        
        self.assertEqual(result_count, 150)
        
        # Should have 3 batch calls (50 + 50 + 50)
        self.assertEqual(self.mock_cursor.executemany.call_count, 3)
        
        # Verify each batch had correct structure
        for call_args in self.mock_cursor.executemany.call_args_list:
            sql = call_args[0][0]
            self.assertIn('INSERT INTO materials', sql)
            self.assertIn('ON CONFLICT', sql)
            self.assertIn('material_number', sql)


if __name__ == '__main__':
    # Run all tests with detailed output
    unittest.main(verbosity=2)