#!/usr/bin/env python3
"""Debug the exact processor flow"""

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

# Process the data exactly as the processor does
result = processor._read_daily_data(input_file)
if result is None:
    print("Failed to read data")
    sys.exit(1)

df, sheet_count = result

# Now follow the _calculate_summary flow exactly
target_month = '202507'
target_year = int(target_month[:4])
target_mon = int(target_month[4:6])
df = df[df['date'].dt.year == target_year]
df = df[df['date'].dt.month == target_mon]

print(f"After filtering, df has {len(df)} rows")

# Convert time strings to datetime for time segment analysis
df['open_datetime'] = pd.to_datetime(df['开台时间'], errors='coerce')
df['close_datetime'] = pd.to_datetime(df['完结时间'], errors='coerce')

# Get hour from open time (do this ONCE outside the loop)
df['open_hour'] = df['open_datetime'].dt.hour

print(f"\nHour distribution after conversion:")
print(df['open_hour'].value_counts().sort_index())

# Check for NaN hours
nan_mask = df['open_hour'].isna()
print(f"\nRows with NaN hour: {nan_mask.sum()}")

if nan_mask.sum() > 0:
    print("\nSamples of rows with NaN hour:")
    nan_df = df[nan_mask]
    print(nan_df[['date', '开台时间', 'open_datetime', 'revenue_before_tax']].head())

# Calculate overnight segment
overnight_mask = (df['open_hour'] >= 22) | (df['open_hour'] < 8)
overnight_revenue = df[overnight_mask]['revenue_before_tax'].sum()
overnight_orders = len(df[overnight_mask])

print(f"\nOvernight segment (22:00-07:59):")
print(f"  Orders: {overnight_orders}")
print(f"  Revenue: ${overnight_revenue:,.2f}")

# Show breakdown
overnight_df = df[overnight_mask]
print("\n  Breakdown by hour:")
for hour in sorted(overnight_df['open_hour'].unique()):
    hour_mask = overnight_df['open_hour'] == hour
    print(f"    Hour {hour:02d}: {hour_mask.sum()} orders, ${overnight_df[hour_mask]['revenue_before_tax'].sum():,.2f}")