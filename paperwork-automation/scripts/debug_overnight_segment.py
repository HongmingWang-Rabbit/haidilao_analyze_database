#!/usr/bin/env python3
"""Debug overnight segment calculation"""

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

# Calculate segments manually
print("Manual segment calculation:\n")

# 08:00-13:59
seg1_mask = (df_july['open_hour'] >= 8) & (df_july['open_hour'] < 14)
seg1_revenue = df_july[seg1_mask]['revenue_before_tax'].sum()
print(f"08:00-13:59: ${seg1_revenue:,.2f} ({len(df_july[seg1_mask])} orders)")

# 14:00-16:59  
seg2_mask = (df_july['open_hour'] >= 14) & (df_july['open_hour'] < 17)
seg2_revenue = df_july[seg2_mask]['revenue_before_tax'].sum()
print(f"14:00-16:59: ${seg2_revenue:,.2f} ({len(df_july[seg2_mask])} orders)")

# 17:00-21:59
seg3_mask = (df_july['open_hour'] >= 17) & (df_july['open_hour'] < 22)
seg3_revenue = df_july[seg3_mask]['revenue_before_tax'].sum()
print(f"17:00-21:59: ${seg3_revenue:,.2f} ({len(df_july[seg3_mask])} orders)")

# 22:00-07:59 (overnight)
seg4_mask = (df_july['open_hour'] >= 22) | (df_july['open_hour'] < 8)
seg4_revenue = df_july[seg4_mask]['revenue_before_tax'].sum()
print(f"22:00-07:59: ${seg4_revenue:,.2f} ({len(df_july[seg4_mask])} orders)")

# Hours in overnight segment
print("\nOrders in overnight segment by hour:")
overnight_df = df_july[seg4_mask]
for hour in sorted(overnight_df['open_hour'].unique()):
    hour_revenue = overnight_df[overnight_df['open_hour'] == hour]['revenue_before_tax'].sum()
    hour_count = len(overnight_df[overnight_df['open_hour'] == hour])
    print(f"  Hour {hour:02d}: {hour_count} orders, ${hour_revenue:,.2f}")

# Total
total_segments = seg1_revenue + seg2_revenue + seg3_revenue + seg4_revenue
print(f"\nTotal from segments: ${total_segments:,.2f}")
print(f"Total overall: ${df_july['revenue_before_tax'].sum():,.2f}")
print(f"Difference: ${abs(total_segments - df_july['revenue_before_tax'].sum()):,.2f}")