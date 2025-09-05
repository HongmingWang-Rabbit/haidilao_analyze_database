"""
CIBC bank statement extractor.

CIBC format:
- Header at row 1 (0-indexed)
- Date column: "Date"
- Debit column: "Debit"
- Credit column: "Credit"
- Description: "Transaction details"
"""

from .base_extractor import BankExtractor
from typing import Dict, Optional
from datetime import datetime
import pandas as pd


class CIBCExtractor(BankExtractor):
    """Extractor for CIBC bank statements."""
    
    def get_header_row(self) -> int:
        """CIBC has header at row 2 (index 1)."""
        return 1
    
    def get_date_column(self) -> str:
        """CIBC uses 'Date' column."""
        return 'Date'
    
    def get_amount_columns(self) -> Dict[str, str]:
        """CIBC uses 'Debit' and 'Credit' columns."""
        return {
            'debit': 'Debit',
            'credit': 'Credit'
        }
    
    def get_description_column(self) -> str:
        """CIBC uses 'Transaction details' column (with space)."""
        return 'Transaction details'  # Note the lack of trailing space in some files
    
    def parse_date(self, row: pd.Series) -> Optional[str]:
        """
        Parse date from row for CIBC format.
        CIBC typically uses DD-MM-YYYY format (like 03-09-2025).
        
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
                # CIBC primarily uses DD-MM-YYYY format
                # Try this format first for better performance
                try:
                    parsed_date = datetime.strptime(date_value, '%d-%m-%Y')
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    pass
                
                # Fall back to other common formats if DD-MM-YYYY doesn't work
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        continue
            elif isinstance(date_value, datetime):
                return date_value.strftime('%Y-%m-%d')
            elif isinstance(date_value, (int, float)):
                # Excel date number
                from datetime import timedelta
                base_date = datetime(1899, 12, 30)  # Excel's base date
                parsed_date = base_date + timedelta(days=int(date_value))
                return parsed_date.strftime('%Y-%m-%d')
        except:
            pass
        
        # If all else fails, use parent class method
        return super().parse_date(row)