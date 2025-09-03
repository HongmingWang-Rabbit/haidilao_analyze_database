from typing import Dict, List, Tuple, Optional

# Handle imports for both direct execution and module imports
try:
    from .bank_transaction_rules import TransactionMatchRule, TransactionType
except ImportError:
    # For direct execution
    from bank_transaction_rules import TransactionMatchRule, TransactionType


class BankDescriptionConfig:
    """
    Enhanced configuration for bank transaction description mapping using tuple-based rules.
    
    This system supports:
    1. Simple string matching (backward compatibility)
    2. Regex pattern matching
    3. Amount-based classification
    4. Combined description + amount rules
    5. Priority-based rule evaluation
    
    Transaction rules are loaded from bank_transaction_rules.py to keep this file manageable.
    """
    
    @classmethod
    def _get_transaction_rules(cls) -> List[Tuple[TransactionMatchRule, Dict]]:
        """Load transaction rules from external file"""
        try:
            from .bank_transaction_rules import BANK_TRANSACTION_RULES
            return BANK_TRANSACTION_RULES
        except ImportError:
            # For direct execution
            try:
                from bank_transaction_rules import BANK_TRANSACTION_RULES
                return BANK_TRANSACTION_RULES
            except ImportError:
                # Fallback to empty rules if file doesn't exist
                return []
    
    @classmethod
    def get_transaction_info(cls, details: str, amount: Optional[float] = None, transaction_type: Optional[str] = None) -> dict:
        """
        Get transaction information based on details text, amount, and transaction type.
        
        Args:
            details: Transaction details text
            amount: Transaction amount (for exact amount matching)
            transaction_type: 'credit' for incoming money, 'debit' for outgoing money
            
        Returns:
            dict: Transaction mapping information with classification
        """
        if not details:
            return cls._get_default_mapping()
        
        # Get rules from external file and evaluate in order
        transaction_rules = cls._get_transaction_rules()
        
        for rule, classification in transaction_rules:
            if rule.matches(details, amount, transaction_type):
                return classification
        
        # If no rule matches, return default mapping
        return cls._get_default_mapping()
    
    @classmethod
    def add_rule(cls, rule: TransactionMatchRule, classification: Dict):
        """
        Add a new transaction rule to the system.
        Note: This adds to the external rules file at runtime.
        
        Args:
            rule: TransactionMatchRule object
            classification: Classification dictionary
        """
        # Import the external rules and modify them
        try:
            from .bank_transaction_rules import BANK_TRANSACTION_RULES
        except ImportError:
            from bank_transaction_rules import BANK_TRANSACTION_RULES
        BANK_TRANSACTION_RULES.append((rule, classification))
    
    @classmethod
    def get_rules_for_description(cls, description: str) -> List[Tuple[TransactionMatchRule, Dict]]:
        """
        Get all rules that would match a given description (for debugging).
        
        Args:
            description: Transaction description
            
        Returns:
            List of matching (rule, classification) tuples
        """
        transaction_rules = cls._get_transaction_rules()
        matching_rules = []
        for rule, classification in transaction_rules:
            if rule.matches(description):
                matching_rules.append((rule, classification))
        return matching_rules
    
    @classmethod
    def _get_default_mapping(cls) -> dict:
        """Return default mapping for unknown transactions"""
        return {
            "品名": TransactionType.UNCATEGORIZED.value,
            "付款详情": "需要手动分类",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        }


