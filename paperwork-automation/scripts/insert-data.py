#!/usr/bin/env python3
"""
Python helper script that uses pandas for advanced Excel data processing.
This is designed as a backup or for advanced use cases where pandas provides
more powerful data manipulation capabilities than the TypeScript implementation.

Enhanced with direct database insertion capabilities.
"""

import os
import sys
import pandas as pd
import re
from datetime import datetime
import warnings
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path for database imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import get_database_manager, setup_database_for_tests

# Suppress pandas warnings
warnings.filterwarnings('ignore')

def extract_date_from_filename(filename):
    """Extract a date from the filename pattern like example_daily_data_2025_6_10.xlsx"""
    pattern = r'(\d{4})_(\d{1,2})_(\d{1,2})'
    match = re.search(pattern, filename)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return None

def format_sql_value(value):
    """Format a value for SQL depending on its type"""
    if pd.isna(value) or value is None:
        return 'NULL'
    elif isinstance(value, (int, float)):
        if pd.isna(value):  # Check for NaN/Inf
            return 'NULL'
        return str(value)
    elif isinstance(value, (datetime, pd.Timestamp)):
        return f"'{value.strftime('%Y-%m-%d')}'"
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    else:
        # Escape single quotes
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

def transform_excel_data(df):
    """Transform Excel data from 营业基础表 sheet into the format needed for database insertion."""
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
    
    # Process ALL rows in the dataframe (all dates)
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
            
        # Map the data according to user specifications
        # Note: seats_total is now a fixed property of each store, not daily data
        store_data = {
            'store_id': store_ids[store_name],
            'date': formatted_date,
            'month': month,
            'is_holiday': row['节假日'] == '节假日',  # True if holiday, False if 工作日
            'tables_served': float(row['营业桌数']) if pd.notna(row['营业桌数']) else None,
            'tables_served_validated': float(row['营业桌数(考核)']) if pd.notna(row['营业桌数(考核)']) else None,
            'turnover_rate': float(row['翻台率(考核)']) if pd.notna(row['翻台率(考核)']) else None,
            'revenue_tax_included': float(row['营业收入(不含税)']) if pd.notna(row['营业收入(不含税)']) else None,
            'takeout_tables': float(row['营业桌数(考核)(外卖)']) if pd.notna(row['营业桌数(考核)(外卖)']) else None,
            'customers': int(row['就餐人数']) if pd.notna(row['就餐人数']) else None,
            'discount_total': float(row['优惠总金额(不含税)']) if pd.notna(row['优惠总金额(不含税)']) else None
        }
        
        transformed_data.append(store_data)
    
    return transformed_data

def generate_upsert_sql(data, table_name):
    """Generate SQL UPSERT statement (INSERT ... ON CONFLICT) from transformed data."""
    if not data:
        return ""
    
    # Updated column list without seats_total
    columns = [
        'store_id', 'date', 'month', 'is_holiday', 'tables_served', 
        'tables_served_validated', 'turnover_rate', 'revenue_tax_included', 
        'takeout_tables', 'customers', 'discount_total'
    ]
    
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
    
    # Generate update columns for ON CONFLICT (exclude store_id and date as they are the conflict keys)
    update_columns = [col for col in columns if col not in ['store_id', 'date']]
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
    
    # Combine into final UPSERT SQL
    sql = f"INSERT INTO {table_name} ({column_names}) VALUES\n"
    sql += ',\n'.join(values_list)
    sql += f"\nON CONFLICT (store_id, date) DO UPDATE SET\n  {update_set};"
    
    return sql

def insert_data_to_database(data, table_name='daily_report', is_test=False):
    """Insert data directly to database"""
    try:
        db_manager = get_database_manager(is_test=is_test)
        
        # Test connection first
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return False
        
        # Generate SQL
        sql = generate_upsert_sql(data, table_name)
        
        if not sql:
            print("⚠️ No SQL generated - no data to insert")
            return True
        
        # Execute SQL
        success = db_manager.execute_sql(sql)
        
        if success:
            print(f"✅ Successfully inserted {len(data)} records to {table_name}")
            return True
        else:
            print(f"❌ Failed to insert data to {table_name}")
            return False
            
    except Exception as e:
        print(f"❌ Database insertion error: {e}")
        return False

def process_excel(input_file, output_file=None, table_name='daily_report', direct_db_insert=False, is_test=False):
    """Process an Excel file and generate SQL or insert directly to database"""
    print(f"📊 Processing Excel file: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        return False
    
    # Extract date from filename
    report_date = extract_date_from_filename(input_file)
    if not report_date:
        print("⚠️ Warning: Could not extract date from filename")
        report_date = datetime.now().strftime('%Y-%m-%d')
    
    # Determine output file if not provided
    if not output_file and not direct_db_insert:
        dir_name = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        
        # Create output directory if it doesn't exist
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        output_file = os.path.join(dir_name, f"insert_data_{report_date}.sql")
    
    try:
        # Read Excel file
        df = pd.read_excel(input_file, sheet_name='营业基础表')
        print(f"📈 Found {len(df)} rows of data")
        
        # Transform data
        transformed_data = transform_excel_data(df)
        print(f"🔄 Transformed {len(transformed_data)} records")
        
        if direct_db_insert:
            # Insert directly to database
            return insert_data_to_database(transformed_data, table_name, is_test)
        else:
            # Generate SQL file
            sql = generate_upsert_sql(transformed_data, table_name)
            
            # Write SQL to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(sql)
            
            print(f"📄 SQL saved to: {output_file}")
            return True
    
    except Exception as e:
        print(f"❌ Error processing Excel file: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate SQL insert statements from Excel data or insert directly to database')
    parser.add_argument('input_file', help='Path to the Excel file')
    parser.add_argument('--output', '-o', help='Path to the output SQL file')
    parser.add_argument('--table', '-t', default='daily_report', help='Target table name')
    parser.add_argument('--debug', '-d', action='store_true', help='Generate CSV file for manual verification')
    parser.add_argument('--direct-db', action='store_true', help='Insert directly to database instead of generating SQL file')
    parser.add_argument('--test-db', action='store_true', help='Use test database (sets up test environment)')
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
    
    print(f"📊 Processing Excel file: {args.input_file}")
    
    # Read Excel file from the correct sheet
    df = pd.read_excel(args.input_file, sheet_name='营业基础表')
    
    # Transform data (process ALL dates in the sheet)
    transformed_data = transform_excel_data(df)
    print(f"📈 Found {len(transformed_data)} rows of data")
    
    # Generate output directory for debug/SQL files
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate CSV for debug mode
    if args.debug:
        # Use input filename for debug CSV
        input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
        csv_file = os.path.join(output_dir, f'debug_{input_basename}.csv')
        debug_df = pd.DataFrame(transformed_data)
        debug_df.to_csv(csv_file, index=False)
        print(f"📄 Debug CSV saved to: {csv_file}")
    
    if direct_db_insert:
        # Insert directly to database
        success = insert_data_to_database(transformed_data, args.table, is_test)
        if not success:
            sys.exit(1)
    else:
        # Generate UPSERT SQL
        sql = generate_upsert_sql(transformed_data, args.table)
        
        # Determine output file path - use input filename
        if args.output:
            output_file = args.output
        else:
            input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
            output_file = os.path.join(output_dir, f'{input_basename}.sql')
        
        # Write SQL to file
        with open(output_file, 'w') as f:
            f.write(sql)
        
        print(f"📄 SQL saved to: {output_file}")
    
    print("✅ Processing completed successfully")

if __name__ == '__main__':
    main() 