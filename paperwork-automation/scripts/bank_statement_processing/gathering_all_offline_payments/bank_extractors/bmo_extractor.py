"""
BMO bank statement extractor.

BMO format:
- Header at row 1 (0-indexed)
- Date column: "Date"
- Debit column: "Debit"
- Credit column: "Credit"
- Description: "Transaction Description"
"""

from .base_extractor import BankExtractor
from typing import Dict


class BMOExtractor(BankExtractor):
    """Extractor for BMO bank statements."""
    
    def get_header_row(self) -> int:
        """BMO has header at row 2 (index 1)."""
        return 1
    
    def get_date_column(self) -> str:
        """BMO uses 'Date' column."""
        return 'Date'
    
    def get_amount_columns(self) -> Dict[str, str]:
        """BMO uses 'Debit' and 'Credit' columns."""
        return {
            'debit': 'Debit',
            'credit': 'Credit'
        }
    
    def get_description_column(self) -> str:
        """BMO uses 'Transaction Description' column."""
        return 'Transaction Description'