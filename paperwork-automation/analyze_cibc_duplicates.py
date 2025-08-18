#!/usr/bin/env python3
"""
Analyze CIBC transaction file for duplicates
"""

import pandas as pd
from pathlib import Path

def analyze_cibc():
    """Analyze CIBC TransactionDetail.xlsx for duplicates"""
    
    file_path = Path("Input/daily_report/bank_transactions_reports/TransactionDetail.xlsx")
    
    if not file_path.exists():
        print(f"CIBC file not found: {file_path}")
        return
        
    print(f"Analyzing CIBC file: {file_path.name}")
    
    # Read the file with header=None to see the structure
    df = pd.read_excel(file_path, engine='openpyxl', header=None)
    print(f"\nFile shape: {df.shape}")
    print(f"\nFirst 20 rows:")
    print(df.head(20))
    
    # Try to identify the data structure
    print("\n\nAnalyzing structure...")
    
    # Look for debit/credit sections
    debit_rows = []
    credit_rows = []
    current_section = None
    
    for idx, row in df.iterrows():
        first_col = str(row[0]) if pd.notna(row[0]) else ""
        
        if 'Debit transactions' in first_col:
            current_section = 'debit'
            print(f"Found debit section at row {idx}")
            continue
        elif 'Credit transactions' in first_col:
            current_section = 'credit'
            print(f"Found credit section at row {idx}")
            continue
        elif 'Total debits' in first_col or 'Total credits' in first_col:
            current_section = None
            continue
            
        # Check if this looks like a transaction row
        if current_section and pd.notna(row[6]) and pd.notna(row[7]):
            try:
                date_val = pd.to_datetime(row[6])
                amount = float(row[7])
                
                if current_section == 'debit':
                    debit_rows.append({
                        'row': idx,
                        'desc': str(row[0]),
                        'date': date_val,
                        'amount': amount
                    })
                else:
                    credit_rows.append({
                        'row': idx,
                        'desc': str(row[0]),
                        'date': date_val,
                        'amount': amount
                    })
            except:
                pass
    
    print(f"\nFound {len(debit_rows)} debit transactions")
    print(f"Found {len(credit_rows)} credit transactions")
    
    # Check for duplicates in each section
    for section_name, transactions in [('Debit', debit_rows), ('Credit', credit_rows)]:
        if transactions:
            print(f"\n{section_name} transactions:")
            df_trans = pd.DataFrame(transactions)
            
            # Find duplicates
            dup_mask = df_trans.duplicated(subset=['desc', 'date', 'amount'], keep=False)
            duplicates = df_trans[dup_mask]
            
            if not duplicates.empty:
                print(f"  Found {len(duplicates)} duplicate rows!")
                print("\n  Duplicate groups:")
                for (desc, date, amount), group in duplicates.groupby(['desc', 'date', 'amount']):
                    print(f"\n    {desc[:50]}... | {date.strftime('%Y-%m-%d')} | ${amount}")
                    print(f"    Rows: {list(group['row'])}")
            else:
                print(f"  No duplicates found")

if __name__ == "__main__":
    analyze_cibc()