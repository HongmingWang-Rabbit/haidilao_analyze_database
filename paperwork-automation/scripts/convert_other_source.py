#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert other source Excel format to Haidilao format.
This script transforms transactional POS data into the standard Haidilao format
with daily reports (营业基础表) and time segment reports (分时段基础表).

⚠️  LEGACY STATUS: Store 6 conversion is no longer needed in daily workflow.
This script is kept for reference but has been removed from automation menu.
"""

import sys
import os

# Fix encoding issues for Windows console
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from utils.database import get_database_manager
import pandas as pd
import numpy as np
import os
from pathlib import Path
import argparse
import sys
import warnings
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Add the project root to sys.path to import local modules
sys.path.append(str(Path(__file__).parent.parent))


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
            print("WARNING: Database connection failed, using default values")
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
                # Use database ID as store code
                'store_code': str(result['id']),
                'opening_date': result['opened_at'].strftime('%Y-%m-%d') if result['opened_at'] else '2024-01-09',
                'holiday_type': '节假日',
                # Get actual seat count from database
                'total_seats': result['seats_total'],
            }
        else:
            print(
                f"WARNING: Store '{store_name}' not found in database, using default values")
            return None

    except Exception as e:
        print(f"WARNING: Database query failed: {e}, using default values")
        return None


def get_last_year_single_table_consumption(store_id, current_date, is_test=False):
    """Get store's last year single table consumption for conversion calculation."""
    try:
        db_manager = get_database_manager(is_test=is_test)

        # Test database connection first
        if not db_manager.test_connection():
            print(
                f"WARNING: Database connection failed for store {store_id}, using fallback estimate")
            return 300.0

        # Calculate last year's date range
        current_year = current_date.year
        last_year = current_year - 1

        print(
            f"Querying last year ({last_year}) data for store {store_id}...")

        # Query last year's data from daily_report
        query = """
        SELECT 
            SUM(revenue_tax_not_included) as total_revenue,
            SUM(tables_served_validated) as total_tables
        FROM daily_report 
        WHERE store_id = %s 
        AND EXTRACT(YEAR FROM date) = %s
        AND tables_served_validated > 0
        """

        result = db_manager.fetch_one(query, (store_id, last_year))

        if result and result['total_revenue'] and result['total_tables']:
            consumption = float(result['total_revenue']) / \
                float(result['total_tables'])
            print(
                f"Found historical data: {result['total_revenue']:.2f} revenue / {result['total_tables']:.2f} tables = {consumption:.2f} CAD per table")
            return consumption
        else:
            # Fallback: use a reasonable estimate based on current data
            print(
                f"WARNING: No last year ({last_year}) data found for store {store_id}, using fallback estimate of 300.00 CAD")
            return 300.0  # Default CAD per table estimate

    except Exception as e:
        print(
            f"WARNING: Error getting last year data for store {store_id}: {e}")
        print(f"   Using fallback estimate of 300.00 CAD per table")
        return 300.0  # Default CAD per table estimate


def calculate_store6_conversion_coefficient(row, last_year_single_table_consumption):
    """
    Calculate Store 6 conversion coefficient based on new rules:
    1. 应收金额小于门店上年度单桌消费15%，折算系数0；
    2. 账单折扣率小于0.7，折算系数0；
    3. 应收金额大于或等于门店上年度单桌消费15%情况下：
       (1) 账单折扣率0.7（含）-0.8，折算系数0.7；
       (2) 账单折扣率0.8（含）-0.88，折算系数0.9；
       (3) 账单折扣率0.88（含）以上，折算系数1；
    4. 外卖算为0
    5. 退款单算为-1
    """

    # Check for refund orders first (退款单算为-1)
    if row.get('是否退款', False):
        return -1.0

    # Check for takeout orders (外卖算为0)
    order_type = str(row.get('订单类型', '')).strip()
    if '外卖' in order_type or 'takeout' in order_type.lower():
        return 0.0

    # Get receivable amount and discount rate
    receivable_amount = row.get('订单税前应收金额_float', 0.0)
    if '订单税前应收金额（不含税）' in row:
        receivable_amount = convert_currency_to_float(row['订单税前应收金额（不含税）'])

    # Use precise discount rate calculated from actual amounts
    discount_rate = row.get('订单折扣率', 1.0)

    # Calculate 15% threshold
    threshold_15_percent = last_year_single_table_consumption * 0.15

    # Rule 1: 应收金额小于门店上年度单桌消费15%，折算系数0
    if receivable_amount < threshold_15_percent:
        return 0.0

    # Rule 2: 账单折扣率小于0.7，折算系数0
    if discount_rate < 0.7:
        return 0.0

    # Rule 3: 应收金额大于或等于门店上年度单桌消费15%情况下
    if receivable_amount >= threshold_15_percent:
        if 0.7 <= discount_rate < 0.8:
            return 0.7
        elif 0.8 <= discount_rate < 0.88:
            return 0.9
        elif discount_rate >= 0.88:
            return 1.0

    # Default fallback
    return 0.0


