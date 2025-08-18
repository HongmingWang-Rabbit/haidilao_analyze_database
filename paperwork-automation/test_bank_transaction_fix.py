#!/usr/bin/env python3
"""
Test script to verify the RBC duplicate fix
"""

import sys
import io
from pathlib import Path
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scripts.process_bank_transactions import BankTransactionProcessor

def test_rbc_duplicate_fix():
    """Test the RBC duplicate removal fix"""
    
    print("Testing RBC duplicate fix...")
    
    # Use July 2025 as test month (where we know duplicates exist)
    processor = BankTransactionProcessor(2025, 7)
    
    # Test the process_rbc_files method
    last_existing_dates = processor.get_last_existing_dates_from_template()
    print(f"\nLast existing dates: {last_existing_dates}")
    
    # Process RBC files
    rbc_transactions = processor.process_rbc_files(last_existing_dates)
    
    # Check results
    for sheet_name, transactions in rbc_transactions.items():
        print(f"\n{sheet_name}: {len(transactions)} transactions")
        
        # Check for duplicates in processed transactions
        if transactions:
            # Create a DataFrame from transactions for easier duplicate checking
            df = pd.DataFrame(transactions)
            
            # Check for duplicates based on key fields
            key_fields = ['Date', 'Transaction Description', 'Debit', 'Credit']
            duplicates = df[df.duplicated(subset=key_fields, keep=False)]
            
            if not duplicates.empty:
                print(f"WARNING: Still found {len(duplicates)} duplicates after processing!")
                print(duplicates[key_fields])
            else:
                print("✓ No duplicates in processed transactions")
            
            # Show first few transactions
            print(f"\nFirst 5 transactions:")
            for i, trans in enumerate(transactions[:5]):
                print(f"  {i+1}. {trans['Date']} - {trans['Transaction Description']} - Debit: {trans['Debit']} - Credit: {trans['Credit']}")

def test_duplicate_detection():
    """Test the improved duplicate detection logic"""
    
    print("\n\nTesting improved duplicate detection...")
    
    # Test cases with variations
    test_cases = [
        # Same transaction
        {
            'existing': {'date': 'Jul 31, 2025', 'desc': 'INTERAC PURCHASE', 'debit': '100', 'credit': ''},
            'new': {'Date': 'Jul 31, 2025', 'Transaction Description': 'INTERAC PURCHASE', 'Debit': '100', 'Credit': ''},
            'expected': True
        },
        # Same transaction with trailing spaces
        {
            'existing': {'date': 'Jul 31, 2025', 'desc': 'INTERAC PURCHASE ', 'debit': '100 ', 'credit': ''},
            'new': {'Date': 'Jul 31, 2025', 'Transaction Description': 'INTERAC PURCHASE', 'Debit': '100', 'Credit': ''},
            'expected': True
        },
        # Different amounts
        {
            'existing': {'date': 'Jul 31, 2025', 'desc': 'INTERAC PURCHASE', 'debit': '100', 'credit': ''},
            'new': {'Date': 'Jul 31, 2025', 'Transaction Description': 'INTERAC PURCHASE', 'Debit': '200', 'Credit': ''},
            'expected': False
        },
        # Different dates
        {
            'existing': {'date': 'Jul 30, 2025', 'desc': 'INTERAC PURCHASE', 'debit': '100', 'credit': ''},
            'new': {'Date': 'Jul 31, 2025', 'Transaction Description': 'INTERAC PURCHASE', 'Debit': '100', 'Credit': ''},
            'expected': False
        }
    ]
    
    from scripts.process_bank_transactions import BankTransactionProcessor
    processor = BankTransactionProcessor(2025, 7)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}:")
        print(f"  Existing: {test_case['existing']}")
        print(f"  New: {test_case['new']}")
        print(f"  Expected duplicate: {test_case['expected']}")
        
        # The actual duplicate detection would need access to a worksheet
        # Here we just show the test case structure
        
if __name__ == "__main__":
    test_rbc_duplicate_fix()
    test_duplicate_detection()