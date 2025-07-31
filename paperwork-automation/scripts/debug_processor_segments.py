#!/usr/bin/env python3
"""Debug the processor's segment calculation"""

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

# Now run the exact calculation that the processor does
target_month = '202507'
target_year = int(target_month[:4])
target_mon = int(target_month[4:6])
df = df_all[df_all['date'].dt.year == target_year]
df = df_all[df_all['date'].dt.month == target_mon]

print(f"Filtered data has {len(df)} rows")

# Convert time strings to datetime for time segment analysis
df['open_datetime'] = pd.to_datetime(df['开台时间'], errors='coerce')
df['close_datetime'] = pd.to_datetime(df['完结时间'], errors='coerce')

# Define time segments (same as processor)
time_segments = {
    '08:00-13:59': (8, 14),
    '14:00-16:59': (14, 17),
    '17:00-21:59': (17, 22),
    '22:00-07:59': (22, 32)  # 32 = 8 + 24 (next day)
}

# Calculate revenue and orders by time segment
for segment_name, (start_hour, end_hour) in time_segments.items():
    # Get hour from open time
    df['open_hour'] = df['open_datetime'].dt.hour
    
    if start_hour < end_hour:
        # Normal case (same day)
        segment_mask = (df['open_hour'] >= start_hour) & (df['open_hour'] < end_hour)
    else:
        # Overnight case (22:00-07:59)
        segment_mask = (df['open_hour'] >= start_hour) | (df['open_hour'] < 8)
    
    # Calculate revenue for this segment (before tax only)
    segment_revenue = df[segment_mask]['revenue_before_tax'].sum()
    segment_orders = len(df[segment_mask])
    
    print(f"{segment_name}: ${segment_revenue:,.2f} ({segment_orders} orders)")
    
    # For overnight segment, show which hours are included
    if segment_name == '22:00-07:59':
        print("  Hours included in overnight segment:")
        overnight_df = df[segment_mask]
        for hour in sorted(overnight_df['open_hour'].unique()):
            hour_revenue = overnight_df[overnight_df['open_hour'] == hour]['revenue_before_tax'].sum()
            hour_count = len(overnight_df[overnight_df['open_hour'] == hour])
            print(f"    Hour {hour:02d}: {hour_count} orders, ${hour_revenue:,.2f}")

# Check if 'open_hour' column exists after loop
print(f"\n'open_hour' column exists in df: {'open_hour' in df.columns}")
print(f"df columns: {list(df.columns)}")