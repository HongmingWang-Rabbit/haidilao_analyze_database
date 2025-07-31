#!/usr/bin/env python3
"""Test date normalization"""

import pandas as pd
from datetime import datetime

def normalize_date(date_value):
    if not date_value:
        return ""
    
    try:
        # Convert to pandas datetime (handles multiple formats)
        date_obj = pd.to_datetime(date_value)
        # Return in a standard format for comparison
        return date_obj.strftime('%Y-%m-%d')
    except:
        # If parsing fails, return original string
        return str(date_value)

print('String date:', normalize_date('Jul 22, 2025'))
print('Datetime date:', normalize_date(datetime(2025, 7, 22, 0, 0)))
print('Equal?', normalize_date('Jul 22, 2025') == normalize_date(datetime(2025, 7, 22, 0, 0)))

# Test the exact values from the duplicate
print('Test with exact duplicate values:')
date1 = "Jul 22, 2025"  # What new transaction has
date2 = datetime(2025, 7, 22, 0, 0)  # What existing sheet has
desc1 = "ACCOUNT TRANSFER"
desc2 = "ACCOUNT TRANSFER"
debit1 = "4000"
debit2 = 4000
credit1 = ""
credit2 = None

print(f'Date comparison: {normalize_date(date1)} == {normalize_date(date2)} -> {normalize_date(date1) == normalize_date(date2)}')
print(f'Desc comparison: "{desc1}" == "{desc2}" -> {desc1 == desc2}')
print(f'Debit comparison: "{debit1}" == "{debit2}" -> {str(debit1) == str(debit2)}')
print(f'Credit comparison: "{credit1}" == "{credit2}" -> {str(credit1) == str(credit2)}')