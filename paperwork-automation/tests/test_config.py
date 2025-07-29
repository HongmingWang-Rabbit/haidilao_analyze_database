#!/usr/bin/env python3
"""
Comprehensive tests for lib/config.py
Tests all configuration constants that were consolidated from scattered files.
"""

import unittest
from pathlib import Path
from datetime import datetime

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from lib.config import (
    # Store configuration
    STORE_NAME_MAPPING, STORE_ID_TO_NAME_MAPPING, VALID_STORE_NAMES, STORE_IDS,
    
    # Time configuration
    TIME_SEGMENTS, TIME_SEGMENT_DISPLAY_NAMES, DEFAULT_DATE_FORMAT, 
    EXCEL_DATE_FORMAT, DISPLAY_DATE_FORMAT, HOLIDAY_INDICATORS,
    
    # Database configuration
    DATABASE_CONFIG, DATABASE_TIMEOUT, QUERY_TIMEOUT, CONNECTION_POOL_SIZE,
    DEFAULT_BATCH_SIZE, EXCEL_CHUNK_SIZE,
    
    # Excel configuration
    EXCEL_COLUMN_MAPPINGS, SHEET_NAME_PATTERNS,
    
    # Material configuration
    MATERIAL_TYPES, MATERIAL_CHILD_TYPES,
    
    # Discount configuration
    DISCOUNT_TYPES,
    
    # Report configuration
    REPORT_WORKSHEET_NAMES, WORKSHEET_COLUMN_WIDTHS, EXCEL_FORMATS,
    
    # File path configuration
    DIRECTORIES, FILE_NAMING_PATTERNS,
    
    # Validation configuration
    VALIDATION_THRESHOLDS, DATA_COMPLETENESS_THRESHOLDS,
    
    # Logging configuration
    LOGGING_CONFIG, LOG_FILE_PATTERN,
    
    # Web scraping configuration
    QBI_CONFIG, BROWSER_CONFIG,
    
    # Performance configuration
    PERFORMANCE_TARGETS, MEMORY_LIMITS,
    
    # Error handling configuration
    RETRY_CONFIG, ERROR_MESSAGES
)


class TestStoreConfiguration(unittest.TestCase):
    """Test store-related configuration constants"""
    
    def test_store_name_mapping_completeness(self):
        """Test that store name mapping contains all expected stores"""
        expected_stores = [
            '加拿大一店', '加拿大二店', '加拿大三店', '加拿大四店',
            '加拿大五店', '加拿大六店', '加拿大七店'
        ]
        
        self.assertEqual(len(STORE_NAME_MAPPING), 7)
        
        for store_name in expected_stores:
            self.assertIn(store_name, STORE_NAME_MAPPING)
            
        # Verify store IDs are sequential 1-7
        expected_ids = set(range(1, 8))
        actual_ids = set(STORE_NAME_MAPPING.values())
        self.assertEqual(actual_ids, expected_ids)
        
    def test_store_id_to_name_mapping_consistency(self):
        """Test that reverse mapping is consistent with forward mapping"""
        self.assertEqual(len(STORE_ID_TO_NAME_MAPPING), len(STORE_NAME_MAPPING))
        
        for name, store_id in STORE_NAME_MAPPING.items():
            self.assertEqual(STORE_ID_TO_NAME_MAPPING[store_id], name)
            
        for store_id, name in STORE_ID_TO_NAME_MAPPING.items():
            self.assertEqual(STORE_NAME_MAPPING[name], store_id)
            
    def test_valid_store_names_list(self):
        """Test that valid store names list matches mapping keys"""
        mapping_keys = set(STORE_NAME_MAPPING.keys())
        valid_names_set = set(VALID_STORE_NAMES)
        
        self.assertEqual(mapping_keys, valid_names_set)
        
    def test_store_ids_list(self):
        """Test that store IDs list is correct"""
        expected_ids = list(range(1, 8))
        self.assertEqual(STORE_IDS, expected_ids)
        self.assertEqual(len(STORE_IDS), 7)


