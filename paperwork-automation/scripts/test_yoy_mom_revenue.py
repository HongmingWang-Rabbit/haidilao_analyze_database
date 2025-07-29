#!/usr/bin/env python3
"""
Test the YoY/MoM analysis revenue data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.generate_monthly_gross_margin_report import MonthlyGrossMarginReportGenerator
from lib.database_queries import ReportDataProvider
from utils.database import DatabaseManager, DatabaseConfig

def test_yoy_mom_revenue():
    """Test YoY/MoM analysis revenue amounts"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    data_provider = ReportDataProvider(db_manager)
    
    try:
        # Create the report generator
        generator = MonthlyGrossMarginReportGenerator("2025-05-01")
        
        print("Testing YoY/MoM analysis data...")
        print(f"Target date: 2025-05-01")
        print(f"Month start: {generator.month_start}")
        print(f"Month end: {generator.month_end}")
        print()
        
        # Get the comparative analysis data
        comparative_data = generator._get_comparative_analysis_data(data_provider)
        
        print("YoY/MoM Revenue Data Verification:")
        print("=" * 80)
        
        for store in comparative_data:
            try:
                store_name = store['store_name'][:20] if len(store['store_name']) > 20 else store['store_name']
            except (UnicodeEncodeError, TypeError):
                store_name = f"Store"
            
            current_rev = store['current_revenue']
            prev_rev = store['prev_revenue']
            last_year_rev = store['last_year_revenue']
            
            print(f"{store_name}:")
            print(f"  Current Month Revenue: ${current_rev:>10,.0f}  (May 2025)")
            print(f"  Previous Month Revenue:${prev_rev:>10,.0f}  (April 2025)")
            print(f"  Last Year Revenue:     ${last_year_rev:>10,.0f}  (May 2024)")
            
            # Check if current month revenue looks reasonable for monthly data
            if current_rev > 500000:  # > $500K looks like monthly
                status = "✅ Monthly amount"
            elif current_rev < 50000:  # < $50K likely daily
                status = "⚠️ Too small (daily?)"
            else:
                status = "❓ Uncertain"
            
            print(f"  Status: {status}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yoy_mom_revenue()