#!/usr/bin/env python3
"""
Debug transaction processing
"""

import pandas as pd
from pathlib import Path
import sys
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scripts.process_bank_transactions import BankTransactionProcessor

def debug_transactions():
    """Debug why no transactions are being found"""
    
    # Check RBC 5401 file
    file_path = Path("Input/daily_report/bank_transactions_reports/RBC Business Bank Account (5401)_Apr 01 2024_Aug 07 2025.xlsx")
    
    print(f"Checking file: {file_path.name}")
    
    df = pd.read_excel(file_path, engine='openpyxl')
    print(f"\nTotal transactions in file: {len(df)}")
    
    # Check July 2025 transactions
    df['Date'] = pd.to_datetime(df['Date'])
    july_2025 = df[(df['Date'].dt.year == 2025) & (df['Date'].dt.month == 7)]
    
    print(f"July 2025 transactions: {len(july_2025)}")
    
    if not july_2025.empty:
        print("\nFirst 5 July 2025 transactions:")
        for idx, row in july_2025.head(5).iterrows():
            print(f"  {row['Date'].strftime('%Y-%m-%d')} | {row['Description 1']} | W:{row.get('Withdrawals', '')} | D:{row.get('Deposits', '')}")
    
    # Check last date in template
    processor = BankTransactionProcessor(2025, 7)
    last_dates = processor.get_last_existing_dates_from_template()
    
    print(f"\nLast date in RBC 5401 template: {last_dates.get('RBC 5401', 'Not found')}")
    
    # Check if July transactions are after last date
    if 'RBC 5401' in last_dates and not july_2025.empty:
        last_date = pd.to_datetime(last_dates['RBC 5401'])
        after_last_date = july_2025[july_2025['Date'] >= last_date]
        print(f"July transactions on or after last date ({last_dates['RBC 5401']}): {len(after_last_date)}")

if __name__ == "__main__":
    debug_transactions()