class TestTimeConfiguration(unittest.TestCase):
    """Test time-related configuration constants"""
    
    def test_time_segments_completeness(self):
        """Test that all expected time segments are defined"""
        expected_segments = [
            "08:00-13:59",   # Morning/Lunch
            "14:00-16:59",   # Afternoon  
            "17:00-21:59",   # Evening/Dinner
            "22:00-(次)07:59" # Late night
        ]
        
        self.assertEqual(len(TIME_SEGMENTS), 4)
        self.assertEqual(TIME_SEGMENTS, expected_segments)
        
    def test_time_segment_display_names(self):
        """Test that display names exist for all time segments"""
        for segment in TIME_SEGMENTS:
            self.assertIn(segment, TIME_SEGMENT_DISPLAY_NAMES)
            self.assertIsInstance(TIME_SEGMENT_DISPLAY_NAMES[segment], str)
            self.assertTrue(len(TIME_SEGMENT_DISPLAY_NAMES[segment]) > 0)
            
    def test_date_formats(self):
        """Test that date formats are valid"""
        # Test DEFAULT_DATE_FORMAT
        test_date = datetime(2025, 6, 15)
        formatted = test_date.strftime(DEFAULT_DATE_FORMAT)
        self.assertEqual(formatted, '2025-06-15')
        
        # Test EXCEL_DATE_FORMAT  
        excel_formatted = test_date.strftime(EXCEL_DATE_FORMAT)
        self.assertEqual(excel_formatted, '20250615')
        
        # Test DISPLAY_DATE_FORMAT
        display_formatted = test_date.strftime(DISPLAY_DATE_FORMAT)
        self.assertEqual(display_formatted, '2025年06月15日')
        
    def test_holiday_indicators(self):
        """Test holiday indicator constants"""
        self.assertIn('WORKDAY', HOLIDAY_INDICATORS)
        self.assertIn('HOLIDAY', HOLIDAY_INDICATORS)
        
        self.assertEqual(HOLIDAY_INDICATORS['WORKDAY'], '工作日')
        self.assertEqual(HOLIDAY_INDICATORS['HOLIDAY'], '节假日')


class TestDatabaseConfiguration(unittest.TestCase):
    """Test database-related configuration constants"""
    
    def test_database_config_structure(self):
        """Test that database config contains required keys"""
        required_keys = ['host', 'user', 'password', 'database', 'port']
        
        for key in required_keys:
            self.assertIn(key, DATABASE_CONFIG)
            
        # Test specific values
        self.assertEqual(DATABASE_CONFIG['host'], 'localhost')
        self.assertEqual(DATABASE_CONFIG['user'], 'hongming')
        self.assertEqual(DATABASE_CONFIG['database'], 'haidilao-paperwork')
        self.assertEqual(DATABASE_CONFIG['port'], 5432)
        
    def test_database_timeouts(self):
        """Test database timeout configurations"""
        self.assertIsInstance(DATABASE_TIMEOUT, int)
        self.assertIsInstance(QUERY_TIMEOUT, int)
        self.assertIsInstance(CONNECTION_POOL_SIZE, int)
        
        self.assertGreater(DATABASE_TIMEOUT, 0)
        self.assertGreater(QUERY_TIMEOUT, DATABASE_TIMEOUT)  # Query timeout should be longer
        self.assertGreater(CONNECTION_POOL_SIZE, 0)
        
    def test_batch_sizes(self):
        """Test batch processing configurations"""
        self.assertIsInstance(DEFAULT_BATCH_SIZE, int)
        self.assertIsInstance(EXCEL_CHUNK_SIZE, int)
        
        self.assertGreater(DEFAULT_BATCH_SIZE, 0)
        self.assertGreater(EXCEL_CHUNK_SIZE, 0)


