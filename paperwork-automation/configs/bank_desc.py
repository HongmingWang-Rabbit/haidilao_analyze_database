from enum import Enum


class TransactionType(Enum):
    INCOME = "收入进账"
    SERVICE_FEE = "服务费"


desc_map: dict[str, dict[str, TransactionType]] = {
    "UBER HOLDINGS C MSP/DIV": {
        "desc": "Uber第三方进账",
        "type": TransactionType.INCOME,
        "need_attachment": False,
        "need_document_number": False,
        "mark_off_line": False,
        "mark_check": False,
    },
    "FANTUAN         MSP/DIV": {
        "desc": "饭团第三方进账",
        "type": TransactionType.INCOME,
        "need_attachment": False,
        "need_document_number": False,
        "mark_off_line": False,
        "mark_check": False,
    },
    "$$$": {
        "desc": "银行服务费",
        "type": TransactionType.SERVICE_FEE,
        "need_attachment": False,
        "need_document_number": False,
        "mark_off_line": True,
        "mark_check": False,
    },
}
