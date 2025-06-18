#!/usr/bin/env python3
"""
Data extraction functions for processing Excel files and generating SQL or inserting to database.
Consolidates logic from insert-data.py and extract-time-segments.py into reusable functions.
"""

import pandas as pd
import os
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path for database imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import get_database_manager

# Suppress pandas warnings
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

def transform_daily_report_data(df):
    """Transform Excel data from 营业基础表 sheet into format needed for database insertion."""
    # Store ID mapping
    store_ids = {
        '加拿大一店': 1,
        '加拿大二店': 2,
        '加拿大三店': 3,
        '加拿大四店': 4,
        '加拿大五店': 5,
        '加拿大六店': 6,
        '加拿大七店': 7
    }
    
    transformed_data = []
    
    for _, row in df.iterrows():
        store_name = row['门店名称']
        
        if store_name not in store_ids:
            continue
            
        # Convert date from YYYYMMDD format to YYYY-MM-DD
        date_int = row['日期']
        try:
            date_str = str(int(date_int))  # Convert to string and remove any decimal
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            formatted_date = f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, TypeError):
            print(f"Warning: Invalid date format {date_int} for store {store_name}, skipping row")
            continue
            
        # Map the data according to database schema
        daily_data = {
            'store_id': store_ids[store_name],
            'date': formatted_date,
            'is_holiday': row['节假日'] == '节假日',  # True if holiday, False if 工作日
            'tables_served': float(row['营业桌数']) if pd.notna(row['营业桌数']) else None,
            'tables_served_validated': float(row['营业桌数(考核)']) if pd.notna(row['营业桌数(考核)']) else None,
            'turnover_rate': float(row['翻台率(考核)']) if pd.notna(row['翻台率(考核)']) else None,
            'revenue': float(row['营业收入(不含税)']) if pd.notna(row['营业收入(不含税)']) else None,
            'takeout_tables': float(row['营业桌数(考核)(外卖)']) if pd.notna(row['营业桌数(考核)(外卖)']) else None,
            'customer_count': float(row['就餐人数']) if pd.notna(row['就餐人数']) else None,
            'discount_amount': float(row['优惠总金额(不含税)']) if pd.notna(row['优惠总金额(不含税)']) else None
        }
        
        transformed_data.append(daily_data)
    
    return transformed_data

def transform_time_segment_data(df):
    """Transform Excel data from 分时段基础表 sheet into the format needed for database insertion."""
    # Store ID mapping
    store_ids = {
        '加拿大一店': 1,
        '加拿大二店': 2,
        '加拿大三店': 3,
        '加拿大四店': 4,
        '加拿大五店': 5,
        '加拿大六店': 6,
        '加拿大七店': 7
    }
    
    # Time segment ID mapping
    time_segment_ids = {
        '08:00-13:59': 1,
        '14:00-16:59': 2,
        '17:00-21:59': 3,
        '22:00-(次)07:59': 4
    }
    
    transformed_data = []
    
    # Process ALL rows in the dataframe (all dates and time segments)
    for _, row in df.iterrows():
        store_name = row['门店名称']
        time_segment_label = row['分时段']
        
        if store_name not in store_ids:
            continue
            
        if time_segment_label not in time_segment_ids:
            print(f"Warning: Unknown time segment '{time_segment_label}', skipping row")
            continue
            
        # Convert date from YYYYMMDD format to YYYY-MM-DD
        date_int = row['日期']
        try:
            date_str = str(int(date_int))  # Convert to string and remove any decimal
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            formatted_date = f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, TypeError):
            print(f"Warning: Invalid date format {date_int} for store {store_name}, skipping row")
            continue
            
        # Map the data according to database schema
        time_segment_data = {
            'store_id': store_ids[store_name],
            'date': formatted_date,
            'time_segment_id': time_segment_ids[time_segment_label],
            'is_holiday': row['节假日'] == '节假日',  # True if holiday, False if 工作日
            'tables_served_validated': float(row['营业桌数(考核)']) if pd.notna(row['营业桌数(考核)']) else None,
            'turnover_rate': float(row['翻台率(考核)']) if pd.notna(row['翻台率(考核)']) else None
        }
        
        transformed_data.append(time_segment_data)
    
    return transformed_data

def generate_upsert_sql(data, table_name, columns):
    """Generate SQL UPSERT statement (INSERT ... ON CONFLICT) from transformed data."""
    if not data:
        return ""
    
    # Generate column names for SQL
    column_names = ', '.join(columns)
    
    # Generate values for each row
    values_list = []
    for row in data:
        values = []
        for col in columns:
            value = row.get(col)
            if value is None:
                values.append('NULL')
            elif isinstance(value, bool):
                values.append('True' if value else 'False')
            elif isinstance(value, str):
                values.append(f"'{value}'")
            else:
                values.append(str(value))
        values_list.append(f"  ({', '.join(values)})")
    
    # Generate update columns for ON CONFLICT based on table type
    if table_name == 'daily_report':
        conflict_keys = ['store_id', 'date']
    elif table_name == 'store_time_report':
        conflict_keys = ['store_id', 'date', 'time_segment_id']
    else:
        conflict_keys = ['store_id', 'date']  # Default
    
    update_columns = [col for col in columns if col not in conflict_keys]
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
    
    # Combine into final UPSERT SQL
    sql = f"INSERT INTO {table_name} ({column_names}) VALUES\n"
    sql += ',\n'.join(values_list)
    sql += f"\nON CONFLICT ({', '.join(conflict_keys)}) DO UPDATE SET\n  {update_set};"
    
    return sql

