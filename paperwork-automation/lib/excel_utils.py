#!/usr/bin/env python3
"""
Centralized Excel processing utilities for Haidilao paperwork automation.
Consolidates common patterns from 20+ files to eliminate duplication.
"""

import pandas as pd
import warnings
from typing import Dict, Optional, Any, Union
from pathlib import Path
import logging

# Critical dtype specification to prevent material number precision loss
# This was duplicated across 20+ files - now centralized
MATERIAL_DTYPE_SPEC = {'物料': str}
DISH_CODE_DTYPE_SPEC = {'菜品编号': str, '菜品代码': str}

# Common dtype specifications for different file types
MATERIAL_DETAIL_DTYPE_SPEC = {
    '物料': str,
    '物料描述': str,
    '数量': float,
    '单价': float
}

DISH_SALES_DTYPE_SPEC = {
    '菜品编号': str,
    '菜品代码': str,
    '菜品名称': str,
    '数量': float,
    '单价': float
}


def suppress_excel_warnings():
    """
    Standard warning suppression for openpyxl.
    Consolidates duplicate warning filters from multiple files.
    """
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')


def safe_read_excel(
    file_path: Union[str, Path], 
    sheet_name: Optional[str] = None,
    dtype_spec: Optional[Dict[str, Any]] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Standardized Excel reading with proper error handling and dtype specifications.
    
    Args:
        file_path: Path to Excel file
        sheet_name: Specific sheet to read (None for first sheet)
        dtype_spec: Column dtype specifications (critical for material numbers)
        **kwargs: Additional pandas.read_excel arguments
        
    Returns:
        DataFrame with properly typed columns
        
    Raises:
        FileNotFoundError: If Excel file doesn't exist
        ValueError: If sheet not found or data invalid
    """
    suppress_excel_warnings()
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    try:
        # First check if it's a fake Excel file (actually TSV with UTF-16)
        # This is common with SAP exports
        with open(file_path, 'rb') as f:
            header = f.read(2)
            if header == b'\xff\xfe':  # UTF-16 LE BOM
                logging.info(f"Detected UTF-16 encoded file, reading as TSV: {file_path}")
                df = pd.read_csv(file_path, sep='\t', encoding='utf-16', dtype=dtype_spec or {})
                logging.info(f"Successfully read {len(df)} rows, {len(df.columns)} columns")
                return df
        
        # Otherwise, determine engine based on file extension
        file_ext = file_path.suffix.lower()
        if file_ext == '.xls':
            engine = 'xlrd'
        elif file_ext in ['.xlsx', '.xlsm']:
            engine = 'openpyxl'
        else:
            # Let pandas auto-detect
            engine = None
            
        # Set default engine and handle dtype specification
        defaults = {
            'dtype': dtype_spec or {}
        }
        if engine:
            defaults['engine'] = engine
            
        defaults.update(kwargs)
        
        if sheet_name:
            defaults['sheet_name'] = sheet_name
            
        logging.info(f"Reading Excel file: {file_path}, sheet: {sheet_name or 'default'}, engine: {engine or 'auto'}")
        df = pd.read_excel(file_path, **defaults)
        
        logging.info(f"Successfully read {len(df)} rows, {len(df.columns)} columns")
        return df
        
    except Exception as e:
        logging.error(f"Failed to read Excel file {file_path}: {e}")
        raise ValueError(f"Failed to read Excel file: {e}")


def clean_dish_code(code: Any) -> Optional[str]:
    """
    Standardized dish code cleaning (remove .0 suffix from pandas float conversion and leading zeros).
    Consolidates identical functions from multiple extraction scripts.
    
    Args:
        code: Raw dish code (may be float, string, or NaN)
        
    Returns:
        Cleaned dish code string or None if invalid
    """
    if pd.isna(code):
        return None
    
    # Convert to string and clean
    code_str = str(code).strip()
    
    # Remove .0 if it's a whole number (e.g., 90001690.0 -> 90001690)
    if code_str.endswith('.0'):
        code_str = code_str[:-2]
    
    # Remove leading zeros but preserve the number as string
    code_str = code_str.lstrip('0')
    
    # Handle case where all digits were zeros
    if not code_str:
        code_str = '0'
    
    return code_str if code_str and code_str != '-' else None


def clean_material_number(material_number: Any) -> Optional[str]:
    """
    Standardized material number cleaning with leading zero removal.
    Critical for preventing float64 precision loss issues.
    
    Args:
        material_number: Raw material number (may be float, string, or NaN)
        
    Returns:
        Cleaned material number string or None if invalid
    """
    if pd.isna(material_number):
        return None
    
    # Convert to string and handle float format
    material_str = str(material_number).strip()
    
    # Remove .0 if present (from float conversion)
    if material_str.endswith('.0'):
        material_str = material_str[:-2]
    
    # Remove leading zeros but preserve the number as string
    material_str = material_str.lstrip('0')
    
    # Handle case where all digits were zeros
    if not material_str:
        material_str = '0'
    
    return material_str


def validate_required_columns(df: pd.DataFrame, required_columns: list, sheet_name: str = "worksheet") -> bool:
    """
    Validate that DataFrame contains all required columns.
    Standardizes column validation across extraction scripts.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        sheet_name: Name of sheet for error reporting
        
    Returns:
        True if all columns present
        
    Raises:
        ValueError: If required columns are missing
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        available_columns = list(df.columns)
        raise ValueError(
            f"Missing required columns in {sheet_name}: {missing_columns}. "
            f"Available columns: {available_columns}"
        )
    
    logging.info(f"Column validation passed for {sheet_name}")
    return True


def clean_numeric_value(value: Any, default: float = 0.0) -> float:
    """
    Standardized numeric value cleaning and conversion.
    Handles NaN, string representations, and formatting issues.
    
    Args:
        value: Raw numeric value
        default: Default value if conversion fails
        
    Returns:
        Cleaned float value
    """
    if pd.isna(value) or value == '' or value == '-':
        return default
    
    try:
        # Handle string representations of numbers
        if isinstance(value, str):
            # Remove common formatting (commas, spaces)
            value = value.replace(',', '').replace(' ', '').strip()
            
        return float(value)
    except (ValueError, TypeError):
        logging.warning(f"Failed to convert '{value}' to float, using default {default}")
        return default


def get_material_reading_dtype() -> Dict[str, Any]:
    """
    Get the critical dtype specification for reading material data.
    Prevents float64 conversion that causes precision loss.
    
    Returns:
        Dictionary with proper dtype specifications for material files
    """
    return MATERIAL_DTYPE_SPEC.copy()


def get_dish_reading_dtype() -> Dict[str, Any]:
    """
    Get dtype specification for reading dish data.
    
    Returns:
        Dictionary with proper dtype specifications for dish files
    """
    return DISH_CODE_DTYPE_SPEC.copy()


def safe_get_sheet_names(file_path: Union[str, Path]) -> list:
    """
    Safely get sheet names from Excel file.
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        List of sheet names
    """
    suppress_excel_warnings()
    
    try:
        xl_file = pd.ExcelFile(file_path, engine='openpyxl')
        return xl_file.sheet_names
    except Exception as e:
        logging.error(f"Failed to get sheet names from {file_path}: {e}")
        return []


def detect_sheet_structure(df: pd.DataFrame, expected_patterns: Dict[str, list]) -> Optional[str]:
    """
    Detect which sheet structure/type the DataFrame matches.
    
    Args:
        df: DataFrame to analyze
        expected_patterns: Dict mapping sheet types to expected column patterns
        
    Returns:
        Detected sheet type or None if no match
    """
    df_columns = set(df.columns)
    
    for sheet_type, required_columns in expected_patterns.items():
        if set(required_columns).issubset(df_columns):
            return sheet_type
    
    return None


# Common sheet structure patterns for detection
COMMON_SHEET_PATTERNS = {
    'daily_store_report': ['门店名称', '日期', '营业收入(不含税)', '营业桌数'],
    'time_segment_report': ['门店名称', '日期', '分时段', '营业桌数(考核)'],
    'material_detail': ['物料', '物料描述', '数量', '单价'],
    'dish_sales': ['菜品编号', '菜品名称', '数量', '单价'],
    'dish_material_usage': ['菜品编号', '物料', '用量', '物料单位']
}


def standardize_column_names(df: pd.DataFrame, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Standardize column names for consistent processing.
    
    Args:
        df: DataFrame with potentially inconsistent column names
        column_mapping: Optional mapping of old names to new names
        
    Returns:
        DataFrame with standardized column names
    """
    if column_mapping:
        df = df.rename(columns=column_mapping)
    
    # Common standardizations
    common_mappings = {
        '門店名稱': '门店名称',  # Traditional Chinese
        '營業收入': '营业收入(不含税)',  # Traditional Chinese
        '菜品編號': '菜品编号',  # Traditional Chinese
        '物料編號': '物料',  # Traditional Chinese
    }
    
    df = df.rename(columns=common_mappings)
    return df


# Export commonly used functions and constants
__all__ = [
    'MATERIAL_DTYPE_SPEC',
    'DISH_CODE_DTYPE_SPEC',
    'suppress_excel_warnings',
    'safe_read_excel',
    'clean_dish_code',
    'clean_material_number',
    'validate_required_columns',
    'clean_numeric_value',
    'get_material_reading_dtype',
    'get_dish_reading_dtype',
    'safe_get_sheet_names',
    'detect_sheet_structure',
    'COMMON_SHEET_PATTERNS',
    'standardize_column_names'
]