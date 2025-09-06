import sys
import os
from typing import List, Dict
import logging
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from type.bank_processing import BankRecord
from configs.bank_statement.bank_transaction_rules import BANK_TRANSACTION_RULES

logger = logging.getLogger(__name__)

def match_transaction_rules(record: BankRecord) -> Dict:
    """
    Match a bank record against transaction rules to get classification data.
    
    Args:
        record: BankRecord to match
        
    Returns:
        Dictionary with classification data or default values
    """
    # Determine transaction type (credit or debit)
    transaction_type = 'credit' if record.credit > 0 else 'debit' if record.debit > 0 else None
    
    # Use full description for matching, fallback to short description
    description = record.full_desctiption or record.short_desctiption or ""
    
    # Use the absolute amount for matching
    amount = abs(record.credit) if record.credit > 0 else abs(record.debit)
    
    # Try to match against each rule
    for rule, classification in BANK_TRANSACTION_RULES:
        if rule.matches(description, amount, transaction_type):
            # Process the classification result
            result = {}
            
            # Always copy 品名 and 付款详情
            result["品名"] = classification.get("品名", "待确认")
            result["付款详情"] = classification.get("付款详情", "")
            
            # For the confirmation fields, set "待确认" if True, empty string otherwise
            if classification.get("单据号", False) == True:
                result["单据号"] = "待确认"
            else:
                result["单据号"] = ""
                
            if classification.get("附件", False) == True:
                result["附件"] = "待确认"
            else:
                result["附件"] = ""
                
            if classification.get("是否登记线下付款表", False) == True:
                result["是否登记线下付款表"] = "待确认"
            else:
                result["是否登记线下付款表"] = ""
                
            if classification.get("是否登记支票使用表", False) == True:
                result["是否登记支票使用表"] = "待确认"
            else:
                result["是否登记支票使用表"] = ""
                    
            return result
    
    # Default if no rule matches - only 品名 is marked as pending
    return {
        "品名": "待确认",
        "付款详情": "",
        "单据号": "",
        "附件": "",
        "是否登记线下付款表": "",
        "是否登记支票使用表": ""
    }

def append_cibc_records_to_worksheet(wb, sheet_name: str, new_records: List[BankRecord]):
    """
    Append new CIBC records to a worksheet.
    
    CIBC format columns:
    - A: Date
    - B: Transaction details
    - C: Debit (positive values)
    - D: Credit (positive values)
    - E: Balance
    - F: 品名 (Category)
    - G: 付款详情 (Payment Details)
    - H: 单据号 (Document Number)
    
    Args:
        wb: Openpyxl workbook object
        sheet_name: Name of the worksheet
        new_records: List of BankRecord objects to append
    """
    if sheet_name not in wb.sheetnames:
        logger.warning(f"Sheet {sheet_name} not found in workbook")
        return
    
    ws = wb[sheet_name]
    
    # Find the last row with data
    last_row = ws.max_row
    
    # Look for the actual last data row (skip empty rows at the end)
    while last_row > 1:
        # Check columns A-D for CIBC format (main data columns)
        if any(ws.cell(row=last_row, column=col).value for col in range(1, 5)):
            break
        last_row -= 1
    
    # Start appending after the last row
    current_row = last_row + 1
    
    logger.info(f"Appending {len(new_records)} CIBC records to sheet {sheet_name} starting at row {current_row}")
    
    # Sort records by date in ascending order before appending
    sorted_records = sorted(new_records, key=lambda x: x.date if x.date else datetime.min)
    
    # Append each record
    for record in sorted_records:
        # Column A: Date - write as datetime object so Excel can format it properly
        if record.date:
            # Write the datetime object directly, Excel will handle formatting
            ws.cell(row=current_row, column=1, value=record.date)
        else:
            ws.cell(row=current_row, column=1, value=None)
        
        # Column B: Transaction details (full description)
        # Replace newlines with spaces for cleaner display
        description = record.full_desctiption
        if description:
            description = description.replace('\n', ' ')
        ws.cell(row=current_row, column=2, value=description)
        
        # Column C: Debit (positive values)
        if record.debit != 0:
            ws.cell(row=current_row, column=3, value=abs(record.debit))
        
        # Column D: Credit (positive values)
        if record.credit != 0:
            ws.cell(row=current_row, column=4, value=abs(record.credit))
        
        # Column E: Balance - we don't calculate this, leave empty
        
        # Get classification from transaction rules
        classification = match_transaction_rules(record)
        
        # Column F: 品名 (Category)
        ws.cell(row=current_row, column=6, value=classification.get("品名", ""))
        
        # Column G: 付款详情 (Payment Details)
        ws.cell(row=current_row, column=7, value=classification.get("付款详情", ""))
        
        # Column H: 单据号 (Document Number)
        ws.cell(row=current_row, column=8, value=classification.get("单据号", ""))
        
        # Column I: 附件 (Attachment)
        ws.cell(row=current_row, column=9, value=classification.get("附件", ""))
        
        # Column J: 是否登记线下付款表 (Offline Payment Registration)
        ws.cell(row=current_row, column=10, value=classification.get("是否登记线下付款表", ""))
        
        # Column K: 是否登记支票使用表 (Check Usage Registration)
        ws.cell(row=current_row, column=11, value=classification.get("是否登记支票使用表", ""))
        
        current_row += 1
    
    logger.debug(f"Completed appending {len(new_records)} CIBC records to {sheet_name}")