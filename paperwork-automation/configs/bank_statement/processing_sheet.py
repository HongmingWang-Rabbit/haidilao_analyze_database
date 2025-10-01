from .banks import BankBrands
from typing import TypedDict, Dict

current_cad_to_usd_rate = 0.7226

# Dictionary mapping sheet names to bank brands
BankWorkSheet = {
    # Each sheet will be assigned a bank, for script to recognize what type of sheet it is
    "CA1D-3817": BankBrands.BMO,
    "CA2D-6027": BankBrands.BMO,
    "CA3D-1680": BankBrands.BMO,
    "CA4D-1699": BankBrands.BMO,
    "CA5D-6333": BankBrands.BMO,
    "CA6D-6317": BankBrands.BMO,
    "CA8D-9592": BankBrands.BMO,
    "CA7D-CIBC 0401": BankBrands.CIBC,
    "RBC 5401": BankBrands.RBC,
    "RBC 5419": BankBrands.RBC,
    "RBC0517-Hi Bowl": BankBrands.RBC,
    "RBC 0922（USD）": BankBrands.RBC,
    "RBC3088（USD）-Hi Bowl": BankBrands.RBC,
    "BMO美金-0798": BankBrands.BMO,
}

BanWorkSheetToFormattedName={
    "CA1D-3817": "BMO3817",
    "CA2D-6027":  "BMO6027",
    "CA3D-1680":  "BMO1680",
    "CA4D-1699":  "BMO1699",
    "CA5D-6333":  "BMO6333",
    "CA6D-6317":  "BMO6317",
    "CA8D-9592":  "BMO9592",
    "CA7D-CIBC 0401": "CIBC0401",
    "RBC 5401": "RBC5401",
    "RBC 5419":  "RBC5419",
    "RBC0517-Hi Bowl":  "RBC0517",
    "RBC 0922（USD）":  "RBC0922",
    "RBC3088（USD）-Hi Bowl":  "RBC3088",
    "BMO美金-0798":  "BMO0798",
}

class PaymentInfo(TypedDict):
    company_code: int
    department_name: str

BankWorkSheetOfflinePaymentInfo:Dict[str, PaymentInfo] = {
    "CA1D-3817": {
        "company_code":9451,
        "department_name":"加拿大一店"
    },
    "CA2D-6027":  {
        "company_code":9451,
        "department_name":"加拿大二店"
    },
    "CA3D-1680":  {
        "company_code":9451,
        "department_name":"加拿大三店"
    },
    "CA4D-1699":  {
        "company_code":9451,
        "department_name":"加拿大四店"
    },
    "CA5D-6333":  {
        "company_code":9451,
        "department_name":"加拿大五店"
    },
    "CA6D-6317":  {
        "company_code":9451,
        "department_name":"加拿大六店"
    },
    "CA8D-9592":  {
        "company_code":9451,
        "department_name":"加拿大八店"
    },
    "CA7D-CIBC 0401": {
        "company_code":9451,
        "department_name":"加拿大七店"
    },
    "RBC 5401": {
        "company_code":9451,
        "department_name":"RBC"
    },
    "RBC 5419":  {
        "company_code":9451,
        "department_name":"RBC"
    },
    "RBC0517-Hi Bowl":  {
        "company_code":9452,
        "department_name":"加拿大Hi-Bowl一店"
    },
    "RBC 0922（USD）":  {
        "company_code":9451,
        "department_name":"RBC"
    },
    "RBC3088（USD）-Hi Bowl":  {
        "company_code":9452,
        "department_name":"RBC"
    },
    "BMO美金-0798":  {
        "company_code":9451,
        "department_name":"BMO"
    },
}