class TestExcelConfiguration(unittest.TestCase):
    """Test Excel processing configuration constants"""
    
    def test_excel_column_mappings_structure(self):
        """Test Excel column mappings contain required report types"""
        required_report_types = [
            'daily_reports', 'time_segments', 'material_details', 'dish_sales'
        ]
        
        for report_type in required_report_types:
            self.assertIn(report_type, EXCEL_COLUMN_MAPPINGS)
            self.assertIn('required_columns', EXCEL_COLUMN_MAPPINGS[report_type])
            self.assertIsInstance(EXCEL_COLUMN_MAPPINGS[report_type]['required_columns'], list)
            
    def test_daily_reports_columns(self):
        """Test daily reports required columns"""
        daily_columns = EXCEL_COLUMN_MAPPINGS['daily_reports']['required_columns']
        
        essential_columns = [
            '门店名称', '日期', '节假日', '营业桌数', '营业收入(不含税)'
        ]
        
        for column in essential_columns:
            self.assertIn(column, daily_columns)
            
    def test_sheet_name_patterns(self):
        """Test sheet name patterns"""
        expected_patterns = [
            'daily_basic', 'time_segment_basic', 'material_export',
            'dish_material_usage', 'monthly_dish_sales', 'inventory_calculation'
        ]
        
        for pattern in expected_patterns:
            self.assertIn(pattern, SHEET_NAME_PATTERNS)
            self.assertIsInstance(SHEET_NAME_PATTERNS[pattern], str)


class TestMaterialConfiguration(unittest.TestCase):
    """Test material type configuration constants"""
    
    def test_material_types_completeness(self):
        """Test that all material types are defined"""
        # Should have 11 material types based on documentation
        self.assertEqual(len(MATERIAL_TYPES), 11)
        
        # Test that all IDs are sequential from 1-11
        expected_ids = set(range(1, 12))
        actual_ids = set(MATERIAL_TYPES.keys())
        self.assertEqual(actual_ids, expected_ids)
        
        # Test that all values are strings and not empty
        for type_id, type_name in MATERIAL_TYPES.items():
            self.assertIsInstance(type_name, str)
            self.assertTrue(len(type_name) > 0)
            self.assertTrue(type_name.startswith('成本-'))
            
    def test_material_child_types_structure(self):
        """Test material child types structure"""
        # Should have 6 child types based on documentation
        self.assertEqual(len(MATERIAL_CHILD_TYPES), 6)
        
        # All child type IDs should exist in main types
        for child_id in MATERIAL_CHILD_TYPES.keys():
            self.assertIn(child_id, MATERIAL_TYPES)
            
        # Child type names should match main type names
        for child_id, child_name in MATERIAL_CHILD_TYPES.items():
            self.assertEqual(child_name, MATERIAL_TYPES[child_id])


class TestDiscountConfiguration(unittest.TestCase):
    """Test discount analysis configuration"""
    
    def test_discount_types_structure(self):
        """Test discount types structure"""
        expected_discount_types = [
            '会员折扣', '生日优惠', '节日优惠', '促销活动', '团购优惠', '其他优惠'
        ]
        
        for discount_type in expected_discount_types:
            self.assertIn(discount_type, DISCOUNT_TYPES)
            self.assertIsInstance(DISCOUNT_TYPES[discount_type], str)


class TestReportConfiguration(unittest.TestCase):
    """Test report generation configuration"""
    
    def test_report_worksheet_names(self):
        """Test report worksheet names"""
        expected_worksheets = [
            'monthly_comparison', 'yearly_comparison', 'yearly_daily_comparison',
            'time_segment', 'business_insight', 'daily_store_tracking'
        ]
        
        for worksheet in expected_worksheets:
            self.assertIn(worksheet, REPORT_WORKSHEET_NAMES)
            self.assertIsInstance(REPORT_WORKSHEET_NAMES[worksheet], str)
            
    def test_worksheet_column_widths(self):
        """Test worksheet column width configurations"""
        width_types = ['standard', 'wide', 'narrow']
        
        for width_type in width_types:
            self.assertIn(width_type, WORKSHEET_COLUMN_WIDTHS)
            widths = WORKSHEET_COLUMN_WIDTHS[width_type]
            self.assertIsInstance(widths, list)
            self.assertTrue(all(isinstance(w, int) and w > 0 for w in widths))
            
    def test_excel_formats(self):
        """Test Excel format strings"""
        expected_formats = [
            'percentage', 'currency_cad', 'currency_usd', 'integer', 'decimal_2'
        ]
        
        for format_type in expected_formats:
            self.assertIn(format_type, EXCEL_FORMATS)
            format_string = EXCEL_FORMATS[format_type]
            self.assertIsInstance(format_string, str)
            self.assertTrue(len(format_string) > 0)


