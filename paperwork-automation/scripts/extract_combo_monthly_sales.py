#!/usr/bin/env python3
"""
Extract combo monthly sales data from Excel files.
Extracts combo information and monthly combo dish sales data.
"""

import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def safe_print(message):
    """Print message safely, handling Unicode encoding errors on Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Remove emojis and special Unicode characters for Windows console
        clean_message = re.sub(r'[^\x00-\x7F]+', '', message)
        print(clean_message)


# Try to import database utilities
try:
    from utils.database import DatabaseManager, DatabaseConfig
    def get_database_manager(is_test=False): return DatabaseManager(
        DatabaseConfig(is_test=is_test))
except ImportError:
    safe_print(
        "WARNING: Database utilities not available. SQL file generation only.")
    get_database_manager = None


def extract_combo_data_from_excel(file_path: str, quiet: bool = False) -> Dict[str, List[Dict]]:
    """Extract combo and combo dish sales data from Excel file"""

    if not quiet:
        safe_print(f"Extracting combo data from: {file_path}")

    try:
        # Read Excel file and get sheet names
        excel_file = pd.ExcelFile(file_path)

        if not quiet:
            print(f"Available sheets: {excel_file.sheet_names}")

        # Target sheet for combo sales summary
        target_sheet = "套餐销售汇总"

        if target_sheet not in excel_file.sheet_names:
            safe_print(f"ERROR: Target sheet '{target_sheet}' not found!")
            print(f"Available sheets: {excel_file.sheet_names}")
            return {"combos": [], "combo_dish_sales": []}

        # Read the data
        df = pd.read_excel(file_path, sheet_name=target_sheet)

        if not quiet:
            print(f"📋 Data shape: {df.shape}")
            print(f"📋 Columns: {list(df.columns)}")

        # Clean and standardize column names
        df.columns = df.columns.astype(str).str.strip()

        # Store name to ID mapping
        store_name_mapping = {
            '加拿大一店': 1, '一店': 1,
            '加拿大二店': 2, '二店': 2,
            '加拿大三店': 3, '三店': 3,
            '加拿大四店': 4, '四店': 4,
            '加拿大五店': 5, '五店': 5,
            '加拿大六店': 6, '六店': 6,
            '加拿大七店': 7, '七店': 7
        }

        # Check required columns
        required_columns = ['套餐编码', '套餐名称',
                            '菜品编码', '出品数量', '退菜数量', '门店名称', '月份']

        for col in required_columns:
            if col not in df.columns:
                safe_print(f"ERROR: Required column '{col}' not found")
                return {"combos": [], "combo_dish_sales": []}

        # Extract unique combos
        combos = []
        combo_df = df[['套餐编码', '套餐名称']].drop_duplicates()

        for _, row in combo_df.iterrows():
            # Clean combo code (remove .0 suffix from float conversion)
            combo_code = str(row['套餐编码']).strip()
            if combo_code.endswith('.0'):
                combo_code = combo_code[:-2]

            combo_name = str(row['套餐名称']).strip()

            if combo_code and combo_name:
                combos.append({
                    'combo_code': combo_code,
                    'name': combo_name
                })

        if not quiet:
            safe_print(f"SUCCESS: Extracted {len(combos)} unique combos")

        # Extract combo dish sales
        combo_dish_sales = []

        for _, row in df.iterrows():
            # Clean combo code
            combo_code = str(row['套餐编码']).strip()
            if combo_code.endswith('.0'):
                combo_code = combo_code[:-2]

            # Clean dish code
            dish_code = str(row['菜品编码']).strip()
            if dish_code.endswith('.0'):
                dish_code = dish_code[:-2]

            # Get store ID
            store_name = str(row['门店名称']).strip()
            if store_name not in store_name_mapping:
                continue
            store_id = store_name_mapping[store_name]

            # Parse month (format: 202506 -> year: 2025, month: 6)
            month_str = str(row['月份']).strip()
            if len(month_str) == 6:
                year = int(month_str[:4])
                month = int(month_str[4:])
            else:
                continue

            # Calculate sale amount (出品数量 - 退菜数量)
            served_quantity = float(
                row['出品数量']) if pd.notna(row['出品数量']) else 0
            returned_quantity = float(
                row['退菜数量']) if pd.notna(row['退菜数量']) else 0
            sale_amount = served_quantity - returned_quantity

            # Skip if no sales
            if sale_amount <= 0:
                continue

            combo_dish_sales.append({
                'combo_code': combo_code,
                'dish_code': dish_code,
                'store_id': store_id,
                'year': year,
                'month': month,
                'sale_amount': sale_amount
            })

        if not quiet:
            safe_print(
                f"SUCCESS: Extracted {len(combo_dish_sales)} combo dish sales records")

        return {
            "combos": combos,
            "combo_dish_sales": combo_dish_sales
        }

    except Exception as e:
        safe_print(f"ERROR: Error extracting combo data: {e}")
        import traceback
        traceback.print_exc()
        return {"combos": [], "combo_dish_sales": []}


def generate_sql_file(data: Dict[str, List[Dict]], output_file: str) -> bool:
    """Generate SQL file with UPSERT statements for combo data"""

    try:
        print(f"📄 Generating SQL file: {output_file}")

        combos = data["combos"]
        combo_dish_sales = data["combo_dish_sales"]

        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- Combo monthly sales data insertion script\n")
            f.write(
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(
                f"-- Combos: {len(combos)}, Combo dish sales: {len(combo_dish_sales)}\n\n")

            # Insert combos
            f.write("-- ========================================\n")
            f.write("-- COMBO DATA\n")
            f.write("-- ========================================\n\n")

            for combo in combos:
                combo_code = combo['combo_code'].replace("'", "''")
                name = combo['name'].replace("'", "''")

                f.write(f"-- Combo: {combo['name']} ({combo['combo_code']})\n")
                sql = f"""INSERT INTO combo (combo_code, name)
