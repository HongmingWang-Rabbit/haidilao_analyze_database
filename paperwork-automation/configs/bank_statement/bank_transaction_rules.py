"""
Bank Transaction Classification Rules
Contains all the tuple-based rules for bank transaction matching.
"""

from pickle import TRUE
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
    RENT = "租金"                               # Rent (1 total)
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
    MATERIAL_EXPENSE = "物料费"                        # Rental fees (1 total)
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
                 # Exact, comparison, or range
                 amount_pattern: Optional[Union[float,
                                                Tuple[str, float], Tuple[float, float]]] = None,
                 transaction_type: Optional[str] = None,  # 'credit' or 'debit'
                 case_sensitive: bool = False):
        """
        Initialize a transaction matching rule.

        Args:
            description_pattern: String or compiled regex pattern for description matching
            amount_pattern: Can be:
                - float: Exact amount for monthly recurring transactions
                - ('>=', float) or ('<=', float): Comparison with a threshold
                - (float, float): Range (min, max) inclusive
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

        # Check amount pattern (exact, comparison, or range)
        amount_match = True
        if self.amount_pattern is not None and amount is not None:
            if isinstance(self.amount_pattern, (int, float)):
                # Exact amount match (with small tolerance for floating point)
                amount_match = abs(abs(amount) - self.amount_pattern) < 0.01
            elif isinstance(self.amount_pattern, tuple) and len(self.amount_pattern) == 2:
                if isinstance(self.amount_pattern[0], str):
                    # Comparison operators: ('>=', value) or ('<=', value)
                    op, value = self.amount_pattern
                    if op == '>=':
                        amount_match = abs(amount) >= value
                    elif op == '<=':
                        amount_match = abs(amount) <= value
                    else:
                        amount_match = False
                else:
                    # Range: (min, max)
                    min_val, max_val = self.amount_pattern
                    amount_match = min_val <= abs(amount) <= max_val
            else:
                amount_match = False

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
        description_pattern="PLAN FEE",
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

    (TransactionMatchRule(
        description_pattern="$$$",
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "银行服务费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="DEPOSIT NOTE FEE",
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "银行服务费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="EXCESS ITEMS",
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "银行服务费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="PAY-FILE FEES",
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "银行手续费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="SERVICE CHARGE",
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "银行服务费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="DEPOSIT COIN FEE",
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "银行服务费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern=re.compile(
            r"^DISCOUNT\s+\d+\s+AT\s+\$\d+(?:\.\d+)?$"
        ),
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "银行服务费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="ACTIVITY FEE",
        transaction_type='debit'
    ), {
        "品名": TransactionType.SERVICE_FEE.value,
        "付款详情": "银行服务费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="CASH MGMT   FEE BOM/B/M",
        transaction_type='debit'
    ), {
        "品名": TransactionType.MANAGEMENT_FEE.value,
        "付款详情": "银行管理费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="B.C. HYDRO-PAP",
        transaction_type='debit'
    ), {
        "品名": TransactionType.ELECTRICITY_FEE.value,
        "付款详情": "门店电费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="TORONTO HYDRO",
        transaction_type='debit'
    ), {
        "品名": TransactionType.ELECTRICITY_FEE.value,
        "付款详情": "门店电费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="SHAW CABLE TV",
        transaction_type='debit'
    ), {
        "品名": TransactionType.INTERNET_FEE.value,
        "付款详情": "门店网费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    # BMO Plan Fee Rebate - exact recurring monthly credit
    (TransactionMatchRule(
        description_pattern="FULL PLAN FEE REBATE",
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

    (TransactionMatchRule(
        description_pattern="FISERV CANADA   MSP/DIV"
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "FISERV刷卡进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    
    (TransactionMatchRule(
        description_pattern="FIRST DATA CANADA",
        transaction_type="debit"
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "Clover刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="FIRST DATA CANADA",
        transaction_type="credit"
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Clover刷卡进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="IOT PAY",
        transaction_type="credit"
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
        "付款详情": "Uber第三方进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="oceanorth",
        transaction_type="credit"
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "加拿大四店SWINGBY第三方收入",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # FANTUAN - 55x occurrences - Chinese delivery platform
    (TransactionMatchRule(
        description_pattern="FANTUAN",
        transaction_type="credit"
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "饭团第三方进账",
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

    (TransactionMatchRule(
        description_pattern=re.compile(
            r'MISC PAYMENT\s+[A-Z]+\d+\s+FIRST DATA CANADA\(J\)', re.IGNORECASE),
        transaction_type="credit"
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Clover刷卡进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # PAYROLL patterns - Multiple store codes (40+ total)
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL TBJ.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "一店工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL J4E.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "六店工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL RX3.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "七店工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL OZB.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "职能部门工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL 3XF.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "二店工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL DHC.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "三店工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),    
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL W9Z.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "四店工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    (TransactionMatchRule(
        description_pattern=re.compile(r'PAYROLL E1F.*BUS/ENT', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "五店工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    (TransactionMatchRule(
        description_pattern="PAYROLL-08N0086",
        transaction_type='debit'
    ), {
        "品名": TransactionType.WAGES_PLUS_INSURANCE.value,
        "付款详情": "大嗨麻辣烫一店工资",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

        (TransactionMatchRule(
        description_pattern=re.compile(r'SNAPPYON.*EXP/RDD', re.IGNORECASE),
        transaction_type='credit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Snappy第三方进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
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

    (TransactionMatchRule(
        description_pattern="HUNGRYPANDA",
        transaction_type='credit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "熊猫外卖第三方进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
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

    # ===== AMOUNT-BASED PATTERNS (Examples of range/comparison usage) =====

    # Generic UBER patterns (fallback for any UBER not caught above)
    (TransactionMatchRule(
        description_pattern=re.compile(r'\bUBER\b', re.IGNORECASE)
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Uber第三方进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="DEALUSE TECHNOL MSP/DIV"
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "DEALUSE（优品会团购）第三方进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="SNAPPYWC9005",
        transaction_type="credit"
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "微信支付宝进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    
    (TransactionMatchRule(
        description_pattern="SNAPPY9005",
        transaction_type="credit"
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Snappy刷卡进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),
    
    (TransactionMatchRule(
        description_pattern=re.compile(r"^MC\d+\s+\d+$"),
        transaction_type='credit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Moneris进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern=re.compile(r"^UP\d+\s+\d+$"),
        transaction_type='credit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Moneris进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern=re.compile(r"^EF\d+\s+\d+$"),
        transaction_type='credit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Moneris进账",
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
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="ALOCHEM         RLS/LOY",
        transaction_type='debit'
    ), {
        "品名": TransactionType.RENTAL_FEE.value,
        "付款详情": "洗碗机租赁费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),


    (TransactionMatchRule(
        description_pattern=re.compile(r"RENT/LEASE.*ALOUETTE WARE WASH CHEMICAL"),
        transaction_type='debit'
    ), {
        "品名": TransactionType.RENTAL_FEE.value,
        "付款详情": "洗碗机租赁费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern=re.compile(r"RENT/LEASE Rent \d+"),
        transaction_type='debit',
        amount_pattern=5000,
    ), {
        "品名": TransactionType.RENTAL_FEE.value,
        "付款详情": "七店员 工宿舍租赁费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    (TransactionMatchRule(
        description_pattern="FISERV CANADA   MSP/DIV",
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "FISERV手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
    # match VSA FEE10412682 MSP/DIV regex FEE10412682 can be any number
    (TransactionMatchRule(
        description_pattern=re.compile(r'VSA FEE\d+ MSP/DIV', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "Moneris刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    # match MON FEE10412682 MSP/DIV
    (TransactionMatchRule(
        description_pattern=re.compile(r'MON FEE\d+ MSP/DIV', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "Moneris刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    # match MRCH22048140016 MSP/DIV regex MRCH22048140016 can be any number
    (TransactionMatchRule(
        description_pattern=re.compile(r'MRCH\d+ MSP/DIV', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "Clover刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="REGIONAL RECYCL AP /CC",
        transaction_type='credit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "卖废品收入进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    # match MRCH22048140016 MSP/DIV regex MRCH22048140016 can be any number
    (TransactionMatchRule(
        description_pattern=re.compile(r'MRCH\d+ MSP/DIV', re.IGNORECASE),
        transaction_type='credit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Clover刷卡进账",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="CLOVER FEES",
        transaction_type='debit'
    ), {
        "品名": TransactionType.INCOME_RECEIVED.value,
        "付款详情": "Clover刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern=re.compile(r'''MISC PAYMENT
MRCH\d+
FIRST DATA CANADA\(J\)''', re.IGNORECASE | re.MULTILINE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "Clover刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern=re.compile(r'INT FEE\d+ MSP/DIV', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "Moneris刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern=re.compile(r'MC FEE \d+ MSP/DIV', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "Moneris刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),


    (TransactionMatchRule(
        description_pattern="SNAPPYDEBIT",
        transaction_type='debit'
    ), {
        "品名": TransactionType.PLATFORM_FEE.value,
        "付款详情": "Snappy平台费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern=re.compile(r'AMX FEE\d+ MSP/DIV', re.IGNORECASE),
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "Moneris刷卡手续费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="ICBC            INS/ASS",
        amount_pattern=146.76,
        transaction_type='debit'
    ), {
        "品名": TransactionType.INSURANCE_FEE.value,
        "付款详情": "七店采购用车保险费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),


    (TransactionMatchRule(
        description_pattern="ICBC            INS/ASS",
        amount_pattern=182.44,
        transaction_type='debit'
    ), {
        "品名": TransactionType.INSURANCE_FEE.value,
        "付款详情": "二店采购用车保险费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="Bill Payment - PAY-FILE FEES",
        transaction_type='debit'
    ), {
        "品名": TransactionType.PROCESSING_FEE.value,
        "付款详情": "银行手续费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="ALECTRA UTIL    MSP/DIV",
        transaction_type='debit'
    ), {
        "品名": TransactionType.ELECTRICITY_FEE.value,
        "付款详情": "三店员工宿舍电费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),


    (TransactionMatchRule(
        description_pattern="Herefordshire C",
        amount_pattern=17843.27,
        transaction_type='debit'
    ), {
        "品名": TransactionType.RENT.value,
        "付款详情": "大嗨麻辣烫一店房租",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="ENBRIDGE GAS    BPY/FAC",
        transaction_type='debit',
        amount_pattern=('<=', 300)
    ), {
        "品名": TransactionType.ELECTRICITY_FEE.value,
        "付款详情": "员工宿舍燃气费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="ENBRIDGE GAS    BPY/FAC",
        transaction_type='debit',
        amount_pattern=('>=', 500)
    ), {
        "品名": TransactionType.ELECTRICITY_FEE.value,
        "付款详情": "门店燃气费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),


    (TransactionMatchRule(
        description_pattern="COOPERATORS CSI INS/ASS",
        transaction_type='debit',
        amount_pattern=477.52
    ), {
        "品名": TransactionType.INSURANCE_FEE.value,
        "付款详情": "四店门店货车保险费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),


    (TransactionMatchRule(
        description_pattern="COOPERATORS CSI INS/ASS",
        transaction_type='debit',
        amount_pattern=477.52
    ), {
        "品名": TransactionType.INSURANCE_FEE.value,
        "付款详情": "四店门店货车保险费",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="COOPERATORS CSI INS/ASS",
        transaction_type='debit',
        amount_pattern=96.76
    ), {
        "品名": TransactionType.INSURANCE_FEE.value,
        "付款详情": "四店员工宿舍保险",
        "单据号": False,
        "附件": True,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="VW CREDIT CAN   LNS/PRE",
        transaction_type='debit',
        amount_pattern=197.99
    ), {
        "品名": TransactionType.RENTAL_FEE.value,
        "付款详情": "蒋冰遇汽车租赁费",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

        (TransactionMatchRule(
        description_pattern="VW CREDIT CAN   LNS/PRE",
        transaction_type='debit',
        amount_pattern=192.95
    ), {
        "品名": TransactionType.INSURANCE_FEE.value,
        "付款详情": "蒋冰遇租车保险",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="PROVINCE OF BC  PRO/PRO",
        transaction_type='debit',
    ), {
        "品名": TransactionType.RENTAL_FEE.value,
        "付款详情": "上月PST",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="BMO PAYMENT     CBP/PFE",
        transaction_type='debit',
    ), {
        "品名": TransactionType.CREDIT_CARD_PAYMENT.value,
        "付款详情": "BMO信用卡还款",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="WEST COAST REDU AP /CC",
        transaction_type='credit',
    ), {
        "品名": TransactionType.NON_OPERATING_INCOME.value,
        "付款详情": "卖垃圾款",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),

    (TransactionMatchRule(
        description_pattern="Herefordshire C",
        transaction_type='debit',
        amount_pattern="17843.27"
    ), {
        "品名": TransactionType.RENT.value,
        "付款详情": "大嗨麻辣烫一店房租",
        "单据号": True,
        "附件": False,
        "是否登记线下付款表": False,
        "是否登记支票使用表": False,
    }),
    
    (TransactionMatchRule(
        description_pattern="Chq Printing Fee",
        transaction_type='debit'
    ), {
        "品名": TransactionType.MATERIAL_EXPENSE.value,
        "付款详情": "支票打印费",
        "单据号": False,
        "附件": False,
        "是否登记线下付款表": True,
        "是否登记支票使用表": False,
    }),
]