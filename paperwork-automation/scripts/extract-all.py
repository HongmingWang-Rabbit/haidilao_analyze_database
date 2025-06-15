#!/usr/bin/env python3
"""
Convenience script to extract both daily reports and time segment data from Excel files.
Runs both insert-data.py and extract-time-segments.py on the same input file.
Enhanced with data format validation and warning system.
Enhanced with direct database insertion capabilities.
"""

import argparse
import subprocess
import sys
import os
import pandas as pd
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path for database imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import get_database_manager, setup_database_for_tests

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore')

def validate_excel_file(input_file):
    """
    Validate the Excel file format and structure.
    Returns (is_valid, warnings_list)
    """
    validation_warnings = []
    is_valid = True
    
    print("🔍 Validating Excel file format...")
    
    try:
        # Check if file exists
        if not os.path.exists(input_file):
            validation_warnings.append(f"❌ File not found: {input_file}")
            return False, validation_warnings
        
        # Check file extension
        if not input_file.lower().endswith(('.xlsx', '.xls')):
            validation_warnings.append(f"⚠️  File extension warning: Expected .xlsx or .xls, got {os.path.splitext(input_file)[1]}")
        
        # Try to read Excel file and get sheet names
        try:
            excel_file = pd.ExcelFile(input_file)
            sheet_names = excel_file.sheet_names
        except Exception as e:
            validation_warnings.append(f"❌ Cannot read Excel file: {str(e)}")
            return False, validation_warnings
        
        # Check for required sheets
        required_sheets = ['营业基础表', '分时段基础表']
        missing_sheets = []
        
        for sheet in required_sheets:
            if sheet not in sheet_names:
                missing_sheets.append(sheet)
        
        if missing_sheets:
            validation_warnings.append(f"❌ Missing required sheets: {', '.join(missing_sheets)}")
            validation_warnings.append(f"📋 Available sheets: {', '.join(map(str, sheet_names))}")
            is_valid = False
        else:
            print(f"✅ Found required sheets: {', '.join(required_sheets)}")
        
        # Validate daily reports sheet (营业基础表)
        if '营业基础表' in sheet_names:
            daily_warnings = validate_daily_sheet(excel_file)
            validation_warnings.extend(daily_warnings)
        
        # Validate time segments sheet (分时段基础表)
        if '分时段基础表' in sheet_names:
            time_warnings = validate_time_segment_sheet(excel_file)
            validation_warnings.extend(time_warnings)
        
        excel_file.close()
        
    except Exception as e:
        validation_warnings.append(f"❌ Unexpected error during validation: {str(e)}")
        is_valid = False
    
    return is_valid, validation_warnings

