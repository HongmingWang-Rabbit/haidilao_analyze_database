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

def extract_bmo_sheet_infomation(
        target_file_path: str,
        current_date: datetime
) -> List[BankRecord]:
    """
    Extract BMO bank statement information from Excel file.
    
    BMO files have a hierarchical structure with multiple accounts in a single file.
    Each account section starts with account name and has its own data table.
    Only processes records within the same month as current_date.
    
    Args:
        target_file_path: Path to the BMO Excel file
        current_date: Current date - only records in the same month will be processed
    
    Returns:
        List of BankRecord objects
    """
    records = []
    
    # Get the month range for filtering
    month_start, month_end = get_month_date_range(current_date)
    
    try:
        # Read the Excel file
        df = pd.read_excel(target_file_path, header=None)
        
        # Find all account sections by looking for account patterns
        account_indices = []
        data_start_indices = []
        
        for i in range(len(df)):
            cell_value = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ""
            
            # Check if this row contains an account name
            # Look for patterns: "HAI DI LAO" or account format ending with "(BMO - DDA)"
            if "HAI DI LAO" in cell_value or "(BMO - DDA)" in cell_value:
                account_indices.append(i)
                
                # Look for the data header row (contains "Date")
                for j in range(i + 1, min(i + 10, len(df))):
                    if pd.notna(df.iloc[j, 0]) and str(df.iloc[j, 0]).strip() == "Date":
                        data_start_indices.append(j)
                        break
        
        # Process each account section
        for idx, (account_idx, data_start_idx) in enumerate(zip(account_indices, data_start_indices)):
            # Extract account name and account number
            account_full_name = str(df.iloc[account_idx, 0])
            
            # Extract account number from format: "HAI DI LAO CANADA RESTURANTS GROUP USD - 00044660798 USD (BMO - DDA)"
            # The account number is between " - " and the next space or currency code
            account_number = ""
            account_name = account_full_name
            
            if " - " in account_full_name:
                # Split by " - " to get the part after the dash
                parts = account_full_name.split(" - ")
                if len(parts) >= 2:
                    # The account number is in the second part, before the currency or (BMO
                    second_part = parts[1].strip()
                    # Split by space to get the first element which should be the account number
                    number_parts = second_part.split()
                    if number_parts:
                        account_number = number_parts[0]
                        # Use account number as the primary identifier
                        account_name = account_number
            
            # Determine the end of this section (next account or end of file)
            if idx < len(account_indices) - 1:
                section_end = account_indices[idx + 1]
            else:
                section_end = len(df)
            
            # Extract the data table for this account
            # Get column headers from the data_start_idx row
            headers = df.iloc[data_start_idx].dropna().tolist()
            
            # Check if there's actual data (not "No Data Available")
            if data_start_idx + 1 < section_end:
                first_data_cell = df.iloc[data_start_idx + 1, 0]
                if pd.notna(first_data_cell) and "No Data Available" not in str(first_data_cell):
                    # Extract data rows
                    for row_idx in range(data_start_idx + 1, section_end):
                        row = df.iloc[row_idx]
                        
                        # Stop if we hit an empty row or another section marker
                        if pd.isna(row[0]) or \
                        "Generated" in str(row[0]) or \
                        "HAI DI LAO" in str(row[0]) or \
                        "End of transactions for the selected date range" in str(row[0]) or \
                        "Last Balance received" in str(row[0]) or \
                        "Total Debits:" in str(row[0]) or \
                        "Total Credits:" in str(row[0]):
                            break
                        
                        # Create BankRecord from the row
                        try:
                            record = BankRecord()
                            
                            # Map columns based on header positions
                            date_col = 0  # Date
                            desc_col = 2  # Transaction Description (short)
                            cust_ref_col = 3  # Customer Reference
                            bank_ref_col = 4  # Bank Reference
                            debit_col = 5  # Debit
                            credit_col = 6  # Credit
                            balance_col = 7  # Balance
                            details_col = 8  # Details (full description)
                            
                            # Parse date
                            date_value = row[date_col]
                            if pd.notna(date_value):
                                if isinstance(date_value, datetime):
                                    record.date = date_value
                                else:
                                    # Try to parse string date
                                    record.date = pd.to_datetime(str(date_value))
                                
                                # Only process records within the current month
                                if not (month_start <= record.date <= month_end):
                                    continue
                            else:
                                continue  # Skip rows without dates
                            
                            # Extract other fields
                            # Transaction Description is the short description
                            record.short_desctiption = str(row[desc_col]) if pd.notna(row[desc_col]) else ""
                            # Details column is the full description
                            if len(row) > details_col:
                                record.full_desctiption = str(row[details_col]) if pd.notna(row[details_col]) else ""
                            else:
                                record.full_desctiption = record.short_desctiption  # Fallback to short if no details column
                            
                            record.customer_reference = str(row[cust_ref_col]) if pd.notna(row[cust_ref_col]) else None
                            record.bank_reference = str(row[bank_ref_col]) if pd.notna(row[bank_ref_col]) else None
                            
                            # Parse amounts (handle cases where non-numeric values appear in amount columns)
                            debit_value = row[debit_col]
                            credit_value = row[credit_col]
                            
                            # Parse debit - check if it's a valid numeric value
                            if pd.notna(debit_value):
                                debit_str = str(debit_value).strip()
                                if debit_str:
                                    try:
                                        record.debit = float(debit_str)
                                    except ValueError:
                                        # If it's not a number, it might be a reference number that's in wrong column
                                        record.debit = 0.0
                                        # If bank_reference is empty and this looks like a reference, use it
                                        if not record.bank_reference and '-' in debit_str:
                                            record.bank_reference = debit_str
                                else:
                                    record.debit = 0.0
                            else:
                                record.debit = 0.0
                            
                            # Parse credit - check if it's a valid numeric value    
                            if pd.notna(credit_value):
                                credit_str = str(credit_value).strip()
                                if credit_str:
                                    try:
                                        record.credit = float(credit_str)
                                    except ValueError:
                                        # If it's not a number, it might be a reference number that's in wrong column
                                        record.credit = 0.0
                                        # If bank_reference is empty and this looks like a reference, use it
                                        if not record.bank_reference and '-' in credit_str:
                                            record.bank_reference = credit_str
                                else:
                                    record.credit = 0.0
                            else:
                                record.credit = 0.0
                            
                            # Skip records where both debit and credit are 0
                            if record.debit == 0.0 and record.credit == 0.0:
                                continue
                            
                            # Add account info to serial number for grouping
                            # Format as BMO + last 4 digits of account number
                            if account_name and len(account_name) >= 4:
                                account_short = account_name[-4:]  # Last 4 digits
                                record.serial_number = f"BMO{account_short}_{row_idx}"
                            else:
                                record.serial_number = f"BMO_{account_name}_{row_idx}"
                            
                            records.append(record)
                            
                        except Exception as e:
                            logger.warning(f"Error parsing BMO row {row_idx}: {str(e)}")
                            continue
        
        logger.info(f"Extracted {len(records)} BMO records for {month_start.strftime('%Y-%m')} from {target_file_path}")
        
    except Exception as e:
        logger.error(f"Error reading BMO file {target_file_path}: {str(e)}")
        raise
    
    return records

