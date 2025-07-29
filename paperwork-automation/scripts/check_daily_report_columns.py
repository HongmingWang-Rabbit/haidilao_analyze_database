#!/usr/bin/env python3
"""
Check daily_report table columns to find cost-related fields
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def check_daily_report_columns():
    """Check columns in daily_report table"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Get table schema
        schema_sql = """
        SELECT 
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'daily_report'
        ORDER BY ordinal_position
        """
        
        columns = db_manager.fetch_all(schema_sql)
        print("Daily Report Table Columns:")
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Check sample data for cost-related columns
        print("\nSample Daily Report Data (April 2025 - Store 1):")
        sample_sql = """
        SELECT * 
        FROM daily_report 
        WHERE store_id = 1 
            AND EXTRACT(YEAR FROM date) = 2025 
            AND EXTRACT(MONTH FROM date) = 4
        ORDER BY date
        LIMIT 3
        """
        
        sample_data = db_manager.fetch_all(sample_sql)
        if sample_data:
            for i, row in enumerate(sample_data):
                print(f"\nRecord {i+1} (Date: {row.get('date', 'N/A')}):")
                for key, value in row.items():
                    if 'cost' in key.lower() or 'expense' in key.lower():
                        print(f"  {key}: {value}")
        else:
            print("No sample data found")
    
    except Exception as e:
        print(f"Error checking daily_report columns: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_daily_report_columns()