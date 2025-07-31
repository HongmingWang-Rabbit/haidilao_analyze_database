#!/usr/bin/env python3
"""Verify final corrected revenues"""

import openpyxl
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check the latest generated file
output_file = "output/hi-bowl/hi_bowl_report_20250731_003807.xlsx"

wb = openpyxl.load_workbook(output_file, data_only=True)
ws = wb['海外新业态管报收入数据-本位币']

# Check time segment revenues
print("Final corrected time segment revenues:")
revenues = [
    ("AS8", "08:00-13:59销售收入"),
    ("AT8", "14:00-16:59销售收入"), 
    ("AU8", "17:00-21:59销售收入"),
    ("AV8", "22:00-07:59销售收入"),
]

total = 0
for cell_ref, desc in revenues:
    value = ws[cell_ref].value or 0
    total += value
    print(f"{cell_ref} ({desc}): ${value:,.2f}")

print(f"\nTotal from time segments: ${total:,.2f}")
print(f"Expected total: $67,260.42")
print(f"Match: {'YES' if abs(total - 67260.42) < 0.01 else 'NO'}")

wb.close()