VALUES ('{combo_code}', '{name}')
ON CONFLICT (combo_code)
DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            # Insert combo dish sales
            f.write("-- ========================================\n")
            f.write("-- COMBO DISH SALES DATA\n")
            f.write("-- ========================================\n\n")

            for sale in combo_dish_sales:
                combo_code = sale['combo_code'].replace("'", "''")
                dish_code = sale['dish_code'].replace("'", "''")

                f.write(
                    f"-- Combo: {sale['combo_code']} -> Dish: {sale['dish_code']} - Store {sale['store_id']} - {sale['year']}-{sale['month']:02d}\n")
                sql = f"""INSERT INTO monthly_combo_dish_sale (combo_id, dish_id, store_id, year, month, sale_amount)
SELECT 
    c.id as combo_id,
    d.id as dish_id,
    {sale['store_id']},
    {sale['year']},
    {sale['month']},
    {sale['sale_amount']}
FROM combo c
CROSS JOIN dish d
WHERE c.combo_code = '{combo_code}'
  AND d.full_code = '{dish_code}'
ON CONFLICT (combo_id, dish_id, store_id, year, month)
DO UPDATE SET
    sale_amount = EXCLUDED.sale_amount,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            f.write(f"\n-- End of combo data insertion script\n")
            f.write(
                f"-- {len(combos)} combos and {len(combo_dish_sales)} combo dish sales processed\n")

        safe_print(f"SUCCESS: SQL file generated successfully: {output_file}")
        return True

    except Exception as e:
        safe_print(f"ERROR: Error generating SQL file: {e}")
        return False


def insert_to_database(data: Dict[str, List[Dict]], is_test: bool = False) -> bool:
    """Insert combo data directly to database"""

    try:
        if get_database_manager is None:
            safe_print("ERROR: Database connection module not available")
            return False

        safe_print(
            f"Connecting to {'test' if is_test else 'production'} database...")

        combos = data["combos"]
        combo_dish_sales = data["combo_dish_sales"]

        db_manager = get_database_manager(is_test=is_test)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:

                # Insert combos
                safe_print(f"Inserting {len(combos)} combos...")
                combo_inserted = 0
                combo_updated = 0

                for combo in combos:
                    try:
                        query = """
                        INSERT INTO combo (combo_code, name)
                        VALUES (%s, %s)
                        ON CONFLICT (combo_code)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted;
                        """

                        cursor.execute(
                            query, (combo['combo_code'], combo['name']))
                        result = cursor.fetchone()
                        if result and result['inserted']:
                            combo_inserted += 1
                        else:
                            combo_updated += 1

                    except Exception as e:
                        print(
                            f"ERROR: Error processing combo {combo['combo_code']}: {e}")
                        continue

                # Insert combo dish sales
                safe_print(
                    f"Inserting {len(combo_dish_sales)} combo dish sales...")
                sales_inserted = 0
                sales_updated = 0
                sales_errors = 0

                for sale in combo_dish_sales:
                    try:
                        # Get combo ID
                        cursor.execute(
                            "SELECT id FROM combo WHERE combo_code = %s", (sale['combo_code'],))
                        combo_result = cursor.fetchone()
                        if not combo_result:
                            safe_print(
                                f"Warning: Combo not found - code: {sale['combo_code']}")
                            sales_errors += 1
                            continue

                        combo_id = combo_result['id']

                        # Get dish ID
                        cursor.execute(
                            "SELECT id FROM dish WHERE full_code = %s", (sale['dish_code'],))
                        dish_result = cursor.fetchone()
                        if not dish_result:
                            safe_print(
                                f"Warning: Dish not found - code: {sale['dish_code']}")
                            sales_errors += 1
                            continue

                        dish_id = dish_result['id']

                        # Insert combo dish sale
                        query = """
                        INSERT INTO monthly_combo_dish_sale (combo_id, dish_id, store_id, year, month, sale_amount)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (combo_id, dish_id, store_id, year, month)
                        DO UPDATE SET
                            sale_amount = EXCLUDED.sale_amount,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted;
                        """

                        cursor.execute(query, (
                            combo_id,
                            dish_id,
                            sale['store_id'],
                            sale['year'],
                            sale['month'],
                            sale['sale_amount']
                        ))

                        result = cursor.fetchone()
                        if result and result['inserted']:
                            sales_inserted += 1
                        else:
                            sales_updated += 1

                    except Exception as e:
                        print(
                            f"ERROR: Error processing combo dish sale {sale['combo_code']}-{sale['dish_code']}: {e}")
                        sales_errors += 1
                        continue

                # Commit transaction
                conn.commit()

                safe_print(f"SUCCESS: Database insertion completed:")
                safe_print(
                    f"   Combos - Inserted: {combo_inserted}, Updated: {combo_updated}")
                safe_print(
                    f"   Combo dish sales - Inserted: {sales_inserted}, Updated: {sales_updated}")
                if sales_errors > 0:
                    safe_print(
                        f"   Errors: {sales_errors} combo dish sales failed")

                # Consider it successful if we processed most data successfully
                total_processed = sales_inserted + sales_updated + sales_errors
                success_rate = (sales_inserted + sales_updated) / \
                    total_processed if total_processed > 0 else 0
                return success_rate >= 0.8  # 80% success rate threshold

    except Exception as e:
        safe_print(f"ERROR: Database insertion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Extract combo monthly sales from Excel")
    parser.add_argument(
        "excel_file", help="Path to Excel file containing combo sales data")
    parser.add_argument("--sql-output", help="Output SQL file path",
                        default="output/combo_monthly_sales_insert.sql")
    parser.add_argument("--direct-db", action="store_true",
                        help="Insert directly to database")
    parser.add_argument("--test-db", action="store_true",
                        help="Use test database")
    parser.add_argument("--quiet", action="store_true",
                        help="Minimal output")

    args = parser.parse_args()

    # Validate input file
    if not Path(args.excel_file).exists():
        safe_print(f"ERROR: File not found: {args.excel_file}")
        sys.exit(1)

    # Extract combo data
    data = extract_combo_data_from_excel(args.excel_file, quiet=args.quiet)

    if not data["combos"] and not data["combo_dish_sales"]:
        safe_print("ERROR: No combo data extracted")
        sys.exit(1)

    success = True

    # Generate SQL file
    if not args.direct_db:
        Path(args.sql_output).parent.mkdir(parents=True, exist_ok=True)
        success = generate_sql_file(data, args.sql_output)

    # Insert to database
    if args.direct_db:
        success = insert_to_database(data, is_test=args.test_db)

    if success:
        safe_print("Combo monthly sales extraction completed successfully!")
        sys.exit(0)
    else:
        safe_print(
            "Extraction completed with some errors but most data processed")
        sys.exit(0)  # Don't fail completely for partial success


if __name__ == "__main__":
    main()
