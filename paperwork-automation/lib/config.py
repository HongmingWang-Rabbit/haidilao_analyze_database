#!/usr/bin/env python3
"""
Centralized configuration and constants for Haidilao paperwork automation.
Consolidates configuration scattered across multiple files.
"""

from typing import Dict, List
from pathlib import Path

# ============================================================================
# STORE CONFIGURATION
# ============================================================================

# Store name to ID mapping (centralized from multiple files)
STORE_NAME_MAPPING: Dict[str, int] = {
    '加拿大一店': 1,
    '加拿大二店': 2,
    '加拿大三店': 3,
    '加拿大四店': 4,
    '加拿大五店': 5,
    '加拿大六店': 6,
    '加拿大七店': 7
}

# Reverse mapping for ID to name lookups
STORE_ID_TO_NAME_MAPPING: Dict[int, str] = {
    v: k for k, v in STORE_NAME_MAPPING.items()
}

# List of all valid store names
VALID_STORE_NAMES: List[str] = list(STORE_NAME_MAPPING.keys())

# Store IDs in order
STORE_IDS: List[int] = list(range(1, 8))


# ============================================================================
# TIME SEGMENT CONFIGURATION
# ============================================================================

# Time segment definitions
TIME_SEGMENTS: List[str] = [
    "08:00-13:59",
    "14:00-16:59", 
    "17:00-21:59",
    "22:00-(次)07:59"
]

# Time segment display names
TIME_SEGMENT_DISPLAY_NAMES: Dict[str, str] = {
    "08:00-13:59": "午餐时段",
    "14:00-16:59": "下午时段",
    "17:00-21:59": "晚餐时段", 
    "22:00-(次)07:59": "夜宵时段"
}


# ============================================================================
# DATE AND TIME CONFIGURATION
# ============================================================================

# Standard date format used throughout the system
DEFAULT_DATE_FORMAT: str = '%Y-%m-%d'
EXCEL_DATE_FORMAT: str = '%Y%m%d'  # YYYYMMDD format used in Excel files
DISPLAY_DATE_FORMAT: str = '%Y年%m月%d日'  # Chinese date display format

# Holiday indicators
HOLIDAY_INDICATORS: Dict[str, str] = {
    'WORKDAY': '工作日',
    'HOLIDAY': '节假日'
}


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Database connection settings
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'hongming',
    'password': '8894',
    'database': 'haidilao-paperwork',
    'port': 5432
}

# Database timeout settings
DATABASE_TIMEOUT: int = 30
QUERY_TIMEOUT: int = 60
CONNECTION_POOL_SIZE: int = 5

# Batch processing settings
DEFAULT_BATCH_SIZE: int = 1000
EXCEL_CHUNK_SIZE: int = 1000


# ============================================================================
# EXCEL PROCESSING CONFIGURATION
# ============================================================================

# Critical column name mappings for different file types
EXCEL_COLUMN_MAPPINGS = {
    'daily_reports': {
        'required_columns': [
            '门店名称', '日期', '节假日', '营业桌数', '营业桌数(考核)', 
            '翻台率(考核)', '营业收入(不含税)', '营业桌数(考核)(外卖)', 
            '就餐人数', '优惠总金额(不含税)'
        ]
    },
    'time_segments': {
        'required_columns': [
            '门店名称', '日期', '分时段', '节假日', 
            '营业桌数(考核)', '翻台率(考核)'
        ]
    },
    'material_details': {
        'required_columns': [
            '物料', '物料描述', '数量', '单价', '金额'
        ]
    },
    'dish_sales': {
        'required_columns': [
            '菜品编号', '菜品名称', '数量', '单价', '金额'
        ]
    }
}

# Sheet name patterns for different report types
SHEET_NAME_PATTERNS = {
    'daily_basic': '营业基础表',
    'time_segment_basic': '分时段基础表',
    'material_export': 'export',
    'dish_material_usage': '计算菜品物料用量',
    'monthly_dish_sales': '菜品月度销售',
    'inventory_calculation': '盘点计算结果'
}


# ============================================================================
# MATERIAL TYPE CONFIGURATION
# ============================================================================

# Material type classifications
MATERIAL_TYPES = {
    1: '成本-锅底类',
    2: '成本-荤菜类', 
    3: '成本-素菜类',
    4: '成本-酒水类',
    5: '成本-调料类',
    6: '成本-其他类',
    7: '成本-包装类',
    8: '成本-冰淇淋',
    9: '成本-零食类',
    10: '成本-饮料类',
    11: '成本-服务用品'
}

# Material child types (subset of main types)
MATERIAL_CHILD_TYPES = {
    1: '成本-锅底类',
    2: '成本-荤菜类',
    3: '成本-素菜类', 
    4: '成本-酒水类',
    5: '成本-调料类',
    6: '成本-其他类'
}


# ============================================================================
# DISCOUNT ANALYSIS CONFIGURATION
# ============================================================================

# Discount type classifications
DISCOUNT_TYPES = {
    '会员折扣': 'Member Discount',
    '生日优惠': 'Birthday Discount', 
    '节日优惠': 'Holiday Discount',
    '促销活动': 'Promotional Activity',
    '团购优惠': 'Group Purchase Discount',
    '其他优惠': 'Other Discounts'
}


# ============================================================================
# REPORT GENERATION CONFIGURATION
# ============================================================================

# Worksheet names for database reports
REPORT_WORKSHEET_NAMES = {
    'monthly_comparison': '对比上月表',
    'yearly_comparison': '同比数据',
    'yearly_daily_comparison': '对比上年表',
    'time_segment': '分时段-上报',
    'business_insight': '营业透视',
    'daily_store_tracking': '门店日-加拿大'
}

