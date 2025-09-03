from datetime import datetime
from typing import Optional

class BankRecord:
    def __init__(self):
        self.date: datetime = None
        self.credit: float = 0.0
        self.debit: float = 0.0
        self.short_desctiption: str = ""
        self.full_desctiption: str = ""
        self.customer_reference: Optional[str] = None
        self.bank_reference: Optional[str] = None
        self.serial_number: Optional[str] = None

