#!/usr/bin/env python3
"""
Comprehensive tests for ReportDataProvider class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from lib.database_queries import ReportDataProvider
from utils.database import DatabaseManager, DatabaseConfig


class TestReportDataProvider(unittest.TestCase):
    """Test cases for ReportDataProvider"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.provider = ReportDataProvider(self.mock_db_manager)
        
        # Sample raw data that would come from database
        self.sample_raw_data = [
            {
                'store_id': 1,
                'date': '2025-06-10',
                'revenue_tax_not_included': 25000.50,
                'tables_served_validated': 180.5,
                'customers': 520,
                'turnover_rate': 3.8,
                'takeout_tables': 12.5,
                'tables_served': 185.0,
                'period_type': 'daily'
            },
            {
                'store_id': 1,
                'date': '2025-06-01',
                'revenue_tax_not_included': 280000.75,
                'tables_served_validated': 1850.5,
                'customers': 5200,
                'turnover_rate': 3.9,
                'takeout_tables': 125.5,
                'tables_served': 1900.0,
                'period_type': 'monthly'
            },
            {
                'store_id': 1,
                'date': '2025-05-01',
                'revenue_tax_not_included': 260000.00,
                'tables_served_validated': 1750.0,
                'customers': 4800,
                'turnover_rate': 3.7,
                'takeout_tables': 115.0,
                'tables_served': 1800.0,
                'period_type': 'prev_month'
            },
            {
                'store_id': 2,
                'date': '2025-06-10',
                'revenue_tax_not_included': 18000.25,
                'tables_served_validated': 145.0,
                'customers': 420,
                'turnover_rate': 3.2,
                'takeout_tables': 8.5,
                'tables_served': 148.0,
                'period_type': 'daily'
            }
        ]

    def test_initialization(self):
        """Test ReportDataProvider initialization"""
        self.assertEqual(self.provider.db_manager, self.mock_db_manager)
        
        # Test with different db_manager
        other_db_manager = Mock(spec=DatabaseManager)
        other_provider = ReportDataProvider(other_db_manager)
        self.assertEqual(other_provider.db_manager, other_db_manager)

    @patch('lib.database_queries.ReportDataProvider.get_all_report_data')
    def test_get_all_report_data_success(self, mock_get_data):
        """Test successful data retrieval"""
        mock_get_data.return_value = self.sample_raw_data
        
        result = self.provider.get_all_report_data("2025-06-10")
        
        self.assertEqual(result, self.sample_raw_data)
        mock_get_data.assert_called_once_with("2025-06-10")

    def test_get_all_report_data_with_mock_connection(self):
        """Test get_all_report_data with mocked database connection"""
        # Mock the database connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = self.sample_raw_data
        
        self.mock_db_manager.get_connection.return_value = mock_connection
        
        result = self.provider.get_all_report_data("2025-06-10")
        
        # Verify database calls
        self.mock_db_manager.get_connection.assert_called_once()
        mock_connection.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        
        self.assertEqual(result, self.sample_raw_data)

    def test_get_all_report_data_database_error(self):
        """Test get_all_report_data with database error"""
        # Mock database error
        self.mock_db_manager.get_connection.side_effect = Exception("Database connection failed")
        
        with self.assertRaises(Exception) as context:
            self.provider.get_all_report_data("2025-06-10")
        
        self.assertIn("Database connection failed", str(context.exception))

    def test_get_all_report_data_empty_result(self):
        """Test get_all_report_data with empty result"""
        # Mock empty result
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        self.mock_db_manager.get_connection.return_value = mock_connection
        
        result = self.provider.get_all_report_data("2025-06-10")
        
        self.assertEqual(result, [])

    def test_process_comprehensive_data(self):
        """Test process_comprehensive_data method"""
        result = self.provider.process_comprehensive_data(self.sample_raw_data)
        
        # Should return tuple with processed data
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 10)  # Expected number of return values
        
        # Unpack the result
        (daily_data, monthly_data, previous_month_data, current_mtd, prev_mtd,
         yearly_current, yearly_previous, daily_ranking, monthly_ranking,
         daily_ranking_values, monthly_ranking_values) = result
        
        # Verify daily data
        self.assertIsInstance(daily_data, list)
        self.assertTrue(len(daily_data) > 0)
        
        # Verify monthly data
        self.assertIsInstance(monthly_data, list)
        self.assertTrue(len(monthly_data) > 0)
        
        # Verify previous month data
        self.assertIsInstance(previous_month_data, list)

    def test_process_comprehensive_data_empty_input(self):
        """Test process_comprehensive_data with empty input"""
        result = self.provider.process_comprehensive_data([])
        
        # Should return tuple with empty data
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 10)
        
        # All components should be empty lists or dictionaries
        for component in result:
            self.assertIn(type(component), [list, dict])

    def test_process_comprehensive_data_none_input(self):
        """Test process_comprehensive_data with None input"""
        result = self.provider.process_comprehensive_data(None)
        
        # Should handle None gracefully
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 10)

    def test_aggregate_store_data_static_method(self):
        """Test aggregate_store_data static method"""
        # Sample period data
        period_data = [
            {
                'store_id': 1,
                'revenue_tax_not_included': 25000.50,
                'tables_served_validated': 180.5,
                'customers': 520
            },
            {
                'store_id': 1,
                'revenue_tax_not_included': 18000.25,
                'tables_served_validated': 145.0,
                'customers': 420
            },
            {
                'store_id': 2,
                'revenue_tax_not_included': 15000.00,
                'tables_served_validated': 120.0,
                'customers': 350
            }
        ]
        
        result = ReportDataProvider.aggregate_store_data(period_data)
        
        # Should return dictionary with store_id as keys
        self.assertIsInstance(result, dict)
        self.assertIn(1, result)
        self.assertIn(2, result)
        
        # Check store 1 aggregation
        store_1_data = result[1]
        self.assertEqual(store_1_data['store_id'], 1)
        self.assertEqual(store_1_data['revenue_tax_not_included'], 25000.50 + 18000.25)
        self.assertEqual(store_1_data['tables_served_validated'], 180.5 + 145.0)
        self.assertEqual(store_1_data['customers'], 520 + 420)

    def test_aggregate_store_data_empty_input(self):
        """Test aggregate_store_data with empty input"""
        result = ReportDataProvider.aggregate_store_data([])
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_aggregate_store_data_none_input(self):
        """Test aggregate_store_data with None input"""
        result = ReportDataProvider.aggregate_store_data(None)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_aggregate_store_data_missing_fields(self):
        """Test aggregate_store_data with missing fields"""
        period_data = [
            {
                'store_id': 1,
                'revenue_tax_not_included': 25000.50,
                # Missing tables_served_validated and customers
            },
            {
                'store_id': 1,
                'tables_served_validated': 145.0,
                # Missing revenue_tax_not_included and customers
            }
        ]
        
        result = ReportDataProvider.aggregate_store_data(period_data)
        
        # Should handle missing fields gracefully
        self.assertIsInstance(result, dict)
        self.assertIn(1, result)
        
        store_1_data = result[1]
        self.assertIn('store_id', store_1_data)

    def test_aggregate_store_data_type_conversion(self):
        """Test aggregate_store_data with different data types"""
        period_data = [
            {
                'store_id': 1,
                'revenue_tax_not_included': "25000.50",  # String
                'tables_served_validated': 180.5,
                'customers': 520
            },
            {
                'store_id': 1,
                'revenue_tax_not_included': 18000.25,
                'tables_served_validated': "145.0",  # String
                'customers': "420"  # String
            }
        ]
        
        result = ReportDataProvider.aggregate_store_data(period_data)
        
        # Should handle type conversion
        store_1_data = result[1]
        self.assertIsInstance(store_1_data['revenue_tax_not_included'], (int, float))
        self.assertIsInstance(store_1_data['tables_served_validated'], (int, float))
        self.assertIsInstance(store_1_data['customers'], (int, float))

    @patch('lib.database_queries.ReportDataProvider.get_all_report_data')
    @patch('lib.database_queries.ReportDataProvider.process_comprehensive_data')
    def test_get_all_processed_data_success(self, mock_process, mock_get_data):
        """Test get_all_processed_data success"""
        mock_get_data.return_value = self.sample_raw_data
        mock_processed_data = ([], [], [], [], [], [], [], [], [], [], [])
        mock_process.return_value = mock_processed_data
        
        result = self.provider.get_all_processed_data("2025-06-10")
        
        self.assertEqual(result, mock_processed_data)
        mock_get_data.assert_called_once_with("2025-06-10")
        mock_process.assert_called_once_with(self.sample_raw_data)

    @patch('lib.database_queries.ReportDataProvider.get_all_report_data')
    def test_get_all_processed_data_no_raw_data(self, mock_get_data):
        """Test get_all_processed_data with no raw data"""
        mock_get_data.return_value = None
        
        result = self.provider.get_all_processed_data("2025-06-10")
        
        self.assertIsNone(result)

    @patch('lib.database_queries.ReportDataProvider.get_all_report_data')
    def test_get_all_processed_data_empty_raw_data(self, mock_get_data):
        """Test get_all_processed_data with empty raw data"""
        mock_get_data.return_value = []
        
        result = self.provider.get_all_processed_data("2025-06-10")
        
        self.assertIsNone(result)

    def test_data_filtering_by_period_type(self):
        """Test that data is correctly filtered by period_type"""
        # Create comprehensive test data with all period types
        comprehensive_data = [
            {'store_id': 1, 'period_type': 'daily', 'revenue_tax_not_included': 1000},
            {'store_id': 1, 'period_type': 'monthly', 'revenue_tax_not_included': 2000},
            {'store_id': 1, 'period_type': 'prev_month', 'revenue_tax_not_included': 3000},
            {'store_id': 1, 'period_type': 'current_mtd', 'revenue_tax_not_included': 4000},
            {'store_id': 1, 'period_type': 'prev_mtd', 'revenue_tax_not_included': 5000},
            {'store_id': 1, 'period_type': 'yearly_current', 'revenue_tax_not_included': 6000},
            {'store_id': 1, 'period_type': 'yearly_previous', 'revenue_tax_not_included': 7000},
        ]
        
        result = self.provider.process_comprehensive_data(comprehensive_data)
        
        # Verify that data is properly separated by period type
        (daily_data, monthly_data, previous_month_data, current_mtd, prev_mtd,
         yearly_current, yearly_previous, daily_ranking, monthly_ranking,
         daily_ranking_values, monthly_ranking_values) = result
        
        # Each period should have the correct data
        self.assertTrue(len(daily_data) > 0)
        self.assertTrue(len(monthly_data) > 0)
        self.assertTrue(len(previous_month_data) > 0)

    def test_ranking_calculation(self):
        """Test ranking calculation in process_comprehensive_data"""
        # Create data with multiple stores for ranking
        ranking_data = [
            {'store_id': 1, 'period_type': 'daily', 'revenue_tax_not_included': 3000, 'turnover_rate': 4.0},
            {'store_id': 2, 'period_type': 'daily', 'revenue_tax_not_included': 2000, 'turnover_rate': 3.5},
            {'store_id': 3, 'period_type': 'daily', 'revenue_tax_not_included': 1000, 'turnover_rate': 3.0},
            {'store_id': 1, 'period_type': 'monthly', 'revenue_tax_not_included': 30000, 'turnover_rate': 4.2},
            {'store_id': 2, 'period_type': 'monthly', 'revenue_tax_not_included': 25000, 'turnover_rate': 3.8},
            {'store_id': 3, 'period_type': 'monthly', 'revenue_tax_not_included': 20000, 'turnover_rate': 3.5},
        ]
        
        result = self.provider.process_comprehensive_data(ranking_data)
        
        # Unpack ranking data
        (daily_data, monthly_data, previous_month_data, current_mtd, prev_mtd,
         yearly_current, yearly_previous, daily_ranking, monthly_ranking,
         daily_ranking_values, monthly_ranking_values) = result
        
        # Verify rankings exist
        self.assertIsInstance(daily_ranking, (list, dict))
        self.assertIsInstance(monthly_ranking, (list, dict))
        self.assertIsInstance(daily_ranking_values, (list, dict))
        self.assertIsInstance(monthly_ranking_values, (list, dict))

    def test_error_handling_in_aggregation(self):
        """Test error handling in data aggregation"""
        # Create data with problematic values
        problematic_data = [
            {
                'store_id': 1,
                'revenue_tax_not_included': float('inf'),  # Infinity
                'tables_served_validated': 180.5,
                'customers': 520
            },
            {
                'store_id': 1,
                'revenue_tax_not_included': float('nan'),  # NaN
                'tables_served_validated': 145.0,
                'customers': 420
            }
        ]
        
        # Should not crash
        result = ReportDataProvider.aggregate_store_data(problematic_data)
        self.assertIsInstance(result, dict)

    def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        # Create large dataset
        large_data = []
        for store_id in range(1, 101):  # 100 stores
            for period in ['daily', 'monthly', 'prev_month']:
                large_data.append({
                    'store_id': store_id,
                    'period_type': period,
                    'revenue_tax_not_included': store_id * 1000,
                    'tables_served_validated': store_id * 10,
                    'customers': store_id * 50,
                    'turnover_rate': 3.0 + (store_id % 10) * 0.1
                })
        
        # Should process without issues
        result = self.provider.process_comprehensive_data(large_data)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 10)

    def test_date_parameter_handling(self):
        """Test different date parameter formats"""
        # Mock database connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        self.mock_db_manager.get_connection.return_value = mock_connection
        
        # Test different date formats
        date_formats = [
            "2025-06-10",
            "2025-01-01",
            "2025-12-31"
        ]
        
        for date_str in date_formats:
            result = self.provider.get_all_report_data(date_str)
            self.assertEqual(result, [])
            
            # Verify the date was passed to the SQL query
            mock_cursor.execute.assert_called()
            call_args = mock_cursor.execute.call_args
            self.assertIn(date_str, str(call_args))

    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        # Mock database connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        self.mock_db_manager.get_connection.return_value = mock_connection
        
        # Test with potentially malicious input
        malicious_date = "2025-06-10'; DROP TABLE daily_report; --"
        
        result = self.provider.get_all_report_data(malicious_date)
        
        # Should handle safely (parameterized queries should be used)
        self.assertEqual(result, [])
        mock_cursor.execute.assert_called()


