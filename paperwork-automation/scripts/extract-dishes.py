#!/usr/bin/env python3
"""
Extract dishes data from company system export and generate SQL or insert to database.
Handles dish_type, dish_child_type, and dish tables with proper relationships.
"""

import pandas as pd
import argparse
import sys
import os
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Try to import database utilities
try:
    import sys
    sys.path.append('.')
    from utils.database import get_database_manager, DatabaseConfig
    get_database_manager = get_database_manager
except ImportError:
    print("Database module not found. SQL file generation only.")
    get_database_manager = None

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def clean_dish_code(code):
    """Clean and validate dish code"""
    if pd.isna(code):
        return None

    # Convert to string and clean
    code_str = str(code).strip()

    # Remove .0 if it's a whole number (e.g., 90001690.0 -> 90001690)
    if code_str.endswith('.0'):
        code_str = code_str[:-2]

    return code_str if code_str and code_str != '-' else None


def escape_sql_string(value):
    """Escape string for SQL insertion"""
    if value is None:
        return 'NULL'

    # Escape single quotes and wrap in quotes
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def extract_dish_types_and_child_types(df: pd.DataFrame, quiet: bool = False) -> Tuple[List[Dict], List[Dict]]:
    """
    Extract unique dish types and child types from DataFrame

    Returns:
        Tuple of (dish_types, dish_child_types)
    """

    if not quiet:
        print("Extracting dish types and child types...")

    # Extract unique dish types
    dish_types = []
    unique_dish_types = df['大类名称'].dropna().unique()

    for i, dish_type_name in enumerate(sorted(unique_dish_types), 1):
        if dish_type_name.strip():  # Skip empty names
            dish_types.append({
                'name': dish_type_name.strip(),
                'sort_order': i * 10  # Leave gaps for future insertions
            })

    if not quiet:
        print(f"Found {len(dish_types)} unique dish types")

    # Extract unique child types with their parent relationships
    dish_child_types = []
    seen_combinations = set()

    for _, row in df.iterrows():
        dish_type_name = row['大类名称']
        child_type_name = row['子类名称']

        if pd.notna(dish_type_name) and pd.notna(child_type_name):
            dish_type_name = dish_type_name.strip()
            child_type_name = child_type_name.strip()

            # Skip empty names and '-' placeholders
            if not dish_type_name or not child_type_name or child_type_name == '-':
                continue

            combination = (dish_type_name, child_type_name)
            if combination not in seen_combinations:
                seen_combinations.add(combination)
                dish_child_types.append({
                    'name': child_type_name,
                    'dish_type_name': dish_type_name,  # We'll resolve this to ID later
                    'sort_order': len(dish_child_types) * 10
                })

    if not quiet:
        print(f"Found {len(dish_child_types)} unique dish child types")

    return dish_types, dish_child_types


def extract_dishes(df: pd.DataFrame, quiet: bool = False) -> List[Dict]:
    """
    Extract unique dishes from DataFrame

    Returns:
        List of dish dictionaries
    """

    if not quiet:
        print("Extracting dishes...")

    dishes = []
    seen_codes = set()

    for index, row in df.iterrows():
        # Extract and clean dish code (primary key)
        full_code = clean_dish_code(row['菜品编码'])

        if not full_code:
            if not quiet:
                print(f"Skipping row {index + 1}: Missing dish code")
            continue

        # Extract size first
        size = row['规格'] if pd.notna(row['规格']) else ''

        # Create unique key with both code and size
        unique_key = f"{full_code}_{size}" if size else full_code

        # Skip duplicates (keep first occurrence)
        if unique_key in seen_codes:
            continue
        seen_codes.add(unique_key)

        # Extract other fields
        name = row['菜品名称(门店pad显示名称)'] if pd.notna(
            row['菜品名称(门店pad显示名称)']) else ''
        system_name = row['菜品名称(系统统一名称)'] if pd.notna(
            row['菜品名称(系统统一名称)']) else ''
        short_code = row['菜品短编码'] if pd.notna(row['菜品短编码']) else ''
        unit = row['菜品单位'] if pd.notna(row['菜品单位']) else '份'
        child_type_name = row['子类名称'] if pd.notna(row['子类名称']) else ''
        dish_type_name = row['大类名称'] if pd.notna(row['大类名称']) else ''

        # Validate required fields
        if not name.strip():
            if not quiet:
                print(f"Skipping dish {full_code}: Missing name")
            continue

        if not child_type_name.strip() or child_type_name == '-':
            if not quiet:
                print(f"Skipping dish {full_code}: Missing child type")
            continue

        # Clean short code
        if short_code == '-':
            short_code = ''

        dishes.append({
            'name': name.strip(),
            'system_name': system_name.strip() if system_name else name.strip(),
            'full_code': full_code,
            'short_code': short_code.strip(),
            'size': size.strip() if size else None,
            'dish_child_type_name': child_type_name.strip(),
            'dish_type_name': dish_type_name.strip(),
            'unit': unit.strip(),
            'serving_size_kg': 0.0,  # Default as requested
            'is_active': True
        })

    if not quiet:
        print(f"Processed {len(dishes)} unique dishes")

    return dishes


