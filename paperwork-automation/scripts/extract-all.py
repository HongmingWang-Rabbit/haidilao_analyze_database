#!/usr/bin/env python3
"""
Convenience script to extract both daily reports and time segment data from Excel files.
Enhanced with data format validation and warning system.
Enhanced with direct database insertion capabilities.
This is the single entry point for all data extraction operations.
"""

from utils.database import setup_database_for_tests
from lib.data_extraction import (
    validate_excel_file,
    extract_daily_reports,
    extract_time_segments
)
import sys
import os
from pathlib import Path
import argparse

# Add lib to path BEFORE any local imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix encoding issues on Windows for Chinese characters
if sys.platform.startswith('win'):
    import codecs
    # Only redirect if not already redirected
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def main():
    parser = argparse.ArgumentParser(
        description='Extract both daily reports and time segment data from Excel files or insert directly to database')
    parser.add_argument('input_file', help='Path to the Excel file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Generate CSV files for manual verification')
    parser.add_argument(
        '--daily-output', help='Path to the daily reports output SQL file')
    parser.add_argument(
        '--time-output', help='Path to the time segments output SQL file')
    parser.add_argument('--skip-validation', action='store_true',
                        help='Skip data format validation')
    parser.add_argument('--direct-db', action='store_true',
                        help='Insert directly to database instead of generating SQL files')
    parser.add_argument('--test-db', action='store_true',
                        help='Use test database')
    parser.add_argument('--setup-test-db', action='store_true',
                        help='Setup test database with schema and initial data')
    parser.add_argument('--daily-only', action='store_true',
                        help='Extract only daily reports (skip time segments)')
    parser.add_argument('--time-only', action='store_true',
                        help='Extract only time segments (skip daily reports)')

    args = parser.parse_args()

    # Setup test database if requested
    if args.setup_test_db:
        print("Setting up test database...")
        if setup_database_for_tests():
            print("Test database setup completed")
        else:
            print("ERROR: Test database setup failed")
            sys.exit(1)
        return

    # Check if we should use direct database insertion
    direct_db_insert = args.direct_db or os.getenv(
        'DIRECT_DB_INSERT', 'false').lower() == 'true'
    is_test = args.test_db

    # Validate Excel file format unless skipped
    if not args.skip_validation:
        is_valid, validation_warnings = validate_excel_file(args.input_file)

        # Stop if critical validation errors found
        if not is_valid:
            print(
                "ERROR: Critical validation errors found. Please fix the Excel file format.")
            sys.exit(1)
        elif validation_warnings:
            # Only show warnings if there are actual issues
            has_errors = any(
                "ERROR" in warning for warning in validation_warnings)
            if has_errors:
                print("WARNING: Issues found in Excel file:")
                for warning in validation_warnings:
                    if "ERROR" in warning:
                        print(f"  {warning}")

    success_count = 0
    total_extractions = 0

    # Extract daily reports (unless time-only specified)
    if not args.time_only:
        total_extractions += 1
        print("Extracting daily report...")
        if extract_daily_reports(
            input_file=args.input_file,
            output_file=args.daily_output,
            debug=args.debug,
            direct_db=direct_db_insert,
            is_test=is_test
        ):
            success_count += 1
            if direct_db_insert:
                print("Daily report inserted to database")

    # Extract time segment reports (unless daily-only specified)
    if not args.daily_only:
        total_extractions += 1
        print("Extracting time segment report...")
        if extract_time_segments(
            input_file=args.input_file,
            output_file=args.time_output,
            debug=args.debug,
            direct_db=direct_db_insert,
            is_test=is_test
        ):
            success_count += 1
            if direct_db_insert:
                print("Time segment report inserted to database")

    if success_count == total_extractions:
        print("Finished")
        sys.exit(0)
    else:
        print("ERROR: Some extractions failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
