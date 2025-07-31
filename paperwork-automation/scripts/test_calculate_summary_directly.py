#!/usr/bin/env python3
"""Test _calculate_summary directly with exact parameters"""

import os
import sys

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

print(f"Read {len(df_all)} rows, {sheet_count} sheets")

# Call _calculate_summary with exact same parameters as processor
summary = processor._calculate_summary(df_all, '202507', sheet_count)

# Check the results
print(f"\nTime segment revenues:")
print(f"  08:00-13:59: ${summary.get('revenue_08:00-13:59', 0):,.2f}")
print(f"  14:00-16:59: ${summary.get('revenue_14:00-16:59', 0):,.2f}")
print(f"  17:00-21:59: ${summary.get('revenue_17:00-21:59', 0):,.2f}")
print(f"  22:00-07:59: ${summary.get('revenue_22:00-07:59', 0):,.2f}")

total = (summary.get('revenue_08:00-13:59', 0) + 
         summary.get('revenue_14:00-16:59', 0) +
         summary.get('revenue_17:00-21:59', 0) +
         summary.get('revenue_22:00-07:59', 0))

print(f"\nTotal: ${total:,.2f}")
print(f"Expected: $67,260.42")
print(f"Match: {'YES' if abs(total - 67260.42) < 0.01 else 'NO'}")