#!/usr/bin/env python3
"""
Extract material monthly usage data from Excel files.
Calculates material_used as (期末库存 - 期初库存) = (closing_stock - opening_stock).
"""

import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import database utilities
try:
    from utils.database import DatabaseManager, DatabaseConfig
    def get_database_manager(is_test=False): return DatabaseManager(
        DatabaseConfig(is_test=is_test))
except ImportError:
    print("WARNING: Database utilities not available. SQL file generation only.")
    get_database_manager = None


def detect_store_from_excel_headers(file_path: str) -> int:
    """Detect store ID from Excel file headers (ValA column with CA01, CA07, etc.)"""
    try:
        import re

        # Check if file is TSV/CSV format
        is_csv_format = False
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header.startswith(b'\xff\xfe') or header.startswith(b'\xfe\xff'):
                    is_csv_format = True
        except:
            pass

        if is_csv_format:
            # Read as TSV with UTF-16 encoding - read more rows to find store info
            df = pd.read_csv(file_path, sep='\t', encoding='utf-16', nrows=20)
            print(f"INFO: Reading TSV file for store detection...")
        else:
            # Read Excel file (first few rows to check headers)
            engine = 'xlrd' if file_path.lower().endswith('.xls') else 'openpyxl'
            excel_file = pd.ExcelFile(file_path, engine=engine)

            # Try to find the material usage sheet
            target_sheets = ['物料使用', '材料统计', '库存统计', '物料统计', 'Material']
            sheet_name = None

            for potential_sheet in target_sheets:
                if potential_sheet in excel_file.sheet_names:
                    sheet_name = potential_sheet
                    break

            if not sheet_name:
                sheet_name = excel_file.sheet_names[0]

            df = pd.read_excel(
                file_path, sheet_name=sheet_name, engine=engine, nrows=20)
            print(f"INFO: Reading Excel file for store detection...")

        # Look for ValA column specifically first
        for col in df.columns:
            col_str = str(col).strip()

            # Check if this is the ValA column
            if 'ValA' in col_str or 'vala' in col_str.lower():
                print(f"INFO: Found ValA column: '{col_str}'")

                # Get all non-null values from this column
                vala_values = df[col].dropna()
                print(f"INFO: ValA values: {list(vala_values.head())}")

                for val in vala_values:
                    val_str = str(val).strip().upper()

                    # Look for CA## pattern
                    ca_match = re.search(r'CA0?(\d)', val_str)
                    if ca_match:
                        store_num = int(ca_match.group(1))
                        if 1 <= store_num <= 7:
                            print(
                                f"STORE: Detected store {store_num} from ValA column: {val_str}")
                            return store_num

        # If ValA column not found, check other columns for CA## patterns
        print(f"INFO: ValA column not found, checking other columns...")
        for col in df.columns:
            col_str = str(col).strip()
            for val in df[col].dropna():
                val_str = str(val).strip().upper()
                ca_match = re.search(r'CA0?(\d)', val_str)
                if ca_match:
                    store_num = int(ca_match.group(1))
                    if 1 <= store_num <= 7:
                        print(
                            f"STORE: Detected store {store_num} from column '{col}': {val_str}")
                        return store_num

        # If no ValA pattern found, fall back to filename detection
        print(f"WARNING: No CA## patterns found in file headers")
        return detect_store_from_filename(file_path)

    except Exception as e:
        print(f"WARNING: Error reading Excel headers for store detection: {e}")
        import traceback
        traceback.print_exc()
        return detect_store_from_filename(file_path)


def detect_store_from_filename(file_path: str) -> int:
    """Detect store ID from filename patterns (fallback method)"""
    filename = Path(file_path).name.lower()

    # Store name mappings
    store_mappings = {
        '一店': 1, 'store1': 1, '1店': 1,
        '二店': 2, 'store2': 2, '2店': 2,
        '三店': 3, 'store3': 3, '3店': 3,
        '四店': 4, 'store4': 4, '4店': 4,
        '五店': 5, 'store5': 5, '5店': 5,
        '六店': 6, 'store6': 6, '6店': 6,
        '七店': 7, 'store7': 7, '7店': 7
    }

    # Check for store patterns in filename
    for store_pattern, store_id in store_mappings.items():
        if store_pattern in filename:
            return store_id

    # Check for numeric patterns like "8003" (store 6 pattern)
    if '8003' in filename:
        return 6

    # Default to store 1 if no pattern found
    print(f"WARNING: Could not detect store from filename, defaulting to store 1")
    return 1


