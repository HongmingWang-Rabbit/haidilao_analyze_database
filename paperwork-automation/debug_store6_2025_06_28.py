#!/usr/bin/env python3
"""
Debug Store 6 conversion for 2025-06-28 specifically.
Analyze the discrepancy between expected 226.6 and actual 231.3 table count.

⚠️  LEGACY STATUS: Store 6 conversion is no longer needed in daily workflow.
This debug script is kept for reference only.
"""

from scripts.convert_other_source import (
    convert_currency_to_float,
    get_last_year_single_table_consumption,
    calculate_store6_conversion_coefficient
)
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def debug_specific_date_conversion():
    """Debug Store 6 conversion for 2025-06-28"""

    input_file = "Input/daily_report/store_6_convertion_file(temporary)/HaiDiLao-report-8003-2025-6 (3).xlsx"
    target_sheet = "2025-06-28"

    print(f"=== DEBUGGING STORE 6 CONVERSION FOR {target_sheet} ===")
    print(f"Expected table count: 226.6")
    print(f"Actual table count: 231.3")
    print(f"Discrepancy: +4.7 tables")
    print()

    try:
        # Read the specific sheet
        df = pd.read_excel(input_file, sheet_name=target_sheet)
        print(
            f"✅ Successfully read sheet '{target_sheet}' with {df.shape[0]} rows, {df.shape[1]} columns")

        # Find header row
        header_row = None
        for i in range(min(5, df.shape[0])):
            if df.iloc[i, 0] and "时间" in str(df.iloc[i, 0]):
                header_row = i
                break

        if header_row is None:
            print("❌ Could not find header row")
            return

        print(f"📍 Found header row at index: {header_row}")

        # Set up columns
        columns = ['时间', '订单编号', '桌号', '就餐人数', '订单税前实收金额Totals', '订单税金Tax', 'GST', 'QST',
                   '折扣金额（合计）', '赠菜金额（合计）', '免单金额（合计）', '订单类型', '订单税前应收金额（不含税）', '小费', '舍入', '桌数', '退款订单', '订单折扣率']

        data_df = df.iloc[header_row+1:].copy()

        if data_df.shape[1] < len(columns):
            actual_columns = columns[:data_df.shape[1]]
            data_df.columns = actual_columns
        else:
            data_df.columns = columns + \
                [f'col_{i}' for i in range(len(columns), data_df.shape[1])]

        # Clean data
        data_df = data_df.dropna(subset=['时间'])
        print(f"📊 After cleaning: {len(data_df)} valid orders")

        # Process columns
        data_df['订单税前实收金额_float'] = data_df['订单税前实收金额Totals'].apply(
            convert_currency_to_float)
        data_df['就餐人数'] = pd.to_numeric(
            data_df['就餐人数'], errors='coerce').fillna(0)

        if '桌数' in data_df.columns:
            data_df['桌数'] = pd.to_numeric(
                data_df['桌数'], errors='coerce').fillna(0)
        else:
            data_df['桌数'] = 1

        if '订单折扣率' in data_df.columns:
            data_df['订单折扣率'] = pd.to_numeric(
                data_df['订单折扣率'], errors='coerce').fillna(1.0)
        else:
            data_df['订单折扣率'] = 1.0

        if '退款订单' in data_df.columns:
            data_df['是否退款'] = data_df['退款订单'] == '是'
        else:
            data_df['是否退款'] = False

        if '订单税前应收金额（不含税）' in data_df.columns:
            data_df['订单税前应收金额_float'] = data_df['订单税前应收金额（不含税）'].apply(
                convert_currency_to_float)
        else:
            data_df['订单税前应收金额_float'] = data_df['订单税前实收金额_float'] / \
                data_df['订单折扣率'].replace(0, 1)

        print(f"🔍 Data columns available: {list(data_df.columns)}")
        print()

        # Get last year consumption (2024 data for store 6)
        sheet_date = datetime.strptime(target_sheet, '%Y-%m-%d')
        last_year_consumption = get_last_year_single_table_consumption(
            6, sheet_date)
        print(
            f"📈 Store 6 last year single table consumption: {last_year_consumption:.2f} CAD")

        # Calculate basic table counts
        valid_orders = data_df[data_df['桌数'] > 0].copy()
        refund_orders = data_df[data_df['是否退款'] == True].copy()

        营业桌数 = valid_orders[~valid_orders['是否退款']]['桌数'].sum()
        print(f"📊 Original table count (营业桌数): {营业桌数:.1f}")

        # Analyze conversion logic step by step
        print("\n=== CONVERSION ANALYSIS ===")

        all_orders = pd.concat([valid_orders, refund_orders]).drop_duplicates() if len(
            refund_orders) > 0 else valid_orders
        conversion_details = []

        threshold_15_percent = last_year_consumption * 0.15
        print(f"💰 15% threshold: {threshold_15_percent:.2f} CAD")
        print()

        for idx, (_, row) in enumerate(all_orders.iterrows()):
            receivable_amount = row.get('订单税前应收金额_float', 0.0)
            discount_rate = row.get('订单折扣率', 1.0)
            tables = row.get('桌数', 0.0)
            is_refund = row.get('是否退款', False)
            order_type = str(row.get('订单类型', '')).strip()

            coefficient = calculate_store6_conversion_coefficient(
                row.to_dict(), last_year_consumption)
            contribution = tables * coefficient

            conversion_details.append({
                'order_idx': idx + 1,
                'receivable_amount': receivable_amount,
                'discount_rate': discount_rate,
                'tables': tables,
                'is_refund': is_refund,
                'order_type': order_type,
                'coefficient': coefficient,
                'contribution': contribution,
                'reason': get_conversion_reason(receivable_amount, discount_rate, is_refund, order_type, threshold_15_percent)
            })

        # Summary statistics
        total_contribution = sum(detail['contribution']
                                 for detail in conversion_details)

        print(f"📋 CONVERSION SUMMARY:")
        print(f"   Total orders processed: {len(conversion_details)}")
        print(f"   Original table count: {营业桌数:.1f}")
        print(f"   Converted table count: {total_contribution:.1f}")
        print(f"   Expected: 226.6")
        print(f"   Actual: {total_contribution:.1f}")
        print(f"   Discrepancy: {total_contribution - 226.6:.1f}")
        print()

        # Detailed breakdown by conversion coefficient
        coefficient_summary = {}
        for detail in conversion_details:
            coef = detail['coefficient']
            if coef not in coefficient_summary:
                coefficient_summary[coef] = {
                    'count': 0, 'tables': 0, 'contribution': 0}
            coefficient_summary[coef]['count'] += 1
            coefficient_summary[coef]['tables'] += detail['tables']
            coefficient_summary[coef]['contribution'] += detail['contribution']

        print("🎯 BREAKDOWN BY CONVERSION COEFFICIENT:")
        for coef in sorted(coefficient_summary.keys()):
            stats = coefficient_summary[coef]
            print(
                f"   Coefficient {coef:4.1f}: {stats['count']:3d} orders, {stats['tables']:6.1f} tables → {stats['contribution']:6.1f} contribution")
        print()

        # Show problematic orders (ones that might be causing the discrepancy)
        print("🔍 ORDERS WITH UNUSUAL CONVERSION:")
        for detail in conversion_details[:20]:  # Show first 20 orders
            if detail['coefficient'] not in [0.0, 0.7, 0.9, 1.0, -1.0]:  # Unusual coefficients
                print(
                    f"   Order {detail['order_idx']:3d}: {detail['tables']:4.1f} tables × {detail['coefficient']:4.1f} = {detail['contribution']:6.1f} ({detail['reason']})")

        # Check for potential issues
        unusual_orders = [d for d in conversion_details if d['coefficient'] not in [
            0.0, 0.7, 0.9, 1.0, -1.0]]
        if unusual_orders:
            print(
                f"⚠️  Found {len(unusual_orders)} orders with unusual coefficients")

        high_contribution_orders = [
            d for d in conversion_details if d['contribution'] > 10]
        if high_contribution_orders:
            print(
                f"⚠️  Found {len(high_contribution_orders)} orders with high contribution (>10 tables)")

        return conversion_details, total_contribution

    except Exception as e:
        print(f"❌ Error during debug analysis: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def get_conversion_reason(receivable_amount, discount_rate, is_refund, order_type, threshold_15_percent):
    """Get human-readable reason for conversion coefficient"""
    if is_refund:
        return "Refund order (-1)"
    if '外卖' in order_type or 'takeout' in order_type.lower():
        return "Takeout order (0)"
    if receivable_amount < threshold_15_percent:
        return f"Below 15% threshold ({receivable_amount:.2f} < {threshold_15_percent:.2f})"
    if discount_rate < 0.7:
        return f"Low discount rate ({discount_rate:.2f} < 0.7)"
    if 0.7 <= discount_rate < 0.8:
        return f"Discount 0.7-0.8 ({discount_rate:.2f}) → coef 0.7"
    if 0.8 <= discount_rate < 0.88:
        return f"Discount 0.8-0.88 ({discount_rate:.2f}) → coef 0.9"
    if discount_rate >= 0.88:
        return f"Discount ≥0.88 ({discount_rate:.2f}) → coef 1.0"
    return "Unknown reason"


if __name__ == "__main__":
    debug_specific_date_conversion()