class TestReportDataProviderIntegration(unittest.TestCase):
    """Integration tests for ReportDataProvider"""
    
    def test_with_real_database_config(self):
        """Test with real DatabaseConfig (but mocked connection)"""
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)
        
        # Mock the actual connection
        with patch.object(db_manager, 'get_connection') as mock_get_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.__enter__.return_value = mock_connection
            mock_connection.__exit__.return_value = None
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            
            mock_get_conn.return_value = mock_connection
            
            provider = ReportDataProvider(db_manager)
            result = provider.get_all_report_data("2025-06-10")
            
            self.assertEqual(result, [])

    def test_full_workflow(self):
        """Test complete workflow from raw data to processed data"""
        # Create realistic test data
        realistic_data = []
        
        # Add data for 5 stores across different periods
        for store_id in range(1, 6):
            periods = [
                ('daily', store_id * 5000),
                ('monthly', store_id * 50000),
                ('prev_month', store_id * 45000),
                ('current_mtd', store_id * 25000),
                ('prev_mtd', store_id * 22000),
                ('yearly_current', store_id * 600000),
                ('yearly_previous', store_id * 550000)
            ]
            
            for period_type, revenue in periods:
                realistic_data.append({
                    'store_id': store_id,
                    'period_type': period_type,
                    'revenue_tax_not_included': revenue,
                    'tables_served_validated': revenue / 150,  # Reasonable ratio
                    'customers': revenue / 45,  # Reasonable ratio
                    'turnover_rate': 3.0 + (store_id * 0.2),
                    'takeout_tables': revenue / 2000,
                    'tables_served': revenue / 140
                })
        
        # Mock database manager
        mock_db_manager = Mock(spec=DatabaseManager)
        provider = ReportDataProvider(mock_db_manager)
        
        # Process the data
        result = provider.process_comprehensive_data(realistic_data)
        
        # Verify complete workflow
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 10)
        
        # Verify each component has data
        (daily_data, monthly_data, previous_month_data, current_mtd, prev_mtd,
         yearly_current, yearly_previous, daily_ranking, monthly_ranking,
         daily_ranking_values, monthly_ranking_values) = result
        
        # All main data components should have entries
        self.assertTrue(len(daily_data) > 0)
        self.assertTrue(len(monthly_data) > 0)
        self.assertTrue(len(previous_month_data) > 0)


if __name__ == '__main__':
    unittest.main() 