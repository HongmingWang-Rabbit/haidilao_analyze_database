from .banks import BankBrands

# Dictionary mapping sheet names to bank brands
BankWorkSheet = {
    # Each sheet will be assigned a bank, for script to recognize what type of sheet it is
    "CA1D-3817": BankBrands.BMO,
    "CA2D-6027": BankBrands.BMO,
    "CA3D-1680": BankBrands.BMO,
    "CA4D-1699": BankBrands.BMO,
    "CA5D-6333": BankBrands.BMO,
    "CA6D-6317": BankBrands.BMO,
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
    "CA7D-CIBC 0401": "CIBC0401",
    "RBC 5401": "RBC5401",
    "RBC 5419":  "RBC5419",
    "RBC0517-Hi Bowl":  "RBC0517",
    "RBC 0922（USD）":  "RBC0922",
    "RBC3088（USD）-Hi Bowl":  "RBC3088",
    "BMO美金-0798":  "BMO0798",
}