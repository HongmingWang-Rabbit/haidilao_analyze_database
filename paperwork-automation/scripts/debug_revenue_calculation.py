#!/usr/bin/env python3
"""Debug revenue calculation to find discrepancy"""

import os
import sys
import pandas as pd

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from lib.hi_bowl_daily_processor import HiBowlDailyProcessor
from lib.excel_utils import safe_read_excel

# Create processor
processor = HiBowlDailyProcessor()

# Read test data
input_file = os.path.join(
    project_root, 'Input', 'daily_report', 'hi-bowl-report',
    'daily-data', 'HaiDiLao-report-2025-7 (1).xlsx'
)

# Process the data
result = processor._read_daily_data(input_file)
if result is None:
    print("Failed to read data")
    sys.exit(1)

df_all, sheet_count = result

# Filter for July 2025
df_july = df_all[(df_all['date'].dt.year == 2025) & (df_all['date'].dt.month == 7)]

print(f"Total records for July 2025: {len(df_july)}")
print(f"\nChecking revenue columns...")

# Check what revenue columns we have
revenue_cols = ['revenue_before_tax', 'tax', 'gross_revenue']
for col in revenue_cols:
    if col in df_july.columns:
        total = df_july[col].sum()
        print(f"{col}: ${total:,.2f}")

# Calculate total revenue (before tax + tax)
if 'revenue_before_tax' in df_july.columns and 'tax' in df_july.columns:
    total_revenue = df_july['revenue_before_tax'].sum() + df_july['tax'].sum()
    print(f"\nTotal revenue (revenue_before_tax + tax): ${total_revenue:,.2f}")

# Add time columns for analysis
df_july['open_datetime'] = pd.to_datetime(df_july['开台时间'], errors='coerce')
df_july['open_hour'] = df_july['open_datetime'].dt.hour

# Check time segment breakdown
print("\n\nTime segment analysis:")
time_segments = {
    '08:00-13:59': (8, 14),
    '14:00-16:59': (14, 17),
    '17:00-21:59': (17, 22),
    '22:00-07:59': (22, 32)  # 32 = 8 + 24 (next day)
}

total_by_segment = 0
for segment_name, (start_hour, end_hour) in time_segments.items():
    if start_hour < end_hour:
        # Normal case (same day)
        segment_mask = (df_july['open_hour'] >= start_hour) & (df_july['open_hour'] < end_hour)
    else:
        # Overnight case (22:00-07:59)
        segment_mask = (df_july['open_hour'] >= start_hour) | (df_july['open_hour'] < (end_hour - 24))
    
    segment_df = df_july[segment_mask]
    segment_revenue = segment_df['revenue_before_tax'].sum() + segment_df['tax'].sum()
    segment_count = len(segment_df)
    
    total_by_segment += segment_revenue
    
    print(f"\n{segment_name}:")
    print(f"  Orders: {segment_count}")
    print(f"  Revenue: ${segment_revenue:,.2f}")
    
    # Show some sample orders
    if segment_count > 0:
        sample = segment_df[['开台时间', 'revenue_before_tax', 'tax']].head(3)
        print(f"  Sample orders:")
        for idx, row in sample.iterrows():
            rev_total = row['revenue_before_tax'] + row['tax']
            print(f"    {row['开台时间']} - Revenue: ${row['revenue_before_tax']:.2f} + Tax: ${row['tax']:.2f} = ${rev_total:.2f}")

print(f"\n\nTotal revenue from segments: ${total_by_segment:,.2f}")
print(f"Difference from total: ${abs(total_revenue - total_by_segment):,.2f}")

# Check for any orders outside normal hours
outside_mask = ~((df_july['open_hour'] >= 8) & (df_july['open_hour'] < 22))
outside_orders = df_july[outside_mask]
if len(outside_orders) > 0:
    print(f"\nOrders outside 08:00-22:00: {len(outside_orders)}")
    outside_revenue = outside_orders['revenue_before_tax'].sum() + outside_orders['tax'].sum()
    print(f"Revenue from outside hours: ${outside_revenue:,.2f}")

# Let's also check just revenue_before_tax totals
print("\n\nRevenue before tax by segment:")
total_before_tax = 0
for segment_name, (start_hour, end_hour) in time_segments.items():
    if start_hour < end_hour:
        segment_mask = (df_july['open_hour'] >= start_hour) & (df_july['open_hour'] < end_hour)
    else:
        segment_mask = (df_july['open_hour'] >= start_hour) | (df_july['open_hour'] < (end_hour - 24))
    
    segment_revenue_before_tax = df_july[segment_mask]['revenue_before_tax'].sum()
    total_before_tax += segment_revenue_before_tax
    print(f"{segment_name}: ${segment_revenue_before_tax:,.2f}")

print(f"\nTotal revenue before tax from segments: ${total_before_tax:,.2f}")
print(f"Total revenue before tax overall: ${df_july['revenue_before_tax'].sum():,.2f}")