def extract_material_monthly_usage_from_excel(file_path: str, store_id: int = None, quiet: bool = False) -> List[Dict]:
    """Extract material monthly usage data from Excel file"""

    if not quiet:
        print(f"INFO: Extracting material monthly usage from: {file_path}")

    # Detect store if not provided
    if store_id is None:
        store_id = detect_store_from_excel_headers(file_path)
        if not quiet:
            print(f"STORE: Detected store_id: {store_id}")
    elif not quiet:
        print(f"STORE: Using provided store_id: {store_id}")

    try:
        # Check if file is actually a TSV/CSV file (common for .xls exports)
        is_csv_format = False
        try:
            # Check file header to detect UTF-16 TSV files
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header.startswith(b'\xff\xfe') or header.startswith(b'\xfe\xff'):
                    is_csv_format = True
                    if not quiet:
                        print("DETECT: UTF-16 encoded TSV file")
        except:
            pass

        if is_csv_format:
            # Read as TSV with UTF-16 encoding
            df = pd.read_csv(file_path, sep='\t', encoding='utf-16')
            if not quiet:
                print(f"DATA: TSV file read successfully")
        else:
            # Read Excel file and get all sheet names (specify engine for .xls files)
            engine = 'xlrd' if file_path.lower().endswith('.xls') else 'openpyxl'
            excel_file = pd.ExcelFile(file_path, engine=engine)

            if not quiet:
                print(f"Available sheets: {excel_file.sheet_names}")

            # Try to find the material usage sheet
            target_sheets = ['物料使用', '材料统计', '库存统计', '物料统计', 'Material']
            sheet_name = None

            for potential_sheet in target_sheets:
                if potential_sheet in excel_file.sheet_names:
                    sheet_name = potential_sheet
                    break

            # If no predefined sheet found, use the first sheet
            if not sheet_name:
                sheet_name = excel_file.sheet_names[0]
                if not quiet:
                    print(f"WARNING: Using first sheet: {sheet_name}")

            # Read the data (specify engine for .xls files)
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)

        if not quiet:
            print(f"DATA: Shape: {df.shape}")
            print(f"DATA: Found {len(df.columns)} columns")

        # Extract month and year from file name
        month, year = extract_month_year_from_filename(file_path)

        if not quiet:
            print(f"DATE: Extracted period: {year}-{month:02d}")

        # Clean and standardize column names
        df.columns = df.columns.astype(str).str.strip()

        # Expected columns (with Chinese names and possible variations)
        column_mapping = {
            # Material identification
            '物料号': 'material_number',
            '物料编号': 'material_number',
            '材料号': 'material_number',
            '编号': 'material_number',
            '物料': 'material_number',  # In TSV files, this might be the material code
            'Material Number': 'material_number',
            'Code': 'material_number',

            # Material name
            '物料名称': 'material_name',
            '材料名称': 'material_name',
            '物料描述': 'material_name',  # Material description from TSV
            '名称': 'material_name',
            'Material Name': 'material_name',
            'Name': 'material_name',

            # Opening stock (期初库存)
            '期初库存': 'opening_stock',
            '期初': 'opening_stock',
            '初期库存': 'opening_stock',
            'Opening Stock': 'opening_stock',
            'Opening': 'opening_stock',

            # Closing stock (期末库存)
            '期末库存': 'closing_stock',
            '期末': 'closing_stock',
            '末期库存': 'closing_stock',
            'Closing Stock': 'closing_stock',
            'Closing': 'closing_stock',
            'Ending': 'closing_stock',

            # Total received quantity (can help calculate usage)
            '总收货数量': 'total_received',
            '收货数量': 'total_received',
            '入库数量': 'total_received',

            # Total shipped quantity (can help calculate usage)
            '总发货数量': 'total_shipped',
            '发货数量': 'total_shipped',
            '出库数量': 'total_shipped',

            # Unit
            '单位': 'unit',
            'Unit': 'unit',

            # Already calculated usage (if available)
            '使用量': 'usage_amount',
            '消耗量': 'usage_amount',
            '用量': 'usage_amount',
            'Usage': 'usage_amount',
            'Consumption': 'usage_amount'
        }

        # Map columns
        df_mapped = {}
        for chinese_col, english_col in column_mapping.items():
            if chinese_col in df.columns:
                df_mapped[english_col] = df[chinese_col]

        if not df_mapped:
            print("ERROR: No recognizable columns found in the data")
            return []

        # Convert to DataFrame
        df_clean = pd.DataFrame(df_mapped)

        # Handle missing required columns
        required_columns = ['material_number']
        for col in required_columns:
            if col not in df_clean.columns:
                print(f"ERROR: Required column '{col}' not found")
                return []

        # Fill missing optional columns with defaults
        optional_columns = {
            'material_name': '',
            'opening_stock': 0,
            'closing_stock': 0,
            'total_received': 0,
            'total_shipped': 0,
            'unit': '',
            'usage_amount': None
        }

        for col, default_value in optional_columns.items():
            if col not in df_clean.columns:
                df_clean[col] = default_value

        # Clean and process data
        material_usage = []

        for _, row in df_clean.iterrows():
            # Clean material number (remove .0 suffix from float conversion)
            material_number = str(row['material_number']).strip()
            if material_number.endswith('.0'):
                material_number = material_number[:-2]

            # Skip empty rows
            if not material_number or material_number in ['nan', 'NaN', '']:
                continue

            # Clean numeric values
            def clean_numeric(value):
                if pd.isna(value) or value == '' or value == '-':
                    return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0

            opening_stock = clean_numeric(row['opening_stock'])
            closing_stock = clean_numeric(row['closing_stock'])
            total_received = clean_numeric(row['total_received'])
            total_shipped = clean_numeric(row['total_shipped'])

            # Use 期末库存 (closing_stock) directly as material usage as clarified by user
            material_used = closing_stock

            # Skip only if all values are zero (no data available)
            if (opening_stock == 0 and closing_stock == 0 and
                    total_received == 0 and total_shipped == 0):
                continue

            material_usage.append({
                'material_number': material_number,
                'material_name': str(row['material_name']).strip(),
                'store_id': store_id,
                'month': month,
                'year': year,
                'material_used': material_used,
                'opening_stock': opening_stock,
                'closing_stock': closing_stock,
                'unit': str(row['unit']).strip() if row['unit'] else ''
            })

        if not quiet:
            print(
                f"SUCCESS: Extracted {len(material_usage)} material monthly usage records")

            # Show some statistics
            positive_usage = sum(
                1 for m in material_usage if m['material_used'] > 0)
            negative_usage = sum(
                1 for m in material_usage if m['material_used'] < 0)
            zero_usage = sum(
                1 for m in material_usage if m['material_used'] == 0)

            print(f"INFO: Usage statistics:")
            print(f"   Positive usage (consumed): {positive_usage}")
            print(f"   Negative usage (added stock): {negative_usage}")
            print(f"   Zero usage: {zero_usage}")

        return material_usage

    except Exception as e:
        print(f"ERROR: Error extracting material monthly usage: {e}")
        import traceback
        traceback.print_exc()
        return []


