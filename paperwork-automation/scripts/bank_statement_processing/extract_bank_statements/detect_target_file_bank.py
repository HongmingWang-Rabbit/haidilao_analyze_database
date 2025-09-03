import sys
import os
from typing import Dict, List
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from configs.bank_statement.banks import BankBrands

def detect_target_file_bank(
    target_file_path: str
) -> BankBrands:
    """
    Detect the bank brand based on the file name pattern.
    
    Args:
        target_file_path: Path to the bank statement file
        
    Returns:
        BankBrands enum value or None if not recognized
    """
    # Extract just the filename from the path
    filename = os.path.basename(target_file_path)
    
    # BMO files start with ReconciliationReport
    # Example: ReconciliationReport_09012025-051357.xls
    if filename.startswith("ReconciliationReport"):
        return BankBrands.BMO
    
    # RBC files start with RBC
    # Example: RBC Business Bank Account (0922)_May 01 2024_Aug 28 2025.xlsx
    elif filename.startswith("RBC"):
        return BankBrands.RBC
    
    # CIBC files start with TransactionSummary, TransactionDetail, or Transaction
    # Examples: TransactionSummary.csv, TransactionDetail.csv
    elif filename.startswith("TransactionSummary") or filename.startswith("TransactionDetail") or filename.startswith("Transaction"):
        return BankBrands.CIBC
    
    return None

def get_all_target_file_paths(
    target_date: datetime
) -> List[str]:
    """
    Get all bank statement file paths for a given month.
    
    Args:
        target_date: Date to determine which month folder to check
        
    Returns:
        List of file paths for bank statements
    """
    # Format the folder name as YYYY-MM
    folder_name = target_date.strftime("%Y-%m")
    
    # Build the path to the month folder
    base_path = Path(__file__).parent.parent.parent.parent
    month_folder = base_path / "history_files" / "bank_daily_report" / folder_name
    
    target_files = []
    
    # Check if the folder exists
    if not month_folder.exists():
        return target_files
    
    # Iterate through all files in the folder
    for file_path in month_folder.iterdir():
        if file_path.is_file():
            filename = file_path.name
            
            # Check if file matches any of the bank statement patterns
            if (filename.startswith("ReconciliationReport") or 
                filename.startswith("RBC") or 
                filename.startswith("TransactionSummary") or
                filename.startswith("Transaction")):
                
                # Exclude temporary files
                if not filename.startswith("~$"):
                    target_files.append(str(file_path))
    
    return sorted(target_files)

def main(
    target_date: datetime
) -> Dict[BankBrands, List[str]]:
    """
    Get all target file paths grouped by bank brand.
    
    Args:
        target_date: Date to determine which month folder to check
        
    Returns:
        Dictionary mapping bank brands to lists of file paths
    """
    # Get all target file paths
    all_file_paths = get_all_target_file_paths(target_date)
    
    # Initialize result dictionary
    bank_files = {
        BankBrands.BMO: [],
        BankBrands.RBC: [],
        BankBrands.CIBC: []
    }
    
    # Group files by bank brand
    for file_path in all_file_paths:
        bank_brand = detect_target_file_bank(file_path)
        
        if bank_brand and bank_brand in bank_files:
            bank_files[bank_brand].append(file_path)
    
    # Remove empty lists from result
    bank_files = {k: v for k, v in bank_files.items() if v}
    
    return bank_files

if __name__ == "__main__":
    # Test the functions
    from datetime import datetime
    
    # Test with August 2025
    test_date = datetime(2025, 8, 1)
    
    print("Testing detect_target_file_bank:")
    test_files = [
        "ReconciliationReport_09012025-051357.xls",
        "RBC Business Bank Account (0922)_May 01 2024_Aug 28 2025.xlsx",
        "TransactionSummary.csv",
        "random_file.xlsx"
    ]
    
    for test_file in test_files:
        bank = detect_target_file_bank(test_file)
        print(f"  {test_file} -> {bank}")
    
    print("\nTesting get_all_target_file_paths:")
    file_paths = get_all_target_file_paths(test_date)
    print(f"  Found {len(file_paths)} files for {test_date.strftime('%Y-%m')}:")
    for path in file_paths:
        print(f"    - {os.path.basename(path)}")
    
    print("\nTesting main:")
    bank_files = main(test_date)
    for bank, files in bank_files.items():
        print(f"  {bank.name}: {len(files)} files")
        for file in files:
            print(f"    - {os.path.basename(file)}")