def process_daily_sheet(sheet_name, df, store_info):
    """Process a single day's transaction data and aggregate it."""
    # Skip empty or header-only sheets
    if df.shape[0] <= 2:
        return None

    # Find the header row (contains "开台时间", "订单编号", etc.)
    header_row = None
    for i in range(min(5, df.shape[0])):
        if df.iloc[i, 0] and ("时间" in str(df.iloc[i, 0]) or "开台时间" in str(df.iloc[i, 0])):
            header_row = i
            break

    if header_row is None:
        print(f"WARNING: Could not find header row in sheet {sheet_name}")
        return None

    # Set proper column names based on the actual structure from the debug output
    columns = ['开台时间', '完结时间', '订单编号', '桌号', '就餐人数', '订单税前实收金额Totals', '订单税金Tax', 'GST', 'QST',
               '折扣金额（合计）', '赠菜金额（合计）', '免单金额（合计）', '订单类型', '订单税前应收金额（不含税）', '小费', '舍入', '桌数', '退款订单', '原始单号', '订单折扣率']
    data_df = df.iloc[header_row+1:].copy()

    # Handle case where there might be fewer columns than expected
    if data_df.shape[1] < len(columns):
        # Use the actual number of columns available
        actual_columns = columns[:data_df.shape[1]]
        data_df.columns = actual_columns
    else:
        data_df.columns = columns + \
            [f'col_{i}' for i in range(len(columns), data_df.shape[1])]

    # Clean and convert data
    data_df = data_df.dropna(subset=['开台时间'])  # Remove rows without timestamp
    data_df['订单税前实收金额_float'] = data_df['订单税前实收金额Totals'].apply(
        convert_currency_to_float)
    data_df['就餐人数'] = pd.to_numeric(data_df['就餐人数'], errors='coerce').fillna(0)

    # Process additional columns if available
    if '桌数' in data_df.columns:
        data_df['桌数'] = pd.to_numeric(data_df['桌数'], errors='coerce').fillna(0)
    else:
        data_df['桌数'] = 1  # Default to 1 table per order

    # Calculate precise discount rate from raw transaction amounts instead of using pre-calculated rounded Column U
    # discount_rate = actual_paid / receivable_amount
    if '订单税前应收金额（不含税）' in data_df.columns:
        data_df['订单税前应收金额_for_rate'] = data_df['订单税前应收金额（不含税）'].apply(
            convert_currency_to_float)
        data_df['订单折扣率'] = data_df.apply(
            lambda row: row['订单税前实收金额_float'] / row['订单税前应收金额_for_rate']
            if row['订单税前应收金额_for_rate'] > 0 else 1.0,
            axis=1
        )
    else:
        # Fallback: if no receivable amount column, use pre-calculated rate
        if '订单折扣率' in data_df.columns:
            data_df['订单折扣率'] = pd.to_numeric(
                data_df['订单折扣率'], errors='coerce').fillna(1.0)
        else:
            data_df['订单折扣率'] = 1.0  # Default to 100% discount rate

    if '退款订单' in data_df.columns:
        data_df['是否退款'] = data_df['退款订单'] == '是'
    else:
        data_df['是否退款'] = False

    if '折扣金额（合计）' in data_df.columns:
        data_df['折扣金额_float'] = data_df['折扣金额（合计）'].apply(
            convert_currency_to_float).abs()  # Take absolute value
    else:
        data_df['折扣金额_float'] = 0.0

    # Add receivable amount conversion if available
    if '订单税前应收金额（不含税）' in data_df.columns:
        data_df['订单税前应收金额_float'] = data_df['订单税前应收金额（不含税）'].apply(
            convert_currency_to_float)
    else:
        # Estimate receivable amount from actual amount and discount
        data_df['订单税前应收金额_float'] = data_df['订单税前实收金额_float'] / \
            data_df['订单折扣率'].replace(0, 1)

    # Parse date from sheet name
    date_str = sheet_name.replace('-', '')  # Convert 2025-06-22 to 20250622

    # Parse the date for last year calculation
    try:
        sheet_date = datetime.strptime(sheet_name, '%Y-%m-%d')
    except:
        sheet_date = datetime.now()  # Fallback to current date

    # Get store's last year single table consumption (only query once per conversion)
    store_id = int(store_info['store_code'])
    if not hasattr(convert_other_source_to_haidilao, '_cached_consumption'):
        convert_other_source_to_haidilao._cached_consumption = get_last_year_single_table_consumption(
            store_id, sheet_date)
        print(f"Store {store_id} last year single table consumption: {convert_other_source_to_haidilao._cached_consumption:.2f} CAD")

    last_year_consumption = convert_other_source_to_haidilao._cached_consumption

    # For revenue calculation: Include ALL order types (堂食, 外卖, 配送)
    # For table calculation: Only use 堂食 (dine-in) orders for table counts

    # Step 1: Calculate REVENUE from ALL order types (excluding refunds)
    all_valid_orders = data_df[data_df['桌数'] > 0].copy()
    all_revenue_orders = all_valid_orders[~all_valid_orders['是否退款']].copy()
    total_revenue = all_revenue_orders['订单税前实收金额_float'].sum()

    print(
        f"  -> Revenue from ALL order types: {len(all_revenue_orders)} orders, {total_revenue:,.2f} CAD")

    # Step 2: Calculate TABLE COUNTS from dine-in orders only
    if '订单类型' in data_df.columns:
        dine_in_orders = data_df[data_df['订单类型'] == '堂食'].copy()
        print(
            f"  -> Table calculation using dine-in orders: {len(dine_in_orders)}/{len(data_df)} orders")
    else:
        dine_in_orders = data_df.copy()  # If no order type column, assume all are dine-in
        print(
            f"  -> No order type column found, assuming all {len(dine_in_orders)} orders are dine-in")

    # Filter out orders with 桌数 = 0 (but keep refunds for negative calculation)
    valid_orders = dine_in_orders[dine_in_orders['桌数'] > 0].copy()
    refund_orders = dine_in_orders[dine_in_orders['是否退款'] == True].copy()

    # Calculate 营业桌数 = sum of all table counts (excluding refunds, but including invalid discount rates)
    营业桌数 = valid_orders[~valid_orders['是否退款']]['桌数'].sum()

    # NEW STORE 6 CONVERSION LOGIC
    # Calculate conversion coefficients for each order
    all_orders = pd.concat([valid_orders, refund_orders]).drop_duplicates()
    conversion_coefficients = []

    for _, row in all_orders.iterrows():
        coefficient = calculate_store6_conversion_coefficient(
            row.to_dict(), last_year_consumption)
        conversion_coefficients.append({
            'order_row': row.name,
            'tables': row['桌数'],
            'coefficient': coefficient,
            'contribution': row['桌数'] * coefficient
        })

    # Calculate 营业桌数(考核) using new conversion logic
    营业桌数_考核 = sum(coef['contribution'] for coef in conversion_coefficients)

    # Debug information
    total_orders = len(conversion_coefficients)
    valid_conversions = [
        c for c in conversion_coefficients if c['coefficient'] > 0]
    negative_conversions = [
        c for c in conversion_coefficients if c['coefficient'] < 0]

    # Only show detailed conversion summary for first sheet to avoid spam
    if not hasattr(process_daily_sheet, '_shown_detail'):
        print(
            f"  -> {total_orders} orders, {len(valid_conversions)} valid, {len(negative_conversions)} refunds")
        tables_count = float(营业桌数)
        assessment_count = float(营业桌数_考核)
        print(
            f"  -> Tables: {tables_count:.1f}, Assessment: {assessment_count:.1f}")
        print(
            f"  -> Revenue: {total_revenue:,.2f} CAD (includes delivery & takeout)")
        process_daily_sheet._shown_detail = True

    # Calculate customers and discount from dine-in orders only (for consistency with table calculations)
    total_customers = valid_orders[~valid_orders['是否退款']]['就餐人数'].sum()
    total_discount = valid_orders[~valid_orders['是否退款']]['折扣金额_float'].sum()

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
        # NEW: Sum of (table count * conversion coefficient) using new rules
        '营业桌数(考核)': round(营业桌数_考核, 2),
        # Assessment turnover rate
        '翻台率(考核)': round(营业桌数_考核 / max(1, store_info['total_seats']), 2),
        '营业收入(不含税)': round(total_revenue, 2),
        '营业桌数(考核)(外卖)': 0,  # Takeout table count (handled in conversion logic)
        '就餐人数': int(total_customers),
        '优惠总金额(不含税)': round(total_discount, 2),  # Total discount amount

        # Additional business metrics
        '营业笔数': len(valid_orders[~valid_orders['是否退款']]),
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
        if df.iloc[i, 0] and ("时间" in str(df.iloc[i, 0]) or "开台时间" in str(df.iloc[i, 0])):
            header_row = i
            break

    if header_row is None:
        return []

    # Set proper column names based on the actual structure from the debug output
    columns = ['开台时间', '完结时间', '订单编号', '桌号', '就餐人数', '订单税前实收金额Totals', '订单税金Tax', 'GST', 'QST',
               '折扣金额（合计）', '赠菜金额（合计）', '免单金额（合计）', '订单类型', '订单税前应收金额（不含税）', '小费', '舍入', '桌数', '退款订单', '原始单号', '订单折扣率']
    data_df = df.iloc[header_row+1:].copy()

    # Handle case where there might be fewer columns than expected
    if data_df.shape[1] < len(columns):
        actual_columns = columns[:data_df.shape[1]]
        data_df.columns = actual_columns
    else:
        data_df.columns = columns + \
            [f'col_{i}' for i in range(len(columns), data_df.shape[1])]

    # Clean and convert data
    data_df = data_df.dropna(subset=['开台时间'])
    data_df['订单税前实收金额_float'] = data_df['订单税前实收金额Totals'].apply(
        convert_currency_to_float)
    data_df['就餐人数'] = pd.to_numeric(data_df['就餐人数'], errors='coerce').fillna(0)
    data_df['分时段'] = data_df['开台时间'].apply(categorize_time_segment)

    # Process additional columns if available
    if '桌数' in data_df.columns:
        data_df['桌数'] = pd.to_numeric(data_df['桌数'], errors='coerce').fillna(0)
    else:
        data_df['桌数'] = 1

    # Calculate precise discount rate from raw transaction amounts instead of using pre-calculated rounded Column U
    # discount_rate = actual_paid / receivable_amount
    if '订单税前应收金额（不含税）' in data_df.columns:
        data_df['订单税前应收金额_for_rate'] = data_df['订单税前应收金额（不含税）'].apply(
            convert_currency_to_float)
        data_df['订单折扣率'] = data_df.apply(
            lambda row: row['订单税前实收金额_float'] / row['订单税前应收金额_for_rate']
            if row['订单税前应收金额_for_rate'] > 0 else 1.0,
            axis=1
        )
    else:
        # Fallback: if no receivable amount column, use pre-calculated rate
        if '订单折扣率' in data_df.columns:
            data_df['订单折扣率'] = pd.to_numeric(
                data_df['订单折扣率'], errors='coerce').fillna(1.0)
        else:
            data_df['订单折扣率'] = 1.0

    if '退款订单' in data_df.columns:
        data_df['是否退款'] = data_df['退款订单'] == '是'
    else:
        data_df['是否退款'] = False

    if '折扣金额（合计）' in data_df.columns:
        data_df['折扣金额_float'] = data_df['折扣金额（合计）'].apply(
            convert_currency_to_float).abs()  # Take absolute value
    else:
        data_df['折扣金额_float'] = 0.0

    # Add receivable amount conversion if available
    if '订单税前应收金额（不含税）' in data_df.columns:
        data_df['订单税前应收金额_float'] = data_df['订单税前应收金额（不含税）'].apply(
            convert_currency_to_float)
    else:
        # Estimate receivable amount from actual amount and discount
        data_df['订单税前应收金额_float'] = data_df['订单税前实收金额_float'] / \
            data_df['订单折扣率'].replace(0, 1)

    # Parse date
    date_str = sheet_name.replace('-', '')

    # Parse the date for last year calculation
    try:
        sheet_date = datetime.strptime(sheet_name, '%Y-%m-%d')
    except:
        sheet_date = datetime.now()  # Fallback to current date

    # Get store's last year single table consumption (use cached value)
    store_id = int(store_info['store_code'])
    if hasattr(convert_other_source_to_haidilao, '_cached_consumption'):
        last_year_consumption = convert_other_source_to_haidilao._cached_consumption
    else:
        last_year_consumption = get_last_year_single_table_consumption(
            store_id, sheet_date)

    # Group by time segment
    time_segments = []
    for segment in ["08:00-13:59", "14:00-16:59", "17:00-21:59", "22:00-(次)07:59"]:
        segment_data = data_df[data_df['分时段'] == segment]

        if len(segment_data) > 0:
            # Filter for 堂食 (dine-in) orders only within this time segment
            if '订单类型' in segment_data.columns:
                segment_dine_in = segment_data[segment_data['订单类型'] == '堂食'].copy(
                )
            else:
                segment_dine_in = segment_data.copy()  # Assume all are dine-in if no column

            # Filter orders by table count > 0 (but keep refunds for negative calculation)
            valid_segment_orders = segment_dine_in[segment_dine_in['桌数'] > 0].copy(
            )
            refund_segment_orders = segment_dine_in[segment_dine_in['是否退款'] == True].copy(
            )

            # Calculate metrics for this time segment using NEW conversion logic
            segment_营业桌数 = valid_segment_orders[~valid_segment_orders['是否退款']]['桌数'].sum(
            )

            # NEW STORE 6 CONVERSION LOGIC for time segments
            all_segment_orders = pd.concat(
                [valid_segment_orders, refund_segment_orders]).drop_duplicates()
            segment_conversion_coefficients = []

            for _, row in all_segment_orders.iterrows():
                coefficient = calculate_store6_conversion_coefficient(
                    row.to_dict(), last_year_consumption)
                segment_conversion_coefficients.append({
                    'tables': row['桌数'],
                    'coefficient': coefficient,
                    'contribution': row['桌数'] * coefficient
                })

            # Calculate 营业桌数(考核) using new conversion logic
            segment_营业桌数_考核 = sum(coef['contribution']
                                  for coef in segment_conversion_coefficients)

            segment_revenue = valid_segment_orders[~valid_segment_orders['是否退款']]['订单税前实收金额_float'].sum(
            )
            segment_customers = valid_segment_orders[~valid_segment_orders['是否退款']]['就餐人数'].sum(
            )
            segment_discount = valid_segment_orders[~valid_segment_orders['是否退款']]['折扣金额_float'].sum(
            )

            segment_info = {
                '日期': date_str,
                '国家': store_info['country'],
                '大区经理': store_info['regional_manager'],
                '门店名称': store_info['store_name'],
                '分时段': segment,
                '节假日': store_info['holiday_type'],
                '所有餐位数': store_info['total_seats'],

                # Required columns for time segment extraction - using NEW conversion logic
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
    try:
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

        return True
    except Exception as e:
        print(f"ERROR: Failed to create Excel file - {e}")
        return False


def convert_other_source_to_haidilao(input_file, output_file, store_config=None, is_test=False):
    """Convert other source Excel to Haidilao format."""
    print("Converting Store 6 report to Haidilao format...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Test mode: {is_test}")

    # Default store configuration for 加拿大六店
    if store_config is None:
        store_config = {
            'country': '加拿大',
            'regional_manager': '蒋冰遇',
            'store_name': '加拿大六店',
            'store_code': '6',  # Fixed: Use correct Store 6 ID
            'opening_date': '2024-01-09',
            'holiday_type': '节假日',
            'total_seats': 56,
        }

    # Try to get actual store information from database
    db_store_info = get_store_info_from_database(
        store_config['store_name'], store_config['store_code'], is_test)
    if db_store_info:
        store_config.update(db_store_info)

    # Read Excel file
    print(f"Reading Excel file: {input_file}")
    try:
        excel_file = pd.ExcelFile(input_file)
        sheet_names = excel_file.sheet_names
        print(f"Found {len(sheet_names)} sheets: {sheet_names}")
    except Exception as e:
        print(f"ERROR reading Excel file: {e}")
        return False

    daily_data_list = []
    time_segment_data_list = []

    # Process each sheet (each sheet represents a day)
    print(f"Processing {len(sheet_names)} daily sheets...")
    for i, sheet_name in enumerate(sheet_names, 1):
        # Show progress every 5 sheets or for first/last
        if i == 1 or i == len(sheet_names) or i % 5 == 0:
            print(f"  Processing sheet {i}/{len(sheet_names)}: {sheet_name}")

        try:
            df = pd.read_excel(input_file, sheet_name=sheet_name)

            # Process daily aggregation
            daily_data = process_daily_sheet(sheet_name, df, store_config)
            if daily_data:
                daily_data_list.append(daily_data)

            # Process time segment breakdown
            time_segment_data = process_time_segment_sheet(
                sheet_name, df, store_config)
            if time_segment_data:
                time_segment_data_list.extend(time_segment_data)

        except Exception as e:
            print(f"ERROR: Failed to process sheet {sheet_name} - {e}")
            continue

    if not daily_data_list:
        print("ERROR: No valid data found to convert")
        print(
            f"   Processed {len(sheet_names)} sheets but found no valid daily data")
        return False

    print(
        f"Successfully processed {len(daily_data_list)} daily records and {len(time_segment_data_list)} time segment records")

    # Create output Excel file
    print(f"Creating output file: {output_file}")
    success = create_haidilao_format_excel(
        daily_data_list, time_segment_data_list, output_file)

    if success:
        print("Conversion completed successfully")
        return True
    else:
        print("ERROR: Failed to create output file")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Convert other source Excel format to Haidilao format')
    parser.add_argument('input_file', help='Path to input Excel file')
    parser.add_argument('--output', '-o', help='Output file path',
                        default='output/converted_haidilao_format.xlsx')
    parser.add_argument(
        '--store-name', help='Store name to use in conversion', default='加拿大六店')
    parser.add_argument(
        '--store-code', help='Store code to use in conversion', default='6')
    parser.add_argument('--country', help='Country name', default='加拿大')
    parser.add_argument(
        '--manager', help='Regional manager name', default='蒋冰遇')
    parser.add_argument('--test', action='store_true',
                        help='Use test database instead of production')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    store_config = {
        'store_name': args.store_name,
        'store_code': args.store_code,
        'country': args.country,
        'regional_manager': args.manager,
        'opening_date': '2024-01-09',
        'holiday_type': '节假日',
        'total_seats': 56,
    }

    try:
        success = convert_other_source_to_haidilao(
            args.input_file,
            args.output,
            store_config,
            is_test=args.test
        )

        if not success:
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: Conversion failed - {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