# Column widths for different worksheet types
WORKSHEET_COLUMN_WIDTHS = {
    'standard': [15, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12],
    'wide': [20, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15],
    'narrow': [12, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
}

# Common Excel formatting settings
EXCEL_FORMATS = {
    'percentage': '0.0%',
    'currency_cad': '$#,##0.00',
    'currency_usd': 'US$#,##0.00', 
    'integer': '#,##0',
    'decimal_2': '#,##0.00'
}


# ============================================================================
# FILE PATH CONFIGURATION
# ============================================================================

# Standard directory structure
DIRECTORIES = {
    'output': Path('output'),
    'input': Path('Input'),
    'scripts': Path('scripts'),
    'lib': Path('lib'),
    'tests': Path('tests'),
    'utils': Path('utils'),
    'sql': Path('haidilao-database-querys')
}

# File naming patterns
FILE_NAMING_PATTERNS = {
    'database_report': 'database_report_{date}.xlsx',
    'gross_margin_report': 'gross_margin_report_{date}.xlsx',
    'monthly_material_report': 'monthly_material_report_{date}.xlsx',
    'sql_output': '{entity}_data_{date}.sql'
}


# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================

# Data validation thresholds
VALIDATION_THRESHOLDS = {
    'max_table_count': 200,  # Maximum reasonable table count per store
    'max_turnover_rate': 10.0,  # Maximum reasonable turnover rate
    'min_revenue': 0,  # Minimum revenue (can be 0)
    'max_revenue': 100000,  # Maximum reasonable daily revenue
    'max_discount_percentage': 0.5  # Maximum discount as percentage of revenue
}

# Required data completeness thresholds
DATA_COMPLETENESS_THRESHOLDS = {
    'min_stores_present': 5,  # Minimum number of stores that must have data
    'min_days_per_month': 25,  # Minimum days of data required for monthly reports
    'min_time_segments': 4  # All 4 time segments must be present
}


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging levels and formats
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

# Log file naming
LOG_FILE_PATTERN = 'automation_{date}.log'


# ============================================================================
# WEB SCRAPING CONFIGURATION (QBI)
# ============================================================================

# QBI system configuration
QBI_CONFIG = {
    'base_url': 'https://qbi.haidilao.com',
    'login_timeout': 30,
    'download_timeout': 60,
    'headless_mode': True  # Default to headless for production
}

# Browser settings
BROWSER_CONFIG = {
    'window_size': (1920, 1080),
    'download_dir': str(DIRECTORIES['input']),
    'implicit_wait': 10
}


# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================

# Performance targets and limits
PERFORMANCE_TARGETS = {
    'core_operation_max_time': 1.0,  # seconds
    'test_suite_max_time': 5.0,  # seconds  
    'report_generation_max_time': 30.0,  # seconds
    'database_query_max_time': 10.0  # seconds
}

# Memory usage limits
MEMORY_LIMITS = {
    'max_dataframe_rows': 100000,
    'max_excel_file_size_mb': 50,
    'max_memory_usage_mb': 500
}


# ============================================================================
# ERROR HANDLING CONFIGURATION
# ============================================================================

# Retry configuration
RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1.0,  # seconds
    'exponential_backoff': True
}

# Error message templates
ERROR_MESSAGES = {
    'file_not_found': "Required file not found: {filename}",
    'invalid_data': "Invalid data in {location}: {details}",
    'database_error': "Database operation failed: {operation}",
    'validation_failed': "Data validation failed: {field} - {reason}"
}


# ============================================================================
# EXPORT ALL CONSTANTS
# ============================================================================

__all__ = [
    # Store configuration
    'STORE_NAME_MAPPING', 'STORE_ID_TO_NAME_MAPPING', 'VALID_STORE_NAMES', 'STORE_IDS',
    
    # Time configuration  
    'TIME_SEGMENTS', 'TIME_SEGMENT_DISPLAY_NAMES',
    'DEFAULT_DATE_FORMAT', 'EXCEL_DATE_FORMAT', 'DISPLAY_DATE_FORMAT',
    'HOLIDAY_INDICATORS',
    
    # Database configuration
    'DATABASE_CONFIG', 'DATABASE_TIMEOUT', 'QUERY_TIMEOUT', 'CONNECTION_POOL_SIZE',
    'DEFAULT_BATCH_SIZE', 'EXCEL_CHUNK_SIZE',
    
    # Excel configuration
    'EXCEL_COLUMN_MAPPINGS', 'SHEET_NAME_PATTERNS',
    
    # Material configuration
    'MATERIAL_TYPES', 'MATERIAL_CHILD_TYPES',
    
    # Discount configuration
    'DISCOUNT_TYPES',
    
    # Report configuration
    'REPORT_WORKSHEET_NAMES', 'WORKSHEET_COLUMN_WIDTHS', 'EXCEL_FORMATS',
    
    # File path configuration
    'DIRECTORIES', 'FILE_NAMING_PATTERNS',
    
    # Validation configuration
    'VALIDATION_THRESHOLDS', 'DATA_COMPLETENESS_THRESHOLDS',
    
    # Logging configuration
    'LOGGING_CONFIG', 'LOG_FILE_PATTERN',
    
    # Web scraping configuration
    'QBI_CONFIG', 'BROWSER_CONFIG',
    
    # Performance configuration
    'PERFORMANCE_TARGETS', 'MEMORY_LIMITS',
    
    # Error handling configuration
    'RETRY_CONFIG', 'ERROR_MESSAGES'
]