#!/usr/bin/env python3
"""
Extract dish monthly sales data from Excel files.
Extracts sale_amount, return_amount, free_meal_amount, gift_amount for each dish by month.
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
    print("⚠️  Database utilities not available. SQL file generation only.")
    get_database_manager = None


def detect_store_from_excel_headers(file_path: str) -> int:
    """Detect store ID from Excel file headers (ValA column with CA01, CA07, etc.)"""
    try:
        # Read Excel file (first few rows to check headers)
        excel_file = pd.ExcelFile(file_path)

        # Try to find the dish sales sheet
        target_sheets = ['销售统计', '菜品销售', '月度销售', '销售数据']
        sheet_name = None

        for potential_sheet in target_sheets:
            if potential_sheet in excel_file.sheet_names:
                sheet_name = potential_sheet
                break

        if not sheet_name:
            sheet_name = excel_file.sheet_names[0]

        df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)

        # Look for ValA column or similar patterns
        for col in df.columns:
            col_str = str(col).strip()

            # Check if this is the ValA column or contains store codes
            if 'ValA' in col_str or 'vala' in col_str.lower():
                # Get the first non-null value from this column
                for val in df[col].dropna():
                    val_str = str(val).strip().upper()

                    # Look for CA## pattern
                    import re
                    ca_match = re.search(r'CA0?(\d)', val_str)
                    if ca_match:
                        store_num = int(ca_match.group(1))
                        if 1 <= store_num <= 7:
                            print(
                                f"🏪 Detected store {store_num} from ValA column: {val_str}")
                            return store_num

            # Also check column values for CA## patterns
            else:
                for val in df[col].dropna():
                    val_str = str(val).strip().upper()
                    import re
                    ca_match = re.search(r'CA0?(\d)', val_str)
                    if ca_match:
                        store_num = int(ca_match.group(1))
                        if 1 <= store_num <= 7:
                            print(
                                f"🏪 Detected store {store_num} from column '{col}': {val_str}")
                            return store_num

        # If no ValA pattern found, fall back to filename detection
        return detect_store_from_filename(file_path)

    except Exception as e:
        print(f"⚠️  Error reading Excel headers for store detection: {e}")
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
    print(f"⚠️  Warning: Could not detect store from filename, defaulting to store 1")
    return 1


def extract_dish_monthly_sales_from_excel(file_path: str, store_id: int = None, quiet: bool = False) -> List[Dict]:
    """Extract dish monthly sales data from Excel file"""

    if not quiet:
        print(f"📊 Extracting dish monthly sales from: {file_path}")

    # Detect store if not provided
    if store_id is None:
        store_id = detect_store_from_excel_headers(file_path)
        if not quiet:
            print(f"🏪 Detected store_id: {store_id}")
    elif not quiet:
        print(f"🏪 Using provided store_id: {store_id}")

    try:
        # Read Excel file and get all sheet names
        excel_file = pd.ExcelFile(file_path)

        if not quiet:
            print(f"Available sheets: {excel_file.sheet_names}")

        # Try to find the monthly sales sheet
        target_sheets = ['销售统计', '菜品销售', '月度销售', '销售数据']
        sheet_name = None

        for potential_sheet in target_sheets:
            if potential_sheet in excel_file.sheet_names:
                sheet_name = potential_sheet
                break

        # If no predefined sheet found, use the first sheet
        if not sheet_name:
            sheet_name = excel_file.sheet_names[0]
            if not quiet:
                print(f"⚠️  Using first sheet: {sheet_name}")

        # Read the data
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        if not quiet:
            print(f"📋 Data shape: {df.shape}")
            print(f"📋 Columns: {list(df.columns)}")

        # Extract month and year from file name or data
        month, year = extract_month_year_from_filename(file_path)

        if not quiet:
            print(f"📅 Extracted period: {year}-{month:02d}")

        # Clean and standardize column names
        df.columns = df.columns.astype(str).str.strip()

        # Extract store info from each row if available
        store_from_data = None
        if '门店名称' in df.columns:
            # Map store names to IDs
            store_name_mapping = {
                '加拿大一店': 1, '一店': 1,
                '加拿大二店': 2, '二店': 2,
                '加拿大三店': 3, '三店': 3,
                '加拿大四店': 4, '四店': 4,
                '加拿大五店': 5, '五店': 5,
                '加拿大六店': 6, '六店': 6,
                '加拿大七店': 7, '七店': 7
            }
            if not quiet:
                unique_stores = df['门店名称'].unique()
                print(f"🏪 Stores found in data: {list(unique_stores)}")

        # Expected columns (with Chinese names and possible variations)
        column_mapping = {
            # Dish identification
            '菜品编码': 'dish_code',
            '菜品代码': 'dish_code',
            '编码': 'dish_code',
            'Code': 'dish_code',

            # Dish name
            '菜品名称': 'dish_name',
            '菜品名称(门店pad显示名称)': 'dish_name',
            '菜品名称(系统统一名称)': 'dish_name',
            '菜品': 'dish_name',
            '名称': 'dish_name',
            'Name': 'dish_name',

            # Store name
            '门店名称': 'store_name',
            '店铺名称': 'store_name',
            '门店': 'store_name',

            # Size/specification
            '规格': 'size',
            '尺寸': 'size',
            'Size': 'size',
            'Spec': 'size',

            # Sales quantities - 出品数量 will be handled separately for calculation
            '出品数量': 'original_sale_amount',  # Original sales amount for calculation

            # Return quantities
            '退菜数量': 'return_amount',
            '退菜': 'return_amount',
            '退货': 'return_amount',
            'Return': 'return_amount',

            # Free meal quantities
            '免单数量': 'free_meal_amount',
            '免费餐数量': 'free_meal_amount',
            '免费': 'free_meal_amount',
            '免费餐': 'free_meal_amount',
            'Free': 'free_meal_amount',

            # Gift quantities
            '赠菜数量': 'gift_amount',
            '赠送数量': 'gift_amount',
            '赠送': 'gift_amount',
            '礼品': 'gift_amount',
            'Gift': 'gift_amount'
        }

        # Map columns
        df_mapped = {}

        # Map all columns first
        for chinese_col, english_col in column_mapping.items():
            if chinese_col in df.columns:
                df_mapped[english_col] = df[chinese_col]

        # Add fallback for sale_amount if we don't have original_sale_amount
        if 'original_sale_amount' not in df_mapped:
            # Fallback to other sale amount columns
            sale_amount_columns = ['销售数量', '销售量', '销售', '实收数量', 'Sales']
            for col in sale_amount_columns:
                if col in df.columns:
                    df_mapped['sale_amount'] = df[col]
                    break

        if not df_mapped:
            print("❌ No recognizable columns found in the data")
            return []

        # Convert to DataFrame
        df_clean = pd.DataFrame(df_mapped)

        # Handle missing required columns
        required_columns = ['dish_code']

        # Check for sale amount data (either direct or calculated)
        has_sale_data = ('sale_amount' in df_clean.columns or
                         'original_sale_amount' in df_clean.columns)

        if not has_sale_data:
            print(
                "❌ No sale amount data found (need either 'sale_amount' or 'original_sale_amount')")
            return []

        for col in required_columns:
            if col not in df_clean.columns:
                print(f"❌ Required column '{col}' not found")
                return []

        # Fill missing optional columns with defaults
        optional_columns = {
            'dish_name': '',
            'size': '',
            'store_name': '',
            'return_amount': 0,
            'free_meal_amount': 0,
            'gift_amount': 0
        }

        for col, default_value in optional_columns.items():
            if col not in df_clean.columns:
                df_clean[col] = default_value

        # Clean and process data
        dish_sales = []

        for _, row in df_clean.iterrows():
            # Clean dish code (remove .0 suffix from float conversion)
            dish_code = str(row['dish_code']).strip()
            if dish_code.endswith('.0'):
                dish_code = dish_code[:-2]

            # Skip empty rows
            if not dish_code or dish_code in ['nan', 'NaN', '']:
                continue

            # Clean numeric values
            def clean_numeric(value):
                if pd.isna(value) or value == '' or value == '-':
                    return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0

            # Calculate sale_amount based on available data
            if 'original_sale_amount' in df_clean.columns:
                # Use 出品数量 - 退菜数量 calculation
                original_amount = clean_numeric(row['original_sale_amount'])
                return_amount = clean_numeric(row['return_amount'])
                sale_amount = original_amount - return_amount

                # Ensure sale_amount is not negative
                if sale_amount < 0:
                    sale_amount = 0.0
            else:
                # Use direct sale_amount
                sale_amount = clean_numeric(row['sale_amount'])
                return_amount = clean_numeric(row['return_amount'])

            free_meal_amount = clean_numeric(row['free_meal_amount'])
            gift_amount = clean_numeric(row['gift_amount'])

            # Skip if no sales data
            if sale_amount == 0 and return_amount == 0 and free_meal_amount == 0 and gift_amount == 0:
                continue

            # Determine store_id from store_name if available
            row_store_id = store_id  # Default to provided store_id
            if 'store_name' in df_clean.columns and row['store_name']:
                store_name = str(row['store_name']).strip()
                if store_name in store_name_mapping:
                    row_store_id = store_name_mapping[store_name]

            dish_sales.append({
                'dish_code': dish_code,
                'dish_name': str(row['dish_name']).strip(),
                'size': str(row['size']).strip() if row['size'] else '',
                'store_id': row_store_id,
                'month': month,
                'year': year,
                'sale_amount': sale_amount,
                'return_amount': return_amount,
                'free_meal_amount': free_meal_amount,
                'gift_amount': gift_amount
            })

        if not quiet:
            print(f"✅ Extracted {len(dish_sales)} dish monthly sales records")

        return dish_sales

    except Exception as e:
        print(f"❌ Error extracting dish monthly sales: {e}")
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
        f"⚠️  Could not extract date from filename, using current date: {now.year}-{now.month:02d}")
    return now.month, now.year


def generate_sql_file(dish_sales: List[Dict], output_file: str) -> bool:
    """Generate SQL file with UPSERT statements for dish monthly sales"""

    try:
        print(f"📄 Generating SQL file: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- Dish monthly sales data insertion script\n")
            f.write(
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Records: {len(dish_sales)}\n\n")

            # Insert dish monthly sales
            f.write("-- ========================================\n")
            f.write("-- DISH MONTHLY SALES DATA\n")
            f.write("-- ========================================\n\n")

            for sale in dish_sales:
                dish_code = sale['dish_code'].replace("'", "''")
                size = sale['size'].replace(
                    "'", "''") if sale['size'] else 'NULL'

                # Create comment with readable info
                f.write(
                    f"-- Dish: {sale['dish_name']} ({sale['dish_code']}) - Store {sale['store_id']} - {sale['year']}-{sale['month']:02d}\n")

                sql = f"""INSERT INTO dish_monthly_sale (dish_id, store_id, month, year, sale_amount, return_amount, free_meal_amount, gift_amount, sales_mode)
