#!/usr/bin/env python3
"""Test the fixed duplicate detection logic"""

# Test the exact values that were causing the issue
existing_debit = 4000  # From Excel sheet
existing_credit = None  # From Excel sheet

transaction_debit = "4000"  # From new transaction 
transaction_credit = ""  # From new transaction

# Old logic
print("OLD LOGIC:")
existing_debit_str_old = str(existing_debit) if existing_debit else ""
existing_credit_str_old = str(existing_credit) if existing_credit else ""
transaction_debit_str_old = str(transaction_debit)
transaction_credit_str_old = str(transaction_credit)

print(f'Existing debit: {repr(existing_debit_str_old)}')
print(f'Transaction debit: {repr(transaction_debit_str_old)}')
print(f'Debit match: {existing_debit_str_old == transaction_debit_str_old}')

print(f'Existing credit: {repr(existing_credit_str_old)}')  
print(f'Transaction credit: {repr(transaction_credit_str_old)}')
print(f'Credit match: {existing_credit_str_old == transaction_credit_str_old}')

print("\nNEW LOGIC:")
existing_debit_str_new = str(existing_debit) if existing_debit and existing_debit != "" else ""
existing_credit_str_new = str(existing_credit) if existing_credit and existing_credit != "" else ""
transaction_debit_str_new = str(transaction_debit) if transaction_debit and transaction_debit != "" else ""
transaction_credit_str_new = str(transaction_credit) if transaction_credit and transaction_credit != "" else ""

print(f'Existing debit: {repr(existing_debit_str_new)}')
print(f'Transaction debit: {repr(transaction_debit_str_new)}')
print(f'Debit match: {existing_debit_str_new == transaction_debit_str_new}')

print(f'Existing credit: {repr(existing_credit_str_new)}')
print(f'Transaction credit: {repr(transaction_credit_str_new)}')
print(f'Credit match: {existing_credit_str_new == transaction_credit_str_new}')

print(f'\nOverall match: {existing_debit_str_new == transaction_debit_str_new and existing_credit_str_new == transaction_credit_str_new}')