import sys
import os
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict
import logging
from pathlib import Path
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from configs.bank_statement.banks import BankBrands
from configs.bank_statement.processing_sheet import BankWorkSheet, BanWorkSheetToFormattedName
from type.bank_processing import BankRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_account_identifier(sheet_name: str, bank_brand: BankBrands) -> str:
    """
    Extract account identifier from sheet name.
    Format: BankBrand + last 4 digits
    
    Args:
        sheet_name: Name of the sheet
        bank_brand: Bank brand
        
    Returns:
        Account identifier (e.g., BMO3817, RBC5419, CIBC0401)
    """
    # Extract last 4 digits from sheet name
    numbers = re.findall(r'\d+', sheet_name)
    
    if numbers:
        # Get the last number found and take last 4 digits
        last_number = numbers[-1]
        last_4 = last_number[-4:] if len(last_number) >= 4 else last_number.zfill(4)
        return f"{bank_brand.name}{last_4}"
    
    # Fallback to sheet name if no numbers found
    return f"{bank_brand.name}_{sheet_name}"

def read_bmo_worksheet(df: pd.DataFrame, sheet_name: str) -> List[BankRecord]:
    """
    Read BMO worksheet data and convert to BankRecord list.
    
    Args:
        df: DataFrame containing the worksheet data
        sheet_name: Name of the sheet for account identification
        
    Returns:
        List of BankRecord objects
    """
    records = []
    # Use the predefined mapping if available, otherwise fall back to extraction
    account_id = BanWorkSheetToFormattedName.get(sheet_name, extract_account_identifier(sheet_name, BankBrands.BMO))
    
    try:
        # BMO sheets typically have headers around row 3-4
        # Try to find the header row by looking for "Date" column
        header_row = None
        for i in range(min(10, len(df))):
            row_values = df.iloc[i].astype(str).str.lower()
            if any('date' in val for val in row_values):
                header_row = i
                break
        
        if header_row is None:
            logger.warning(f"Could not find header row in BMO sheet {sheet_name}")
            return records
        
        # Set column names from header row
        df.columns = df.iloc[header_row].values
        df_data = df.iloc[header_row+1:].reset_index(drop=True)
        
        # Process each row
        for idx, row in df_data.iterrows():
            try:
                # Skip rows without date
                if pd.isna(row.get('Date')) and pd.isna(row.iloc[0]):
                    continue
                
                record = BankRecord()
                
                # Parse date (first column usually)
                date_val = row.iloc[0] if pd.notna(row.iloc[0]) else row.get('Date')
                if pd.notna(date_val):
                    if isinstance(date_val, datetime):
                        record.date = date_val
                    else:
                        record.date = pd.to_datetime(str(date_val), errors='coerce')
                    
                    if pd.isna(record.date):
                        continue
                else:
                    continue
                
                # Extract other fields based on column position
                # BMO format: Date, [blank], Transaction Description (short), Customer Ref, Bank Ref, Debit, Credit, Details (full)
                if len(row) > 2:
                    # Transaction Description is the short description
                    record.short_desctiption = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
                if len(row) > 3:
                    record.customer_reference = str(row.iloc[3]) if pd.notna(row.iloc[3]) else None
                if len(row) > 4:
                    record.bank_reference = str(row.iloc[4]) if pd.notna(row.iloc[4]) else None
                if len(row) > 5:
                    debit_val = row.iloc[5]
                    if pd.notna(debit_val):
                        try:
                            # Negative values in debit column are actual debits
                            val = float(str(debit_val).replace(',', '').replace('$', ''))
                            record.debit = abs(val) if val < 0 else 0.0
                        except:
                            record.debit = 0.0
                if len(row) > 6:
                    credit_val = row.iloc[6]
                    if pd.notna(credit_val):
                        try:
                            # Positive values in credit column are credits
                            val = float(str(credit_val).replace(',', '').replace('$', ''))
                            record.credit = abs(val) if val > 0 else 0.0
                        except:
                            record.credit = 0.0
                if len(row) > 7:
                    # Details column is the full description
                    record.full_desctiption = str(row.iloc[7]) if pd.notna(row.iloc[7]) else ""
                else:
                    # Fallback to short description if no details column
                    record.full_desctiption = record.short_desctiption
                
                # Skip zero-value records
                if record.debit == 0.0 and record.credit == 0.0:
                    continue
                
                # Set serial number
                record.serial_number = f"{account_id}_{idx}"
                
                records.append(record)
                
            except Exception as e:
                logger.debug(f"Error processing BMO row {idx}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error reading BMO worksheet {sheet_name}: {str(e)}")
    
    return records