class TestFilePathConfiguration(unittest.TestCase):
    """Test file path configuration"""
    
    def test_directories_structure(self):
        """Test directories configuration"""
        expected_dirs = [
            'output', 'input', 'scripts', 'lib', 'tests', 'utils', 'sql'
        ]
        
        for dir_name in expected_dirs:
            self.assertIn(dir_name, DIRECTORIES)
            self.assertIsInstance(DIRECTORIES[dir_name], Path)
            
    def test_file_naming_patterns(self):
        """Test file naming patterns"""
        expected_patterns = [
            'database_report', 'gross_margin_report', 
            'monthly_material_report', 'sql_output'
        ]
        
        for pattern_name in expected_patterns:
            self.assertIn(pattern_name, FILE_NAMING_PATTERNS)
            pattern = FILE_NAMING_PATTERNS[pattern_name]
            self.assertIsInstance(pattern, str)
            self.assertIn('{date}', pattern)


class TestValidationConfiguration(unittest.TestCase):
    """Test validation configuration"""
    
    def test_validation_thresholds(self):
        """Test validation threshold values"""
        required_thresholds = [
            'max_table_count', 'max_turnover_rate', 'min_revenue',
            'max_revenue', 'max_discount_percentage'
        ]
        
        for threshold in required_thresholds:
            self.assertIn(threshold, VALIDATION_THRESHOLDS)
            value = VALIDATION_THRESHOLDS[threshold]
            self.assertIsInstance(value, (int, float))
            
        # Test specific threshold logic
        self.assertGreater(VALIDATION_THRESHOLDS['max_table_count'], 0)
        self.assertGreater(VALIDATION_THRESHOLDS['max_turnover_rate'], 0)
        self.assertGreaterEqual(VALIDATION_THRESHOLDS['min_revenue'], 0)
        self.assertLessEqual(VALIDATION_THRESHOLDS['max_discount_percentage'], 1.0)
        
    def test_data_completeness_thresholds(self):
        """Test data completeness thresholds"""
        required_completeness = [
            'min_stores_present', 'min_days_per_month', 'min_time_segments'
        ]
        
        for threshold in required_completeness:
            self.assertIn(threshold, DATA_COMPLETENESS_THRESHOLDS)
            value = DATA_COMPLETENESS_THRESHOLDS[threshold]
            self.assertIsInstance(value, int)
            self.assertGreater(value, 0)
            
        # Test specific values
        self.assertEqual(DATA_COMPLETENESS_THRESHOLDS['min_time_segments'], 4)
        self.assertLessEqual(DATA_COMPLETENESS_THRESHOLDS['min_stores_present'], 7)


class TestLoggingConfiguration(unittest.TestCase):
    """Test logging configuration"""
    
    def test_logging_config_structure(self):
        """Test logging configuration structure"""
        required_keys = ['level', 'format', 'date_format']
        
        for key in required_keys:
            self.assertIn(key, LOGGING_CONFIG)
            self.assertIsInstance(LOGGING_CONFIG[key], str)
            
        # Test log file pattern
        self.assertIsInstance(LOG_FILE_PATTERN, str)
        self.assertIn('{date}', LOG_FILE_PATTERN)


class TestWebScrapingConfiguration(unittest.TestCase):
    """Test web scraping configuration"""
    
    def test_qbi_config_structure(self):
        """Test QBI configuration structure"""
        required_keys = ['base_url', 'login_timeout', 'download_timeout', 'headless_mode']
        
        for key in required_keys:
            self.assertIn(key, QBI_CONFIG)
            
        # Test specific values
        self.assertTrue(QBI_CONFIG['base_url'].startswith('https://'))
        self.assertIsInstance(QBI_CONFIG['login_timeout'], int)
        self.assertIsInstance(QBI_CONFIG['headless_mode'], bool)
        
    def test_browser_config_structure(self):
        """Test browser configuration structure"""
        required_keys = ['window_size', 'download_dir', 'implicit_wait']
        
        for key in required_keys:
            self.assertIn(key, BROWSER_CONFIG)
            
        # Test window size is tuple
        self.assertIsInstance(BROWSER_CONFIG['window_size'], tuple)
        self.assertEqual(len(BROWSER_CONFIG['window_size']), 2)


