#!/usr/bin/env python3
"""
Batch extract material prices from store-specific material_detail folders.

This script processes the new store-organized material_detail folder structure:
Input/monthly_report/material_detail/
├── 1/ (store 1 files)
├── 2/ (store 2 files)  
├── 3/ (store 3 files)
├── 4/ (store 4 files)
├── 5/ (store 5 files)
├── 6/ (store 6 files)
└── 7/ (store 7 files)

Features:
- Processes all store subfolders automatically
- Extracts material prices from Excel files in each store folder
- Associates prices with the correct store based on folder structure
- Handles both export.XLSX and similar Excel file formats
- Implements price history activation (deactivates old prices)
- Supports test and production database modes

Usage:
    python scripts/extract_material_detail_prices_by_store_batch.py [--material-detail-path PATH] [--debug] [--test]
"""

from utils.database import DatabaseManager, DatabaseConfig
import pandas as pd
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Fix Windows console encoding for emoji characters
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except AttributeError:
        # Fallback for older Python versions or different environments
        pass

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_store_mapping() -> Dict[str, int]:
    """Get store folder name to store ID mapping."""
    return {
        '1': 1,  # 加拿大一店
        '2': 2,  # 加拿大二店
        '3': 3,  # 加拿大三店
        '4': 4,  # 加拿大四店
        '5': 5,  # 加拿大五店
        '6': 6,  # 加拿大六店
        '7': 7,  # 加拿大七店
    }


def find_excel_files_in_store_folder(store_folder: Path) -> List[Path]:
    """Find Excel files in a store folder."""
    excel_patterns = ['*.xlsx', '*.xls', '*.XLSX', '*.XLS']
    excel_files = []

    for pattern in excel_patterns:
        excel_files.extend(store_folder.glob(pattern))

    return excel_files