def read_rbc_worksheet(df: pd.DataFrame, sheet_name: str) -> List[BankRecord]:
    """
    Read RBC worksheet data and convert to BankRecord list.
    
    Args:
        df: DataFrame containing the worksheet data
        sheet_name: Name of the sheet for account identification
        
    Returns:
        List of BankRecord objects
    """
    records = []
    # Use the predefined mapping if available, otherwise fall back to extraction
    account_id = BanWorkSheetToFormattedName.get(sheet_name, extract_account_identifier(sheet_name, BankBrands.RBC))
    
    try:
        # RBC has different header structure - look for 'Effective Date' or 'Date'
        header_row = None
        for i in range(min(10, len(df))):
            row_values = df.iloc[i].astype(str).str.lower()
            if any('effective date' in val or 'date' in val for val in row_values):
                header_row = i
                break
        
        if header_row is None:
            logger.warning(f"Could not find header row in RBC sheet {sheet_name}")
            return records
        
        # Read data with proper header
        df_data = df.iloc[header_row+1:].reset_index(drop=True)
        
        # Process each row
        for idx, row in df_data.iterrows():
            try:
                # Skip rows without date (date is in column 1 for RBC)
                if pd.isna(row.iloc[1]):
                    continue
                
                record = BankRecord()
                
                # Parse date from column 1 (Excel serial number)
                date_val = row.iloc[1]
                if pd.notna(date_val):
                    try:
                        # Handle Excel serial date format
                        if isinstance(date_val, (int, float)):
                            # Excel date serial number (days since 1900-01-01)
                            record.date = pd.to_datetime('1900-01-01') + pd.Timedelta(days=int(date_val) - 2)
                        elif isinstance(date_val, datetime):
                            record.date = date_val
                        else:
                            record.date = pd.to_datetime(str(date_val), errors='coerce')
                    except:
                        continue
                    
                    if pd.isna(record.date):
                        continue
                else:
                    continue
                
                # Extract other fields
                # RBC format: Description, Effective Date, Serial Number, Debits, Credits
                if len(row) > 0:
                    record.full_desctiption = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                if len(row) > 2:
                    record.bank_reference = str(row.iloc[2]) if pd.notna(row.iloc[2]) else None
                if len(row) > 3:
                    debit_val = row.iloc[3]
                    if pd.notna(debit_val):
                        try:
                            record.debit = float(str(debit_val).replace(',', '').replace('$', ''))
                        except:
                            record.debit = 0.0
                if len(row) > 4:
                    credit_val = row.iloc[4]
                    if pd.notna(credit_val):
                        try:
                            record.credit = float(str(credit_val).replace(',', '').replace('$', ''))
                        except:
                            record.credit = 0.0
                
                # Skip zero-value records
                if record.debit == 0.0 and record.credit == 0.0:
                    continue
                
                # Set serial number
                record.serial_number = f"{account_id}_{idx}"
                
                records.append(record)
                
            except Exception as e:
                logger.debug(f"Error processing RBC row {idx}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error reading RBC worksheet {sheet_name}: {str(e)}")
    
    return records

def read_cibc_worksheet(df: pd.DataFrame, sheet_name: str) -> List[BankRecord]:
    """
    Read CIBC worksheet data and convert to BankRecord list.
    
    Args:
        df: DataFrame containing the worksheet data
        sheet_name: Name of the sheet for account identification
        
    Returns:
        List of BankRecord objects
    """
    records = []
    # Use the predefined mapping if available, otherwise fall back to extraction
    account_id = BanWorkSheetToFormattedName.get(sheet_name, extract_account_identifier(sheet_name, BankBrands.CIBC))
    
    try:
        # CIBC header structure
        header_row = None
        for i in range(min(10, len(df))):
            row_values = df.iloc[i].astype(str).str.lower()
            if any('date' in val for val in row_values):
                header_row = i
                break
        
        if header_row is None:
            logger.warning(f"Could not find header row in CIBC sheet {sheet_name}")
            return records
        
        # Read data with proper header
        df_data = df.iloc[header_row+1:].reset_index(drop=True)
        
        # Process each row
        for idx, row in df_data.iterrows():
            try:
                # Skip rows without date
                if pd.isna(row.iloc[0]):
                    continue
                
                record = BankRecord()
                
                # Parse date
                date_val = row.iloc[0]
                if pd.notna(date_val):
                    if isinstance(date_val, datetime):
                        record.date = date_val
                    else:
                        record.date = pd.to_datetime(str(date_val), errors='coerce')
                    
                    if pd.isna(record.date):
                        continue
                else:
                    continue
                
                # Extract other fields
                # CIBC format: Date, Transaction details, Debit, Credit, Balance
                if len(row) > 1:
                    desc = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
                    # Replace newlines with space for cleaner output
                    record.full_desctiption = desc.replace('\n', ' ')
                if len(row) > 2:
                    debit_val = row.iloc[2]
                    if pd.notna(debit_val):
                        try:
                            record.debit = float(str(debit_val).replace(',', '').replace('$', ''))
                        except:
                            record.debit = 0.0
                if len(row) > 3:
                    credit_val = row.iloc[3]
                    if pd.notna(credit_val):
                        try:
                            record.credit = float(str(credit_val).replace(',', '').replace('$', ''))
                        except:
                            record.credit = 0.0
                
                # Skip zero-value records
                if record.debit == 0.0 and record.credit == 0.0:
                    continue
                
                # Set serial number
                record.serial_number = f"{account_id}_{idx}"
                
                records.append(record)
                
            except Exception as e:
                logger.debug(f"Error processing CIBC row {idx}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error reading CIBC worksheet {sheet_name}: {str(e)}")
    
    return records

