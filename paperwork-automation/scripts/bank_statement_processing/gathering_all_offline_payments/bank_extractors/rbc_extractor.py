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
from typing import Dict


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