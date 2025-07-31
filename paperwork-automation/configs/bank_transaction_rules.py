"""
Bank Transaction Classification Rules
Contains all the tuple-based rules for bank transaction matching.
"""

import re
from typing import List, Tuple, Dict, Optional, Union
from enum import Enum


class TransactionType(Enum):
    # ALL REAL TYPES - Based on comprehensive analysis of example_bank_sheet_20250723.xlsx
    # Total: 28 actual transaction types found
    INSURANCE_FEE = "保险费"                    # Insurance fees (14 total)
    CREDIT_CARD = "信用卡"                      # Credit card (8 total)
    CREDIT_CARD_PAYMENT = "信用卡还款"          # Credit card payment (3 total)
    LOAN_RECEIVED = "借款到账"                  # Loan received (1 total)
    CUSTOMS_DUTY = "关税"                       # Customs duty (1 total)
    INTERNAL_TRANSFER = "内部转款"              # Internal transfer (43 total)
    INTEREST = "利息"                           # Interest (4 total)
    CHARGEBACK = "回冲"                         # Reversal/chargeback (6 total)
    DORMITORY_FEE = "宿舍费用"                  # Dormitory fees (1 total)
    WAGES = "工资"                              # Wages (28 total)
    WAGES_PLUS_INSURANCE = "工资+保险费"        # Wages + insurance (16 total)
    PLATFORM_FEE = "平台费"                     # Platform fees (12 total)
    PENDING_CONFIRMATION = "待确认"             # Pending confirmation (1 total)
    RENT = "房租"                               # Rent (1 total)
    PROCESSING_FEE = "手续费"                   # Processing fees (38 total)
    INCOME_RECEIVED = "收入进账"                # Income received (575 total)
    SERVICE_FEE = "服务费"                      # Service fees (12 total)
    CLEANING_FEE = "清洁费"                     # Cleaning fees (1 total)
    GAS_FEE = "燃气费"                          # Gas fees (5 total)
    ELECTRICITY_FEE = "电费"                    # Electricity fees (7 total)
    MONITORING_FEE = "监测费"                   # Monitoring fees (1 total)
    LEASE_FEE = "租赁费"                        # Lease fees (10 total)
    TAX_FEE = "税费"                            # Tax fees (2 total)
    MANAGEMENT_FEE = "管理费"                   # Management fees (4 total)
    INTERNET_FEE = "网费"                       # Internet fees (2 total)
    NON_OPERATING_INCOME = "营业外收入"         # Non-operating income (5 total)
    RENTAL_FEE = "租赁费"                        # Rental fees (1 total)
    # Expense reimbursement system (64 total)
    EXPENSE_REIMBURSEMENT = "费用报销系统"

    # Default
    UNCATEGORIZED = "未分类交易"                # Uncategorized transaction


class TransactionMatchRule:
    """
    A rule for matching bank transactions using description and/or amount patterns.

    This class supports:
    1. Simple string matching (for backward compatibility)
    2. Regex pattern matching on description
    3. Amount-based matching (exact or range)
    4. Combined description + amount matching
    """

    def __init__(self,
                 description_pattern: Optional[Union[str, re.Pattern]] = None,
                 amount_pattern: Optional[float] = None,  # Exact amount only
                 transaction_type: Optional[str] = None,  # 'credit' or 'debit'
                 case_sensitive: bool = False):
        """
        Initialize a transaction matching rule.

        Args:
            description_pattern: String or compiled regex pattern for description matching
            amount_pattern: Exact amount for monthly recurring transactions
            transaction_type: 'credit' for incoming money, 'debit' for outgoing money
            case_sensitive: Whether description matching should be case sensitive
        """
        self.description_pattern = description_pattern
        self.amount_pattern = amount_pattern
        self.transaction_type = transaction_type
        self.case_sensitive = case_sensitive

        # Compile regex patterns if needed
        if isinstance(description_pattern, str):
            flags = 0 if case_sensitive else re.IGNORECASE
            self.description_regex = re.compile(
                re.escape(description_pattern), flags)
        elif isinstance(description_pattern, re.Pattern):
            self.description_regex = description_pattern
        else:
            self.description_regex = None

    def matches(self, description: str, amount: Optional[float] = None, transaction_type: Optional[str] = None) -> bool:
        """
        Check if this rule matches the given transaction.

        Args:
            description: Transaction description
            amount: Transaction amount (for exact amount matching)
            transaction_type: 'credit' for incoming money, 'debit' for outgoing money

        Returns:
            bool: True if the rule matches
        """
        # Check description pattern
        description_match = True
        if self.description_regex:
            description_match = bool(
                self.description_regex.search(description or ""))

        # Check exact amount pattern (for recurring monthly transactions)
        amount_match = True
        if self.amount_pattern is not None and amount is not None:
            # Exact amount match (with small tolerance for floating point)
            amount_match = abs(abs(amount) - self.amount_pattern) < 0.01

        # Check transaction type (credit/debit) - now uses passed parameter
        type_match = True
        if self.transaction_type is not None and transaction_type is not None:
            type_match = self.transaction_type == transaction_type

        return description_match and amount_match and type_match


