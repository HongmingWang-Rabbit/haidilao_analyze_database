#!/usr/bin/env python3
"""
Test duplicate removal for all banks
"""

import sys
import io
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scripts.process_bank_transactions import BankTransactionProcessor

def test_all_banks():
    """Test duplicate removal for all banks"""
    
    print("Testing bank transaction processing with duplicate removal...\n")
    
    # Use July 2025 as test month
    processor = BankTransactionProcessor(2025, 7)
    
    # Get last existing dates
    last_existing_dates = processor.get_last_existing_dates_from_template()
    
    print("\n=== Testing BMO Processing ===")
    bmo_transactions = processor.process_bmo_reconciliation(last_existing_dates)
    for sheet, trans in bmo_transactions.items():
        print(f"{sheet}: {len(trans)} transactions")
    
    print("\n=== Testing CIBC Processing ===")
    cibc_transactions = processor.process_cibc_file(last_existing_dates)
    print(f"CIBC: {len(cibc_transactions)} transactions")
    
    print("\n=== Testing RBC Processing ===")
    rbc_transactions = processor.process_rbc_files(last_existing_dates)
    for sheet, trans in rbc_transactions.items():
        print(f"{sheet}: {len(trans)} transactions")
    
    print("\n\nDuplicate removal summary:")
    print("- RBC: Check console logs for duplicate removal messages")
    print("- CIBC: Check console logs for duplicate removal messages")
    print("- BMO: Check console logs for duplicate removal messages")

if __name__ == "__main__":
    test_all_banks()