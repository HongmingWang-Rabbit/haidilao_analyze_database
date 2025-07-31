#!/usr/bin/env python3
"""Debug datetime parsing issue"""

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

# Get the raw data before parsing
result = processor._read_daily_data(input_file)
if result is None:
    print("Failed to read data")
    sys.exit(1)

df_all, sheet_count = result

# Check the raw time data for early morning hours
df = df_all[(df_all['date'].dt.year == 2025) & (df_all['date'].dt.month == 7)]

# Look at the raw time strings
print("Sample of raw 开台时间 values:")
print(df['开台时间'].head(20))
print(f"\nData type of 开台时间: {df['开台时间'].dtype}")

# Try to parse and check for issues
df['open_datetime'] = pd.to_datetime(df['开台时间'], errors='coerce')
df['open_hour'] = df['open_datetime'].dt.hour

# Find rows where hour would be 0, 1, or 3
early_morning_mask = df['open_hour'].isin([0, 1, 3])
early_morning_df = df[early_morning_mask]

print(f"\n\nFound {len(early_morning_df)} orders in hours 0, 1, 3")
print("\nSample of early morning orders:")
print(early_morning_df[['开台时间', 'open_datetime', 'open_hour', 'revenue_before_tax']].head(10))

# Check if the datetime parsing is different in processor
print("\n\nChecking if dates are causing issues:")
for idx, row in early_morning_df.head(5).iterrows():
    print(f"Date: {row['date']}, Time: {row['开台时间']}, Parsed hour: {row['open_hour']}")