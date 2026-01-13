#!/usr/bin/env python3
"""
Takeout Revenue Data Extraction Module

DEPRECATED: This module is deprecated as of January 2026.
Takeout revenue is now extracted directly from daily store reports during
the daily data extraction process.

See: lib/data_extraction.py - transform_daily_report_data() and save_takeout_revenue()
Column: '营业收入(外卖)(不含税)' in daily_store_report files

The Input/daily_report/takeout_report/ folder is no longer needed.

---
Legacy Documentation (for reference):
Extracts daily takeout revenue data from Excel files in Input/daily_report/takeout_report/
and inserts into daily_takeout_revenue database table.

Data Source Format:
- Columns: Document Date, Text (contains store name), Amount in Local Currency
- Text format: "MM-DD日加拿大X店外卖收入" where X is store number (Chinese)
- Amount is negative (revenue/credit), needs to be converted to positive
"""

import warnings
warnings.warn(
    "takeout_extraction module is deprecated. "
    "Takeout revenue is now extracted from daily store reports via data_extraction.py",
    DeprecationWarning,
    stacklevel=2
)

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from utils.database import get_database_manager
from lib.config import STORE_NAME_MAPPING

# Configure logging
logger = logging.getLogger(__name__)


def extract_store_id_from_text(text: str) -> Optional[int]:
    """
    Extract store ID from the Text column.

    Args:
        text: Text value like "01-03日加拿大五店外卖收入"

    Returns:
        Store ID (1-8) or None if not matched
    """
    if not text or pd.isna(text):
        return None

    text_str = str(text)
    # Use centralized store name mapping from lib/config.py
    for store_name, store_id in STORE_NAME_MAPPING.items():
        if store_name in text_str:
            return store_id

    return None


