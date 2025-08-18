#!/usr/bin/env python3
"""
Test the new duplicate detection approach
"""

import sys
import io
from pathlib import Path
from datetime import datetime
import logging

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scripts.process_bank_transactions import BankTransactionProcessor

def test_new_approach():
    """Test the new duplicate detection approach"""
    
    print("Testing new duplicate detection approach...\n")
    
    # Use July 2025 as test month
    processor = BankTransactionProcessor(2025, 7)
    
    # Get last existing dates
    last_existing_dates = processor.get_last_existing_dates_from_template()
    print("Last existing dates:")
    for sheet, date in last_existing_dates.items():
        print(f"  {sheet}: {date}")
    
    # Get last date transactions
    print("\n\nLast date transactions:")
    last_date_transactions = processor.get_last_date_transactions_from_template()
    for sheet, transactions in last_date_transactions.items():
        print(f"\n{sheet}: {len(transactions)} transactions on last date")
        if transactions and len(transactions) <= 3:
            for trans in transactions:
                print(f"  - {trans['date']} | {trans['description'][:40]}... | D:{trans['debit']} C:{trans['credit']}")
    
    # Test with a specific example
    print("\n\nTesting duplicate detection:")
    
    # Create a test transaction that should be detected as duplicate
    test_transaction = {
        'Date': 'Aug 01, 2025',
        'Transaction Description': 'Account transfer - HAI DI LAO CANA',
        'Debit': '',
        'Credit': '200000'
    }
    
    sheet_name = 'RBC 5401'
    is_duplicate = processor.is_transaction_in_last_date_reference(
        test_transaction, sheet_name, last_date_transactions
    )
    
    print(f"\nTest transaction: {test_transaction}")
    print(f"Is duplicate in {sheet_name}: {is_duplicate}")
    
    # Test with a non-duplicate
    test_transaction2 = {
        'Date': 'Aug 01, 2025',
        'Transaction Description': 'Different transaction',
        'Debit': '100',
        'Credit': ''
    }
    
    is_duplicate2 = processor.is_transaction_in_last_date_reference(
        test_transaction2, sheet_name, last_date_transactions
    )
    
    print(f"\nTest transaction 2: {test_transaction2}")
    print(f"Is duplicate in {sheet_name}: {is_duplicate2}")

if __name__ == "__main__":
    test_new_approach()