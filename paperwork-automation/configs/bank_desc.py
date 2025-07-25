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
    # Expense reimbursement system (64 total)
    EXPENSE_REIMBURSEMENT = "费用报销系统"

    # Default
    UNCATEGORIZED = "未分类交易"                # Uncategorized transaction


class BankDescriptionConfig:
    """Configuration for bank transaction description mapping"""

    # Enhanced mapping structure based on actual data analysis
    # NOTE: True/False values indicate whether cell content needs manual review for color marking
    desc_map: dict[str, dict] = {

        # ===== SERVICE FEES =====
        "PAY-FILE FEES": {
            "品名": TransactionType.PROCESSING_FEE.value,
            "付款详情": "银行手续费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },
        "ACTIVITY FEE": {
            "品名": TransactionType.SERVICE_FEE.value,
            "付款详情": "银行服务费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },
        "SERVICE CHARGE": {
            "品名": TransactionType.SERVICE_FEE.value,
            "付款详情": "银行账户服务费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },
        "FULL-SERVICE": {
            "品名": TransactionType.SERVICE_FEE.value,
            "付款详情": "银行全服务费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },
        "SELF-SERVICE": {
            "品名": TransactionType.SERVICE_FEE.value,
            "付款详情": "银行自助服务费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },
        "DEPOSIT NOTE FEE": {
            "品名": TransactionType.PROCESSING_FEE.value,
            "付款详情": "存款单据费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },

        # ===== BILL PAYMENTS =====
        "BILL PAYMENT": {
            "品名": TransactionType.EXPENSE_REIMBURSEMENT.value,
            "付款详情": "账单付款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },
        "BILL PYMT": {
            "品名": TransactionType.EXPENSE_REIMBURSEMENT.value,
            "付款详情": "账单付款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },
        "B.C. HYDRO & POWER AUTHORITY": {
            "品名": TransactionType.ELECTRICITY_FEE.value,
            "付款详情": "BC省电费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "TORONTO HYDRO": {
            "品名": TransactionType.ELECTRICITY_FEE.value,
            "付款详情": "多伦多电费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },

        # ===== RENT PAYMENTS =====
        "Herefordshire": {
            "品名": TransactionType.RENT.value,
            "付款详情": "店铺房租",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },

        # ===== TRANSFERS =====
        "ACCOUNT TRANSFER": {
            "品名": TransactionType.INTERNAL_TRANSFER.value,
            "付款详情": "账户间转账",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "FUNDS TRANSFER": {
            "品名": TransactionType.EXPENSE_REIMBURSEMENT.value,
            "付款详情": "费用报销转账",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "CASH MANAGEMENT": {
            "品名": TransactionType.INTERNAL_TRANSFER.value,
            "付款详情": "现金管理转账",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },

        # ===== EXPENSE REIMBURSEMENT =====
        "MISCELLANEOUS DR": {
            "品名": TransactionType.EXPENSE_REIMBURSEMENT.value,
            "付款详情": "费用报销支出",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "EXPENSE PAYMENT": {
            "品名": TransactionType.EXPENSE_REIMBURSEMENT.value,
            "付款详情": "费用报销支付",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },

        # ===== LOANS =====
        "INCOMING WIRE PMT": {
            "品名": TransactionType.LOAN_RECEIVED.value,
            "付款详情": "电汇借款到账",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },

        # ===== INCOME TRANSACTIONS =====
        "UBER HOLDINGS": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "Uber外卖佣金",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "Uber Holdings Canad": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "Uber外卖佣金",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "FANTUAN": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "饭团外卖佣金",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "SNAPPY": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "Snappy第三方进账",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "CLOVER": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "Clover刷卡进账",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "MONERIS": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "Moneris刷卡收入",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "DP": {  # First Data Canada deposits
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "POS机刷卡收入",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "FIRST DATA CANADA": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "POS机刷卡收入",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "IOT PAY TECHNOLOGIES INC": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "移动支付收入",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "IOT PAY": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "移动支付收入",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "DEPOSIT": {  # Bank deposits
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "银行现金存款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "DIRECT DEPOSIT": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "直接存款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "BUS ETRANSFER DEPOSIT": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "电子转账收入",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "Branch Credit": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "分行存款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "INTERAC Email Money Transfer": {
            "品名": TransactionType.INCOME_RECEIVED.value,
            "付款详情": "电子邮件转账",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },

        # ===== CREDIT CARD PAYMENTS =====
        "RBC CREDIT CARD": {
            "品名": TransactionType.CREDIT_CARD_PAYMENT.value,
            "付款详情": "RBC信用卡还款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },
        "MISC PAYMENT": {
            "品名": TransactionType.CREDIT_CARD_PAYMENT.value,
            "付款详情": "杂项付款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },

        # ===== PAYROLL AND EMPLOYEE =====
        "BUSINESS PAD": {
            "品名": TransactionType.WAGES.value,
            "付款详情": "员工工资发放",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "DIRECT DEP": {
            "品名": TransactionType.WAGES.value,
            "付款详情": "直接存款发放",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "PAYROLL": {
            "品名": TransactionType.WAGES.value,
            "付款详情": "工资发放",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "SNAPPYDEBIT": {
            "品名": TransactionType.PLATFORM_FEE.value,
            "付款详情": "Snappy平台费",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },

        # ===== INTEREST =====
        "DEPOSIT INTEREST": {
            "品名": TransactionType.INTEREST.value,
            "付款详情": "存款利息",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "Interest": {
            "品名": TransactionType.INTEREST.value,
            "付款详情": "利息收入",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },

        # ===== WEB PAYMENTS =====
        "WEB PAYMENT": {
            "品名": TransactionType.EXPENSE_REIMBURSEMENT.value,
            "付款详情": "网上付款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": True,
            "是否登记支票使用表": False,
        },

        # ===== REVERSALS =====
        "REVERSAL": {
            "品名": TransactionType.CHARGEBACK.value,
            "付款详情": "交易冲正",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
        "REFUND": {
            "品名": TransactionType.CHARGEBACK.value,
            "付款详情": "交易退款",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        },
    }

    @classmethod
    def get_transaction_info(cls, details: str) -> dict:
        """
        Get transaction information based on details text.

        Args:
            details: Transaction details text

        Returns:
            dict: Transaction mapping information
        """
        if not details:
            return cls._get_default_mapping()

        # Convert to uppercase for case-insensitive matching
        details_upper = details.upper()

        # Check for exact matches first
        for key, mapping in cls.desc_map.items():
            if key.upper() in details_upper:
                return mapping

        # Check for partial matches with common patterns
        partial_patterns = {
            'UBER': cls.desc_map.get('UBER HOLDINGS', {}),
            'SNAPPY': cls.desc_map.get('SNAPPY', {}),
            'CLOVER': cls.desc_map.get('CLOVER', {}),
            'MONERIS': cls.desc_map.get('MONERIS', {}),
            'IOT': cls.desc_map.get('IOT PAY', {}),
            'HYDRO': cls.desc_map.get('B.C. HYDRO & POWER AUTHORITY', {}),
            'FIRST DATA': cls.desc_map.get('FIRST DATA CANADA', {}),
            'SERVICE': cls.desc_map.get('SERVICE CHARGE', {}),
            'DEPOSIT': cls.desc_map.get('DEPOSIT', {}),
            'TRANSFER': cls.desc_map.get('ACCOUNT TRANSFER', {}),
            'BILL': cls.desc_map.get('BILL PAYMENT', {}),
            'PAYROLL': cls.desc_map.get('PAYROLL', {}),
            'BUSINESS PAD': cls.desc_map.get('BUSINESS PAD', {}),
        }

        for pattern, mapping in partial_patterns.items():
            if pattern in details_upper and mapping:
                return mapping

        # If no match found, return default mapping
        return cls._get_default_mapping()

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


# Legacy support - maintain the original structure for backward compatibility
desc_map = BankDescriptionConfig.desc_map
