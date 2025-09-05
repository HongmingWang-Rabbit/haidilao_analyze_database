"""
Base class for bank-specific extractors.
"""

import pandas as pd
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BankExtractor(ABC):
    """Abstract base class for bank-specific data extractors."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.bank_name = self.__class__.__name__.replace('Extractor', '')
        
    @abstractmethod
    def get_header_row(self) -> int:
        """
        Get the row index where the header is located (0-indexed).
        
        Returns:
            Header row index
        """
        pass
    
    @abstractmethod
    def get_date_column(self) -> str:
        """
        Get the name of the date column for this bank.
        
        Returns:
            Date column name
        """
        pass
    
    @abstractmethod
    def get_amount_columns(self) -> Dict[str, str]:
        """
        Get the names of debit and credit columns.
        
        Returns:
            Dictionary with 'debit' and 'credit' keys
        """
        pass
    
    @abstractmethod
    def get_description_column(self) -> str:
        """
        Get the name of the transaction description column.
        
        Returns:
            Description column name
        """
        pass
    
    def extract_from_sheet(self, file_path: Path, sheet_name: str, payment_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract offline payments from a specific sheet.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to process
            payment_info: Payment info from configuration
            
        Returns:
            List of extracted payment records
        """
        logger.debug(f"[{self.bank_name}] Processing sheet: {sheet_name}")
        
        try:
            # Read the sheet with bank-specific header row
            # Force '是否登记线下付款表' column to be read as string to preserve "待确认" values
            df = pd.read_excel(
                file_path, 
                sheet_name=sheet_name, 
                header=self.get_header_row(),
                engine='openpyxl',
                dtype={'是否登记线下付款表': str}  # Force as string to preserve mixed types
            )
            
            # Check if the required column exists
            if '是否登记线下付款表' not in df.columns:
                logger.debug(f"[{self.bank_name}] Sheet {sheet_name} does not have '是否登记线下付款表' column")
                return []
            
            # Filter for rows with '待确认'
            pending_rows = df[df['是否登记线下付款表'] == '待确认'].copy()
            
            if pending_rows.empty:
                logger.debug(f"[{self.bank_name}] No pending confirmations in sheet {sheet_name}")
                return []
            
            # Process each pending row
            records = []
            for idx, row in pending_rows.iterrows():
                record = self.create_payment_record(row, payment_info, sheet_name)
                if record:
                    records.append(record)
            
            logger.info(f"[{self.bank_name}] Extracted {len(records)} records from sheet {sheet_name}")
            return records
            
        except Exception as e:
            logger.error(f"[{self.bank_name}] Error processing sheet {sheet_name}: {e}")
            return []
    
    def create_payment_record(self, row: pd.Series, payment_info: Dict, sheet_name: str) -> Optional[Dict[str, Any]]:
        """
        Create a payment record for the offline payment sheet.
        
        Args:
            row: Data row from bank statement
            payment_info: Payment info from configuration
            sheet_name: Name of the source sheet
            
        Returns:
            Dictionary with payment record data, or None if invalid
        """
        try:
            # Parse date and format as YYYY-MM-DD
            payment_date = self.parse_date(row)
            
            # Determine currency
            currency = 'USD' if 'USD' in sheet_name or '美金' in sheet_name else 'CAD'
            
            # Get amount
            amount = self.get_amount(row)
            
            # Get description
            description = self.get_description(row)
            
            # Get exchange rate from config (imported at the top of the module)
            from configs.bank_statement.processing_sheet import current_cad_to_usd_rate
            
            # Build the record (removed '来源' field)
            record = {
                '公司代码': payment_info['company_code'],
                '付款日期': payment_date or '',
                '申请部门': payment_info['department_name'],
                '品名': row.get('品名', '') if pd.notna(row.get('品名')) else '',
                '付款说明': description,
                '付款币种': currency,
                '付款金额（$）': amount,
                '兑换人民币汇率': current_cad_to_usd_rate,  # Use the rate from config
                '折算美金': '',  # To be filled manually or calculated
            }
            
            return record
            
        except Exception as e:
            logger.error(f"[{self.bank_name}] Error creating payment record: {e}")
            return None
    
    def parse_date(self, row: pd.Series) -> Optional[str]:
        """
        Parse date from row using bank-specific date column.
        
        Args:
            row: Data row
            
        Returns:
            Formatted date string (YYYY-MM-DD) or None
        """
        date_col = self.get_date_column()
        
        if date_col not in row or pd.isna(row[date_col]):
            return None
        
        date_value = row[date_col]
        
        try:
            if isinstance(date_value, str):
                # Try common date formats
                # Added '%d-%m-%Y' format for DD-MM-YYYY (like 03-09-2025)
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%m-%d-%Y', '%b %d, %Y', '%B %d, %Y']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        return parsed_date.strftime('%Y-%m-%d')  # Changed to YYYY-MM-DD format
                    except:
                        continue
            elif isinstance(date_value, datetime):
                return date_value.strftime('%Y-%m-%d')  # Changed to YYYY-MM-DD format
            elif isinstance(date_value, (int, float)):
                # Excel date number
                from datetime import timedelta
                base_date = datetime(1899, 12, 30)  # Excel's base date
                parsed_date = base_date + timedelta(days=int(date_value))
                return parsed_date.strftime('%Y-%m-%d')  # Changed to YYYY-MM-DD format
        except:
            pass
        
        return str(date_value) if date_value else None
    
    def get_amount(self, row: pd.Series) -> Optional[float]:
        """
        Get transaction amount from row.
        
        Args:
            row: Data row
            
        Returns:
            Amount as float or None
        """
        amount_cols = self.get_amount_columns()
        
        # Try debit first
        debit_col = amount_cols.get('debit')
        if debit_col and debit_col in row and pd.notna(row[debit_col]):
            try:
                return abs(float(row[debit_col]))
            except:
                pass
        
        # Then try credit
        credit_col = amount_cols.get('credit')
        if credit_col and credit_col in row and pd.notna(row[credit_col]):
            try:
                return abs(float(row[credit_col]))
            except:
                pass
        
        return None
    
    def get_description(self, row: pd.Series) -> str:
        """
        Get transaction description from row.
        
        Args:
            row: Data row
            
        Returns:
            Description string
        """
        # First try 付款详情
        if '付款详情' in row and pd.notna(row['付款详情']):
            return str(row['付款详情'])
        
        # Then try bank-specific description column
        desc_col = self.get_description_column()
        if desc_col in row and pd.notna(row[desc_col]):
            return str(row[desc_col])
        
        return ''