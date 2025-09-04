"""
Factory for creating bank-specific extractors.
"""

import sys
from pathlib import Path
from typing import Optional
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.bank_statement.processing_sheet import BankWorkSheet
from configs.bank_statement.banks import BankBrands

from .base_extractor import BankExtractor
from .bmo_extractor import BMOExtractor
from .cibc_extractor import CIBCExtractor
from .rbc_extractor import RBCExtractor

logger = logging.getLogger(__name__)


class BankExtractorFactory:
    """Factory for creating bank-specific extractors."""
    
    # Mapping of bank brands to extractor classes
    EXTRACTORS = {
        BankBrands.BMO: BMOExtractor,
        BankBrands.CIBC: CIBCExtractor,
        BankBrands.RBC: RBCExtractor,
    }
    
    @classmethod
    def create_extractor(cls, sheet_name: str) -> Optional[BankExtractor]:
        """
        Create an appropriate extractor for the given sheet.
        
        Args:
            sheet_name: Name of the sheet to process
            
        Returns:
            Bank-specific extractor instance or None if not configured
        """
        # Get bank brand from sheet name
        bank_brand = BankWorkSheet.get(sheet_name)
        
        if not bank_brand:
            logger.warning(f"No bank configuration found for sheet: {sheet_name}")
            return None
        
        # Get extractor class for this bank
        extractor_class = cls.EXTRACTORS.get(bank_brand)
        
        if not extractor_class:
            logger.warning(f"No extractor implemented for bank: {bank_brand}")
            return None
        
        return extractor_class()
    
    @classmethod
    def get_bank_type(cls, sheet_name: str) -> Optional[str]:
        """
        Get the bank type for a given sheet name.
        
        Args:
            sheet_name: Name of the sheet
            
        Returns:
            Bank type string (BMO, CIBC, RBC) or None
        """
        bank_brand = BankWorkSheet.get(sheet_name)
        
        if bank_brand == BankBrands.BMO:
            return 'BMO'
        elif bank_brand == BankBrands.CIBC:
            return 'CIBC'
        elif bank_brand == BankBrands.RBC:
            return 'RBC'
        
        return None