#!/usr/bin/env python3
"""
Extract all data from Excel files (daily store report and time segment report).
This script provides a simple interface for data extraction compatible with automation-menu.py
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.data_extraction import (
    extract_daily_reports,
    extract_time_segments
)


def main():
    parser = argparse.ArgumentParser(description='Extract data from Excel files')
    parser.add_argument('input_file', help='Path to input Excel file')
    parser.add_argument('--daily-only', action='store_true',
                        help='Extract only daily store report data')
    parser.add_argument('--time-only', action='store_true',
                        help='Extract only time segment report data')
    parser.add_argument('--direct-db', action='store_true',
                        help='Insert directly to database instead of generating SQL')
    parser.add_argument('--enhanced', action='store_true',
                        help='Enhanced extraction mode (both daily and time data)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"ERROR: Input file not found: {args.input_file}")
        sys.exit(1)
    
    success = True
    
    # Process based on mode
    if args.daily_only or args.enhanced or (not args.daily_only and not args.time_only):
        print("📊 Processing daily store report data...")
        result = extract_daily_reports(
            input_file=args.input_file,
            direct_db=args.direct_db
        )
        if not result:
            print("❌ Failed to process daily data")
            success = False
        else:
            print("✅ Daily data processed successfully")
    
    if args.time_only or args.enhanced or (not args.daily_only and not args.time_only):
        print("⏰ Processing time segment report data...")
        result = extract_time_segments(
            input_file=args.input_file,
            direct_db=args.direct_db
        )
        if not result:
            print("❌ Failed to process time segment data")
            success = False
        else:
            print("✅ Time segment data processed successfully")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()