def validate_daily_sheet(excel_file):
    """Validate the 营业基础表 sheet format."""
    warnings_list = []
    
    try:
        df = pd.read_excel(excel_file, sheet_name='营业基础表')
        
        # Expected columns for daily reports
        expected_columns = [
            '门店名称', '日期', '节假日', '营业桌数', '营业桌数(考核)', 
            '翻台率(考核)', '营业收入(不含税)', '营业桌数(考核)(外卖)', 
            '就餐人数', '优惠总金额(不含税)'
        ]
        
        # Check if DataFrame is empty
        if df.empty:
            warnings_list.append("❌ 营业基础表 sheet is empty")
            return warnings_list
        
        # Check for required columns
        missing_columns = []
        for col in expected_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            warnings_list.append(f"❌ 营业基础表 missing columns: {', '.join(missing_columns)}")
            warnings_list.append(f"📋 Available columns: {', '.join(df.columns.tolist())}")
        else:
            print("✅ 营业基础表 has all required columns")
        
        # Validate store names
        if '门店名称' in df.columns:
            expected_stores = ['加拿大一店', '加拿大二店', '加拿大三店', '加拿大四店', '加拿大五店', '加拿大六店', '加拿大七店']
            actual_stores = df['门店名称'].unique().tolist()
            
            unknown_stores = [store for store in actual_stores if store not in expected_stores]
            if unknown_stores:
                warnings_list.append(f"⚠️  Unknown stores in 营业基础表: {', '.join(unknown_stores)}")
            
            missing_stores = [store for store in expected_stores if store not in actual_stores]
            if missing_stores:
                warnings_list.append(f"⚠️  Missing stores in 营业基础表: {', '.join(missing_stores)}")
            
            if not unknown_stores and not missing_stores:
                print(f"✅ 营业基础表 contains all {len(expected_stores)} expected stores")
        
        # Validate date format
        if '日期' in df.columns:
            date_issues = validate_date_column(df['日期'], '营业基础表')
            warnings_list.extend(date_issues)
        
        # Validate holiday column
        if '节假日' in df.columns:
            holiday_issues = validate_holiday_column(df['节假日'], '营业基础表')
            warnings_list.extend(holiday_issues)
        
        # Check for numeric columns
        numeric_columns = ['营业桌数', '营业桌数(考核)', '翻台率(考核)', '营业收入(不含税)', '营业桌数(考核)(外卖)', '就餐人数', '优惠总金额(不含税)']
        for col in numeric_columns:
            if col in df.columns:
                numeric_issues = validate_numeric_column(df[col], col, '营业基础表')
                warnings_list.extend(numeric_issues)
        
        print(f"📊 营业基础表 contains {len(df)} rows of data")
        
    except Exception as e:
        warnings_list.append(f"❌ Error validating 营业基础表: {str(e)}")
    
    return warnings_list

def validate_time_segment_sheet(excel_file):
    """Validate the 分时段基础表 sheet format."""
    warnings_list = []
    
    try:
        df = pd.read_excel(excel_file, sheet_name='分时段基础表')
        
        # Expected columns for time segments
        expected_columns = [
            '门店名称', '日期', '分时段', '节假日', '营业桌数(考核)', '翻台率(考核)'
        ]
        
        # Check if DataFrame is empty
        if df.empty:
            warnings_list.append("❌ 分时段基础表 sheet is empty")
            return warnings_list
        
        # Check for required columns
        missing_columns = []
        for col in expected_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            warnings_list.append(f"❌ 分时段基础表 missing columns: {', '.join(missing_columns)}")
            warnings_list.append(f"📋 Available columns: {', '.join(df.columns.tolist())}")
        else:
            print("✅ 分时段基础表 has all required columns")
        
        # Validate time segments
        if '分时段' in df.columns:
            expected_segments = ['08:00-13:59', '14:00-16:59', '17:00-21:59', '22:00-(次)07:59']
            actual_segments = df['分时段'].unique().tolist()
            
            unknown_segments = [seg for seg in actual_segments if seg not in expected_segments]
            if unknown_segments:
                warnings_list.append(f"⚠️  Unknown time segments in 分时段基础表: {', '.join(unknown_segments)}")
            
            missing_segments = [seg for seg in expected_segments if seg not in actual_segments]
            if missing_segments:
                warnings_list.append(f"⚠️  Missing time segments in 分时段基础表: {', '.join(missing_segments)}")
            
            if not unknown_segments and not missing_segments:
                print(f"✅ 分时段基础表 contains all {len(expected_segments)} expected time segments")
        
        # Validate store names
        if '门店名称' in df.columns:
            expected_stores = ['加拿大一店', '加拿大二店', '加拿大三店', '加拿大四店', '加拿大五店', '加拿大六店', '加拿大七店']
            actual_stores = df['门店名称'].unique().tolist()
            
            unknown_stores = [store for store in actual_stores if store not in expected_stores]
            if unknown_stores:
                warnings_list.append(f"⚠️  Unknown stores in 分时段基础表: {', '.join(unknown_stores)}")
        
        # Validate date format
        if '日期' in df.columns:
            date_issues = validate_date_column(df['日期'], '分时段基础表')
            warnings_list.extend(date_issues)
        
        # Validate holiday column
        if '节假日' in df.columns:
            holiday_issues = validate_holiday_column(df['节假日'], '分时段基础表')
            warnings_list.extend(holiday_issues)
        
        print(f"📊 分时段基础表 contains {len(df)} rows of data")
        
    except Exception as e:
        warnings_list.append(f"❌ Error validating 分时段基础表: {str(e)}")
    
    return warnings_list

