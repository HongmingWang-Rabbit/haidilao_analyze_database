#!/usr/bin/env python3
"""
Convert other source Excel format to Haidilao format.
This script transforms transactional POS data into the standard Haidilao format
with daily reports (营业基础表) and time segment reports (分时段基础表).
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import argparse
import sys
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# Add the project root to sys.path to import local modules
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import get_database_manager

def convert_currency_to_float(value):
    """Convert currency string to float."""
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        # Remove $ and convert to float
        return float(value.replace('$', '').replace(',', ''))
    return float(value)

def categorize_time_segment(timestamp_str):
    """Categorize timestamp into Haidilao time segments."""
    try:
        # Parse the timestamp
        dt = pd.to_datetime(timestamp_str)
        hour = dt.hour
        
        # Haidilao time segments
        if 8 <= hour < 14:
            return "08:00-13:59"
        elif 14 <= hour < 17:
            return "14:00-16:59"
        elif 17 <= hour < 22:
            return "17:00-21:59"
        else:  # 22:00 - 07:59 (next day)
            return "22:00-(次)07:59"
    except:
        return "08:00-13:59"  # Default fallback

def get_store_info_from_database(store_name, store_code=None, is_test=False):
    """Get store information from database, including correct seat count."""
    try:
        db_manager = get_database_manager(is_test=is_test)
        
        # Test connection first
        if not db_manager.test_connection():
            print("⚠️  Database connection failed, using default values")
            return None
        
        # Query store information by name or code
        if store_code:
            result = db_manager.fetch_one(
                "SELECT * FROM store WHERE name = %s OR id = %s",
                (store_name, store_code)
            )
        else:
            result = db_manager.fetch_one(
                "SELECT * FROM store WHERE name = %s",
                (store_name,)
            )
        
        if result:
            return {
                'country': result['country'],
                'regional_manager': result['manager'],
                'store_name': result['name'],
                'store_code': str(result['id']),  # Use database ID as store code
                'opening_date': result['opened_at'].strftime('%Y-%m-%d') if result['opened_at'] else '2024-01-09',
                'holiday_type': '节假日',
                'total_seats': result['seats_total'],  # Get actual seat count from database
            }
        else:
            print(f"⚠️  Store '{store_name}' not found in database, using default values")
            return None
            
    except Exception as e:
        print(f"⚠️  Database query failed: {e}, using default values")
        return None

def process_daily_sheet(sheet_name, df, store_info):
    """Process a single day's transaction data and aggregate it."""
    # Skip empty or header-only sheets
    if df.shape[0] <= 2:
        return None
    
    # Find the header row (contains "时间", "订单编号", etc.)
    header_row = None
    for i in range(min(5, df.shape[0])):
        if df.iloc[i, 0] and "时间" in str(df.iloc[i, 0]):
            header_row = i
            break
    
    if header_row is None:
        print(f"⚠️  Warning: Could not find header row in sheet {sheet_name}")
        return None
    
    # Set proper column names based on the actual structure
    columns = ['时间', '订单编号', '桌号', '就餐人数', '订单税前实收金额Totals', '订单税金Tax', 'GST', 'QST', 
               '折扣金额（合计）', '赠菜金额（合计）', '免单金额（合计）', '订单类型', '订单税前应收金额（不含税）', '小费', '舍入', '桌数', '退款订单', '订单折扣率']
    data_df = df.iloc[header_row+1:].copy()
    
    # Handle case where there might be fewer columns than expected
    if data_df.shape[1] < len(columns):
        # Use the actual number of columns available
        actual_columns = columns[:data_df.shape[1]]
        data_df.columns = actual_columns
    else:
        data_df.columns = columns + [f'col_{i}' for i in range(len(columns), data_df.shape[1])]
    
    # Clean and convert data
    data_df = data_df.dropna(subset=['时间'])  # Remove rows without timestamp
    data_df['订单税前实收金额_float'] = data_df['订单税前实收金额Totals'].apply(convert_currency_to_float)
    data_df['就餐人数'] = pd.to_numeric(data_df['就餐人数'], errors='coerce').fillna(0)
    
    # Process additional columns if available
    if '桌数' in data_df.columns:
        data_df['桌数'] = pd.to_numeric(data_df['桌数'], errors='coerce').fillna(0)
    else:
        data_df['桌数'] = 1  # Default to 1 table per order
    
    if '订单折扣率' in data_df.columns:
        data_df['订单折扣率'] = pd.to_numeric(data_df['订单折扣率'], errors='coerce').fillna(1.0)
    else:
        data_df['订单折扣率'] = 1.0  # Default to 100% discount rate
    
    if '退款订单' in data_df.columns:
        data_df['是否退款'] = data_df['退款订单'] == '是'
    else:
        data_df['是否退款'] = False
    
    if '折扣金额（合计）' in data_df.columns:
        data_df['折扣金额_float'] = data_df['折扣金额（合计）'].apply(convert_currency_to_float).abs()  # Take absolute value
    else:
        data_df['折扣金额_float'] = 0.0
    
    # Parse date from sheet name
    date_str = sheet_name.replace('-', '')  # Convert 2025-06-22 to 20250622
    
    # Filter out refund orders (退款订单 = 是 or 桌数 = 0)
    valid_orders = data_df[~data_df['是否退款'] & (data_df['桌数'] > 0)]
    
    # Calculate 营业桌数 = sum of all table counts (excluding refunds)
    营业桌数 = valid_orders['桌数'].sum()
    
    # Calculate 营业桌数(考核) = sum(桌数 * 订单折扣率) where 订单折扣率 >= 0.7
    qualified_orders = valid_orders[valid_orders['订单折扣率'] >= 0.7]
    营业桌数_考核 = (qualified_orders['桌数'] * qualified_orders['订单折扣率']).sum()
    
    # Calculate revenue excluding refunds
    total_revenue = valid_orders['订单税前实收金额_float'].sum()
    total_customers = valid_orders['就餐人数'].sum()
    
    # Calculate discount amount directly from the 折扣金额（合计） column
    total_discount = valid_orders['折扣金额_float'].sum()
    
    # Aggregate daily data with all required columns
    daily_data = {
        '日期': date_str,
        '国家': store_info['country'],
        '大区经理': store_info['regional_manager'],
        '门店名称': store_info['store_name'],
        '门店编码': store_info['store_code'],
        '开业时间': store_info['opening_date'],
        '节假日': store_info['holiday_type'],
        '所有餐位数': store_info['total_seats'],
        
        # Required columns for extraction system
        '营业桌数': int(营业桌数),  # Sum of all table counts (excluding refunds)
        '营业桌数(考核)': round(营业桌数_考核, 2),  # Sum of (table count * discount rate) where rate >= 0.7
        '翻台率(考核)': round(营业桌数_考核 / max(1, store_info['total_seats']), 2),  # Assessment turnover rate
        '营业收入(不含税)': round(total_revenue, 2),
        '营业桌数(考核)(外卖)': 0,  # Takeout table count (not applicable for this data)
        '就餐人数': int(total_customers),
        '优惠总金额(不含税)': round(total_discount, 2),  # Total discount amount
        
        # Additional business metrics
        '营业笔数': len(valid_orders),
        '营业额': round(total_revenue, 2),
        '平均客单价': round(total_revenue / max(1, total_customers), 2) if total_customers > 0 else 0,
        '翻台率': round(营业桌数 / max(1, store_info['total_seats']), 2),
        '营业时长': 14,
        '客满率': round((营业桌数 / max(1, store_info['total_seats'])) * 100, 1),
    }
    
    return daily_data

