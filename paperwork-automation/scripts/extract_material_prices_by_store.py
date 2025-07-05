#!/usr/bin/env python3
"""
Extract material prices from Excel files by store.
This script extracts material price data from Excel files that contain store-specific pricing information.

Usage:
    python scripts/extract_material_prices_by_store.py [--input INPUT_FILE] [--store-id STORE_ID] [--debug] [--test]

Features:
- Extracts material prices from Excel files with store-specific pricing
- Maps store names to store IDs
- Handles both numeric and text store identifiers
- Supports test database mode
- Implements price history activation (marks previous prices as inactive)
"""

from utils.database import DatabaseManager, DatabaseConfig
import pandas as pd
import sys
import os
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def detect_store_from_excel_headers(file_path: str) -> Optional[int]:
    """Detect store ID from Excel file headers or filename."""
    try:
        # Try to detect from filename
        filename = Path(file_path).name

        # Look for store patterns in filename (CA01, CA02, etc.)
        store_match = re.search(r'CA(\d+)', filename, re.IGNORECASE)
        if store_match:
            return int(store_match.group(1))

        # Try to read Excel file to detect store information
        try:
            df = pd.read_excel(file_path, nrows=10)  # Read first 10 rows only

            # Look for store information in the first few rows
            for col in df.columns:
                for idx, row in df.iterrows():
                    cell_value = str(row[col])
                    if 'CA' in cell_value.upper():
                        store_match = re.search(
                            r'CA(\d+)', cell_value, re.IGNORECASE)
                        if store_match:
                            return int(store_match.group(1))
        except Exception:
            pass

        return None
    except Exception as e:
        print(f"Error detecting store from file: {e}")
        return None


def get_store_mapping() -> Dict[str, int]:
    """Get store name to ID mapping."""
    return {
        '加拿大一店': 1,
        '加拿大二店': 2,
        '加拿大三店': 3,
        '加拿大四店': 4,
        '加拿大五店': 5,
        '加拿大六店': 6,
        '加拿大七店': 7,
        'CA01': 1,
        'CA02': 2,
        'CA03': 3,
        'CA04': 4,
        'CA05': 5,
        'CA06': 6,
        'CA07': 7,
    }


def extract_material_prices_from_excel(file_path: str, store_id: int = None, debug: bool = False) -> List[Dict]:
    """
    Extract material prices from Excel file.

    Args:
        file_path: Path to the Excel file
        store_id: Store ID (auto-detected if None)
        debug: Enable debug output

    Returns:
        List of material price dictionaries
    """
    try:
        print(f"📊 Reading material prices from: {file_path}")

        # Auto-detect store if not provided
        if store_id is None:
            store_id = detect_store_from_excel_headers(file_path)
            if store_id is None:
                print("❌ Could not detect store ID from file. Please specify --store-id")
                return []

        print(f"🏪 Processing for store ID: {store_id}")

        # Try to read Excel file
        try:
            # Try different engines
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
            except Exception:
                df = pd.read_excel(file_path, engine='xlrd')
        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")
            return []

        if debug:
            print(f"📋 Excel shape: {df.shape}")
            print(f"📋 Columns: {list(df.columns)}")

        # Expected columns for material prices
        # Common Chinese column names for material price data
        expected_columns = {
            'material_number': ['物料号', '物料编号', '材料号', '编号', '物料编码', 'Material Number', 'Code'],
            'material_name': ['物料名称', '材料名称', '物料描述', '名称', 'Material Name', 'Name', 'Description'],
            'unit_price': ['单价', '价格', '成本', '单位价格', 'Unit Price', 'Price', 'Cost'],
            'unit': ['单位', '计量单位', 'Unit', 'UOM'],
            'effective_date': ['生效日期', '有效日期', '日期', 'Effective Date', 'Date'],
            'currency': ['货币', '币种', 'Currency']
        }

        # Map columns
        column_mapping = {}
        for standard_col, possible_cols in expected_columns.items():
            for col in possible_cols:
                if col in df.columns:
                    column_mapping[standard_col] = col
                    break

        if debug:
            print(f"📋 Column mapping: {column_mapping}")

        # Check for required columns
        required_columns = ['material_number', 'unit_price']
        missing_columns = [
            col for col in required_columns if col not in column_mapping]

        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return []

        # Extract material prices
        material_prices = []

        for _, row in df.iterrows():
            try:
                # Extract material number
                material_number = str(
                    row[column_mapping['material_number']]).strip()

                # Clean material number (remove .0 suffix if present)
                if material_number.endswith('.0'):
                    material_number = material_number[:-2]

                # Skip empty rows
                if not material_number or material_number.lower() in ['nan', 'none', '']:
                    continue

                # Extract price
                unit_price = float(row[column_mapping['unit_price']])

                # Skip zero or negative prices
                if unit_price <= 0:
                    continue

                # Extract optional fields
                material_name = ''
                if 'material_name' in column_mapping:
                    material_name = str(
                        row[column_mapping['material_name']]).strip()

                unit = ''
                if 'unit' in column_mapping:
                    unit = str(row[column_mapping['unit']]).strip()

                currency = 'CAD'
                if 'currency' in column_mapping:
                    currency = str(row[column_mapping['currency']]).strip()
                    if not currency or currency.lower() in ['nan', 'none']:
                        currency = 'CAD'

                # Use current date as effective date if not provided
                effective_date = datetime.now().date()
                if 'effective_date' in column_mapping:
                    try:
                        effective_date = pd.to_datetime(
                            row[column_mapping['effective_date']]).date()
                    except Exception:
                        pass  # Use current date as fallback

                material_prices.append({
                    'material_number': material_number,
                    'material_name': material_name,
                    'store_id': store_id,
                    'unit_price': unit_price,
                    'unit': unit,
                    'currency': currency,
                    'effective_date': effective_date,
                    'is_active': True
                })

            except Exception as e:
                if debug:
                    print(f"⚠️ Error processing row: {e}")
                continue

        print(
            f"✅ Extracted {len(material_prices)} material prices for store {store_id}")
        return material_prices

    except Exception as e:
        print(f"❌ Error extracting material prices: {e}")
        return []


