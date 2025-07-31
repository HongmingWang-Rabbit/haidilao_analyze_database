#!/usr/bin/env python3
"""Test pandas version and behavior"""

import pandas as pd
import numpy as np

print(f"Pandas version: {pd.__version__}")
print(f"NumPy version: {np.__version__}")

# Test the exact scenario
df = pd.DataFrame({
    'open_hour': [0, 1, 3, 22, 23] * 20,  # 100 rows total
    'revenue': [100] * 100
})

print(f"\nDataFrame shape: {df.shape}")
print(f"Hour value counts: {df['open_hour'].value_counts().sort_index().to_dict()}")

# Test the mask
mask1 = df['open_hour'] >= 22
mask2 = df['open_hour'] < 8
combined = mask1 | mask2

print(f"\nMask test:")
print(f"  mask1 (>= 22) sum: {mask1.sum()}")
print(f"  mask2 (< 8) sum: {mask2.sum()}")
print(f"  combined (OR) sum: {combined.sum()}")

# Test using it in a filter
filtered = df[combined]
print(f"\nFiltered rows: {len(filtered)}")
print(f"Revenue sum: {filtered['revenue'].sum()}")