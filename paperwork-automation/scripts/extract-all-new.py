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
from pathlib import Path
import argparse
import os

# Add lib to path BEFORE any local imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


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
        print("🔄 Setting up test database...")
        if setup_database_for_tests():
            print("✅ Test database setup completed")
        else:
            print("❌ Test database setup failed")
            sys.exit(1)
        return

    # Check if we should use direct database insertion
    direct_db_insert = args.direct_db or os.getenv(
        'DIRECT_DB_INSERT', 'false').lower() == 'true'
    is_test = args.test_db

    if direct_db_insert:
        print("🔗 Direct database insertion mode enabled")
        if is_test:
            print("🧪 Using test database")
        else:
            print("🏭 Using production database")

    print(f"📊 Processing Excel file: {args.input_file}")
    print("=" * 60)

    # Validate Excel file format unless skipped
    if not args.skip_validation:
        is_valid, validation_warnings = validate_excel_file(args.input_file)

        # Display all warnings
        if validation_warnings:
            print("\n📋 VALIDATION RESULTS:")
            for warning in validation_warnings:
                print(warning)
            print()

        # Stop if critical validation errors found
        if not is_valid:
            print(
                "❌ Critical validation errors found. Please fix the Excel file format before proceeding.")
            print("💡 Use --skip-validation flag to bypass validation if needed.")
            sys.exit(1)
        elif validation_warnings:
            print("⚠️  Validation warnings found, but proceeding with extraction...")
        else:
            print("✅ Excel file format validation passed!")

        print("=" * 60)
    else:
        print("⚠️  Skipping data format validation...")
        print("=" * 60)

    success_count = 0
    total_extractions = 0

    # Extract daily reports (unless time-only specified)
    if not args.time_only:
        total_extractions += 1
        print("\n1. 📈 Extracting daily reports...")
        if extract_daily_reports(
            input_file=args.input_file,
            output_file=args.daily_output,
            debug=args.debug,
            direct_db=direct_db_insert,
            is_test=is_test
        ):
            success_count += 1

        print("\n" + "=" * 60)

    # Extract time segment reports (unless daily-only specified)
    if not args.daily_only:
        total_extractions += 1
        step_num = 2 if not args.time_only else 1
        print(f"\n{step_num}. ⏰ Extracting time segment reports...")
        if extract_time_segments(
            input_file=args.input_file,
            output_file=args.time_output,
            debug=args.debug,
            direct_db=direct_db_insert,
            is_test=is_test
        ):
            success_count += 1

        print("\n" + "=" * 60)

    print(
        f"\n📊 Completed: {success_count}/{total_extractions} extractions successful")

    if success_count == total_extractions:
        print("🎉 All extractions completed successfully!")
        if direct_db_insert:
            print("💾 Data has been inserted directly to the database")
        else:
            print("📄 SQL files have been generated")
        sys.exit(0)
    else:
        print("❌ Some extractions failed. Check the error messages above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