def insert_material_prices_to_database(material_prices: List[Dict], is_test: bool = False) -> bool:
    """
    Insert material prices to database.

    Args:
        material_prices: List of material price dictionaries
        is_test: Use test database

    Returns:
        Success status
    """
    try:
        print(
            f"🗄️ Connecting to {'test' if is_test else 'production'} database...")

        config = DatabaseConfig(is_test=is_test)
        db_manager = DatabaseManager(config)

        inserted = 0
        updated = 0
        errors = 0

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:

                for price_data in material_prices:
                    try:
                        # First, get material_id from material_number
                        cursor.execute("""
                            SELECT id FROM material 
                            WHERE material_number = %s
                        """, (price_data['material_number'],))

                        material_result = cursor.fetchone()
                        if not material_result:
                            print(
                                f"⚠️ Material not found: {price_data['material_number']}")
                            errors += 1
                            continue

                        material_id = material_result['id']

                        # Deactivate previous prices for this material-store combination
                        cursor.execute("""
                            UPDATE material_price_history 
                            SET is_active = FALSE 
                            WHERE material_id = %s AND store_id = %s
                        """, (material_id, price_data['store_id']))

                        # Insert new price record
                        cursor.execute("""
                            INSERT INTO material_price_history (
                                material_id, store_id, price, currency, effective_date, is_active
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (material_id, store_id, effective_date) 
                            DO UPDATE SET
                                price = EXCLUDED.price,
                                currency = EXCLUDED.currency,
                                is_active = EXCLUDED.is_active
                            RETURNING (xmax = 0) AS inserted
                        """, (
                            material_id,
                            price_data['store_id'],
                            price_data['unit_price'],
                            price_data['currency'],
                            price_data['effective_date'],
                            price_data['is_active']
                        ))

                        result = cursor.fetchone()
                        if result and result['inserted']:
                            inserted += 1
                        else:
                            updated += 1

                    except Exception as e:
                        print(
                            f"❌ Error processing material {price_data['material_number']}: {e}")
                        errors += 1
                        continue

                # Commit all changes
                conn.commit()

        print(f"✅ Database insertion complete:")
        print(f"   📝 Inserted: {inserted}")
        print(f"   🔄 Updated: {updated}")
        print(f"   ❌ Errors: {errors}")

        return errors == 0

    except Exception as e:
        print(f"❌ Database insertion failed: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Extract material prices by store from Excel files')
    parser.add_argument('--input', '-i', type=str,
                        help='Input Excel file path')
    parser.add_argument('--store-id', '-s', type=int,
                        help='Store ID (auto-detected if not provided)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug output')
    parser.add_argument('--test', '-t', action='store_true',
                        help='Use test database')

    args = parser.parse_args()

    # Get input file
    input_file = args.input
    if not input_file:
        # Try to find Excel files in current directory
        excel_files = list(Path('.').glob('*.xlsx')) + \
            list(Path('.').glob('*.xls'))
        if excel_files:
            input_file = str(excel_files[0])
            print(f"📁 Using found Excel file: {input_file}")
        else:
            print(
                "❌ No input file specified and no Excel files found in current directory")
            return False

    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return False

    # Extract material prices
    material_prices = extract_material_prices_from_excel(
        input_file,
        store_id=args.store_id,
        debug=args.debug
    )

    if not material_prices:
        print("❌ No material prices extracted")
        return False

    # Insert to database
    success = insert_material_prices_to_database(
        material_prices, is_test=args.test)

    if success:
        print("🎉 Material price extraction completed successfully!")
        return True
    else:
        print("❌ Material price extraction completed with errors")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
