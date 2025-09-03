import sys
import os
import pandas as pd
from datetime import datetime
from typing import List, Optional, Tuple
import logging
import calendar

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from type.bank_processing import BankRecord

logger = logging.getLogger(__name__)

def get_month_date_range(current_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end date for the month of the current_date.
    
    Args:
        current_date: The reference date
        
    Returns:
        Tuple of (month_start, month_end) datetime objects
    """
    year = current_date.year
    month = current_date.month
    
    # First day of the month
    month_start = datetime(year, month, 1)
    
    # Last day of the month
    last_day = calendar.monthrange(year, month)[1]
    month_end = datetime(year, month, last_day, 23, 59, 59)
    
    return month_start, month_end

def extract_cibc_sheet_infomation(
        target_file_path: str,
        current_date: datetime
) -> List[BankRecord]:
    """
    Extract CIBC bank statement information from CSV file.
    
    CIBC files have a standard columnar structure with transaction types (C/D).
    The amount column is single with transaction type determining debit/credit.
    Only processes records within the same month as current_date.
    
    Args:
        target_file_path: Path to the CIBC CSV file
        current_date: Current date - only records in the same month will be processed
    
    Returns:
        List of BankRecord objects
    """
    records = []
    
    # Get the month range for filtering
    month_start, month_end = get_month_date_range(current_date)
    
    try:
        # Read the CSV file
        df = pd.read_csv(target_file_path)
        
        # Check which format we have (old vs new)
        # New format has 'BANK_NAME', old format has 'Account name'
        is_new_format = 'BANK_NAME' in df.columns
        
        if is_new_format:
            # New format columns
            expected_columns = ['BANK_NAME', 'Account number', 'Currency', 'Ledger date', 
                              'Transaction type', 'Description', 'ADDITIONAL DETAILS', 'Value date', 
                              'Amount', 'Bank reference', 'Client reference', 
                              'TOTAL DEBIT AMOUNT', 'TOTAL CREDIT AMOUNT']
            
            # Verify required columns exist
            required_columns = ['Ledger date', 'Transaction type', 'Description', 'Amount']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Extract account information from first row if available
            account_info = ""
            if len(df) > 0:
                first_row = df.iloc[0]
                account_number = first_row.get('Account number', '')
                # Use just the account number for identification
                account_info = str(account_number) if account_number else ""
        else:
            # Old format columns
            expected_columns = ['Account name', 'Account number', 'Currency', 'Ledger date', 
                              'Transaction type', 'Description', 'Value date', 'Amount', 
                              'Bank reference', 'Client reference', 'TRANSACTION AMOUNT']
            
            # Verify required columns exist
            required_columns = ['Ledger date', 'Transaction type', 'Description', 'Amount']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Extract account information from first row if available
            account_info = ""
            if len(df) > 0:
                first_row = df.iloc[0]
                account_number = first_row.get('Account number', '')
                # Use just the account number for identification
                account_info = str(account_number) if account_number else ""
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                record = BankRecord()
                
                # Parse date from M/D/YYYY format
                date_value = row['Ledger date']
                if pd.notna(date_value):
                    # Handle date parsing - CIBC uses M/D/YYYY format
                    record.date = pd.to_datetime(str(date_value), format='%m/%d/%Y', errors='coerce')
                    if pd.isna(record.date):
                        # Try alternative parsing if format is different
                        record.date = pd.to_datetime(str(date_value))
                    
                    # Only process records within the current month
                    if not (month_start <= record.date <= month_end):
                        continue
                else:
                    continue  # Skip rows without dates
                
                # Extract description
                if is_new_format:
                    # Combine Description and ADDITIONAL DETAILS for full description
                    desc = str(row['Description']) if pd.notna(row['Description']) else ""
                    additional = str(row.get('ADDITIONAL DETAILS', '')) if pd.notna(row.get('ADDITIONAL DETAILS', '')) else ""
                    record.full_desctiption = f"{desc} {additional}".strip() if additional else desc
                else:
                    record.full_desctiption = str(row['Description']) if pd.notna(row['Description']) else ""
                
                # Extract references
                if 'Client reference' in row and pd.notna(row['Client reference']):
                    record.customer_reference = str(row['Client reference']).strip()
                else:
                    record.customer_reference = None
                
                if 'Bank reference' in row and pd.notna(row['Bank reference']):
                    record.bank_reference = str(row['Bank reference']).strip()
                else:
                    record.bank_reference = None
                
                # Parse amount based on transaction type
                amount = row.get('Amount', 0)
                transaction_type = str(row.get('Transaction type', '')).lower()
                
                if pd.notna(amount):
                    amount_value = float(amount)
                    
                    # Determine if it's debit or credit based on transaction type
                    # New format uses "Debit transactions" and "Credit transactions"
                    # Old format uses "D" and "C"
                    if 'debit' in transaction_type or transaction_type == 'd':
                        record.debit = amount_value
                        record.credit = 0.0
                    elif 'credit' in transaction_type or transaction_type == 'c':
                        record.credit = amount_value
                        record.debit = 0.0
                    else:
                        # If transaction type is unclear, try to determine from amount sign
                        if amount_value < 0:
                            record.debit = abs(amount_value)
                            record.credit = 0.0
                        else:
                            record.credit = amount_value
                            record.debit = 0.0
                else:
                    record.debit = 0.0
                    record.credit = 0.0
                
                # Skip records where both debit and credit are 0
                if record.debit == 0.0 and record.credit == 0.0:
                    continue
                
                # Generate serial number with account info
                # Format as CIBC + last 4 digits of account number
                if account_info and len(account_info) >= 4:
                    account_short = account_info[-4:]  # Last 4 digits
                    record.serial_number = f"CIBC{account_short}_{idx}"
                else:
                    record.serial_number = f"CIBC_{account_info}_{idx}"
                
                records.append(record)
                
            except Exception as e:
                logger.warning(f"Error parsing CIBC row {idx}: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(records)} CIBC records for {month_start.strftime('%Y-%m')} from {target_file_path}")
        
    except Exception as e:
        logger.error(f"Error reading CIBC file {target_file_path}: {str(e)}")
        raise
    
    return records

if __name__ == "__main__":
    # Test with sample file
    test_file = r"D:\personal_programming_work\honeypot_frontend_v2\haidilao_analyze_database\paperwork-automation\history_files\bank_daily_report\2025-08\TransactionDetail.csv"
    
    if os.path.exists(test_file):
        # Use September 1, 2025 as current date
        current_date = datetime(2025, 9, 1)
        records = extract_cibc_sheet_infomation(test_file, current_date)
        print(f"Extracted {len(records)} CIBC records (before {current_date.strftime('%Y-%m-%d')})")
        
        for i, record in enumerate(records[:5]):  # Show first 5 records
            print(f"\nRecord {i+1}:")
            print(f"  Date: {record.date}")
            print(f"  Short Desc: {record.short_desctiption if record.short_desctiption else '(none)'}")
            print(f"  Full Desc:  {record.full_desctiption}")
            print(f"  Debit: {record.debit}")
            print(f"  Credit: {record.credit}")
            print(f"  Customer Ref: {record.customer_reference}")
            print(f"  Bank Ref: {record.bank_reference}")
    else:
        print(f"Test file not found: {test_file}")