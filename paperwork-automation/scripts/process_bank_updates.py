#!/usr/bin/env python3
"""
Bank Statement Update Processing Script
Uses the new bank statement extraction and update system to process bank files
"""

import sys
import os
from datetime import datetime
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.bank_statement_processing.update_target_bank_sheet.update_bank_workbook import update_bank_workbook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to process bank statement updates."""
    parser = argparse.ArgumentParser(
        description='Process bank statements and update workbook with new transactions'
    )
    parser.add_argument(
        '--target-date', 
        type=str, 
        required=True,
        help='Target date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--output-folder',
        type=str,
        help='Optional output folder path. If not provided, uses default.'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Parse target date
        target_date = datetime.strptime(args.target_date, '%Y-%m-%d')
        
        print("\n" + "="*60)
        print("BANK STATEMENT UPDATE PROCESSING")
        print("="*60)
        print(f"Processing for: {target_date.strftime('%B %Y')}")
        print(f"Target month: {target_date.strftime('%Y-%m')}")
        
        # Process bank statements
        print("\nProcessing steps:")
        print("  1. Locating CA All 7 Stores Detail.xlsx workbook")
        print("  2. Extracting bank statements from source files")
        print("  3. Comparing with existing records")
        print("  4. Appending new transactions")
        print("  5. Applying transaction classifications")
        print()
        
        # Call the update function
        update_bank_workbook(target_date, args.output_folder)
        
        print("\n" + "="*60)
        print("BANK PROCESSING COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        # Show output location
        if args.output_folder:
            output_path = Path(args.output_folder)
        else:
            base_path = Path(__file__).parent.parent
            output_path = base_path / "output" / "bank_statements" / target_date.strftime("%Y-%m")
        
        print(f"\nOutput location:")
        print(f"   {output_path}")
        print(f"\nUpdated file:")
        print(f"   Updated_CA All 7 Stores Detail.xlsx")
        
        print("\nWhat's new in the updated file:")
        print("  - New transactions appended to each bank sheet")
        print("  - Dates formatted per bank standards")
        print("  - Transaction categories auto-classified")
        print("  - Payment details filled in")
        print("  - Items needing review marked as pending")
        print()
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\nERROR: Required file not found")
        print(f"   {str(e)}")
        print("\nSolution:")
        print("  - Ensure CA All 7 Stores Detail.xlsx exists in:")
        print(f"    history_files/bank_daily_report/{target_date.strftime('%Y-%m')}/")
        print("  - Check that bank statement files are present")
        return 1
        
    except PermissionError as e:
        print(f"\nERROR: Permission denied")
        print(f"   {str(e)}")
        print("\nSolution:")
        print("  - Close the Excel file if it's open")
        print("  - Check file permissions")
        return 1
        
    except Exception as e:
        logger.error(f"Error processing bank updates: {e}", exc_info=True)
        print(f"\nERROR: Bank processing failed")
        print(f"   {str(e)}")
        print("\nFor more details, run with --debug flag")
        return 1

if __name__ == "__main__":
    sys.exit(main())