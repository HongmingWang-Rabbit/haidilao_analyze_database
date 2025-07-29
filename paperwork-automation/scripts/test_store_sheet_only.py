#!/usr/bin/env python3
"""
Test generating just the store gross profit sheet
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.database_queries import ReportDataProvider
from lib.store_gross_profit_worksheet import StoreGrossProfitWorksheetGenerator
from utils.database import DatabaseManager, DatabaseConfig
from openpyxl import Workbook

def test_store_sheet_only():
    """Test generating only the store gross profit sheet"""
    
    try:
        # Initialize components
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        data_provider = ReportDataProvider(db_manager)
        
        # Create worksheet generator
        worksheet_gen = StoreGrossProfitWorksheetGenerator(data_provider)
        
        # Create workbook
        wb = Workbook()
        
        print("Testing store gross profit worksheet generation...")
        
        # Generate the worksheet
        worksheet_gen.generate_worksheet(wb, "2025-05-01")
        
        print("Worksheet generation completed!")
        print(f"Worksheets in workbook: {[ws.title for ws in wb.worksheets]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_store_sheet_only()