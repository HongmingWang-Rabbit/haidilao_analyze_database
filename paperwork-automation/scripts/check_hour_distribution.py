#!/usr/bin/env python3
"""Check hour distribution to understand the issue"""

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
df_july = df_all[(df_all['date'].dt.year == 2025) & (df_all['date'].dt.month == 7)]

# Add time columns
df_july['open_datetime'] = pd.to_datetime(df_july['开台时间'], errors='coerce')
df_july['open_hour'] = df_july['open_datetime'].dt.hour

# Show hour distribution
print("Hour distribution of orders:")
hour_counts = df_july['open_hour'].value_counts().sort_index()
for hour, count in hour_counts.items():
    revenue = df_july[df_july['open_hour'] == hour]['revenue_before_tax'].sum()
    print(f"Hour {hour:02d}: {count:3d} orders, ${revenue:,.2f} revenue")

# Check for NaN hours
nan_hours = df_july[df_july['open_hour'].isna()]
if len(nan_hours) > 0:
    print(f"\nOrders with invalid time: {len(nan_hours)}")
    print(f"Revenue from invalid time orders: ${nan_hours['revenue_before_tax'].sum():,.2f}")

# Total revenue check
total_revenue = df_july['revenue_before_tax'].sum()
print(f"\nTotal revenue (before tax): ${total_revenue:,.2f}")