# Enhanced mapping structure using TransactionMatchRule objects
# Based on analysis of real transaction data from CA全部7家店明细.xlsx
# Format: List of (rule, classification) tuples, ordered from most specific to least specific
BANK_TRANSACTION_RULES: List[Tuple[TransactionMatchRule, Dict]] = [

    # ===== EXACT RECURRING PATTERNS (From Real Data Analysis) =====

    # BMO Plan Fee - exact recurring monthly amount
    (TransactionMatchRule(
        description_pattern="Service Charge",
        amount_pattern=120.00,
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "BMO月度账户费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    # BMO Plan Fee Rebate - exact recurring monthly credit
    (TransactionMatchRule(
        description_pattern="Service Charge / Correction",
        amount_pattern=120.00,
        transaction_type='credit'
    ), {
        "品名": TransactionType.CHARGEBACK.value,
        "付款详情": "BMO账户费退款",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # ACURA Finance - exact recurring monthly payment
    (TransactionMatchRule(
        description_pattern="Preauthorized Debit / Correction",
        amount_pattern=396.37,
        transaction_type='debit'
    ), {
        "品名": TransactionType.LEASE_FEE.value,
        "付款详情": "ACURA汽车租赁费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    # ===== HIGH-FREQUENCY PATTERNS (From Real Data) =====

    # IOT PAY - Most frequent (194x) - Mobile payment income (WeChat/Alipay)
    (TransactionMatchRule(
        description_pattern=re.compile(r'IOT PAY.*MSP/DIV', re.IGNORECASE)
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "微信支付宝进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # UBER HOLDINGS - 44x occurrences - Delivery platform income
    (TransactionMatchRule(
        description_pattern=re.compile(
            r'UBER HOLDINGS.*MSP/DIV', re.IGNORECASE)
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Uber外卖佣金",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # FANTUAN - 55x occurrences - Chinese delivery platform
    (TransactionMatchRule(
        description_pattern=re.compile(r'FANTUAN.*MSP/DIV', re.IGNORECASE)
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "饭团外卖佣金",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # DP codes - Clover/POS deposits (120x total across different codes)
    (TransactionMatchRule(
        description_pattern=re.compile(r'DP\d+.*MSP/DIV', re.IGNORECASE)
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Clover刷卡进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # BR. patterns - Branch deposits/cash (200+ total occurrences)
    (TransactionMatchRule(
        description_pattern=re.compile(r'BR\.\s*\d+', re.IGNORECASE)
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "现金收入",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # PAYROLL patterns - Multiple store codes (40+ total)
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES.value,
        "付款详情": "员工工资发放",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    # ICBC Insurance - 6x occurrences
    (TransactionMatchRule(
        description_pattern=re.compile(r'ICBC.*INS/ASS', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.INSURANCE_FEE.value,
        "付款详情": "ICBC保险费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    # BMO Internal Transfer Pattern (from real data: 0004-1813-817 3587, 0888-1996-317 3587)
    (TransactionMatchRule(
        description_pattern=re.compile(
            r'\d{4}-\d{4}-\d{3}\s+\d{4}', re.IGNORECASE)
    ), {
        "品名": TransactionType.INTERNAL_TRANSFER.value,
        "付款详情": "BMO内部转款",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # ===== LEGACY PATTERNS (Essential ones only) =====

    # General service fees (for patterns not covered above)
    (TransactionMatchRule(
        description_pattern=re.compile(
            r'SERVICE.*CHARGE|BANK.*FEE', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "银行服务费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    # Credit card transactions
    (TransactionMatchRule(
        description_pattern=re.compile(
            r'CREDIT\s+CARD|VISA|MASTERCARD|AMEX', re.IGNORECASE)
    ), {
        "品名": TransactionType.CREDIT_CARD_PAYMENT.value,
        "付款详情": "信用卡相关交易",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    # ===== FALLBACK PATTERNS (Catch-all rules) =====

    # General transfer patterns
    (TransactionMatchRule(
        description_pattern=re.compile(
            r'TRANSFER|FUNDS.*TRANSFER', re.IGNORECASE)
    ), {
        "品名": TransactionType.INTERNAL_TRANSFER.value,
        "付款详情": "账户转账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # Generic deposit patterns (catch-all for remaining deposits)
    (TransactionMatchRule(
        description_pattern=re.compile(r'\bDEPOSIT\b', re.IGNORECASE),
        transaction_type='credit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "银行现金存款",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # Generic UBER patterns (fallback for any UBER not caught above)
    (TransactionMatchRule(
        description_pattern=re.compile(r'\bUBER\b', re.IGNORECASE)
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Uber外卖佣金",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # Interest patterns
    (TransactionMatchRule(
        description_pattern=re.compile(r'INTEREST', re.IGNORECASE)
    ), {
        "品名": TransactionType.INTEREST.value,
        "付款详情": "利息收入",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),
    (TransactionMatchRule(
        description_pattern="OPENTABLE       MSP/DIV",
        transaction_type='debit'
    ), {
        "品名": TransactionType.PLATFORM_FEE.value,
        "付款详情": "OpenTable平台费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
]