def get_file_by_datetime(current_date: datetime) -> str:
    """
    Get the CA全部 file path for the given date.
    
    Args:
        current_date: Date to find the file for
        
    Returns:
        Full path to the file, or None if not found
    """
    # Format the folder as YYYY-MM
    folder_name = current_date.strftime("%Y-%m")
    
    # Build the path
    base_path = Path(__file__).parent.parent.parent.parent
    folder_path = base_path / "history_files" / "bank_daily_report" / folder_name
    
    if not folder_path.exists():
        logger.warning(f"Folder not found: {folder_path}")
        return None
    
    # Look for files starting with CA全部
    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.name.startswith("CA全部") and file_path.suffix == '.xlsx':
            # Skip temporary files
            if not file_path.name.startswith("~$"):
                logger.info(f"Found file: {file_path}")
                return str(file_path)
    
    logger.warning(f"No CA全部 file found in {folder_path}")
    return None

def read_all_worksheet(current_date: datetime) -> Dict[str, List[BankRecord]]:
    """
    Read all worksheets from the CA全部 file for the given date.
    
    Args:
        current_date: Date to process
        
    Returns:
        Dictionary mapping account identifiers to lists of BankRecord objects
    """
    # Get the file path
    file_path = get_file_by_datetime(current_date)
    
    if not file_path:
        logger.error(f"No file found for date {current_date.strftime('%Y-%m')}")
        return {}
    
    results = {}
    
    try:
        # Read all sheets
        xls = pd.ExcelFile(file_path)
        logger.info(f"Processing {len(xls.sheet_names)} sheets from {os.path.basename(file_path)}")
        
        for sheet_name in xls.sheet_names:
            # Skip if not in mapping
            if sheet_name not in BankWorkSheet:
                logger.warning(f"Unknown sheet: {sheet_name}")
                continue
            
            bank_brand = BankWorkSheet[sheet_name]
            logger.info(f"Processing sheet: {sheet_name} ({bank_brand.name})")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Process based on bank type
            if bank_brand == BankBrands.BMO:
                records = read_bmo_worksheet(df, sheet_name)
            elif bank_brand == BankBrands.RBC:
                records = read_rbc_worksheet(df, sheet_name)
            elif bank_brand == BankBrands.CIBC:
                records = read_cibc_worksheet(df, sheet_name)
            else:
                logger.warning(f"Unsupported bank brand: {bank_brand}")
                continue
            
            if records:
                # Get account identifier from first record
                account_id = records[0].serial_number.rsplit('_', 1)[0] if records else extract_account_identifier(sheet_name, bank_brand)
                results[account_id] = records
                logger.info(f"  Extracted {len(records)} records for {account_id}")
            else:
                logger.warning(f"  No records extracted from {sheet_name}")
                
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
    
    return results

def test_read_all():
    """Test function to read all worksheets for August 2025."""
    test_date = datetime(2025, 8, 1)
    
    print(f"\nTesting read_all_worksheet for {test_date.strftime('%Y-%m')}")
    print("="*60)
    
    results = read_all_worksheet(test_date)
    
    if not results:
        print("No data extracted")
        return
    
    print(f"\nExtracted data from {len(results)} accounts:")
    
    for account_id, records in results.items():
        total_debit = sum(r.debit for r in records)
        total_credit = sum(r.credit for r in records)
        
        print(f"\n{account_id}:")
        print(f"  Records: {len(records)}")
        print(f"  Total Debit: ${total_debit:,.2f}")
        print(f"  Total Credit: ${total_credit:,.2f}")
        
        # Show first 5 records
        if records:
            print(f"  First 5 transactions:")
            for i, record in enumerate(records[:5], 1):
                print(f"    {i}. Date: {record.date}")
                print(f"       Short Desc: {record.short_desctiption[:50] if record.short_desctiption else '(empty)'}")
                print(f"       Full Desc: {record.full_desctiption[:50] if record.full_desctiption else '(empty)'}")
                print(f"       Debit: ${record.debit:,.2f}, Credit: ${record.credit:,.2f}")

if __name__ == "__main__":
    test_read_all()