def validate_date_column(date_series, sheet_name):
    """Validate date column format (should be YYYYMMDD)."""
    warnings_list = []
    
    try:
        # Check for null values
        null_count = date_series.isnull().sum()
        if null_count > 0:
            warnings_list.append(f"⚠️  {sheet_name}: {null_count} rows have missing dates")
        
        # Check date format (should be YYYYMMDD as integer)
        invalid_dates = []
        for idx, date_val in enumerate(date_series.dropna()):
            try:
                # Convert to string and check format
                date_str = str(int(date_val)) if pd.notna(date_val) else None
                if date_str and len(date_str) == 8:
                    # Try to parse as date
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    
                    # Basic validation
                    if year < 2020 or year > 2030:
                        invalid_dates.append(f"Row {idx+2}: Invalid year {year}")
                    elif month < 1 or month > 12:
                        invalid_dates.append(f"Row {idx+2}: Invalid month {month}")
                    elif day < 1 or day > 31:
                        invalid_dates.append(f"Row {idx+2}: Invalid day {day}")
                else:
                    invalid_dates.append(f"Row {idx+2}: Invalid date format '{date_val}' (expected YYYYMMDD)")
            except (ValueError, TypeError):
                invalid_dates.append(f"Row {idx+2}: Cannot parse date '{date_val}'")
        
        if invalid_dates:
            warnings_list.append(f"❌ {sheet_name} date format issues:")
            for issue in invalid_dates[:5]:  # Show first 5 issues
                warnings_list.append(f"   {issue}")
            if len(invalid_dates) > 5:
                warnings_list.append(f"   ... and {len(invalid_dates) - 5} more date issues")
        else:
            print(f"✅ {sheet_name} date format is correct")
    
    except Exception as e:
        warnings_list.append(f"❌ Error validating dates in {sheet_name}: {str(e)}")
    
    return warnings_list

def validate_holiday_column(holiday_series, sheet_name):
    """Validate holiday column values."""
    warnings_list = []
    
    try:
        expected_values = ['工作日', '节假日']
        actual_values = holiday_series.dropna().unique().tolist()
        
        invalid_values = [val for val in actual_values if val not in expected_values]
        if invalid_values:
            warnings_list.append(f"⚠️  {sheet_name}: Invalid holiday values: {', '.join(map(str, invalid_values))}")
            warnings_list.append(f"   Expected values: {', '.join(expected_values)}")
        else:
            print(f"✅ {sheet_name} holiday values are correct")
    
    except Exception as e:
        warnings_list.append(f"❌ Error validating holiday column in {sheet_name}: {str(e)}")
    
    return warnings_list

def validate_numeric_column(numeric_series, column_name, sheet_name):
    """Validate numeric column for reasonable values."""
    warnings_list = []
    
    try:
        # Check for non-numeric values
        non_numeric_count = 0
        for val in numeric_series:
            if pd.notna(val):
                try:
                    float(val)
                except (ValueError, TypeError):
                    non_numeric_count += 1
        
        if non_numeric_count > 0:
            warnings_list.append(f"⚠️  {sheet_name}.{column_name}: {non_numeric_count} non-numeric values found")
        
        # Check for negative values where they shouldn't be
        if column_name in ['营业桌数', '营业桌数(考核)', '就餐人数']:
            negative_count = (numeric_series < 0).sum()
            if negative_count > 0:
                warnings_list.append(f"⚠️  {sheet_name}.{column_name}: {negative_count} negative values found (should be positive)")
        
        # Check for extremely high values that might be data entry errors
        if column_name == '翻台率(考核)':
            high_turnover = (numeric_series > 10).sum()
            if high_turnover > 0:
                warnings_list.append(f"⚠️  {sheet_name}.{column_name}: {high_turnover} values > 10 (unusually high turnover rate)")
        
    except Exception as e:
        warnings_list.append(f"❌ Error validating {column_name} in {sheet_name}: {str(e)}")
    
    return warnings_list