if __name__ == "__main__":
    # Test with sample file
    test_file = r"D:\personal_programming_work\honeypot_frontend_v2\haidilao_analyze_database\paperwork-automation\history_files\bank_daily_report\2025-08\ReconciliationReport_09022025-011316.xls"
    
    if os.path.exists(test_file):
        # Use September 1, 2025 as current date
        current_date = datetime(2025, 9, 1)
        records = extract_bmo_sheet_infomation(test_file, current_date)
        print(f"Extracted {len(records)} BMO records (before {current_date.strftime('%Y-%m-%d')})")
        
        # Group by account for better visualization
        from collections import defaultdict
        accounts = defaultdict(list)
        for record in records:
            if record.serial_number:
                account_key = record.serial_number.rsplit('_', 1)[0]
                accounts[account_key].append(record)
        
        print(f"\nAccounts found: {list(accounts.keys())}")
        
        # Show first 5 records from each account
        for account_key, account_records in accounts.items():
            print(f"\n{'='*60}")
            print(f"Account: {account_key}")
            print(f"Total transactions: {len(account_records)}")
            print(f"{'='*60}")
            
            for i, record in enumerate(account_records[:5]):  # Show first 5 records
                print(f"\nRecord {i+1}:")
                print(f"  Date:         {record.date}")
                print(f"  Short Desc:   {record.short_desctiption if record.short_desctiption else '(empty)'}")
                print(f"  Full Desc:    {record.full_desctiption if record.full_desctiption else '(empty)'}")
                print(f"  Debit:        ${record.debit:,.2f}")
                print(f"  Credit:       ${record.credit:,.2f}")
                print(f"  Customer Ref: {record.customer_reference if record.customer_reference else '(none)'}")
                print(f"  Bank Ref:     {record.bank_reference if record.bank_reference else '(none)'}")
                print(f"  Serial:       {record.serial_number}")
            
            if len(account_records) > 5:
                print(f"\n  ... and {len(account_records) - 5} more transactions")
    else:
        print(f"Test file not found: {test_file}")