def generate_sql_file(dish_types: List[Dict], dish_child_types: List[Dict],
                      dishes: List[Dict], output_file: str) -> bool:
    """Generate SQL file with UPSERT statements for all dish-related data"""

    try:
        print(f"Generating SQL file: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- Dishes data insertion script\n")
            f.write(
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Dish types: {len(dish_types)}\n")
            f.write(f"-- Dish child types: {len(dish_child_types)}\n")
            f.write(f"-- Dishes: {len(dishes)}\n\n")

            # Insert dish types
            f.write("-- ========================================\n")
            f.write("-- DISH TYPES\n")
            f.write("-- ========================================\n\n")

            for dish_type in dish_types:
                name = escape_sql_string(dish_type['name'])
                sort_order = dish_type['sort_order']

                sql = f"""INSERT INTO dish_type (name, sort_order, is_active)
VALUES ({name}, {sort_order}, TRUE)
ON CONFLICT (name) 
DO UPDATE SET
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            # Insert dish child types
            f.write("-- ========================================\n")
            f.write("-- DISH CHILD TYPES\n")
            f.write("-- ========================================\n\n")

            for child_type in dish_child_types:
                name = escape_sql_string(child_type['name'])
                dish_type_name = escape_sql_string(
                    child_type['dish_type_name'])
                sort_order = child_type['sort_order']

                sql = f"""INSERT INTO dish_child_type (name, dish_type_id, sort_order, is_active)
VALUES (
    {name},
    (SELECT id FROM dish_type WHERE name = {dish_type_name}),
    {sort_order},
    TRUE
)
ON CONFLICT (dish_type_id, name) 
DO UPDATE SET
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            # Insert dishes
            f.write("-- ========================================\n")
            f.write("-- DISHES\n")
            f.write("-- ========================================\n\n")

            for dish in dishes:
                name = escape_sql_string(dish['name'])
                system_name = escape_sql_string(dish['system_name'])
                full_code = escape_sql_string(dish['full_code'])
                short_code = escape_sql_string(
                    dish['short_code']) if dish['short_code'] else 'NULL'
                child_type_name = escape_sql_string(
                    dish['dish_child_type_name'])
                dish_type_name = escape_sql_string(dish['dish_type_name'])
                unit = escape_sql_string(dish['unit'])
                serving_size_kg = dish['serving_size_kg']

                size = escape_sql_string(
                    dish['size']) if dish['size'] else 'NULL'

                sql = f"""INSERT INTO dish (name, system_name, full_code, short_code, size, dish_child_type_id, unit, serving_size_kg, is_active)
VALUES (
    {name},
    {system_name},
    {full_code},
    {short_code},
    {size},
    (SELECT dct.id FROM dish_child_type dct 
     JOIN dish_type dt ON dct.dish_type_id = dt.id 
     WHERE dct.name = {child_type_name} AND dt.name = {dish_type_name}),
    {unit},
    {serving_size_kg},
    TRUE
)
ON CONFLICT (full_code, size) 
DO UPDATE SET
    name = EXCLUDED.name,
    system_name = EXCLUDED.system_name,
    short_code = EXCLUDED.short_code,
    dish_child_type_id = EXCLUDED.dish_child_type_id,
    unit = EXCLUDED.unit,
    serving_size_kg = EXCLUDED.serving_size_kg,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            f.write(f"\n-- End of dishes insertion script\n")
            f.write(
                f"-- {len(dish_types)} dish types, {len(dish_child_types)} child types, {len(dishes)} dishes processed\n")

        print(f"SQL file generated successfully: {output_file}")
        return True

    except Exception as e:
        print(f"Error generating SQL file: {e}")
        import traceback
        traceback.print_exc()
        return False


def insert_to_database(dish_types: List[Dict], dish_child_types: List[Dict],
                       dishes: List[Dict], is_test: bool = False, quiet: bool = False) -> bool:
    """Insert dishes data directly to database"""

    try:
        if get_database_manager is None:
            if not quiet:
                print("Database connection module not available")
            return False

        if not quiet:
            print(
                f"Connecting to {'test' if is_test else 'production'} database...")

        db_manager = get_database_manager(is_test=is_test)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:

                # Step 1: Insert dish types
                if not quiet:
                    print(f"Inserting {len(dish_types)} dish types...")
                dish_type_inserted = 0
                dish_type_updated = 0

                for dish_type in dish_types:
                    query = """
                    INSERT INTO dish_type (name, sort_order, is_active)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) 
                    DO UPDATE SET
                        sort_order = EXCLUDED.sort_order,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) AS inserted;
                    """

                    cursor.execute(query, (
                        dish_type['name'],
                        dish_type['sort_order'],
                        True
                    ))

                    result = cursor.fetchone()
                    if result and result['inserted']:
                        dish_type_inserted += 1
                    else:
                        dish_type_updated += 1

                # Step 2: Insert dish child types
                if not quiet:
                    print(
                        f"Inserting {len(dish_child_types)} dish child types...")
                child_type_inserted = 0
                child_type_updated = 0

                for child_type in dish_child_types:
                    # First get the dish_type_id
                    cursor.execute(
                        "SELECT id FROM dish_type WHERE name = %s", (child_type['dish_type_name'],))
                    dish_type_result = cursor.fetchone()

                    if not dish_type_result:
                        if not quiet:
                            print(
                                f"Warning: Dish type '{child_type['dish_type_name']}' not found for child type '{child_type['name']}'")
                        continue

                    dish_type_id = dish_type_result['id']

                    query = """
                    INSERT INTO dish_child_type (name, dish_type_id, sort_order, is_active)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (dish_type_id, name) 
                    DO UPDATE SET
                        sort_order = EXCLUDED.sort_order,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) AS inserted;
                    """

                    cursor.execute(query, (
                        child_type['name'],
                        dish_type_id,
                        child_type['sort_order'],
                        True
                    ))

                    result = cursor.fetchone()
                    if result and result['inserted']:
                        child_type_inserted += 1
                    else:
                        child_type_updated += 1

                # Step 3: Insert dishes
                if not quiet:
                    print(f"Inserting {len(dishes)} dishes...")
                dishes_inserted = 0
                dishes_updated = 0

                for dish in dishes:
                    # Get the dish_child_type_id
                    cursor.execute("""
                        SELECT dct.id FROM dish_child_type dct 
                        JOIN dish_type dt ON dct.dish_type_id = dt.id 
                        WHERE dct.name = %s AND dt.name = %s
                    """, (dish['dish_child_type_name'], dish['dish_type_name']))

                    child_type_result = cursor.fetchone()

                    if not child_type_result:
                        if not quiet:
                            print(
                                f"Warning: Child type '{dish['dish_child_type_name']}' under '{dish['dish_type_name']}' not found for dish '{dish['name']}'")
                        continue

                    dish_child_type_id = child_type_result['id']

                    query = """
                    INSERT INTO dish (name, system_name, full_code, short_code, size, dish_child_type_id, unit, serving_size_kg, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (full_code, size) 
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        system_name = EXCLUDED.system_name,
                        short_code = EXCLUDED.short_code,
                        dish_child_type_id = EXCLUDED.dish_child_type_id,
                        unit = EXCLUDED.unit,
                        serving_size_kg = EXCLUDED.serving_size_kg,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) AS inserted;
                    """

                    cursor.execute(query, (
                        dish['name'],
                        dish['system_name'],
                        dish['full_code'],
                        dish['short_code'] if dish['short_code'] else None,
                        dish['size'],
                        dish_child_type_id,
                        dish['unit'],
                        dish['serving_size_kg'],
                        dish['is_active']
                    ))

                    result = cursor.fetchone()
                    if result and result['inserted']:
                        dishes_inserted += 1
                    else:
                        dishes_updated += 1

                # Commit the transaction
                conn.commit()

        if not quiet:
            print(f"Database insertion completed:")
            print(
                f"   Dish Types - Inserted: {dish_type_inserted}, Updated: {dish_type_updated}")
            print(
                f"   Child Types - Inserted: {child_type_inserted}, Updated: {child_type_updated}")
            print(
                f"   Dishes - Inserted: {dishes_inserted}, Updated: {dishes_updated}")
            print(
                f"   Total processed: {len(dish_types) + len(dish_child_types) + len(dishes)} records")

        return True

    except Exception as e:
        if not quiet:
            print(f"Database insertion failed: {e}")
            import traceback
            traceback.print_exc()
        return False


def extract_dishes_to_sql(input_file: str, output_file: str = None, debug: bool = False,
                          direct_db: bool = False, is_test: bool = False, quiet: bool = False) -> bool:
    """
    Main extraction function

    Args:
        input_file: Path to the Excel file
        output_file: Path to output SQL file (ignored if direct_db=True)
        debug: Generate CSV for debugging
        direct_db: Insert directly to database instead of generating SQL
        is_test: Use test database

    Returns:
        bool: Success status
    """

    try:
        if not quiet:
            print(f"Reading dishes data from: {input_file}")

        # Read the Excel file
        df = pd.read_excel(input_file, sheet_name=0)

        if not quiet:
            print(f"Found {len(df)} rows of dishes data")

        # Extract dish types, child types, and dishes
        dish_types, dish_child_types = extract_dish_types_and_child_types(
            df, quiet)
        dishes = extract_dishes(df, quiet)

        if not dish_types or not dishes:
            if not quiet:
                print("No valid data found")
            return False

        # Generate debug CSV if requested
        if debug:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Save dish types debug
            dish_types_file = f"output/dish_types_debug_{timestamp}.csv"
            dish_types_df = pd.DataFrame(dish_types)
            dish_types_df.to_csv(
                dish_types_file, index=False, encoding='utf-8-sig')
            print(f"🐛 Dish types debug CSV saved to: {dish_types_file}")

            # Save child types debug
            child_types_file = f"output/dish_child_types_debug_{timestamp}.csv"
            child_types_df = pd.DataFrame(dish_child_types)
            child_types_df.to_csv(
                child_types_file, index=False, encoding='utf-8-sig')
            print(f"🐛 Child types debug CSV saved to: {child_types_file}")

            # Save dishes debug
            dishes_file = f"output/dishes_debug_{timestamp}.csv"
            dishes_df = pd.DataFrame(dishes)
            dishes_df.to_csv(dishes_file, index=False, encoding='utf-8-sig')
            print(f"🐛 Dishes debug CSV saved to: {dishes_file}")

        # Handle direct database insertion
        if direct_db:
            return insert_to_database(dish_types, dish_child_types, dishes, is_test, quiet)

        # Generate SQL file
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"output/dishes_insert_{timestamp}.sql"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        success = generate_sql_file(
            dish_types, dish_child_types, dishes, output_file)

        if success:
            print(
                f"{len(dish_types)} dish types, {len(dish_child_types)} child types, {len(dishes)} dishes ready for insertion")

        return success

    except Exception as e:
        print(f"Error extracting dishes: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Extract dishes data from company system export and generate SQL or insert to database')
    parser.add_argument('input_file', help='Path to the dishes Excel file')
    parser.add_argument('--output', '-o', help='Path to the output SQL file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Generate CSV files for manual verification')
    parser.add_argument('--direct-db', action='store_true',
                        help='Insert directly to database instead of generating SQL files')
    parser.add_argument('--test-db', action='store_true',
                        help='Use test database (only with --direct-db)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress verbose output')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Input file not found: {args.input_file}")
        sys.exit(1)

    # Check if we should use direct database insertion
    direct_db_insert = args.direct_db or os.getenv(
        'DIRECT_DB_INSERT', 'false').lower() == 'true'
    is_test = args.test_db
    quiet = args.quiet

    if not quiet:
        if direct_db_insert:
            print("Direct database insertion mode enabled")
            if is_test:
                print("Using test database")
            else:
                print("Using production database")

        print(f"HAIDILAO DISHES EXTRACTION")
        print(f"Processing file...")
        print("=" * 60)

    # Extract dishes
    success = extract_dishes_to_sql(
        input_file=args.input_file,
        output_file=args.output,
        debug=args.debug,
        direct_db=direct_db_insert,
        is_test=is_test,
        quiet=quiet
    )

    if not quiet:
        print("=" * 60)

    if success:
        if quiet:
            print("Finished")
        else:
            print("Dishes extraction completed successfully!")
            if direct_db_insert:
                print("Dishes have been inserted/updated in the database")
            else:
                print("SQL file has been generated")
        sys.exit(0)
    else:
        if quiet:
            print("ERROR: Extraction failed")
        else:
            print("Dishes extraction failed. Check the error messages above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