def run_script(script_name, input_file, debug=False, output=None, direct_db=False, test_db=False):
    """Run a Python script with the given arguments."""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    cmd = ['python3', script_path, input_file]
    
    if debug:
        cmd.append('--debug')
    
    if output:
        cmd.extend(['--output', output])
    
    if direct_db:
        cmd.append('--direct-db')
    
    if test_db:
        cmd.append('--test-db')
    
    print(f"🚀 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description='Extract both daily reports and time segment data from Excel files or insert directly to database')
    parser.add_argument('input_file', help='Path to the Excel file')
    parser.add_argument('--debug', '-d', action='store_true', help='Generate CSV files for manual verification')
    parser.add_argument('--daily-output', help='Path to the daily reports output SQL file')
    parser.add_argument('--time-output', help='Path to the time segments output SQL file')
    parser.add_argument('--skip-validation', action='store_true', help='Skip data format validation')
    parser.add_argument('--direct-db', action='store_true', help='Insert directly to database instead of generating SQL files')
    parser.add_argument('--test-db', action='store_true', help='Use test database')
    parser.add_argument('--setup-test-db', action='store_true', help='Setup test database with schema and initial data')
    
    args = parser.parse_args()
    
    # Setup test database if requested
    if args.setup_test_db:
        print("🔄 Setting up test database...")
        if setup_database_for_tests():
            print("✅ Test database setup completed")
        else:
            print("❌ Test database setup failed")
            sys.exit(1)
        return
    
    # Check if we should use direct database insertion
    direct_db_insert = args.direct_db or os.getenv('DIRECT_DB_INSERT', 'false').lower() == 'true'
    is_test = args.test_db
    
    if direct_db_insert:
        print("🔗 Direct database insertion mode enabled")
        if is_test:
            print("🧪 Using test database")
        else:
            print("🏭 Using production database")
    
    print(f"📊 Processing Excel file: {args.input_file}")
    print("=" * 60)
    
    # Validate Excel file format unless skipped
    if not args.skip_validation:
        is_valid, validation_warnings = validate_excel_file(args.input_file)
        
        # Display all warnings
        if validation_warnings:
            print("\n📋 VALIDATION RESULTS:")
            for warning in validation_warnings:
                print(warning)
            print()
        
        # Stop if critical validation errors found
        if not is_valid:
            print("❌ Critical validation errors found. Please fix the Excel file format before proceeding.")
            print("💡 Use --skip-validation flag to bypass validation if needed.")
            sys.exit(1)
        elif validation_warnings:
            print("⚠️  Validation warnings found, but proceeding with extraction...")
        else:
            print("✅ Excel file format validation passed!")
        
        print("=" * 60)
    else:
        print("⚠️  Skipping data format validation...")
        print("=" * 60)
    
    success_count = 0
    
    # Extract daily reports
    print("\n1. 📈 Extracting daily reports from '营业基础表' sheet...")
    if run_script('insert-data.py', args.input_file, args.debug, args.daily_output, direct_db_insert, is_test):
        success_count += 1
    
    print("\n" + "=" * 60)
    
    # Extract time segment reports
    print("\n2. ⏰ Extracting time segment reports from '分时段基础表' sheet...")
    if run_script('extract-time-segments.py', args.input_file, args.debug, args.time_output, direct_db_insert, is_test):
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"\n📊 Completed: {success_count}/2 extractions successful")
    
    if success_count == 2:
        print("🎉 All extractions completed successfully!")
        if direct_db_insert:
            print("💾 Data has been inserted directly to the database")
        else:
            print("📄 SQL files have been generated")
        sys.exit(0)
    else:
        print("❌ Some extractions failed. Check the error messages above.")
        sys.exit(1)

if __name__ == '__main__':
    main() 