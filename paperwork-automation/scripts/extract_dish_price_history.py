#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Haidilao Dish Price History Extraction Script

This script extracts dish price history data from the monthly dish sales Excel file
and populates the dish_price_history table in the database.

Usage:
    python scripts/extract-dish-price-history.py [--input INPUT_FILE] [--debug] [--test]

Features:
- Extracts from dish sales detail sheet
- Maps store names to store IDs
- Looks up dish IDs from dish codes and sizes
- Extracts effective date from filename
- Handles price history activation (marks previous prices as inactive)
- Supports test database mode
"""

from utils.database import DatabaseManager, DatabaseConfig
import pandas as pd
import sys
import os
import re
import argparse

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_date_from_filename(filename):
    """Extract date from filename in format YYYYMMDD."""
    date_match = re.search(r'(\d{8})', filename)
    if date_match:
        date_str = date_match.group(1)
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return None


def get_store_mapping():
    """Get store name to ID mapping."""
    return {
        '\u52a0\u62ff\u5927\u4e00\u5e97': 1,  # 加拿大一店
        '\u52a0\u62ff\u5927\u4e8c\u5e97': 2,  # 加拿大二店
        '\u52a0\u62ff\u5927\u4e09\u5e97': 3,  # 加拿大三店
        '\u52a0\u62ff\u5927\u56db\u5e97': 4,  # 加拿大四店
        '\u52a0\u62ff\u5927\u4e94\u5e97': 5,  # 加拿大五店
        '\u52a0\u62ff\u5927\u516d\u5e97': 6,  # 加拿大六店
        '\u52a0\u62ff\u5927\u4e03\u5e97': 7   # 加拿大七店
    }


def lookup_dish_ids(db_manager, dish_codes_sizes):
    """Look up dish IDs from full_code and size combinations."""
    if not dish_codes_sizes:
        return {}

    # Create placeholders for the query
    placeholders = ','.join(['(%s, %s)'] * len(dish_codes_sizes))

    query = f"""
    SELECT full_code, size, id 
    FROM dish 
    WHERE (full_code, COALESCE(size, '')) IN ({placeholders})
    """

    # Flatten the dish_codes_sizes for query parameters
    params = []
    for code, size in dish_codes_sizes:
        params.extend([code, size or ''])

    results = db_manager.fetch_all(query, tuple(params))

    # Create lookup dictionary
    dish_lookup = {}
    for result in results:
        key = (result['full_code'], result['size'] or '')
        dish_lookup[key] = result['id']

    return dish_lookup


def lookup_store_ids(db_manager, store_names):
    """Look up store IDs from store names."""
    if not store_names:
        return {}

    placeholders = ','.join(['%s'] * len(store_names))
    query = f"SELECT name, id FROM store WHERE name IN ({placeholders})"

    results = db_manager.fetch_all(query, tuple(store_names))

    return {result['name']: result['id'] for result in results}


def deactivate_previous_prices(db_manager, dish_id, store_id, effective_date):
    """Mark previous prices as inactive for the same dish-store combination."""
    query = """
    UPDATE dish_price_history 
    SET is_active = FALSE 
    WHERE dish_id = %s AND store_id = %s AND effective_date < %s AND is_active = TRUE
    """

    return db_manager.execute_sql(query, (dish_id, store_id, effective_date))


def process_dish_price_history(input_file, debug=False, is_test=False):
    """Process dish price history from Excel file."""
    print(f"🍲 Processing dish price history from: {input_file}")

    # Extract effective date from filename
    effective_date = extract_date_from_filename(input_file)
    if not effective_date:
        print("❌ Could not extract date from filename")
        return False

    print(f"📅 Effective date: {effective_date}")

    # Read Excel file
    try:
        # Try the Chinese sheet name first, then fall back to first sheet
        excel_file = pd.ExcelFile(input_file)
        sheet_names = excel_file.sheet_names

        target_sheet = None
        for sheet in sheet_names:
            if '\u83dc\u54c1\u9500\u552e\u660e\u7ec6\u8868' in sheet:  # 菜品销售明细表
                target_sheet = sheet
                break

        if not target_sheet and sheet_names:
            target_sheet = sheet_names[0]  # Use first sheet as fallback

        if not target_sheet:
            print("❌ No suitable sheet found in Excel file")
            return False

        df = pd.read_excel(input_file, sheet_name=target_sheet)
        excel_file.close()
        print(f"📊 Read {len(df)} rows from Excel sheet: {target_sheet}")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

    # Define column names using Unicode
    store_col = '\u95e8\u5e97\u540d\u79f0'      # 门店名称
    dish_code_col = '\u83dc\u54c1\u7f16\u7801'  # 菜品编码
    size_col = '\u89c4\u683c'                   # 规格
    price_col = '\u83dc\u54c1\u5355\u4ef7'      # 菜品单价

    # Check if required columns exist
    required_cols = [store_col, dish_code_col, price_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing required columns: {missing_cols}")
        print(f"Available columns: {list(df.columns)}")
        return False

    # Filter out rows with zero or null prices
    df = df[df[price_col].notna() & (df[price_col] > 0)]
    print(f"📊 After filtering zero prices: {len(df)} rows")

    # Get unique combinations of dish code, size, store, and price
    cols_to_extract = [store_col, dish_code_col, price_col]
    if size_col in df.columns:
        cols_to_extract.append(size_col)
    else:
        print("⚠️ Size column not found, will use empty size")
        df[size_col] = ''  # Add empty size column
        cols_to_extract.append(size_col)

    price_data = df[cols_to_extract].drop_duplicates()
    print(f"📊 Unique dish-store-price combinations: {len(price_data)}")

    # Get store mapping
    store_mapping = get_store_mapping()

    # Filter for known stores
    price_data = price_data[price_data[store_col].isin(store_mapping.keys())]
    print(f"📊 After filtering known stores: {len(price_data)}")

    if price_data.empty:
        print("⚠️ No valid data found after filtering")
        return False

    # Initialize database
    config = DatabaseConfig(is_test=is_test)
    db_manager = DatabaseManager(config)

    try:
        # Test connection first
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return False

        # Get unique dish codes and sizes for lookup
        dish_codes_sizes = set()
        for _, row in price_data.iterrows():
            # Convert dish code to string and remove .0 if it's a float
            dish_code = str(row[dish_code_col])
            if dish_code.endswith('.0'):
                dish_code = dish_code[:-2]

            size = str(row[size_col]) if pd.notna(row[size_col]) else ''
            dish_codes_sizes.add((dish_code, size))

        print(
            f"🔍 Looking up {len(dish_codes_sizes)} unique dish combinations...")

        # Look up dish IDs
        dish_lookup = lookup_dish_ids(db_manager, dish_codes_sizes)
        print(f"✅ Found {len(dish_lookup)} dishes in database")

        # Look up store IDs
        store_names = set(price_data[store_col].unique())
        store_lookup = lookup_store_ids(db_manager, store_names)
        print(f"✅ Found {len(store_lookup)} stores in database")

        # Process price history records
        success_count = 0
        skip_count = 0

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for _, row in price_data.iterrows():
                    store_name = row[store_col]
                    # Convert dish code to string and remove .0 if it's a float
                    dish_code = str(row[dish_code_col])
                    if dish_code.endswith('.0'):
                        dish_code = dish_code[:-2]

                    size = str(row[size_col]) if pd.notna(
                        row[size_col]) else ''
                    price = float(row[price_col])

                    # Look up IDs
                    dish_key = (dish_code, size)
                    dish_id = dish_lookup.get(dish_key)
                    store_id = store_lookup.get(store_name)

                    if not dish_id:
                        if debug:
                            print(
                                f"⚠️ Dish not found: {dish_code} (size: {size})")
                        skip_count += 1
                        continue

                    if not store_id:
                        if debug:
                            print(f"⚠️ Store not found: {store_name}")
                        skip_count += 1
                        continue

                    try:
                        # Deactivate previous prices for this dish-store combination
                        deactivate_previous_prices(
                            db_manager, dish_id, store_id, effective_date)

                        # Insert new price history record
                        insert_query = """
                        INSERT INTO dish_price_history 
                        (dish_id, store_id, price, currency, effective_date, is_active) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (dish_id, store_id, effective_date) 
                        DO UPDATE SET 
                            price = EXCLUDED.price,
                            currency = EXCLUDED.currency,
                            is_active = EXCLUDED.is_active
                        """

                        cursor.execute(insert_query, (
                            dish_id, store_id, price, 'CAD', effective_date, True
                        ))

                        success_count += 1

                        if debug:
                            print(
                                f"✅ Inserted: Store {store_name} -> Dish {dish_code} -> ${price}")

                    except Exception as e:
                        if debug:
                            print(f"❌ Error inserting record: {e}")
                        skip_count += 1

                # Commit all changes
                conn.commit()

        print(f"\n🎯 EXTRACTION RESULTS:")
        print(
            f"   ✅ Successfully inserted: {success_count} price history records")
        print(f"   ⚠️ Skipped: {skip_count} records")
        print(f"   📅 Effective date: {effective_date}")

        return success_count > 0

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description='Extract dish price history from Excel file')
    parser.add_argument('--input',
                        default='Input/monthly_report/monthly_dish_sale/\u6d77\u5916\u83dc\u54c1\u9500\u552e\u62a5\u8868_20250626_1903.xlsx',
                        help='Input Excel file path')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug output')
    parser.add_argument('--test', action='store_true',
                        help='Use test database')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)

    success = process_dish_price_history(args.input, args.debug, args.test)

    if success:
        print("\n🎉 Dish price history extraction completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Dish price history extraction failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
