"""
RBC bank statement extractor.

RBC format:
- Header at row 1 (0-indexed)
- Date column: "Effective Date"
- Debit column: "Debits"
- Credit column: "Credits"
- Description: "Description"
"""

from .base_extractor import BankExtractor
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class RBCExtractor(BankExtractor):
    """Extractor for RBC bank statements."""
    
    def get_header_row(self) -> int:
        """RBC has header at row 2 (index 1)."""
        return 1
    
    def get_date_column(self) -> str:
        """RBC uses 'Effective Date' column."""
        return 'Effective Date'
    
    def get_amount_columns(self) -> Dict[str, str]:
        """RBC uses 'Debits' and 'Credits' columns (plural)."""
        return {
            'debit': 'Debits',
            'credit': 'Credits'
        }
    
    def get_description_column(self) -> str:
        """RBC uses 'Description' column."""
        return 'Description'
    
    def parse_date(self, row: pd.Series) -> Optional[str]:
        """
        Parse date from row for RBC format.
        For RBC, we simply return the date string as-is from the Excel file,
        since RBC already uses their own format (YYYY-DD-MM) in the Excel.
        
        Args:
            row: Data row
            
        Returns:
            Date string as it appears in the Excel file
        """
        date_col = self.get_date_column()
        
        if date_col not in row or pd.isna(row[date_col]):
            return None
        
        date_value = row[date_col]
        
        logger.info(f"[RBC] Date value from Excel: '{date_value}' (type: {type(date_value).__name__})")
        
        # If it's already a string, just return it as-is
        # RBC Excel files already have dates in their preferred format
        if isinstance(date_value, str):
            logger.info(f"[RBC] Returning date as-is from Excel: {date_value}")
            return date_value
        
        # If it's a datetime object, format it as YYYY-DD-MM for RBC
        elif isinstance(date_value, datetime):
            # For datetime objects, we need to swap month and day for RBC format
            year = date_value.year
            month = date_value.month
            day = date_value.day
            rbc_format = f"{year:04d}-{day:02d}-{month:02d}"
            logger.info(f"[RBC] Converting datetime to RBC format: {date_value.strftime('%Y-%m-%d')} -> {rbc_format}")
            return rbc_format
        
        # If it's a number (Excel date), convert and format for RBC
        elif isinstance(date_value, (int, float)):
            try:
                from datetime import timedelta
                base_date = datetime(1899, 12, 30)  # Excel's base date
                parsed_date = base_date + timedelta(days=int(date_value))
                # Format as YYYY-DD-MM for RBC
                year = parsed_date.year
                month = parsed_date.month
                day = parsed_date.day
                rbc_format = f"{year:04d}-{day:02d}-{month:02d}"
                logger.info(f"[RBC] Converting Excel number to RBC format: {date_value} -> {rbc_format}")
                return rbc_format
            except:
                pass
        
        # Last resort - convert to string
        return str(date_value) if date_value else None