class TestPerformanceConfiguration(unittest.TestCase):
    """Test performance configuration"""
    
    def test_performance_targets(self):
        """Test performance target values"""
        required_targets = [
            'core_operation_max_time', 'test_suite_max_time',
            'report_generation_max_time', 'database_query_max_time'
        ]
        
        for target in required_targets:
            self.assertIn(target, PERFORMANCE_TARGETS)
            value = PERFORMANCE_TARGETS[target]
            self.assertIsInstance(value, (int, float))
            self.assertGreater(value, 0)
            
    def test_memory_limits(self):
        """Test memory limit configurations"""
        required_limits = [
            'max_dataframe_rows', 'max_excel_file_size_mb', 'max_memory_usage_mb'
        ]
        
        for limit in required_limits:
            self.assertIn(limit, MEMORY_LIMITS)
            value = MEMORY_LIMITS[limit]
            self.assertIsInstance(value, int)
            self.assertGreater(value, 0)


class TestErrorHandlingConfiguration(unittest.TestCase):
    """Test error handling configuration"""
    
    def test_retry_config_structure(self):
        """Test retry configuration structure"""
        required_keys = ['max_retries', 'retry_delay', 'exponential_backoff']
        
        for key in required_keys:
            self.assertIn(key, RETRY_CONFIG)
            
        self.assertIsInstance(RETRY_CONFIG['max_retries'], int)
        self.assertIsInstance(RETRY_CONFIG['retry_delay'], (int, float))
        self.assertIsInstance(RETRY_CONFIG['exponential_backoff'], bool)
        
    def test_error_messages_structure(self):
        """Test error message templates"""
        required_messages = [
            'file_not_found', 'invalid_data', 'database_error', 'validation_failed'
        ]
        
        for message_type in required_messages:
            self.assertIn(message_type, ERROR_MESSAGES)
            message = ERROR_MESSAGES[message_type]
            self.assertIsInstance(message, str)
            self.assertTrue(len(message) > 0)


class TestConfigurationIntegration(unittest.TestCase):
    """Test integration between different configuration sections"""
    
    def test_store_and_time_segment_consistency(self):
        """Test consistency between store and time segment configurations"""
        # Number of stores should match validation thresholds
        max_stores = DATA_COMPLETENESS_THRESHOLDS.get('min_stores_present', 0)
        self.assertLessEqual(max_stores, len(STORE_NAME_MAPPING))
        
        # Number of time segments should match validation
        min_segments = DATA_COMPLETENESS_THRESHOLDS.get('min_time_segments', 0)
        self.assertEqual(len(TIME_SEGMENTS), min_segments)
        
    def test_material_types_and_report_consistency(self):
        """Test consistency between material types and report configurations"""
        # Material types should be reasonable for reporting
        self.assertGreater(len(MATERIAL_TYPES), 5)  # Should have meaningful variety
        self.assertLess(len(MATERIAL_TYPES), 20)    # But not too many
        
        # Child types should be subset of main types
        self.assertLessEqual(len(MATERIAL_CHILD_TYPES), len(MATERIAL_TYPES))
        
    def test_performance_and_validation_consistency(self):
        """Test consistency between performance targets and validation thresholds"""
        # Memory limits should be reasonable for validation thresholds
        max_rows = MEMORY_LIMITS['max_dataframe_rows']
        chunk_size = EXCEL_CHUNK_SIZE
        
        self.assertGreater(max_rows, chunk_size)  # Memory limit should exceed chunk size
        
        # Timeout values should be ordered appropriately
        core_time = PERFORMANCE_TARGETS['core_operation_max_time']
        test_time = PERFORMANCE_TARGETS['test_suite_max_time']
        report_time = PERFORMANCE_TARGETS['report_generation_max_time']
        
        self.assertLess(core_time, test_time)     # Core ops faster than full test suite
        self.assertLess(test_time, report_time)   # Test suite faster than report gen


if __name__ == '__main__':
    # Run all tests with detailed output
    unittest.main(verbosity=2)