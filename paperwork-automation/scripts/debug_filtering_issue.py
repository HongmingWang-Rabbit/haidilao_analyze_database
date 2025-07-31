#!/usr/bin/env python3
"""Debug the filtering issue"""

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

# Check the issue with filtering
target_month = '202507'
target_year = int(target_month[:4])
target_mon = int(target_month[4:6])

print(f"Total rows before filtering: {len(df_all)}")
print(f"Unique years in data: {df_all['date'].dt.year.unique()}")
print(f"Unique months in data: {df_all['date'].dt.month.unique()}")

# Apply the filters one by one
df_year = df_all[df_all['date'].dt.year == target_year]
print(f"\nRows after year filter (year={target_year}): {len(df_year)}")

# This is the bug! The processor has:
# df = df_all[df_all['date'].dt.year == target_year]
# df = df_all[df_all['date'].dt.month == target_mon]  # Should be df, not df_all!

# What the processor does (WRONG):
df_wrong = df_all[df_all['date'].dt.month == target_mon]
print(f"Rows after WRONG month filter (uses df_all): {len(df_wrong)}")

# What it should do (CORRECT):
df_correct = df_year[df_year['date'].dt.month == target_mon]
print(f"Rows after CORRECT month filter (uses df_year): {len(df_correct)}")

print(f"\nThe bug causes us to lose the year filter and only apply the month filter!")