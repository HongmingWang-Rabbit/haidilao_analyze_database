#!/usr/bin/env python3
"""
Extract time segment data from Excel files and generate SQL insert statements.
Processes data from the '分时段基础表' sheet for the store_time_report table.

Enhanced with direct database insertion capabilities.
"""

import pandas as pd
import argparse
import os
import re
import sys
from datetime import datetime
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path for database imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import get_database_manager, setup_database_for_tests

# Suppress pandas warnings
warnings.filterwarnings('ignore')

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

def generate_upsert_sql(data, table_name):
    """Generate SQL UPSERT statement (INSERT ... ON CONFLICT) from transformed data."""
    if not data:
        return ""
    
    # Column list for store_time_report table
    columns = [
        'store_id', 'date', 'time_segment_id', 'is_holiday', 
        'tables_served_validated', 'turnover_rate'
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
    
    # Generate update columns for ON CONFLICT (exclude store_id, date, time_segment_id as they are the conflict keys)
    update_columns = [col for col in columns if col not in ['store_id', 'date', 'time_segment_id']]
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
    
    # Combine into final UPSERT SQL
    sql = f"INSERT INTO {table_name} ({column_names}) VALUES\n"
    sql += ',\n'.join(values_list)
    sql += f"\nON CONFLICT (store_id, date, time_segment_id) DO UPDATE SET\n  {update_set};"
    
    return sql

def insert_data_to_database(data, table_name='store_time_report', is_test=False):
    """Insert time segment data directly to database"""
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
            print(f"✅ Successfully inserted {len(data)} time segment records to {table_name}")
            return True
        else:
            print(f"❌ Failed to insert time segment data to {table_name}")
            return False
            
    except Exception as e:
        print(f"❌ Database insertion error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate SQL insert statements from Excel time segment data or insert directly to database')
    parser.add_argument('input_file', help='Path to the Excel file')
    parser.add_argument('--output', '-o', help='Path to the output SQL file')
    parser.add_argument('--table', '-t', default='store_time_report', help='Target table name')
    parser.add_argument('--debug', '-d', action='store_true', help='Generate CSV file for manual verification')
    parser.add_argument('--direct-db', action='store_true', help='Insert directly to database instead of generating SQL file')
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
    
    print(f"📊 Processing Excel file: {args.input_file}")
    
    # Read Excel file from the correct sheet
    try:
        df = pd.read_excel(args.input_file, sheet_name='分时段基础表')
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        print("Make sure the file contains a '分时段基础表' sheet")
        sys.exit(1)
    
    # Transform data (process ALL dates and time segments in the sheet)
    transformed_data = transform_time_segment_data(df)
    print(f"📈 Found {len(transformed_data)} rows of time segment data")
    
    # Generate output directory for debug/SQL files
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate CSV for debug mode
    if args.debug:
        # Use input filename for debug CSV
        input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
        csv_file = os.path.join(output_dir, f'debug_time_segments_{input_basename}.csv')
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
        
        # Determine output file path - use input filename with time_segments prefix
        if args.output:
            output_file = args.output
        else:
            input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
            output_file = os.path.join(output_dir, f'time_segments_{input_basename}.sql')
        
        # Write SQL to file
        with open(output_file, 'w') as f:
            f.write(sql)
        
        print(f"📄 SQL saved to: {output_file}")
    
    print("✅ Processing completed successfully")

if __name__ == '__main__':
    main() 