def extract_material_prices_from_store_excel(file_path: Path, store_id: int, target_date: Optional[str] = None, debug: bool = False) -> List[Dict]:
    """
    Extract material prices from a store's Excel file.

    Args:
        file_path: Path to the Excel file
        store_id: Store ID
        debug: Enable debug output

    Returns:
        List of material price dictionaries
    """
    try:
        print(f"📊 Processing store {store_id} file: {file_path.name}")

        # Read Excel file with proper dtype to preserve material numbers
        try:
            # Read with material column as string to prevent float64 conversion
            # Force material column to be read as string
            dtype_spec = {'物料': str}
            df = pd.read_excel(file_path, engine='openpyxl', dtype=dtype_spec)

            if debug:
                print(f"   📊 Read {len(df)} rows from {file_path.name}")
                print(f"   📋 Columns: {list(df.columns)}")

        except Exception as e:
            if debug:
                print(f"   ❌ Error reading {file_path.name}: {e}")
            return []

        # Expected columns for material price data
        # Handle both Chinese and English column names
        expected_columns = {
            'material_number': ['物料', '物料号', '物料编号', '材料号', '编号', 'Material Number', 'Code'],
            'material_name': ['物料描述', '物料名称', '材料名称', '名称', 'Material Name', 'Name', 'Description'],
            'unit_price': ['系统发出单价', '单价', '价格', '成本', '单位价格', '标准价格', 'Unit Price', 'Price', 'Cost', 'Standard Price'],
            'quantity': ['数量', '数量', 'Quantity', 'Qty', 'Amount'],
            'unit': ['单位', '计量单位', '单位描述', 'Unit', 'UOM'],
            'currency': ['货币', '币种', 'Currency'],
            'end_date': ['结束日期', '截止日期', '结束时间', 'End Date', 'Ending Date', 'Date']
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
        required_columns = ['material_number']
        missing_columns = [
            col for col in required_columns if col not in column_mapping]

        if missing_columns:
            print(
                f"⚠️ Missing required columns in {file_path.name}: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")

            # Try alternative approach - look for any column that might be material number
            material_col_candidates = [col for col in df.columns if any(keyword in str(
                col).lower() for keyword in ['物料', '材料', '编号', 'material', 'code'])]

            if material_col_candidates:
                print(
                    f"🔍 Found potential material columns: {material_col_candidates}")
                column_mapping['material_number'] = material_col_candidates[0]
            else:
                print(f"❌ No material number column found in {file_path.name}")
                return []

        # Extract material prices
        material_prices = []

        for _, row in df.iterrows():
            try:
                # Clean material number - remove leading zeros and convert to standard format
                material_number = row[column_mapping['material_number']]
                if pd.isna(material_number):
                    continue

                # Convert to string and remove leading zeros
                material_number = str(material_number).strip()

                # Remove leading zeros but keep the number as string
                material_number = material_number.lstrip('0')

                # Handle edge case where all digits are zeros
                if not material_number:
                    material_number = '0'

                # Only show first few for debugging
                if debug and len(material_prices) < 3:
                    print(
                        f"   🔍 Raw material: {repr(row[column_mapping['material_number']])} → cleaned: {material_number}")

                # Skip if material number is empty or invalid
                if not material_number or not material_number.isdigit():
                    continue

                # Try to extract price - look for any numeric column that might be price
                unit_price = None
                if 'unit_price' in column_mapping:
                    try:
                        unit_price = float(row[column_mapping['unit_price']])
                    except (ValueError, TypeError):
                        pass

                # If no explicit price column, try to find a numeric column with price-like values
                if unit_price is None or unit_price <= 0:
                    for col in df.columns:
                        if any(keyword in str(col).lower() for keyword in ['价格', '单价', '成本', 'price', 'cost']):
                            try:
                                price_value = float(row[col])
                                if price_value > 0:
                                    unit_price = price_value
                                    break
                            except (ValueError, TypeError):
                                continue

                # Skip if no valid price found
                if unit_price is None or unit_price <= 0:
                    continue

                # Extract quantity information
                quantity = 1.0  # Default quantity
                if 'quantity' in column_mapping:
                    try:
                        quantity = float(row[column_mapping['quantity']])
                        if quantity <= 0:
                            quantity = 1.0
                    except (ValueError, TypeError):
                        quantity = 1.0
                else:
                    # Try to find quantity in any column that contains quantity-related keywords
                    for col in df.columns:
                        if any(keyword in str(col).lower() for keyword in ['数量', '数量', 'quantity', 'qty', 'amount']):
                            try:
                                quantity = float(row[col])
                                if quantity > 0:
                                    break
                            except (ValueError, TypeError):
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

                # Use target date if provided, otherwise extract from Excel
                effective_date = None

                if target_date:
                    # Use the target date provided by the automation workflow
                    try:
                        effective_date = datetime.strptime(
                            target_date, '%Y-%m-%d').date()
                        if debug:
                            print(f"📅 Using target date: {effective_date}")
                    except ValueError as e:
                        if debug:
                            print(
                                f"⚠️ Invalid target date format: {target_date}, error: {e}")

                # If no target date or parsing failed, try to extract from Excel
                if effective_date is None and 'end_date' in column_mapping:
                    try:
                        end_date_value = row[column_mapping['end_date']]
                        if pd.notna(end_date_value):
                            if isinstance(end_date_value, str):
                                # Parse string date
                                effective_date = pd.to_datetime(
                                    end_date_value).date()
                            else:
                                # Handle datetime or date objects
                                effective_date = pd.to_datetime(
                                    end_date_value).date()
                            if debug:
                                print(
                                    f"📅 Extracted date from Excel: {effective_date}")
                    except Exception as e:
                        if debug:
                            print(f"⚠️ Error parsing Excel date: {e}")

                # Fallback to current date only as last resort
                if effective_date is None:
                    effective_date = datetime.now().date()
                    if debug:
                        print(
                            f"⚠️ Using current date as last resort fallback: {effective_date}")
                    else:
                        print(
                            f"⚠️ Warning: No date found in Excel or target date, using current date: {effective_date}")

                material_prices.append({
                    'material_number': material_number,
                    'material_name': material_name,
                    'store_id': store_id,
                    'unit_price': unit_price,
                    'quantity': quantity,
                    'unit': unit,
                    'currency': currency,
                    'effective_date': effective_date,
                    'is_active': True
                })

            except Exception as e:
                if debug:
                    print(f"⚠️ Error processing row in {file_path.name}: {e}")
                continue

        # Handle duplicates - pick representative product per material per store per month
        # Group by material_number, store_id, and effective_date
        unique_prices = {}
        for price in material_prices:
            key = (price['material_number'],
                   price['store_id'], price['effective_date'])
            if key not in unique_prices:
                unique_prices[key] = []
            unique_prices[key].append(price)

        final_prices = []
        for key, price_list in unique_prices.items():
            material_number, store_id, effective_date = key

            if len(price_list) == 1:
                # Single price entry - keep as is
                final_prices.append(price_list[0])
            else:
                # Multiple price entries - pick representative product based on highest total contribution

                # Group by material description to separate different products
                product_groups = {}
                for price_entry in price_list:
                    product_name = price_entry['material_name']
                    if product_name not in product_groups:
                        product_groups[product_name] = []
                    product_groups[product_name].append(price_entry)

                # Calculate total contribution for each product
                product_contributions = {}
                product_weighted_averages = {}

                for product_name, entries in product_groups.items():
                    total_contribution = 0
                    total_quantity = 0
                    weighted_sum = 0

                    for entry in entries:
                        quantity = entry.get('quantity', 1.0)
                        contribution = entry['unit_price'] * quantity
                        total_contribution += contribution
                        total_quantity += quantity
                        weighted_sum += contribution

                    # Calculate weighted average for this product
                    if total_quantity > 0:
                        product_weighted_avg = weighted_sum / total_quantity
                    else:
                        product_weighted_avg = sum(
                            e['unit_price'] for e in entries) / len(entries)

                    product_contributions[product_name] = total_contribution
                    product_weighted_averages[product_name] = product_weighted_avg

                # Pick the product with highest total contribution
                representative_product = max(
                    product_contributions, key=product_contributions.get)
                representative_price = product_weighted_averages[representative_product]
                representative_contribution = product_contributions[representative_product]

                if debug:
                    print(
                        f"   🎯 Material {material_number}: Multiple products found")
                    for product, contribution in product_contributions.items():
                        avg_price = product_weighted_averages[product]
                        marker = " ← SELECTED" if product == representative_product else ""
                        print(
                            f"      - {product}: {avg_price:.4f} CAD (contribution: {contribution:.2f}){marker}")
                    print(
                        f"   ✅ Selected: {representative_product} with price {representative_price:.4f} CAD")

                # Create new price entry with representative product
                # Use first entry as template
                representative_entry = price_list[0].copy()
                representative_entry['unit_price'] = representative_price
                representative_entry[
                    'material_name'] = f"{representative_product} (selected from {len(product_groups)} products)"

                final_prices.append(representative_entry)

        if len(final_prices) != len(material_prices):
            consolidated_count = len(material_prices) - len(final_prices)
            print(f"🔄 Consolidated {len(material_prices)} entries into {len(final_prices)} unique materials ({consolidated_count} duplicates resolved by selecting representative products)")

        return final_prices

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return []


def process_all_store_folders(material_detail_path: Path, target_date: Optional[str] = None, debug: bool = False) -> Dict[int, List[Dict]]:
    """
    Process all store folders and extract material prices.

    Args:
        material_detail_path: Path to the material_detail folder
        debug: Enable debug output

    Returns:
        Dictionary mapping store_id to list of material prices
    """
    store_mapping = get_store_mapping()
    all_store_prices = {}

    print(f"🔍 Scanning material detail folder: {material_detail_path}")

    # Process each store subfolder
    for store_folder_name, store_id in store_mapping.items():
        store_folder = material_detail_path / store_folder_name

        if not store_folder.exists() or not store_folder.is_dir():
            print(f"⚠️ Store {store_id} folder not found: {store_folder}")
            continue

        print(f"\n🏪 Processing Store {store_id} ({store_folder.name})")

        # Find Excel files in the store folder
        excel_files = find_excel_files_in_store_folder(store_folder)

        if not excel_files:
            print(f"⚠️ No Excel files found in store {store_id} folder")
            continue

        store_prices = []

        # Process each Excel file in the store folder
        for excel_file in excel_files:
            prices = extract_material_prices_from_store_excel(
                excel_file, store_id, target_date, debug)
            store_prices.extend(prices)

        if store_prices:
            all_store_prices[store_id] = store_prices
            print(
                f"📊 Store {store_id} total: {len(store_prices)} material prices")
        else:
            print(f"⚠️ No prices extracted for store {store_id}")

    return all_store_prices


def insert_all_store_prices_to_database(all_store_prices: Dict[int, List[Dict]], is_test: bool = False) -> bool:
    """
    Insert all store prices to database.

    Args:
        all_store_prices: Dictionary mapping store_id to list of material prices
        is_test: Use test database

    Returns:
        Success status
    """
    try:
        print(
            f"🗄️ Connecting to {'test' if is_test else 'production'} database...")

        config = DatabaseConfig(is_test=is_test)
        db_manager = DatabaseManager(config)

        total_inserted = 0
        total_updated = 0
        total_errors = 0

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:

                for store_id, store_prices in all_store_prices.items():
                    print(
                        f"\n🏪 Processing store {store_id}: {len(store_prices)} prices")

                    store_inserted = 0
                    store_updated = 0
                    store_errors = 0

                    for price_data in store_prices:
                        try:
                            # First, get material_id from material_number and store_id
                            cursor.execute("""
                                SELECT id FROM material 
                                WHERE material_number = %s AND store_id = %s
                            """, (price_data['material_number'], price_data['store_id']))

                            material_result = cursor.fetchone()
                            if not material_result:
                                print(
                                    f"⚠️ Material not found: {price_data['material_number']}")
                                store_errors += 1
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
                                store_inserted += 1
                            else:
                                store_updated += 1

                        except Exception as e:
                            print(
                                f"❌ Error processing material {price_data['material_number']} for store {store_id}: {e}")
                            store_errors += 1
                            continue

                    print(f"   📝 Inserted: {store_inserted}")
                    print(f"   🔄 Updated: {store_updated}")
                    print(f"   ❌ Errors: {store_errors}")

                    total_inserted += store_inserted
                    total_updated += store_updated
                    total_errors += store_errors

                # Commit all changes
                conn.commit()

        print(f"\n✅ Batch processing complete:")
        print(f"   📝 Total inserted: {total_inserted}")
        print(f"   🔄 Total updated: {total_updated}")
        print(f"   ❌ Total errors: {total_errors}")
        print(f"   🏪 Stores processed: {len(all_store_prices)}")

        # Consider successful if we processed stores and extracted prices,
        # even if no materials were inserted/updated (materials may not exist in database yet)
        total_prices_extracted = sum(len(prices)
                                     for prices in all_store_prices.values())
        return len(all_store_prices) > 0 and total_prices_extracted > 0

    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Batch extract material prices from store-specific material_detail folders')
    parser.add_argument('--material-detail-path', '-p', type=str,
                        default='Input/monthly_report/material_detail',
                        help='Path to material_detail folder (default: Input/monthly_report/material_detail)')
    parser.add_argument('--target-date', type=str,
                        help='Target date for price records (YYYY-MM-DD). If not provided, will try to extract from Excel files.')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug output')
    parser.add_argument('--test', '-t', action='store_true',
                        help='Use test database')

    args = parser.parse_args()

    # Validate material_detail path
    material_detail_path = Path(args.material_detail_path)
    if not material_detail_path.exists():
        print(f"❌ Material detail folder not found: {material_detail_path}")
        return False

    print("🍲 HAIDILAO MATERIAL PRICE BATCH EXTRACTION")
    print("=" * 60)
    print(f"📁 Material detail path: {material_detail_path}")
    print(
        f"📅 Target date: {args.target_date if args.target_date else 'Extract from Excel files'}")
    print(f"🗄️ Database: {'test' if args.test else 'production'}")
    print(f"🐛 Debug mode: {'enabled' if args.debug else 'disabled'}")
    print("=" * 60)

    # Process all store folders
    all_store_prices = process_all_store_folders(
        material_detail_path, target_date=args.target_date, debug=args.debug)

    if not all_store_prices:
        print("❌ No material prices extracted from any store")
        return False

    # Summary
    total_prices = sum(len(prices) for prices in all_store_prices.values())
    print(f"\n📊 Extraction Summary:")
    print(f"   🏪 Stores processed: {len(all_store_prices)}")
    print(f"   💰 Total prices extracted: {total_prices}")

    # Insert to database
    success = insert_all_store_prices_to_database(
        all_store_prices, is_test=args.test)

    print("=" * 60)
    if success:
        print("🎉 Material price batch extraction completed successfully!")
        print("   ℹ️ Note: Missing material warnings are expected for new material codes")
        return True
    else:
        print("❌ Material price batch extraction failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