def process_time_segment_sheet(sheet_name, df, store_info):
    """Process a single day's transaction data and break it down by time segments."""
    # Skip empty or header-only sheets
    if df.shape[0] <= 2:
        return []
    
    # Find the header row
    header_row = None
    for i in range(min(5, df.shape[0])):
        if df.iloc[i, 0] and "时间" in str(df.iloc[i, 0]):
            header_row = i
            break
    
    if header_row is None:
        return []
    
    # Set proper column names based on the actual structure
    columns = ['时间', '订单编号', '桌号', '就餐人数', '订单税前实收金额Totals', '订单税金Tax', 'GST', 'QST', 
               '折扣金额（合计）', '赠菜金额（合计）', '免单金额（合计）', '订单类型', '订单税前应收金额（不含税）', '小费', '舍入', '桌数', '退款订单', '订单折扣率']
    data_df = df.iloc[header_row+1:].copy()
    
    # Handle case where there might be fewer columns than expected
    if data_df.shape[1] < len(columns):
        actual_columns = columns[:data_df.shape[1]]
        data_df.columns = actual_columns
    else:
        data_df.columns = columns + [f'col_{i}' for i in range(len(columns), data_df.shape[1])]
    
    # Clean and convert data
    data_df = data_df.dropna(subset=['时间'])
    data_df['订单税前实收金额_float'] = data_df['订单税前实收金额Totals'].apply(convert_currency_to_float)
    data_df['就餐人数'] = pd.to_numeric(data_df['就餐人数'], errors='coerce').fillna(0)
    data_df['分时段'] = data_df['时间'].apply(categorize_time_segment)
    
    # Process additional columns if available
    if '桌数' in data_df.columns:
        data_df['桌数'] = pd.to_numeric(data_df['桌数'], errors='coerce').fillna(0)
    else:
        data_df['桌数'] = 1
    
    if '订单折扣率' in data_df.columns:
        data_df['订单折扣率'] = pd.to_numeric(data_df['订单折扣率'], errors='coerce').fillna(1.0)
    else:
        data_df['订单折扣率'] = 1.0
    
    if '退款订单' in data_df.columns:
        data_df['是否退款'] = data_df['退款订单'] == '是'
    else:
        data_df['是否退款'] = False
    
    if '折扣金额（合计）' in data_df.columns:
        data_df['折扣金额_float'] = data_df['折扣金额（合计）'].apply(convert_currency_to_float).abs()  # Take absolute value
    else:
        data_df['折扣金额_float'] = 0.0
    
    # Parse date
    date_str = sheet_name.replace('-', '')
    
    # Group by time segment
    time_segments = []
    for segment in ["08:00-13:59", "14:00-16:59", "17:00-21:59", "22:00-(次)07:59"]:
        segment_data = data_df[data_df['分时段'] == segment]
        
        if len(segment_data) > 0:
            # Filter out refund orders for this segment
            valid_segment_orders = segment_data[~segment_data['是否退款'] & (segment_data['桌数'] > 0)]
            
            # Calculate metrics for this time segment
            segment_营业桌数 = valid_segment_orders['桌数'].sum()
            qualified_segment_orders = valid_segment_orders[valid_segment_orders['订单折扣率'] >= 0.7]
            segment_营业桌数_考核 = (qualified_segment_orders['桌数'] * qualified_segment_orders['订单折扣率']).sum()
            segment_revenue = valid_segment_orders['订单税前实收金额_float'].sum()
            segment_customers = valid_segment_orders['就餐人数'].sum()
            segment_discount = valid_segment_orders['折扣金额_float'].sum()
            
            segment_info = {
                '日期': date_str,
                '国家': store_info['country'],
                '大区经理': store_info['regional_manager'],
                '门店名称': store_info['store_name'],
                '分时段': segment,
                '节假日': store_info['holiday_type'],
                '所有餐位数': store_info['total_seats'],
                
                # Required columns for time segment extraction
                '营业桌数(考核)': round(segment_营业桌数_考核, 2),
                '翻台率(考核)': round(segment_营业桌数_考核 / max(1, store_info['total_seats']), 2),
                
                # Additional time segment metrics
                '营业桌数': int(segment_营业桌数),
                '就餐人数': int(segment_customers),
                '营业额': round(segment_revenue, 2),
                '翻台率': round(segment_营业桌数 / max(1, store_info['total_seats']), 2),
                '优惠总金额(不含税)': round(segment_discount, 2),
            }
        else:
            # Create empty segment data
            segment_info = {
                '日期': date_str,
                '国家': store_info['country'],
                '大区经理': store_info['regional_manager'],
                '门店名称': store_info['store_name'],
                '分时段': segment,
                '节假日': store_info['holiday_type'],
                '所有餐位数': store_info['total_seats'],
                
                # Required columns for time segment extraction
                '营业桌数(考核)': 0.0,
                '翻台率(考核)': 0.0,
                
                # Additional time segment metrics  
                '营业桌数': 0,
                '就餐人数': 0,
                '营业额': 0.0,
                '翻台率': 0.0,
                '优惠总金额(不含税)': 0.0,
            }
        
        time_segments.append(segment_info)
    
    return time_segments