SELECT 
    d.id as dish_id,
    {sale['store_id']},
    {sale['month']},
    {sale['year']},
    {sale['sale_amount']},
    {sale['return_amount']},
    {sale['free_meal_amount']},
    {sale['gift_amount']},
    'dine-in'
FROM dish d
WHERE d.full_code = '{dish_code}'
  AND (d.size = '{size}' OR (d.size IS NULL AND '{size}' = 'NULL'))
ON CONFLICT (dish_id, store_id, month, year, sales_mode)
DO UPDATE SET
    sale_amount = EXCLUDED.sale_amount,
    return_amount = EXCLUDED.return_amount,
    free_meal_amount = EXCLUDED.free_meal_amount,
    gift_amount = EXCLUDED.gift_amount,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            f.write(f"\n-- End of dish monthly sales insertion script\n")
            f.write(f"-- {len(dish_sales)} records processed\n")

        print(f"✅ SQL file generated successfully: {output_file}")
        return True

    except Exception as e:
        print(f"❌ Error generating SQL file: {e}")
        return False


def insert_to_database(dish_sales: List[Dict], is_test: bool = False) -> bool:
    """Insert dish monthly sales directly to database with proper aggregation"""

    try:
        if get_database_manager is None:
            print("❌ Database connection module not available")
            return False

        print(
            f"🗄️  Connecting to {'test' if is_test else 'production'} database...")

        db_manager = get_database_manager(is_test=is_test)

        # CRITICAL FIX: Pre-aggregate dish sales to handle multiple Excel rows for same dish
        print("🔄 Pre-aggregating dish sales data to handle multiple rows for same dish...")

        import pandas as pd

        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame(dish_sales)

        print(f"📊 Original data: {len(df)} records")

        # Group by dish+store+month+year and sum the quantities
        aggregation_keys = ['dish_code', 'size', 'store_id', 'month', 'year']
        sum_columns = ['sale_amount', 'return_amount',
                       'free_meal_amount', 'gift_amount']

        # Keep the first dish_name for each group
        df_other = df.groupby(aggregation_keys, as_index=False)[
            'dish_name'].first()

        # Sum the quantities
        df_aggregated = df.groupby(aggregation_keys, as_index=False)[
            sum_columns].sum()

        # Merge back together
        df_final = df_other.merge(df_aggregated, on=aggregation_keys)

        print(
            f"📊 After aggregation: {len(df_final)} unique dish records (was {len(df)} rows)")

        # Convert back to list of dictionaries
        dish_sales_aggregated = df_final.to_dict('records')

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:

                print(
                    f"📊 Inserting {len(dish_sales_aggregated)} aggregated dish monthly sales records...")
                inserted = 0
                updated = 0
                errors = 0

                for sale in dish_sales_aggregated:
                    try:
                        # Get dish ID
                        if sale['size']:
                            cursor.execute("""
                                SELECT id FROM dish 
                                WHERE full_code = %s AND size = %s
                            """, (sale['dish_code'], sale['size']))
                        else:
                            cursor.execute("""
                                SELECT id FROM dish 
                                WHERE full_code = %s AND size IS NULL
                            """, (sale['dish_code'],))

                        dish_result = cursor.fetchone()
                        if not dish_result:
                            print(
                                f"⚠️  Warning: Dish not found - code: {sale['dish_code']}, size: {sale['size']}")
                            errors += 1
                            continue

                        dish_id = dish_result['id']

                        # Insert/update aggregated dish monthly sales
                        query = """
                        INSERT INTO dish_monthly_sale (dish_id, store_id, month, year, sale_amount, return_amount, free_meal_amount, gift_amount, sales_mode)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (dish_id, store_id, month, year, sales_mode)
                        DO UPDATE SET
                            sale_amount = EXCLUDED.sale_amount,
                            return_amount = EXCLUDED.return_amount,
                            free_meal_amount = EXCLUDED.free_meal_amount,
                            gift_amount = EXCLUDED.gift_amount,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted;
                        """

                        cursor.execute(query, (
                            dish_id,
                            sale['store_id'],
                            sale['month'],
                            sale['year'],
                            sale['sale_amount'],
                            sale['return_amount'],
                            sale['free_meal_amount'],
                            sale['gift_amount'],
                            'dine-in'
                        ))

                        result = cursor.fetchone()
                        if result and result['inserted']:
                            inserted += 1
                        else:
                            updated += 1

                    except Exception as e:
                        print(f"❌ Error inserting dish sale: {e}")
                        errors += 1
                        continue

                conn.commit()

                print(
                    f"✅ Database insertion completed: {inserted} inserted, {updated} updated, {errors} errors")

                if errors > 0:
                    print(
                        f"⚠️  {errors} records had errors but most data was processed successfully")

                return errors == 0  # Return True only if no errors

    except Exception as e:
        print(f"❌ Database insertion failed: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Extract dish monthly sales from Excel")
    parser.add_argument(
        "excel_file", help="Path to Excel file containing dish sales data")
    parser.add_argument("--sql-output", help="Output SQL file path",
                        default="output/dish_monthly_sales_insert.sql")
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
        print(f"❌ File not found: {args.excel_file}")
        sys.exit(1)

    # Extract dish monthly sales
    dish_sales = extract_dish_monthly_sales_from_excel(
        args.excel_file, store_id=args.store_id, quiet=args.quiet)

    if not dish_sales:
        print("❌ No dish monthly sales data extracted")
        sys.exit(1)

    success = True

    # Generate SQL file
    if not args.direct_db:
        Path(args.sql_output).parent.mkdir(parents=True, exist_ok=True)
        success = generate_sql_file(dish_sales, args.sql_output)

    # Insert to database
    if args.direct_db:
        success = insert_to_database(dish_sales, is_test=args.test_db)

    if success:
        print("🎉 Dish monthly sales extraction completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Extraction completed with some errors but most data processed")
        sys.exit(0)  # Don't fail completely for partial success


if __name__ == "__main__":
    main()
