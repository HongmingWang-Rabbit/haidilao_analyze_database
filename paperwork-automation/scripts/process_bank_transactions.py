#!/usr/bin/env python3
"""
Bank Transaction Processing Script
Processes all bank files and appends new transactions to existing sheets
"""

from configs.bank_desc import BankDescriptionConfig
from openpyxl.styles import PatternFill, Font, Border, Side
from openpyxl import load_workbook, Workbook
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BankTransactionProcessor:
    """Process bank transactions from multiple sources and append to existing worksheets"""

    def __init__(self, target_year: int, target_month: int):
        self.target_year = target_year
        self.target_month = target_month
        self.input_dir = Path("Input/daily_report/bank_transactions_reports")
        self.template_file = self.input_dir / "CA全部7家店明细.xlsx"

        # Always save to output folder with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.output_file = Path("output") / \
            f"Bank_Transactions_Report_{timestamp}.xlsx"

        # Account mapping: input account identifier -> output sheet name
        self.account_mapping = {
            # BMO accounts (from ReconciliationReport)
            "3817": "CA1D-3817",
            "6027": "CA2D-6027",
            "1680": "CA3D-1680",
            "1699": "CA4D-1699",
            "6333": "CA5D-6333",
            "6317": "CA6D-6317",
            "0798": "BMO美金-0798",

            # CIBC account (from TransactionDetail.csv)
            "0401": "CA7D-CIBC 0401",

            # RBC accounts (from individual files)
            "5401": "RBC 5401",
            "5419": "RBC 5419",
            "0517": "RBC0517-Hi Bowl",
            "0922": "RBC 0922（USD）",
            "3088": "RBC3088（USD）-Hi Bowl"
        }

    def process_all_transactions(self) -> None:
        """Main processing function"""
        logger.info(
            f"Processing bank transactions for {self.target_year}-{self.target_month:02d}")

        # Collect all transactions by sheet name
        all_transactions = {}

        # Process BMO reconciliation report (multiple accounts)
        bmo_transactions = self.process_bmo_reconciliation()
        for sheet_name, transactions in bmo_transactions.items():
            if transactions:
                all_transactions[sheet_name] = transactions
                logger.info(
                    f"Extracted {len(transactions)} transactions for {sheet_name}")

        # Process CIBC transaction detail
        cibc_transactions = self.process_cibc_file()
        if cibc_transactions:
            all_transactions["CA7D-CIBC 0401"] = cibc_transactions
            logger.info(
                f"Extracted {len(cibc_transactions)} transactions for CA7D-CIBC 0401")

        # Process RBC files (individual accounts)
        rbc_transactions = self.process_rbc_files()
        for sheet_name, transactions in rbc_transactions.items():
            if transactions:
                all_transactions[sheet_name] = transactions
                logger.info(
                    f"Extracted {len(transactions)} transactions for {sheet_name}")

        if not all_transactions:
            logger.warning("No transactions found for processing")
            return

        # Update existing workbook
        self.append_to_existing_workbook(all_transactions)

    def process_bmo_reconciliation(self) -> Dict[str, List[Dict]]:
        """Process BMO reconciliation report containing multiple accounts"""
        file_path = None
        for f in self.input_dir.glob("ReconciliationReport*.xls"):
            file_path = f
            break

        if not file_path or not file_path.exists():
            logger.warning("BMO ReconciliationReport not found")
            return {}

        logger.info(f"Processing BMO reconciliation: {file_path.name}")

        try:
            # Read the Excel file
            df = pd.read_excel(file_path, engine='xlrd')

            # The file structure has account headers and transaction rows
            transactions_by_account = {}
            current_account = None

            for idx, row in df.iterrows():
                # Look for account header lines
                first_col = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""

                # Check if this is an account header
                for account_num in ["3817", "6027", "1680", "1699", "6333", "6317", "0798"]:
                    if account_num in first_col:
                        current_account = account_num
                        sheet_name = self.account_mapping[account_num]
                        if sheet_name not in transactions_by_account:
                            transactions_by_account[sheet_name] = []
                        break

                # If we have a current account and this looks like transaction data
                if current_account and self.is_transaction_row(row):
                    transaction = self.parse_bmo_transaction_row(
                        row, current_account)
                    if transaction:  # Date filtering now done in parse method
                        sheet_name = self.account_mapping[current_account]
                        transactions_by_account[sheet_name].append(transaction)

            return transactions_by_account

        except Exception as e:
            logger.error(f"Error processing BMO reconciliation: {e}")
            return {}

    def is_transaction_row(self, row) -> bool:
        """Check if a row contains transaction data"""
        # Look for date pattern in first column and amount in other columns
        first_col = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""

        # Check if first column looks like a date
        if any(month in first_col for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
            return True
        return False

    def parse_bmo_transaction_row(self, row, account_num: str) -> Optional[Dict]:
        """Parse a BMO transaction row"""
        try:
            # Map columns based on BMO format
            date_str = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""

            # Parse date
            try:
                date_obj = pd.to_datetime(date_str)
                # Filter by target month/year immediately after parsing
                if date_obj.year != self.target_year or date_obj.month != self.target_month:
                    return None
            except:
                return None

            # BMO Column Structure:
            # Column 0: Date
            # Column 1: Flag (* or NaN)
            # Column 2: Transaction Description
            # Column 3: Customer Reference
            # Column 4: Bank Reference
            # Column 5: Debit
            # Column 6: Credit
            # Column 7: Balance
            # Column 8: Details

            description = str(row.iloc[2]) if len(
                row) > 2 and pd.notna(row.iloc[2]) else ""
            customer_ref = str(row.iloc[3]) if len(
                row) > 3 and pd.notna(row.iloc[3]) else ""
            bank_ref = str(row.iloc[4]) if len(
                row) > 4 and pd.notna(row.iloc[4]) else ""
            details = str(row.iloc[8]) if len(
                row) > 8 and pd.notna(row.iloc[8]) else ""

            # Extract debit/credit from specific columns
            debit = ""
            credit = ""

            if len(row) > 5 and pd.notna(row.iloc[5]):
                debit_val = row.iloc[5]
                if isinstance(debit_val, (int, float)) and debit_val != 0:
                    debit = abs(debit_val)

            if len(row) > 6 and pd.notna(row.iloc[6]):
                credit_val = row.iloc[6]
                if isinstance(credit_val, (int, float)) and credit_val != 0:
                    credit = abs(credit_val)

            # Get classification
            classification = BankDescriptionConfig.get_transaction_info(
                details)

            return {
                'Date': date_obj.strftime('%Y-%m-%d'),
                'Transaction Description': description,
                'Customer Reference': customer_ref,
                'Bank Reference': bank_ref,
                'Debit': debit,
                'Credit': credit,
                'Details': details,
                '品名': classification['品名'],
                '付款详情': classification['付款详情'],
                '单据号': "",
                '附件': "",
                '是否登记线下付款表': "",
                '是否登记支票使用表': "",
                '_account': account_num
            }

        except Exception as e:
            logger.error(f"Error parsing BMO transaction row: {e}")
            return None

    def process_cibc_file(self) -> List[Dict]:
        """Process CIBC TransactionDetail.csv"""
        file_path = self.input_dir / "TransactionDetail.csv"
        if not file_path.exists():
            logger.warning("CIBC TransactionDetail.csv not found")
            return []

        logger.info(f"Processing CIBC: {file_path.name}")

        try:
            df = pd.read_csv(file_path)
            transactions = []

            for _, row in df.iterrows():
                date_value = pd.to_datetime(row['Ledger date'])
                if not self.is_target_month(date_value.strftime('%Y-%m-%d')):
                    continue

                description = str(row.get('Description', ''))
                additional_details = str(row.get('ADDITIONAL DETAILS', ''))
                amount = row.get('Amount', 0)
                transaction_type_col = str(row.get('Transaction type', ''))

                # Determine debit/credit based on transaction type
                if 'Debit' in transaction_type_col:
                    debit = abs(amount)
                    credit = ''
                elif 'Credit' in transaction_type_col:
                    debit = ''
                    credit = abs(amount)
                else:
                    debit = abs(amount) if amount < 0 else ''
                    credit = amount if amount > 0 else ''

                # Use ADDITIONAL DETAILS for classification if available, otherwise use Description
                classification_text = additional_details if additional_details.strip() else description
                classification = BankDescriptionConfig.get_transaction_info(
                    classification_text)
                transaction = {
                    'Date': date_value.strftime('%Y-%m-%d'),
                    'Transaction Description': description,
                    'Customer Reference': str(row.get('Client reference', '')),
                    'Bank Reference': str(row.get('Bank reference', '')),
                    'Debit': debit,
                    'Credit': credit,
                    'Details': classification_text,
                    '品名': classification['品名'],
                    '付款详情': classification['付款详情'],
                    '单据号': "",
                    '附件': "",
                    '是否登记线下付款表': "",
                    '是否登记支票使用表': "",
                    '_account': '0401'
                }
                transactions.append(transaction)

            return transactions

        except Exception as e:
            logger.error(f"Error processing CIBC file: {e}")
            return []

    def process_rbc_files(self) -> Dict[str, List[Dict]]:
        """Process individual RBC files"""
        transactions_by_account = {}

        rbc_files = {
            "5401": "RBC Business Bank Account (5401)*.xlsx",
            "5419": "RBC Business Bank Account (5419)*.xlsx",
            "0517": "RBC Business Bank Account (0517)*.xlsx",
            "0922": "RBC Business Bank Account (0922)*.xlsx",
            "3088": "RBC Business Bank Account (3088)*.xlsx"
        }

        for account_num, pattern in rbc_files.items():
            files = list(self.input_dir.glob(pattern))
            if not files:
                logger.warning(f"RBC file for account {account_num} not found")
                continue

            file_path = files[0]  # Take first match
            logger.info(f"Processing RBC {account_num}: {file_path.name}")

            try:
                df = pd.read_excel(file_path, engine='openpyxl')
                transactions = []

                for _, row in df.iterrows():
                    date_value = pd.to_datetime(row['Date'])
                    if not self.is_target_month(date_value.strftime('%Y-%m-%d')):
                        continue

                    # Combine description fields
                    desc_fields = ['Description 1', 'Description 2',
                                   'Description 3', 'Description 4', 'Description 5']
                    description = " ".join([str(row.get(
                        field, '')) for field in desc_fields if pd.notna(row.get(field, ''))]).strip()

                    withdrawals = row.get('Withdrawals', 0)
                    deposits = row.get('Deposits', 0)

                    debit = withdrawals if pd.notna(
                        withdrawals) and withdrawals > 0 else ''
                    credit = deposits if pd.notna(
                        deposits) and deposits > 0 else ''

                    classification = BankDescriptionConfig.get_transaction_info(
                        description)
                    transaction = {
                        'Date': date_value.strftime('%Y-%m-%d'),
                        'Transaction Description': description,
                        'Customer Reference': "",
                        'Bank Reference': "",
                        'Debit': debit,
                        'Credit': credit,
                        'Details': description,  # Use description as details for RBC
                        '品名': classification['品名'],
                        '付款详情': classification['付款详情'],
                        '单据号': "",
                        '附件': "",
                        '是否登记线下付款表': "",
                        '是否登记支票使用表': "",
                        '_account': account_num
                    }
                    transactions.append(transaction)

                if transactions:
                    sheet_name = self.account_mapping[account_num]
                    transactions_by_account[sheet_name] = transactions

            except Exception as e:
                logger.error(f"Error processing RBC file {account_num}: {e}")

        return transactions_by_account

    def is_target_month(self, date_str: str) -> bool:
        """Check if date is in target month/year"""
        try:
            date_obj = pd.to_datetime(date_str)
            return date_obj.year == self.target_year and date_obj.month == self.target_month
        except:
            return False

    def append_to_existing_workbook(self, all_transactions: Dict[str, List[Dict]]) -> None:
        """Append transactions to existing workbook sheets"""
        try:
            if self.template_file.exists():
                logger.info(f"Loading template workbook: {self.template_file}")
                wb = load_workbook(self.template_file)
            else:
                logger.error(
                    f"Template file does not exist: {self.template_file}")
                return

            total_added = 0
            total_skipped = 0

            for sheet_name, transactions in all_transactions.items():
                if sheet_name not in wb.sheetnames:
                    logger.warning(
                        f"Sheet '{sheet_name}' not found in workbook")
                    continue

                ws = wb[sheet_name]
                added, skipped = self.append_to_worksheet(ws, transactions)
                total_added += added
                total_skipped += skipped
                logger.info(
                    f"Sheet '{sheet_name}': Added {added} new transactions (skipped {skipped} duplicates)")

            # Save to output folder only (never modify template)
            self.output_file.parent.mkdir(exist_ok=True)
            try:
                wb.save(self.output_file)
                logger.info(f"Created output file: {self.output_file}")
                print(
                    f"SUCCESS: Bank report saved to output folder: {self.output_file}")
                print(
                    f"SUMMARY: Added {total_added} new transactions, skipped {total_skipped} duplicates")
            except Exception as e:
                logger.error(f"Failed to save output file: {e}")
                print(f"ERROR: Could not save output file: {e}")

        except Exception as e:
            logger.error(f"Error updating workbook: {e}")
            raise

    def get_header_positions_for_sheet(self, sheet_name: str) -> Dict[str, int]:
        """Get bank-specific header positions based on sheet name"""
        if 'CIBC' in sheet_name:
            # CIBC format: 11 columns
            return {
                'Date': 1,
                'Transaction Description': 2,  # "Transaction details"
                'Customer Reference': 2,       # Combined in Transaction details
                'Bank Reference': 2,           # Combined in Transaction details
                'Debit': 3,
                'Credit': 4,
                'Details': 2,                  # Use Transaction details
                '品名': 6,
                '付款详情': 7,
                '单据号': 8,
                '附件': 9,
                '是否登记线下付款表': 10,
                '是否登记支票使用表': 11
            }
        elif sheet_name.startswith('RBC'):
            # RBC format: 12 columns
            return {
                'Date': 2,                     # "Effective Date"
                'Transaction Description': 1,  # "Description"
                'Customer Reference': 3,       # "Serial Number"
                'Bank Reference': 3,           # "Serial Number"
                'Debit': 4,                    # "Debits"
                'Credit': 5,                   # "Credits"
                'Details': 1,                  # Use Description
                '品名': 7,
                '付款详情': 8,
                '单据号': 9,
                '附件': 10,
                '是否登记线下付款表': 11,
                '是否登记支票使用表': 12
            }
        else:
            # BMO format: 14 columns (default)
            return {
                'Date': 1,
                'Transaction Description': 3,
                'Customer Reference': 4,
                'Bank Reference': 5,
                'Debit': 6,
                'Credit': 7,
                'Details': 8,
                '品名': 9,
                '付款详情': 10,
                '单据号': 11,
                '附件': 12,
                '是否登记线下付款表': 13,
                '是否登记支票使用表': 14
            }

    def append_to_worksheet(self, ws, transactions: List[Dict]) -> tuple:
        """Append transactions to existing worksheet"""
        # Find the last row with data (starting from row 3)
        last_row = 2  # Headers are in row 2
        for row in range(3, ws.max_row + 1):
            if any(ws.cell(row=row, column=col).value for col in range(1, 12)):
                last_row = row
            else:
                break

        # Get bank-specific header positions
        header_positions = self.get_header_positions_for_sheet(ws.title)

        added_count = 0
        skipped_count = 0

        for transaction in transactions:
            # Check for duplicates
            is_duplicate = self.is_duplicate_transaction(
                ws, transaction, last_row)
            if is_duplicate:
                skipped_count += 1
                continue

            # Add new transaction
            new_row = last_row + 1 + added_count

            for field, col_idx in header_positions.items():
                if field in transaction:
                    cell = ws.cell(row=new_row, column=col_idx,
                                   value=transaction[field])

                    # Apply green background color for coloring fields based on configuration
                    if field in ['单据号', '附件', '是否登记线下付款表', '是否登记支票使用表']:
                        # Get classification for this transaction's details
                        details = transaction.get('Details', '')
                        classification = BankDescriptionConfig.get_transaction_info(
                            details)
                        if classification.get(field, False):
                            cell.fill = PatternFill(
                                start_color='90EE90', end_color='90EE90', fill_type='solid')  # Light green

                    # Apply red background color for uncategorized transactions (需要手动分类)
                    elif field == '品名' and transaction.get(field) == '未分类交易':
                        cell.fill = PatternFill(
                            start_color='FFB6C1', end_color='FFB6C1', fill_type='solid')  # Light red

            added_count += 1

        return added_count, skipped_count

    def is_duplicate_transaction(self, ws, transaction: Dict, last_row: int) -> bool:
        """Check if transaction already exists in worksheet"""
        # Check last 100 rows for duplicates (performance optimization)
        start_row = max(3, last_row - 100)

        for row in range(start_row, last_row + 1):
            existing_date = ws.cell(row=row, column=1).value
            existing_desc = ws.cell(row=row, column=3).value
            existing_debit = ws.cell(row=row, column=6).value
            existing_credit = ws.cell(row=row, column=7).value

            # Convert to strings for comparison
            existing_date_str = str(existing_date) if existing_date else ""
            existing_desc_str = str(existing_desc) if existing_desc else ""
            existing_debit_str = str(existing_debit) if existing_debit else ""
            existing_credit_str = str(
                existing_credit) if existing_credit else ""

            transaction_date_str = str(transaction.get('Date', ''))
            transaction_desc_str = str(
                transaction.get('Transaction Description', ''))
            transaction_debit_str = str(transaction.get('Debit', ''))
            transaction_credit_str = str(transaction.get('Credit', ''))

            # Check if key fields match
            if (existing_date_str == transaction_date_str and
                existing_desc_str == transaction_desc_str and
                existing_debit_str == transaction_debit_str and
                    existing_credit_str == transaction_credit_str):
                return True

        return False


def main():
    parser = argparse.ArgumentParser(description='Process bank transactions')
    parser.add_argument('--target-date', type=str, required=True,
                        help='Target date in YYYY-MM-DD format')
    args = parser.parse_args()

    try:
        target_date = datetime.strptime(args.target_date, '%Y-%m-%d')
        processor = BankTransactionProcessor(
            target_date.year, target_date.month)
        processor.process_all_transactions()
        logger.info("Bank transaction processing completed successfully")
        logger.info(f"Output saved to: {processor.output_file}")
        print("Bank transaction processing completed successfully!")

    except Exception as e:
        logger.error(f"Error processing bank transactions: {e}")
        print("ERROR: Bank transaction processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
