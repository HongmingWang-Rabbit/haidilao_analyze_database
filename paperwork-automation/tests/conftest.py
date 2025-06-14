"""
Pytest configuration and shared fixtures for paperwork automation tests.
"""

import pytest
import pandas as pd
import tempfile
import os
import sys
from unittest.mock import MagicMock

# Add the scripts directory to the path for all tests
@pytest.fixture(scope="session", autouse=True)
def setup_path():
    """Add scripts directory to Python path for all tests."""
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

@pytest.fixture
def sample_daily_data():
    """Fixture providing sample daily report data."""
    return {
        '门店名称': ['加拿大一店', '加拿大二店', '加拿大三店'],
        '日期': [20250610, 20250610, 20250610],
        '节假日': ['工作日', '节假日', '工作日'],
        '营业桌数': [50.0, 45.0, 40.0],
        '营业桌数(考核)': [48.0, 43.0, 38.0],
        '翻台率(考核)': [2.5, 2.8, 2.2],
        '营业收入(不含税)': [15000.0, 18000.0, 12000.0],
        '营业桌数(考核)(外卖)': [5.0, 8.0, 3.0],
        '就餐人数': [120, 150, 95],
        '优惠总金额(不含税)': [500.0, 800.0, 300.0]
    }

@pytest.fixture
def sample_time_segment_data():
    """Fixture providing sample time segment data."""
    return {
        '门店名称': ['加拿大一店', '加拿大一店', '加拿大二店', '加拿大二店'],
        '日期': [20250610, 20250610, 20250610, 20250610],
        '分时段': ['08:00-13:59', '14:00-16:59', '17:00-21:59', '22:00-(次)07:59'],
        '节假日': ['工作日', '工作日', '节假日', '节假日'],
        '营业桌数(考核)': [25.0, 20.0, 30.0, 15.0],
        '翻台率(考核)': [1.5, 2.0, 2.8, 1.2]
    }

@pytest.fixture
def sample_daily_dataframe(sample_daily_data):
    """Fixture providing a pandas DataFrame with sample daily data."""
    return pd.DataFrame(sample_daily_data)

@pytest.fixture
def sample_time_segment_dataframe(sample_time_segment_data):
    """Fixture providing a pandas DataFrame with sample time segment data."""
    return pd.DataFrame(sample_time_segment_data)

@pytest.fixture
def temp_excel_file(sample_daily_data):
    """Fixture providing a temporary Excel file with sample data."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            pd.DataFrame(sample_daily_data).to_excel(writer, sheet_name='营业基础表', index=False)
            # Add a dummy time segment sheet
            time_data = {
                '门店名称': ['加拿大一店'],
                '日期': [20250610],
                '分时段': ['08:00-13:59'],
                '节假日': ['工作日'],
                '营业桌数(考核)': [25.0],
                '翻台率(考核)': [1.5]
            }
            pd.DataFrame(time_data).to_excel(writer, sheet_name='分时段基础表', index=False)
        
        yield temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

@pytest.fixture
def temp_output_dir():
    """Fixture providing a temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def mock_subprocess_success():
    """Fixture providing a mock successful subprocess result."""
    mock_result = MagicMock()
    mock_result.stdout = "Processing completed successfully"
    mock_result.stderr = ""
    mock_result.returncode = 0
    return mock_result

@pytest.fixture
def mock_subprocess_failure():
    """Fixture providing a mock failed subprocess result."""
    mock_result = MagicMock()
    mock_result.stdout = "Some output"
    mock_result.stderr = "Error: Processing failed"
    mock_result.returncode = 1
    return mock_result

@pytest.fixture
def expected_store_mapping():
    """Fixture providing the expected store ID mapping."""
    return {
        '加拿大一店': 1,
        '加拿大二店': 2,
        '加拿大三店': 3,
        '加拿大四店': 4,
        '加拿大五店': 5,
        '加拿大六店': 6,
        '加拿大七店': 7
    }

@pytest.fixture
def expected_time_segment_mapping():
    """Fixture providing the expected time segment ID mapping."""
    return {
        '08:00-13:59': 1,
        '14:00-16:59': 2,
        '17:00-21:59': 3,
        '22:00-(次)07:59': 4
    } 