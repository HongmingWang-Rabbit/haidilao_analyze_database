#!/usr/bin/env python3
"""Debug overnight segment in detail"""

import os
import sys
import pandas as pd

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from lib.hi_bowl_daily_processor import HiBowlDailyProcessor

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
df = df_all[(df_all['date'].dt.year == 2025) & (df_all['date'].dt.month == 7)]

# Convert time strings to datetime
df['open_datetime'] = pd.to_datetime(df['开台时间'], errors='coerce')
df['close_datetime'] = pd.to_datetime(df['完结时间'], errors='coerce')

# Get hour from open time
df['open_hour'] = df['open_datetime'].dt.hour

print("Hour distribution in the data:")
print(df['open_hour'].value_counts().sort_index())

print("\nChecking overnight segment logic:")
print("Condition: (hour >= 22) OR (hour < 8)")

# Test the overnight mask
overnight_mask = (df['open_hour'] >= 22) | (df['open_hour'] < 8)
overnight_df = df[overnight_mask]

print(f"\nTotal overnight orders: {len(overnight_df)}")
print(f"Total overnight revenue: ${overnight_df['revenue_before_tax'].sum():,.2f}")

print("\nBreakdown by hour:")
for hour in sorted(overnight_df['open_hour'].unique()):
    hour_df = overnight_df[overnight_df['open_hour'] == hour]
    print(f"  Hour {hour:02d}: {len(hour_df)} orders, ${hour_df['revenue_before_tax'].sum():,.2f}")

# Check for NaN hours
nan_hours = df[df['open_hour'].isna()]
print(f"\nOrders with NaN hour: {len(nan_hours)}")
if len(nan_hours) > 0:
    print("Sample of orders with NaN hour:")
    print(nan_hours[['开台时间', 'revenue_before_tax']].head())

# Check if the filtering is different
print("\n\nNow testing with the exact processor logic:")
# Simulate the processor's calculation
summary = processor._calculate_summary(df_all, '202507', sheet_count)
print(f"Processor's overnight revenue: ${summary.get('revenue_22:00-07:59', 0):,.2f}")
print(f"Processor's overnight orders: {summary.get('orders_22:00-07:59', 0)}")