def transform_takeout_data(df: pd.DataFrame) -> List[Dict]:
    """
    Transform Excel data into database-ready format.

    Args:
        df: DataFrame from takeout Excel file

    Returns:
        List of dictionaries with store_id, date, amount
    """
    transformed_data = []

    for _, row in df.iterrows():
        # Extract store ID from Text column
        text = row.get('Text', '')
        store_id = extract_store_id_from_text(text)

        if store_id is None:
            continue

        # Get and format date
        doc_date = row.get('Document Date')
        if pd.isna(doc_date):
            continue

        # Handle date conversion
        if isinstance(doc_date, str):
            try:
                formatted_date = datetime.strptime(doc_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                try:
                    formatted_date = datetime.strptime(doc_date, '%Y/%m/%d').strftime('%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Could not parse date: {doc_date}")
                    continue
        else:
            try:
                formatted_date = pd.Timestamp(doc_date).strftime('%Y-%m-%d')
            except Exception:
                logger.warning(f"Could not convert date: {doc_date}")
                continue

        # Get amount (convert negative to positive)
        amount = row.get('Amount in Local Currency', 0)
        if pd.isna(amount):
            continue
        amount = abs(float(amount))  # Revenue is stored as negative, convert to positive

        transformed_data.append({
            'store_id': store_id,
            'date': formatted_date,
            'amount': amount,
            'currency': 'CAD'
        })

    return transformed_data


def extract_takeout_revenue(year: int = None, direct_db: bool = True, is_test: bool = False) -> bool:
    """
    Extract takeout revenue from Excel files and insert to database.

    Args:
        year: Specific year to process (2025 or 2026), or None for all
        direct_db: If True, insert directly to database
        is_test: Use test database

    Returns:
        Success status
    """
    project_root = Path(__file__).parent.parent
    takeout_folder = project_root / "Input" / "daily_report" / "takeout_report"

    if not takeout_folder.exists():
        logger.error(f"Takeout folder not found: {takeout_folder}")
        print(f"ERROR: Takeout folder not found: {takeout_folder}")
        return False

    # Find Excel files
    if year:
        excel_files = list(takeout_folder.glob(f"{year}.XLSX")) + list(takeout_folder.glob(f"{year}.xlsx"))
    else:
        excel_files = list(takeout_folder.glob("*.XLSX")) + list(takeout_folder.glob("*.xlsx"))

    # Filter out temp files
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]

    if not excel_files:
        logger.error("No takeout Excel files found")
        print("ERROR: No takeout Excel files found")
        return False

    all_data = []

    for file_path in excel_files:
        print(f"Processing: {file_path.name}")
        logger.info(f"Processing takeout file: {file_path.name}")
        try:
            df = pd.read_excel(file_path)
            transformed = transform_takeout_data(df)
            all_data.extend(transformed)
            print(f"  Extracted {len(transformed)} records")
            logger.info(f"Extracted {len(transformed)} records from {file_path.name}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            print(f"  ERROR reading file: {e}")
            continue

    if not all_data:
        print("No data extracted from files")
        logger.warning("No data extracted from takeout files")
        return False

    print(f"\nTotal records extracted: {len(all_data)}")

    if direct_db:
        return insert_takeout_data_to_database(all_data, is_test)

    return True


def insert_takeout_data_to_database(data: List[Dict], is_test: bool = False) -> bool:
    """
    Insert takeout revenue data to database with upsert.

    Args:
        data: List of dictionaries with store_id, date, amount, currency
        is_test: Use test database

    Returns:
        Success status
    """
    try:
        db_manager = get_database_manager(is_test=is_test)

        if not db_manager.test_connection():
            logger.error("Database connection failed")
            print("ERROR: Database connection failed")
            return False

        print(f"Inserting {len(data)} takeout revenue records...")
        logger.info(f"Inserting {len(data)} takeout revenue records to database")

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                inserted = 0
                updated = 0

                for record in data:
                    cursor.execute("""
                        INSERT INTO daily_takeout_revenue (store_id, date, amount, currency)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, date) DO UPDATE SET
                            amount = EXCLUDED.amount,
                            currency = EXCLUDED.currency,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted
                    """, (record['store_id'], record['date'], record['amount'], record['currency']))

                    result = cursor.fetchone()
                    if result and result.get('inserted', result[0] if isinstance(result, tuple) else False):
                        inserted += 1
                    else:
                        updated += 1

                conn.commit()

                print(f"\nTakeout revenue processing completed:")
                print(f"  New records: {inserted}")
                print(f"  Updated records: {updated}")
                logger.info(f"Takeout extraction completed: {inserted} inserted, {updated} updated")

                return True

    except Exception as e:
        logger.error(f"Database insertion failed: {e}")
        print(f"ERROR: Database insertion failed - {e}")
        return False


def get_takeout_summary(is_test: bool = False) -> Dict:
    """
    Get summary of takeout data in database.

    Args:
        is_test: Use test database

    Returns:
        Dictionary with summary statistics
    """
    try:
        db_manager = get_database_manager(is_test=is_test)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT store_id) as stores,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date,
                        SUM(amount) as total_amount
                    FROM daily_takeout_revenue
                """)
                result = cursor.fetchone()

                if result:
                    return {
                        'total_records': result['total_records'] or result[0],
                        'stores': result['stores'] or result[1],
                        'earliest_date': result['earliest_date'] or result[2],
                        'latest_date': result['latest_date'] or result[3],
                        'total_amount': float(result['total_amount'] or result[4] or 0)
                    }

        return {}

    except Exception as e:
        logger.error(f"Error getting takeout summary: {e}")
        return {}


if __name__ == "__main__":
    # Command line execution
    import argparse

    parser = argparse.ArgumentParser(description="Extract takeout revenue data")
    parser.add_argument("--year", type=int, help="Specific year to process (2025 or 2026)")
    parser.add_argument("--test", action="store_true", help="Use test database")
    parser.add_argument("--summary", action="store_true", help="Show database summary only")

    args = parser.parse_args()

    if args.summary:
        summary = get_takeout_summary(is_test=args.test)
        print("\nTakeout Revenue Database Summary:")
        print(f"  Total records: {summary.get('total_records', 0)}")
        print(f"  Stores: {summary.get('stores', 0)}")
        print(f"  Date range: {summary.get('earliest_date')} to {summary.get('latest_date')}")
        print(f"  Total amount: ${summary.get('total_amount', 0):,.2f} CAD")
    else:
        success = extract_takeout_revenue(year=args.year, direct_db=True, is_test=args.test)
        exit(0 if success else 1)