def extract_daily_reports(input_file, output_file=None, debug=False, direct_db=False, is_test=False):
    """Extract daily reports from Excel file and either generate SQL or insert to database."""
    try:
        # Read Excel file from the correct sheet
        df = pd.read_excel(input_file, sheet_name='营业基础表')
        
        # Transform data
        transformed_data = transform_daily_report_data(df)
        print(f"📈 Found {len(transformed_data)} rows of daily report data")
        
        # Generate output directory for debug/SQL files
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate CSV for debug mode
        if debug:
            input_basename = os.path.splitext(os.path.basename(input_file))[0]
            csv_file = os.path.join(output_dir, f'debug_daily_reports_{input_basename}.csv')
            debug_df = pd.DataFrame(transformed_data)
            debug_df.to_csv(csv_file, index=False)
            print(f"📄 Debug CSV saved to: {csv_file}")
        
        if direct_db:
            # Insert directly to database
            success = insert_daily_data_to_database(transformed_data, is_test)
            return success
        else:
            # Generate UPSERT SQL
            columns = [
                'store_id', 'date', 'is_holiday', 'tables_served', 'tables_served_validated',
                'turnover_rate', 'revenue', 'takeout_tables', 'customer_count', 'discount_amount'
            ]
            sql = generate_upsert_sql(transformed_data, 'daily_report', columns)
            
            # Determine output file path
            if output_file:
                sql_file = output_file
            else:
                input_basename = os.path.splitext(os.path.basename(input_file))[0]
                sql_file = os.path.join(output_dir, f'daily_reports_{input_basename}.sql')
            
            # Write SQL to file
            with open(sql_file, 'w') as f:
                f.write(sql)
            
            print(f"📄 SQL saved to: {sql_file}")
            return True
            
    except Exception as e:
        print(f"❌ Error extracting daily reports: {e}")
        return False

def extract_time_segments(input_file, output_file=None, debug=False, direct_db=False, is_test=False):
    """Extract time segment data from Excel file and either generate SQL or insert to database."""
    try:
        # Read Excel file from the correct sheet
        df = pd.read_excel(input_file, sheet_name='分时段基础表')
        
        # Transform data
        transformed_data = transform_time_segment_data(df)
        print(f"📈 Found {len(transformed_data)} rows of time segment data")
        
        # Generate output directory for debug/SQL files
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate CSV for debug mode
        if debug:
            input_basename = os.path.splitext(os.path.basename(input_file))[0]
            csv_file = os.path.join(output_dir, f'debug_time_segments_{input_basename}.csv')
            debug_df = pd.DataFrame(transformed_data)
            debug_df.to_csv(csv_file, index=False)
            print(f"📄 Debug CSV saved to: {csv_file}")
        
        if direct_db:
            # Insert directly to database
            success = insert_time_data_to_database(transformed_data, is_test)
            return success
        else:
            # Generate UPSERT SQL
            columns = [
                'store_id', 'date', 'time_segment_id', 'is_holiday', 
                'tables_served_validated', 'turnover_rate'
            ]
            sql = generate_upsert_sql(transformed_data, 'store_time_report', columns)
            
            # Determine output file path
            if output_file:
                sql_file = output_file
            else:
                input_basename = os.path.splitext(os.path.basename(input_file))[0]
                sql_file = os.path.join(output_dir, f'time_segments_{input_basename}.sql')
            
            # Write SQL to file
            with open(sql_file, 'w') as f:
                f.write(sql)
            
            print(f"📄 SQL saved to: {sql_file}")
            return True
            
    except Exception as e:
        print(f"❌ Error extracting time segments: {e}")
        return False

def insert_daily_data_to_database(data, is_test=False):
    """Insert daily report data directly to database"""
    try:
        db_manager = get_database_manager(is_test=is_test)
        
        # Test connection first
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return False
        
        # Generate SQL
        columns = [
            'store_id', 'date', 'is_holiday', 'tables_served', 'tables_served_validated',
            'turnover_rate', 'revenue', 'takeout_tables', 'customer_count', 'discount_amount'
        ]
        sql = generate_upsert_sql(data, 'daily_report', columns)
        
        if not sql:
            print("⚠️ No SQL generated - no data to insert")
            return True
        
        # Execute SQL
        success = db_manager.execute_sql(sql)
        
        if success:
            print(f"✅ Successfully inserted {len(data)} daily report records to daily_report")
            return True
        else:
            print(f"❌ Failed to insert daily report data to daily_report")
            return False
            
    except Exception as e:
        print(f"❌ Database insertion error: {e}")
        return False

def insert_time_data_to_database(data, is_test=False):
    """Insert time segment data directly to database"""
    try:
        db_manager = get_database_manager(is_test=is_test)
        
        # Test connection first
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return False
        
        # Generate SQL
        columns = [
            'store_id', 'date', 'time_segment_id', 'is_holiday', 
            'tables_served_validated', 'turnover_rate'
        ]
        sql = generate_upsert_sql(data, 'store_time_report', columns)
        
        if not sql:
            print("⚠️ No SQL generated - no data to insert")
            return True
        
        # Execute SQL
        success = db_manager.execute_sql(sql)
        
        if success:
            print(f"✅ Successfully inserted {len(data)} time segment records to store_time_report")
            return True
        else:
            print(f"❌ Failed to insert time segment data to store_time_report")
            return False
            
    except Exception as e:
        print(f"❌ Database insertion error: {e}")
        return False