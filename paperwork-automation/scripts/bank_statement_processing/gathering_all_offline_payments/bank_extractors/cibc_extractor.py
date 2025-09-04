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
from typing import Dict


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