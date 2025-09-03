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

def extract_rbc_sheet_infomation(
        target_file_path: str,
        current_date: datetime
) -> List[BankRecord]:
    """
    Extract RBC bank statement information from CSV file.
    
    RBC files have a standard columnar structure with dates as integers (YYYYMMDD).
    Multiple description columns need to be combined.
    Starts processing only after encountering the first row with a Balance value,
    then processes all subsequent rows (pending transactions come first).
    Only processes records within the same month as current_date.
    
    Args:
        target_file_path: Path to the RBC CSV file
        current_date: Current date for month filtering
    
    Returns:
        List of BankRecord objects
    """
    records = []
    
    # Get the month range for filtering
    month_start, month_end = get_month_date_range(current_date)
    
    try:
        # Read the CSV file
        df = pd.read_csv(target_file_path)
        
        # Expected columns
        expected_columns = ['Date', 'Company Name', 'Account Name', 'Account Nickname', 
                          'Account Number', 'Transit Number', 'Description 1', 
                          'Description 2', 'Description 3', 'Description 4', 
                          'Description 5', 'Currency', 'Withdrawals', 'Deposits', 'Balance']
        
        # Verify columns exist
        missing_columns = [col for col in ['Date', 'Withdrawals', 'Deposits'] if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Extract account information from first row if available
        account_info = ""
        if len(df) > 0:
            first_row = df.iloc[0]
            account_number = first_row.get('Account Number', '')
            # Use just the account number for identification
            account_info = str(account_number) if account_number else ""
        
        # Find the first row with a non-empty Balance value
        start_processing = False
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Check if we should start processing
                if not start_processing:
                    balance_value = row.get('Balance')
                    if pd.notna(balance_value) and balance_value != '':
                        # Found first row with balance - start processing from here
                        start_processing = True
                    else:
                        continue  # Skip rows until we find one with balance
                
                record = BankRecord()
                
                # Parse date from integer format (YYYYMMDD)
                date_value = row['Date']
                if pd.notna(date_value):
                    # Convert integer date to string then to datetime
                    date_str = str(int(date_value))
                    record.date = datetime.strptime(date_str, '%Y%m%d')
                    
                    # Only process records within the current month
                    if not (month_start <= record.date <= month_end):
                        continue
                else:
                    continue  # Skip rows without dates
                
                # Combine description columns (filter out NaN values)
                description_parts = []
                for i in range(1, 6):
                    desc_col = f'Description {i}'
                    if desc_col in row and pd.notna(row[desc_col]):
                        desc_value = str(row[desc_col]).strip()
                        if desc_value:
                            description_parts.append(desc_value)
                
                record.full_desctiption = ' | '.join(description_parts) if description_parts else ""
                
                # Customer reference often in Description 2
                if 'Description 2' in row and pd.notna(row['Description 2']):
                    desc2 = str(row['Description 2']).strip()
                    # Check if it looks like a reference (contains numbers or specific patterns)
                    if any(char.isdigit() for char in desc2) or '-' in desc2:
                        record.customer_reference = desc2
                else:
                    record.customer_reference = None
                
                # RBC doesn't provide bank reference in this format
                record.bank_reference = None
                
                # Parse amounts
                withdrawal = row.get('Withdrawals', 0)
                deposit = row.get('Deposits', 0)
                
                record.debit = float(withdrawal) if pd.notna(withdrawal) else 0.0
                record.credit = float(deposit) if pd.notna(deposit) else 0.0
                
                # Skip records where both debit and credit are 0
                if record.debit == 0.0 and record.credit == 0.0:
                    continue
                
                # Generate serial number with account info
                # Format as RBC + last 4 digits of account number
                if account_info and len(account_info) >= 4:
                    account_short = account_info[-4:]  # Last 4 digits
                    record.serial_number = f"RBC{account_short}_{idx}"
                else:
                    record.serial_number = f"RBC_{account_info}_{idx}"
                
                records.append(record)
                
            except Exception as e:
                logger.warning(f"Error parsing RBC row {idx}: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(records)} RBC records for {month_start.strftime('%Y-%m')} from {target_file_path}")
        
    except Exception as e:
        logger.error(f"Error reading RBC file {target_file_path}: {str(e)}")
        raise
    
    return records

if __name__ == "__main__":
    # Test with sample file
    test_file = r"D:\personal_programming_work\honeypot_frontend_v2\haidilao_analyze_database\paperwork-automation\history_files\bank_daily_report\2025-08\RBC Business Bank Account (0922)_May 01 2024_Aug 28 2025.csv"
    
    if os.path.exists(test_file):
        # Use August 29, 2025 as current date for testing August data
        current_date = datetime(2025, 8, 29)
        records = extract_rbc_sheet_infomation(test_file, current_date)
        print(f"Extracted {len(records)} RBC records for {current_date.strftime('%Y-%m')} (with Balance values only)")
        
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