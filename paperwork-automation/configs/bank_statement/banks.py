from enum import Enum

class BankBrands(Enum):
    # Each bank will have different generated report, so we will need different ways to process them
    BMO = "BMO",
    CIBC = "CIBC",
    RBC = "RBC"