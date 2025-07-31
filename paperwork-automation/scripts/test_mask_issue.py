#!/usr/bin/env python3
"""Test the mask issue in isolation"""

import pandas as pd
import numpy as np

# Create test data similar to what we have
hours = [0, 1, 3, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
counts = [18, 11, 2, 1, 28, 36, 31, 30, 24, 20, 45, 66, 64, 42, 66, 37, 34]

# Create a dataframe with repeated hours
data = []
for hour, count in zip(hours, counts):
    for _ in range(count):
        data.append({'open_hour': hour, 'revenue': 100.0})

df = pd.DataFrame(data)
print(f"Total rows: {len(df)}")
print(f"Hour distribution: {df['open_hour'].value_counts().sort_index().to_dict()}")

# Test the overnight mask
start_hour = 22
segment_mask = (df['open_hour'] >= start_hour) | (df['open_hour'] < 8)

print(f"\nOvernight mask test:")
print(f"  Rows with hour >= 22: {(df['open_hour'] >= start_hour).sum()}")
print(f"  Rows with hour < 8: {(df['open_hour'] < 8).sum()}")
print(f"  Combined OR mask: {segment_mask.sum()}")

# Show which hours are captured
overnight_df = df[segment_mask]
print(f"\nHours captured by mask: {sorted(overnight_df['open_hour'].unique())}")
print(f"Hour counts in overnight segment: {overnight_df['open_hour'].value_counts().sort_index().to_dict()}")

# Double check the math
expected = counts[0] + counts[1] + counts[2] + counts[-2] + counts[-1]  # hours 0,1,3,22,23
print(f"\nExpected total: {expected}")
print(f"Actual total: {segment_mask.sum()}")
print(f"Match: {expected == segment_mask.sum()}")