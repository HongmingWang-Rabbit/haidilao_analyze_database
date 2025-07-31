#!/usr/bin/env python3
"""Test the fixed date detection"""

import sys
sys.path.insert(0, '.')

from scripts.process_bank_transactions import BankTransactionProcessor
from openpyxl import load_workbook

# Create processor instance to test the method
processor = BankTransactionProcessor(2025, 7)

# Test with template
wb = load_workbook('Input/daily_report/bank_transactions_reports/CA全部7家店明细.xlsx')

# Test CIBC
ws_cibc = wb['CA7D-CIBC 0401']
cibc_result = processor.get_last_existing_date(ws_cibc)
print(f"CIBC last date: {cibc_result}")

# Test RBC  
ws_rbc = wb['RBC 5401']
rbc_result = processor.get_last_existing_date(ws_rbc)
print(f"RBC last date: {rbc_result}")

# Test BMO (CA1D-3817)
ws_bmo = wb['CA1D-3817']
bmo_result = processor.get_last_existing_date(ws_bmo)
print(f"BMO last date: {bmo_result}")

wb.close()