def create_haidilao_format_excel(daily_data_list, time_segment_data_list, output_file):
    """Create Excel file in Haidilao format with proper styling."""
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Create DataFrames first
    daily_df = pd.DataFrame(daily_data_list)
    time_df = pd.DataFrame(time_segment_data_list)
    
    # Write to Excel file using pandas for better compatibility
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        daily_df.to_excel(writer, sheet_name='营业基础表', index=False)
        time_df.to_excel(writer, sheet_name='分时段基础表', index=False)
    
    print(f"✅ Converted Excel file saved: {output_file}")

def convert_other_source_to_haidilao(input_file, output_file, store_config=None, is_test=False):
    """Main conversion function."""
    
    # Default store configuration (you can customize this)
    default_store_info = {
        'country': '加拿大',
        'regional_manager': '蒋冰遇',
        'store_name': '加拿大六店',  # Default to recognized store
        'store_code': '119812',
        'opening_date': '2024-01-09',
        'holiday_type': '节假日',
        'total_seats': 56,
    }
    
    store_info = store_config if store_config else default_store_info
    
    print(f"🔄 Converting {input_file} to Haidilao format...")
    print(f"📍 Store: {store_info['store_name']} ({store_info['store_code']})")
    
    # Try to get actual store information from database
    db_store_info = get_store_info_from_database(store_info['store_name'], store_info['store_code'], is_test)
    if db_store_info:
        print(f"✅ Found store in database with {db_store_info['total_seats']} seats")
        store_info = db_store_info
    else:
        print(f"⚠️  Using default configuration with {store_info['total_seats']} seats")
    
    # Read all sheets from the input file
    excel_file = pd.ExcelFile(input_file)
    sheet_names = [name for name in excel_file.sheet_names if name.startswith('2025-')]
    
    print(f"📊 Found {len(sheet_names)} daily sheets to process")
    
    daily_data_list = []
    time_segment_data_list = []
    
    for sheet_name in sorted(sheet_names):
        print(f"  📅 Processing {sheet_name}...")
        df = pd.read_excel(input_file, sheet_name=sheet_name, header=None)
        
        # Process daily aggregation
        daily_data = process_daily_sheet(sheet_name, df, store_info)
        if daily_data:
            daily_data_list.append(daily_data)
        
        # Process time segment breakdown
        time_segments = process_time_segment_sheet(sheet_name, df, store_info)
        time_segment_data_list.extend(time_segments)
    
    print(f"📋 Generated {len(daily_data_list)} daily records")
    print(f"⏰ Generated {len(time_segment_data_list)} time segment records")
    
    # Create output Excel file
    create_haidilao_format_excel(daily_data_list, time_segment_data_list, output_file)
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Convert other source Excel format to Haidilao format')
    parser.add_argument('input_file', help='Path to the other source Excel file')
    parser.add_argument('--output', '-o', help='Output file path', default='output/converted_haidilao_format.xlsx')
    parser.add_argument('--store-name', help='Store name to use in conversion', default='加拿大六店')
    parser.add_argument('--store-code', help='Store code to use in conversion', default='119812')
    parser.add_argument('--country', help='Country name', default='加拿大')
    parser.add_argument('--manager', help='Regional manager name', default='蒋冰遇')
    parser.add_argument('--test', action='store_true', help='Use test database instead of production')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Create store configuration
    store_config = {
        'country': args.country,
        'regional_manager': args.manager,
        'store_name': args.store_name,
        'store_code': args.store_code,
        'opening_date': '2024-01-01',
        'holiday_type': '节假日',
        'total_seats': 60,
    }
    
    print("🍲 Haidilao Format Converter")
    print("=" * 50)
    
    # Perform conversion
    if convert_other_source_to_haidilao(args.input_file, args.output, store_config, args.test):
        print("\n🎉 Conversion completed successfully!")
        print(f"📄 Output file: {args.output}")
        print(f"💡 You can now use this file with: python3 scripts/extract-all.py {args.output}")
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 