import sys
import os
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict
import logging
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from type.bank_processing import BankRecord
from configs.bank_statement.banks import BankBrands
from scripts.bank_statement_processing.extract_bank_statements.BMO import extract_bmo_sheet_infomation
from scripts.bank_statement_processing.extract_bank_statements.RBC import extract_rbc_sheet_infomation
from scripts.bank_statement_processing.extract_bank_statements.CIBC import extract_cibc_sheet_infomation
from scripts.bank_statement_processing.extract_bank_statements.detect_target_file_bank import (
    detect_target_file_bank, 
    get_all_target_file_paths,
    main as get_bank_files_by_brand
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_bank_statement_file(
        target_file_path: str,
        current_date: datetime
) -> List[BankRecord]:
    """
    Main extraction dispatcher that determines bank type and calls appropriate extractor.
    
    Args:
        target_file_path: Path to the bank statement file
        current_date: Current date - records on or after this date will be skipped
    
    Returns:
        List of BankRecord objects extracted from the file
    """
    try:
        # Detect bank brand from file path
        bank_brand = detect_target_file_bank(target_file_path)
        
        if not bank_brand:
            raise ValueError(f"Could not determine bank type for file: {target_file_path}")
        
        # Dispatch to appropriate extractor
        if bank_brand == BankBrands.BMO:
            return extract_bmo_sheet_infomation(target_file_path, current_date)
        elif bank_brand == BankBrands.RBC:
            return extract_rbc_sheet_infomation(target_file_path, current_date)
        elif bank_brand == BankBrands.CIBC:
            return extract_cibc_sheet_infomation(target_file_path, current_date)
        else:
            raise ValueError(f"Unsupported bank brand: {bank_brand}")
            
    except Exception as e:
        logger.error(f"Error extracting bank statements from {target_file_path}: {str(e)}")
        raise

def group_records_by_account(records: List[BankRecord]) -> Dict[str, List[BankRecord]]:
    """
    Group bank records by account identifier extracted from serial number.
    
    Args:
        records: List of BankRecord objects
    
    Returns:
        Dictionary mapping account identifiers to lists of records
    """
    grouped = defaultdict(list)
    
    for record in records:
        # Extract account info from serial number (format: BANK_ACCOUNT_INDEX)
        if record.serial_number:
            parts = record.serial_number.rsplit('_', 1)  # Split from right to remove index
            if len(parts) >= 2:
                account_key = parts[0]
            else:
                account_key = "Unknown"
        else:
            account_key = "Unknown"
        
        grouped[account_key].append(record)
    
    return dict(grouped)

def print_bank_records_summary(bank_name: str, file_path: str, records: List[BankRecord]):
    """
    Print a formatted summary of bank records grouped by account.
    
    Args:
        bank_name: Name of the bank
        file_path: Path to the source file
        records: List of BankRecord objects
    """
    print(f"\n{'='*80}")
    print(f"Bank: {bank_name}")
    print(f"File: {os.path.basename(file_path)}")
    print(f"Total Records: {len(records)}")
    print(f"{'='*80}")
    
    if not records:
        print("  No records found in this file.")
        return
    
    # Group records by account
    grouped_records = group_records_by_account(records)
    
    for account_key, account_records in grouped_records.items():
        print(f"\n  Account: {account_key}")
        print(f"  Number of transactions: {len(account_records)}")
        
        # Calculate totals
        total_debit = sum(r.debit for r in account_records)
        total_credit = sum(r.credit for r in account_records)
        
        print(f"  Total Debits:  ${total_debit:,.2f}")
        print(f"  Total Credits: ${total_credit:,.2f}")
        print(f"  Net Change:    ${(total_credit - total_debit):,.2f}")
        
        # Show first few transactions with full details
        print(f"\n  First 5 transactions (detailed):")
        for i, record in enumerate(account_records[:5], 1):
            print(f"    {i}. Date: {record.date}")
            print(f"       Short Desc: {record.short_desctiption if record.short_desctiption else '(none)'}")
            print(f"       Full Desc: {record.full_desctiption if record.full_desctiption else '(empty)'}")
            print(f"       Debit: ${record.debit:,.2f}")
            print(f"       Credit: ${record.credit:,.2f}")
            print(f"       Customer Ref: {record.customer_reference if record.customer_reference else '(none)'}")
            print(f"       Bank Ref: {record.bank_reference if record.bank_reference else '(none)'}")
            print(f"       Serial: {record.serial_number if record.serial_number else '(none)'}")

def extract_bank_statements(
        target_date: datetime
) -> Dict[BankBrands, List[BankRecord]]:
    """
    Extract all bank statements for the target date (month).
    
    Args:
        target_date: Date to determine which month folder to check for bank statements
    
    Returns:
        Dictionary mapping bank brands to lists of BankRecord objects
    """
    # Get all bank files grouped by brand for the target month
    bank_files = get_bank_files_by_brand(target_date)
    
    if not bank_files:
        logger.warning(f"No bank files found for {target_date.strftime('%Y-%m')}")
        return {}
    
    # Initialize result dictionary
    all_records_by_bank = {}
    
    # Process each bank's files
    for bank_brand, file_paths in bank_files.items():
        logger.info(f"Processing {bank_brand.name} bank files")
        bank_records = []
        
        for file_path in file_paths:
            try:
                logger.info(f"Extracting from {os.path.basename(file_path)}")
                records = extract_bank_statement_file(file_path, target_date)
                bank_records.extend(records)
                logger.info(f"Successfully extracted {len(records)} records from {os.path.basename(file_path)}")
                
            except Exception as e:
                logger.error(f"Failed to extract from {file_path}: {str(e)}")
                # Continue processing other files even if one fails
                continue
        
        # Add to results if we have any records
        if bank_records:
            all_records_by_bank[bank_brand] = bank_records
            logger.info(f"Total {bank_brand.name} records: {len(bank_records)}")
    
    return all_records_by_bank


def test_all_extractions():
    """
    Test function to extract and display all bank records from sample files.
    Groups records by bank and account.
    """
    print("\n" + "="*80)
    print("BANK STATEMENT EXTRACTION TEST")
    print("="*80)
    
    # Use August 2025 as test month
    test_date = datetime(2025, 8, 1)
    
    # Use September 1, 2025 as current date (to exclude future transactions)
    current_date = datetime(2025, 9, 1)
    
    # Get all bank files grouped by brand
    bank_files = get_bank_files_by_brand(test_date)
    
    if not bank_files:
        print(f"No bank files found for {test_date.strftime('%Y-%m')}")
        return
    
    print(f"Current date filter: {current_date.strftime('%Y-%m-%d')} (excluding records on or after this date)")
    
    all_records_by_bank = {}
    
    # Process each bank's files
    for bank_brand, file_paths in bank_files.items():
        print(f"\n{'='*80}")
        print(f"Processing {bank_brand.name} Bank Files")
        print(f"{'='*80}")
        
        bank_records = []
        
        for file_path in file_paths:
            try:
                print(f"\nProcessing: {os.path.basename(file_path)}")
                records = extract_bank_statement_file(file_path, current_date)
                bank_records.extend(records)
                print_bank_records_summary(bank_brand.name, file_path, records)
                
            except Exception as e:
                print(f"  ERROR: Failed to process {os.path.basename(file_path)}")
                print(f"  Reason: {str(e)}")
                logger.error(f"Failed to process {file_path}: {str(e)}", exc_info=True)
        
        all_records_by_bank[bank_brand.name] = bank_records
    
    # Print overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    
    for bank_name, records in all_records_by_bank.items():
        total_debit = sum(r.debit for r in records)
        total_credit = sum(r.credit for r in records)
        
        print(f"\n{bank_name}:")
        print(f"  Total Transactions: {len(records)}")
        print(f"  Total Debits:       ${total_debit:,.2f}")
        print(f"  Total Credits:      ${total_credit:,.2f}")
        print(f"  Net Change:         ${(total_credit - total_debit):,.2f}")
    
    # Grand totals
    all_records = [r for records in all_records_by_bank.values() for r in records]
    if all_records:
        print(f"\n{'='*80}")
        print("GRAND TOTALS")
        print(f"{'='*80}")
        print(f"Total Transactions: {len(all_records)}")
        print(f"Total Debits:       ${sum(r.debit for r in all_records):,.2f}")
        print(f"Total Credits:      ${sum(r.credit for r in all_records):,.2f}")
        print(f"Net Change:         ${(sum(r.credit for r in all_records) - sum(r.debit for r in all_records)):,.2f}")

if __name__ == "__main__":
    # Run the comprehensive test
    test_all_extractions()