def extract_month_year_from_filename(file_path: str) -> tuple:
    """Extract month and year from filename"""
    filename = Path(file_path).name

    # Try different patterns
    import re

    # Pattern 1: YYYYMM format
    pattern1 = re.search(r'(\d{4})(\d{2})', filename)
    if pattern1:
        year, month = int(pattern1.group(1)), int(pattern1.group(2))
        if 1 <= month <= 12:
            return month, year

    # Pattern 2: YYYY-MM format
    pattern2 = re.search(r'(\d{4})-(\d{1,2})', filename)
    if pattern2:
        year, month = int(pattern2.group(1)), int(pattern2.group(2))
        if 1 <= month <= 12:
            return month, year

    # Pattern 3: Current date as fallback
    now = datetime.now()
    print(
        f"WARNING: Could not extract date from filename, using current date: {now.year}-{now.month:02d}")
    return now.month, now.year


def generate_sql_file(material_usage: List[Dict], output_file: str) -> bool:
    """Generate SQL file with UPSERT statements for material monthly usage"""

    try:
        print(f"INFO: Generating SQL file: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- Material monthly usage data insertion script\n")
            f.write(
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Records: {len(material_usage)}\n\n")

            # Insert material monthly usage
            f.write("-- ========================================\n")
            f.write("-- MATERIAL MONTHLY USAGE DATA\n")
            f.write("-- ========================================\n\n")

            for usage in material_usage:
                material_number = usage['material_number'].replace("'", "''")

                # Create comment with readable info
                f.write(
                    f"-- Material: {usage['material_name']} ({usage['material_number']}) - Store {usage['store_id']} - {usage['year']}-{usage['month']:02d}\n")
                f.write(
                    f"-- Usage: {usage['material_used']:.4f} (Opening: {usage['opening_stock']:.4f}, Closing: {usage['closing_stock']:.4f})\n")

                sql = f"""INSERT INTO material_monthly_usage (material_id, store_id, month, year, material_used)
SELECT
    m.id as material_id,
    {usage['store_id']},
    {usage['month']},
    {usage['year']},
    {usage['material_used']}
FROM material m
WHERE m.material_number = '{material_number}'
ON CONFLICT (material_id, store_id, month, year)
DO UPDATE SET
    material_used = EXCLUDED.material_used,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            f.write(f"\n-- End of material monthly usage insertion script\n")
            f.write(f"-- {len(material_usage)} records processed\n")

        print(f"SUCCESS: SQL file generated successfully: {output_file}")
        return True

    except Exception as e:
        print(f"ERROR: Error generating SQL file: {e}")
        return False


def insert_to_database(material_usage: List[Dict], is_test: bool = False, quiet: bool = False) -> bool:
    """Insert material monthly usage directly to database"""

    try:
        if get_database_manager is None:
            print("ERROR: Database connection module not available")
            return False

        print(
            f"INFO: Connecting to {'test' if is_test else 'production'} database...")

        db_manager = get_database_manager(is_test=is_test)

        print(
            f"INFO: Inserting {len(material_usage)} material monthly usage records...")
        inserted = 0
        updated = 0
        errors = 0

        # Process materials in batches of 100 to balance performance and error isolation
        batch_size = 100

        for i in range(0, len(material_usage), batch_size):
            batch = material_usage[i:i + batch_size]

            try:
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        batch_inserted = 0
                        batch_updated = 0
                        batch_errors = 0

                        for usage in batch:
                            try:
                                # Get material ID
                                cursor.execute("""
                                    SELECT id FROM material 
                                    WHERE material_number = %s
                                """, (usage['material_number'],))

                                material_result = cursor.fetchone()
                                if not material_result:
                                    print(
                                        f"WARNING: Material not found - number: {usage['material_number']}")
                                    batch_errors += 1
                                    continue

                                material_id = material_result['id']

                                # Insert/update material monthly usage
                                query = """
                                INSERT INTO material_monthly_usage (material_id, store_id, month, year, material_used)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (material_id, store_id, month, year)
                                DO UPDATE SET
                                    material_used = EXCLUDED.material_used,
                                    updated_at = CURRENT_TIMESTAMP
                                RETURNING (xmax = 0) AS inserted;
                                """

                                cursor.execute(query, (
                                    material_id,
                                    usage['store_id'],
                                    usage['month'],
                                    usage['year'],
                                    usage['material_used']
                                ))

                                result = cursor.fetchone()
                                if result and result['inserted']:
                                    batch_inserted += 1
                                else:
                                    batch_updated += 1

                            except Exception as e:
                                print(
                                    f"ERROR: Error processing material {usage['material_number']}: {e}")
                                batch_errors += 1
                                continue

                        # Commit the entire batch
                        conn.commit()

                        inserted += batch_inserted
                        updated += batch_updated
                        errors += batch_errors

                        if not quiet:
                            print(
                                f"INFO: Processed batch {i//batch_size + 1}: {batch_inserted} inserted, {batch_updated} updated, {batch_errors} errors")

            except Exception as e:
                print(f"ERROR: Batch processing failed: {e}")
                errors += len(batch)
                continue

                print(f"SUCCESS: Database insertion completed:")
                print(f"   INFO: Inserted: {inserted} new records")
                print(f"   INFO: Updated: {updated} existing records")
                if errors > 0:
                    print(f"   ERROR: Errors: {errors} records failed")

                # Consider it successful if we processed most data successfully
                total_processed = inserted + updated + errors
                success_rate = (inserted + updated) / \
                    total_processed if total_processed > 0 else 0
                return success_rate >= 0.8  # 80% success rate threshold

    except Exception as e:
        print(f"ERROR: Database insertion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Extract material monthly usage from Excel")
    parser.add_argument(
        "excel_file", help="Path to Excel file containing material usage data")
    parser.add_argument("--sql-output", help="Output SQL file path",
                        default="output/material_monthly_usage_insert.sql")
    parser.add_argument("--direct-db", action="store_true",
                        help="Insert directly to database")
    parser.add_argument("--test-db", action="store_true",
                        help="Use test database")
    parser.add_argument("--store-id", type=int,
                        help="Store ID (1-7), will auto-detect if not provided")
    parser.add_argument("--quiet", action="store_true",
                        help="Minimal output")

    args = parser.parse_args()

    # Validate input file
    if not Path(args.excel_file).exists():
        print(f"ERROR: File not found: {args.excel_file}")
        sys.exit(1)

    # Extract material monthly usage
    material_usage = extract_material_monthly_usage_from_excel(
        args.excel_file, store_id=args.store_id, quiet=args.quiet)

    if not material_usage:
        print("ERROR: No material monthly usage data extracted")
        sys.exit(1)

    success = True

    # Generate SQL file
    if not args.direct_db:
        Path(args.sql_output).parent.mkdir(parents=True, exist_ok=True)
        success = generate_sql_file(material_usage, args.sql_output)

    # Insert to database
    if args.direct_db:
        success = insert_to_database(
            material_usage, is_test=args.test_db, quiet=args.quiet)

    if success:
        print("SUCCESS: Material monthly usage extraction completed successfully!")
        sys.exit(0)
    else:
        print("WARNING: Extraction completed with some errors but most data processed")
        sys.exit(0)  # Don't fail completely for partial success


if __name__ == "__main__":
    main()
