#!/usr/bin/env python3
"""
Data extraction functions for processing Excel files and generating SQL or inserting to database.
Consolidates logic from insert-data.py and extract-time-segments.py into reusable functions.
"""

from utils.database import get_database_manager
import pandas as pd
import os
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path for database imports
sys.path.append(str(Path(__file__).parent.parent))

# Fix encoding issues on Windows for Chinese characters
if sys.platform.startswith('win'):
    import codecs
    # Only redirect if not already redirected
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Suppress pandas warnings
warnings.filterwarnings('ignore')


def validate_excel_file(input_file):
    """
    Validate the Excel file format and structure.
    Returns (is_valid, warnings_list)
    """
    validation_warnings = []
    is_valid = True

    try:
        # Check if file exists
        if not os.path.exists(input_file):
            validation_warnings.append(f"ERROR: File not found: {input_file}")
            return False, validation_warnings

        # Check file extension
        if not input_file.lower().endswith(('.xlsx', '.xls')):
            validation_warnings.append(
                f"WARNING: Unexpected file extension: {os.path.splitext(input_file)[1]}")

        # Try to read Excel file and get sheet names
        try:
            excel_file = pd.ExcelFile(input_file)
            sheet_names = excel_file.sheet_names
        except Exception as e:
            validation_warnings.append(
                f"ERROR: Cannot read Excel file: {str(e)}")
            return False, validation_warnings

        # Check for traditional required sheets first
        required_sheets = ['营业基础表', '分时段基础表']
        missing_sheets = []

        for sheet in required_sheets:
            if sheet not in sheet_names:
                missing_sheets.append(sheet)

        # If traditional sheets are missing, check for new format
        if missing_sheets:
            # Check if this is a single-purpose file (daily or time segment)
            first_sheet = sheet_names[0] if sheet_names else None

            if first_sheet:
                if '日报' in first_sheet and '不含税' in first_sheet:
                    # Daily report format detected - this is fine
                    is_valid = True
                elif '分时段' in first_sheet and '不含税' in first_sheet:
                    # Time segment format detected - this is fine
                    is_valid = True
                else:
                    validation_warnings.append(
                        f"WARNING: Unknown format, will attempt to use first sheet: {first_sheet}")

                is_valid = True
            else:
                validation_warnings.append(
                    f"ERROR: No sheets found in Excel file")
                is_valid = False

        # Validate the appropriate sheet based on what we found (silently)
        if '营业基础表' in sheet_names:
            daily_warnings = validate_daily_sheet(excel_file, '营业基础表')
            # Only add critical errors
            critical_warnings = [w for w in daily_warnings if "ERROR" in w]
            validation_warnings.extend(critical_warnings)
        elif sheet_names and ('日报' in sheet_names[0] and '不含税' in sheet_names[0]):
            daily_warnings = validate_daily_sheet(excel_file, sheet_names[0])
            # Only add critical errors
            critical_warnings = [w for w in daily_warnings if "ERROR" in w]
            validation_warnings.extend(critical_warnings)

        if '分时段基础表' in sheet_names:
            time_warnings = validate_time_segment_sheet(excel_file, '分时段基础表')
            # Only add critical errors
            critical_warnings = [w for w in time_warnings if "ERROR" in w]
            validation_warnings.extend(critical_warnings)
        elif sheet_names and ('分时段' in sheet_names[0] and '不含税' in sheet_names[0]):
            time_warnings = validate_time_segment_sheet(
                excel_file, sheet_names[0])
            # Only add critical errors
            critical_warnings = [w for w in time_warnings if "ERROR" in w]
            validation_warnings.extend(critical_warnings)

        excel_file.close()

    except Exception as e:
        validation_warnings.append(
            f"ERROR: Unexpected error during validation: {str(e)}")
        is_valid = False

    return is_valid, validation_warnings


def validate_daily_sheet(excel_file, sheet_name='营业基础表'):
    """Validate the daily report sheet format."""
    warnings_list = []

    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Expected columns for daily reports - be more flexible
        expected_columns = [
            '门店名称', '日期', '节假日', '营业桌数', '营业桌数(考核)',
            '翻台率(考核)', '营业收入(不含税)', '营业桌数(考核)(外卖)',
            '就餐人数', '优惠总金额(不含税)'
        ]

        # Check if DataFrame is empty
        if df.empty:
            warnings_list.append(f"ERROR: {sheet_name} sheet is empty")
            return warnings_list

        # Check for required columns - only report missing critical ones
        missing_columns = []
        for col in expected_columns:
            if col not in df.columns:
                missing_columns.append(col)

        if len(missing_columns) > 5:  # Only report if many columns are missing
            warnings_list.append(
                f"ERROR: {sheet_name} missing many expected columns")

        # Validate date format if column exists
        date_column = None
        for col in df.columns:
            if '日期' in col:
                date_column = col
                break

        if date_column:
            date_issues = validate_date_column(df[date_column], sheet_name)
            # Only add critical date issues
            critical_issues = [
                issue for issue in date_issues if "ERROR" in issue]
            warnings_list.extend(critical_issues)

    except Exception as e:
        warnings_list.append(f"ERROR: Error validating {sheet_name}: {str(e)}")

    return warnings_list


def validate_time_segment_sheet(excel_file, sheet_name='分时段基础表'):
    """Validate the time segment sheet format."""
    warnings_list = []

    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Expected columns for time segments - be more flexible
        expected_columns = [
            '门店名称', '日期', '分时段', '节假日', '营业桌数(考核)', '翻台率(考核)'
        ]

        # Check if DataFrame is empty
        if df.empty:
            warnings_list.append(f"ERROR: {sheet_name} sheet is empty")
            return warnings_list

        # Check for required columns - only report missing critical ones
        missing_columns = []
        for col in expected_columns:
            if col not in df.columns:
                missing_columns.append(col)

        if len(missing_columns) > 3:  # Only report if many columns are missing
            warnings_list.append(
                f"ERROR: {sheet_name} missing many expected columns")

    except Exception as e:
        warnings_list.append(f"ERROR: Error validating {sheet_name}: {str(e)}")

    return warnings_list


def validate_date_column(date_series, sheet_name):
    """Validate date column format and content."""
    warnings_list = []

    try:
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(date_series):
            try:
                date_series = pd.to_datetime(date_series, errors='coerce')
            except Exception:
                warnings_list.append(
                    f"ERROR: Cannot convert date column in {sheet_name} to datetime format")
                return warnings_list

        # Check for null dates
        null_dates = date_series.isnull().sum()
        if null_dates > 0:
            warnings_list.append(
                f"ERROR: {null_dates} null/invalid dates found in {sheet_name}")

        # Skip date range validation - dates are typically fine

    except Exception as e:
        warnings_list.append(
            f"ERROR: Error validating dates in {sheet_name}: {str(e)}")

    return warnings_list


def validate_holiday_column(holiday_series, sheet_name):
    """Validate holiday column values."""
    warnings_list = []

    try:
        expected_values = ['工作日', '节假日']
        actual_values = holiday_series.dropna().unique().tolist()

        invalid_values = [
            val for val in actual_values if val not in expected_values]
        if invalid_values:
            warnings_list.append(
                f"⚠️  {sheet_name}: Invalid holiday values: {', '.join(map(str, invalid_values))}")
            warnings_list.append(
                f"   Expected values: {', '.join(expected_values)}")
        else:
            print(f"✅ {sheet_name} holiday values are correct")

    except Exception as e:
        warnings_list.append(
            f"❌ Error validating holiday column in {sheet_name}: {str(e)}")

    return warnings_list


def validate_numeric_column(numeric_series, column_name, sheet_name):
    """Validate numeric column for reasonable values."""
    warnings_list = []

    try:
        # Check for non-numeric values
        non_numeric_count = 0
        for val in numeric_series:
            if pd.notna(val):
                try:
                    float(val)
                except (ValueError, TypeError):
                    non_numeric_count += 1

        if non_numeric_count > 0:
            warnings_list.append(
                f"⚠️  {sheet_name}.{column_name}: {non_numeric_count} non-numeric values found")

        # Check for negative values where they shouldn't be
        if column_name in ['营业桌数', '营业桌数(考核)', '就餐人数']:
            negative_count = (numeric_series < 0).sum()
            if negative_count > 0:
                warnings_list.append(
                    f"⚠️  {sheet_name}.{column_name}: {negative_count} negative values found (should be positive)")

        # Check for extremely high values that might be data entry errors
        if column_name == '翻台率(考核)':
            high_turnover = (numeric_series > 10).sum()
            if high_turnover > 0:
                warnings_list.append(
                    f"⚠️  {sheet_name}.{column_name}: {high_turnover} values > 10 (unusually high turnover rate)")

    except Exception as e:
        warnings_list.append(
            f"❌ Error validating {column_name} in {sheet_name}: {str(e)}")

    return warnings_list


def safe_float_conversion(value):
    """Safely convert value to float, handling dashes and other non-numeric strings."""
    if pd.isna(value):
        return None

    # Convert to string to handle different data types
    str_value = str(value).strip()

    # Handle dash character (commonly used for missing/null data in Excel)
    if str_value == '-' or str_value == '':
        return None

    try:
        return float(str_value)
    except (ValueError, TypeError):
        # If conversion fails, return None instead of crashing
        return None


def transform_daily_report_data(df):
    """Transform Excel data from 营业基础表 sheet or aggregate time segment data into daily format."""
    # Store ID mapping
    store_ids = {
        '加拿大一店': 1,
        '加拿大二店': 2,
        '加拿大三店': 3,
        '加拿大四店': 4,
        '加拿大五店': 5,
        '加拿大六店': 6,
        '加拿大七店': 7,
        "加拿大八店": 8
    }

    # Check if this is time segment data (has '分时段' column)
    if '分时段' in df.columns:
        print("📊 Detected time segment data - aggregating into daily totals...")
        return aggregate_time_segment_to_daily(df, store_ids)

    # Original daily report processing
    transformed_data = []

    for _, row in df.iterrows():
        store_name = row['门店名称']

        if store_name not in store_ids:
            continue

        # Convert date from YYYYMMDD format to YYYY-MM-DD
        date_int = row['日期']
        try:
            # Convert to string and remove any decimal
            date_str = str(int(date_int))
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            formatted_date = f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, TypeError):
            # Skip rows with invalid date format silently
            continue

        # Map the data according to database schema using safe float conversion
        daily_data = {
            'store_id': store_ids[store_name],
            'date': formatted_date,
            'is_holiday': row['节假日'] == '节假日',  # True if holiday, False if 工作日
            'tables_served': safe_float_conversion(row['营业桌数']),
            'tables_served_validated': safe_float_conversion(row['营业桌数(考核)']),
            'turnover_rate': safe_float_conversion(row['翻台率(考核)']),
            'revenue_tax_not_included': safe_float_conversion(row['营业收入(不含税)']),
            'takeout_tables': safe_float_conversion(row['营业桌数(考核)(外卖)']),
            'customers': safe_float_conversion(row['就餐人数']),
            'discount_total': safe_float_conversion(row['优惠总金额(不含税)']),
            # Takeout revenue from daily store report (replaces separate takeout_report folder)
            'takeout_revenue': safe_float_conversion(row.get('营业收入(外卖)(不含税)', 0))
        }

        transformed_data.append(daily_data)

    return transformed_data


def aggregate_time_segment_to_daily(df, store_ids):
    """Aggregate time segment data into daily totals for each store."""
    # Group by store and date to aggregate time segments
    daily_aggregated = {}

    for _, row in df.iterrows():
        store_name = row['门店名称']

        if store_name not in store_ids:
            continue

        # Convert date from YYYYMMDD format to YYYY-MM-DD
        date_int = row['日期']
        try:
            date_str = str(int(date_int))
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            formatted_date = f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, TypeError):
            continue

        # Create unique key for store-date combination
        key = (store_ids[store_name], formatted_date)

        if key not in daily_aggregated:
            daily_aggregated[key] = {
                'store_id': store_ids[store_name],
                'date': formatted_date,
                'is_holiday': row['节假日'] == '节假日',
                'tables_served': 0,
                'tables_served_validated': 0,
                'revenue_tax_not_included': 0,
                'takeout_tables': 0,
                'customers': 0,
                'discount_total': 0,
                # Store available seats for turnover calculation
                'available_seats': safe_float_conversion(row['所有餐位数']) or 53
            }

        # Aggregate numeric values (sum most fields)
        daily_aggregated[key]['tables_served'] += safe_float_conversion(
            row['营业桌数']) or 0
        daily_aggregated[key]['tables_served_validated'] += safe_float_conversion(
            row['营业桌数(考核)']) or 0
        daily_aggregated[key]['revenue_tax_not_included'] += safe_float_conversion(
            row['营业收入(不含税)']) or 0
        daily_aggregated[key]['takeout_tables'] += safe_float_conversion(
            row['营业桌数(考核)(外卖)']) or 0
        daily_aggregated[key]['customers'] += safe_float_conversion(
            row['就餐人数']) or 0
        daily_aggregated[key]['discount_total'] += safe_float_conversion(
            row['优惠总金额(不含税)']) or 0

    # Convert to list and calculate correct turnover rates
    transformed_data = []
    for key, data in daily_aggregated.items():
        # Calculate turnover rate correctly: Total tables / Available seats
        available_seats = data['available_seats']
        total_tables_validated = data['tables_served_validated']

        if available_seats > 0:
            data['turnover_rate'] = total_tables_validated / available_seats
        else:
            data['turnover_rate'] = 0

        # Remove helper field
        del data['available_seats']

        transformed_data.append(data)

        # Debug output for first few records
        if len(transformed_data) <= 3:
            print(
                f"   🔄 Aggregated {data['store_id']} on {data['date']}: {data['tables_served_validated']:.1f} tables, {data['turnover_rate']:.3f} turnover")

    print(
        f"✅ Aggregated {len(transformed_data)} daily records from time segment data")
    return transformed_data


def transform_time_segment_data(df):
    """Transform Excel data from 分时段基础表 sheet into the format needed for database insertion."""
    # Store ID mapping
    store_ids = {
        '加拿大一店': 1,
        '加拿大二店': 2,
        '加拿大三店': 3,
        '加拿大四店': 4,
        '加拿大五店': 5,
        '加拿大六店': 6,
        '加拿大七店': 7,
        "加拿大八店": 8
    }

    # Time segment ID mapping
    time_segment_ids = {
        '08:00-13:59': 1,
        '14:00-16:59': 2,
        '17:00-21:59': 3,
        '22:00-(次)07:59': 4
    }

    transformed_data = []

    # Process ALL rows in the dataframe (all dates and time segments)
    for _, row in df.iterrows():
        store_name = row['门店名称']
        time_segment_label = row['分时段']

        if store_name not in store_ids:
            continue

        if time_segment_label not in time_segment_ids:
            # Skip unknown time segments silently (e.g., '-' or empty values)
            continue

        # Convert date from YYYYMMDD format to YYYY-MM-DD
        date_int = row['日期']
        try:
            # Convert to string and remove any decimal
            date_str = str(int(date_int))
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            formatted_date = f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, TypeError):
            # Skip rows with invalid date format silently
            continue

        # Map the data according to database schema using safe float conversion
        time_segment_data = {
            'store_id': store_ids[store_name],
            'date': formatted_date,
            'time_segment_id': time_segment_ids[time_segment_label],
            'is_holiday': row['节假日'] == '节假日',  # True if holiday, False if 工作日
            'tables_served_validated': safe_float_conversion(row['营业桌数(考核)']),
            'turnover_rate': safe_float_conversion(row['翻台率(考核)'])
        }

        transformed_data.append(time_segment_data)

    return transformed_data


def generate_upsert_sql(data, table_name, columns):
    """Generate SQL UPSERT statement (INSERT ... ON CONFLICT) from transformed data."""
    if not data:
        return ""

    # Generate update columns for ON CONFLICT based on table type
    if table_name == 'daily_report':
        conflict_keys = ['store_id', 'date']
    elif table_name == 'store_time_report':
        conflict_keys = ['store_id', 'date', 'time_segment_id']
    else:
        conflict_keys = ['store_id', 'date']  # Default

    # Deduplicate data based on conflict keys to prevent "ON CONFLICT DO UPDATE command cannot affect row a second time"
    seen_keys = set()
    deduplicated_data = []
    duplicate_count = 0

    for row in data:
        # Create a tuple of conflict key values for this row
        key_tuple = tuple(row.get(key) for key in conflict_keys)

        if key_tuple not in seen_keys:
            seen_keys.add(key_tuple)
            deduplicated_data.append(row)
        else:
            duplicate_count += 1

    if duplicate_count > 0:
        print(
            f"⚠️  Warning: Found {duplicate_count} duplicate records with same conflict keys, keeping only the first occurrence")

    # Generate column names for SQL
    column_names = ', '.join(columns)

    # Generate values for each deduplicated row
    values_list = []
    for row in deduplicated_data:
        values = []
        for col in columns:
            value = row.get(col)
            if value is None:
                values.append('NULL')
            elif isinstance(value, bool):
                values.append('True' if value else 'False')
            elif isinstance(value, str):
                values.append(f"'{value}'")
            else:
                values.append(str(value))
        values_list.append(f"  ({', '.join(values)})")

    update_columns = [col for col in columns if col not in conflict_keys]
    update_set = ', '.join(
        [f"{col} = EXCLUDED.{col}" for col in update_columns])

    # Combine into final UPSERT SQL with override behavior
    sql = f"-- UPSERT with override: Will INSERT new records or UPDATE existing ones\n"
    sql += f"-- Conflict resolution on: ({', '.join(conflict_keys)})\n"
    sql += f"INSERT INTO {table_name} ({column_names}) VALUES\n"
    sql += ',\n'.join(values_list)
    sql += f"\nON CONFLICT ({', '.join(conflict_keys)}) DO UPDATE SET\n  {update_set};"

    return sql


def extract_daily_reports(input_file, output_file=None, debug=False, direct_db=False, is_test=False):
    """Extract daily reports from Excel file and either generate SQL or insert to database."""
    try:
        # Determine which sheet to use
        excel_file = pd.ExcelFile(input_file)
        sheet_names = excel_file.sheet_names

        # Try traditional sheet name first
        if '营业基础表' in sheet_names:
            sheet_name = '营业基础表'
        elif sheet_names and ('日报' in sheet_names[0] and '不含税' in sheet_names[0]):
            sheet_name = sheet_names[0]
        else:
            # Fallback to first sheet
            sheet_name = sheet_names[0] if sheet_names else None

        if not sheet_name:
            print("ERROR: No suitable sheet found for daily reports")
            return False

        # Read Excel file from the determined sheet
        df = pd.read_excel(input_file, sheet_name=sheet_name)
        excel_file.close()

        # Transform data
        transformed_data = transform_daily_report_data(df)

        # Generate output directory for debug/SQL files
        output_dir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))), 'output')
        os.makedirs(output_dir, exist_ok=True)

        # Generate CSV for debug mode
        if debug:
            input_basename = os.path.splitext(os.path.basename(input_file))[0]
            csv_file = os.path.join(
                output_dir, f'debug_daily_reports_{input_basename}.csv')
            debug_df = pd.DataFrame(transformed_data)
            debug_df.to_csv(csv_file, index=False)

        if direct_db:
            # Insert directly to database
            success = insert_daily_data_to_database(transformed_data, is_test)
            return success
        else:
            # Generate UPSERT SQL
            columns = [
                'store_id', 'date', 'is_holiday', 'tables_served', 'tables_served_validated',
                'turnover_rate', 'revenue_tax_not_included', 'takeout_tables', 'customers', 'discount_total'
            ]
            sql = generate_upsert_sql(
                transformed_data, 'daily_report', columns)

            # Determine output file path
            if output_file:
                sql_file = output_file
            else:
                input_basename = os.path.splitext(
                    os.path.basename(input_file))[0]
                sql_file = os.path.join(
                    output_dir, f'daily_reports_{input_basename}.sql')

            # Write SQL to file
            with open(sql_file, 'w') as f:
                f.write(sql)

            return True

    except Exception as e:
        print(f"ERROR: Failed to extract daily reports - {e}")
        return False


def extract_time_segments(input_file, output_file=None, debug=False, direct_db=False, is_test=False):
    """Extract time segment data from Excel file and either generate SQL or insert to database."""
    try:
        # Determine which sheet to use
        excel_file = pd.ExcelFile(input_file)
        sheet_names = excel_file.sheet_names

        # Try traditional sheet name first
        if '分时段基础表' in sheet_names:
            sheet_name = '分时段基础表'
        elif sheet_names and ('分时段' in sheet_names[0] and '不含税' in sheet_names[0]):
            sheet_name = sheet_names[0]
        else:
            # Fallback to first sheet
            sheet_name = sheet_names[0] if sheet_names else None

        if not sheet_name:
            print("ERROR: No suitable sheet found for time segments")
            return False

        # Read Excel file from the determined sheet
        df = pd.read_excel(input_file, sheet_name=sheet_name)
        excel_file.close()

        # Transform data
        transformed_data = transform_time_segment_data(df)

        # Generate output directory for debug/SQL files
        output_dir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))), 'output')
        os.makedirs(output_dir, exist_ok=True)

        # Generate CSV for debug mode
        if debug:
            input_basename = os.path.splitext(os.path.basename(input_file))[0]
            csv_file = os.path.join(
                output_dir, f'debug_time_segments_{input_basename}.csv')
            debug_df = pd.DataFrame(transformed_data)
            debug_df.to_csv(csv_file, index=False)

        if direct_db:
            # Insert directly to database
            success = insert_time_data_to_database(transformed_data, is_test)
            return success
        else:
            # Generate UPSERT SQL
            columns = [
                'store_id', 'date', 'time_segment_id', 'is_holiday',
                'tables_served_validated', 'turnover_rate'
            ]
            sql = generate_upsert_sql(
                transformed_data, 'store_time_report', columns)

            # Determine output file path
            if output_file:
                sql_file = output_file
            else:
                input_basename = os.path.splitext(
                    os.path.basename(input_file))[0]
                sql_file = os.path.join(
                    output_dir, f'time_segments_{input_basename}.sql')

            # Write SQL to file
            with open(sql_file, 'w') as f:
                f.write(sql)

            return True

    except Exception as e:
        print(f"ERROR: Failed to extract time segments - {e}")
        return False


def save_discount_details(data, db_manager):
    """Save discount details to daily_discount_detail table"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get the ID for "其他优惠" (Other promotions) discount type
                cursor.execute("SELECT id FROM discount_type WHERE name = '其他优惠'")
                result = cursor.fetchone()
                if not result:
                    # Create the discount type if it doesn't exist
                    cursor.execute(
                        "INSERT INTO discount_type (name, description) VALUES (%s, %s) RETURNING id",
                        ('其他优惠', 'Other promotions')
                    )
                    discount_type_id = cursor.fetchone()['id']
                else:
                    discount_type_id = result['id']

                # Insert discount details
                inserted = 0
                for record in data:
                    if record.get('discount_total', 0) > 0:
                        cursor.execute("""
                            INSERT INTO daily_discount_detail
                            (store_id, date, discount_type_id, discount_amount, discount_count)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (store_id, date, discount_type_id) DO UPDATE
                            SET discount_amount = EXCLUDED.discount_amount,
                                discount_count = EXCLUDED.discount_count,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            record['store_id'],
                            record['date'],
                            discount_type_id,
                            record['discount_total'],
                            1  # Default count as we don't have detailed info
                        ))
                        inserted += 1

                conn.commit()
                print(f"   ✅ Saved {inserted} discount records")

    except Exception as e:
        print(f"   ⚠️  Error saving discount details: {e}")


def save_takeout_revenue(data, db_manager):
    """
    Save takeout revenue to daily_takeout_revenue table.

    Extracts takeout_revenue field from daily report data and inserts into
    the daily_takeout_revenue table. This replaces the standalone takeout_report
    folder extraction.
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                inserted = 0
                updated = 0

                for record in data:
                    takeout_revenue = record.get('takeout_revenue', 0)
                    # Only insert if there's actual revenue data
                    if takeout_revenue is None:
                        continue

                    cursor.execute("""
                        INSERT INTO daily_takeout_revenue (store_id, date, amount, currency)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, date) DO UPDATE SET
                            amount = EXCLUDED.amount,
                            currency = EXCLUDED.currency,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted
                    """, (
                        record['store_id'],
                        record['date'],
                        takeout_revenue,
                        'CAD'
                    ))

                    result = cursor.fetchone()
                    if result and (result.get('inserted', False) if isinstance(result, dict) else result[0]):
                        inserted += 1
                    else:
                        updated += 1

                conn.commit()
                print(f"   ✅ Takeout revenue: {inserted} new, {updated} updated")

    except Exception as e:
        print(f"   ⚠️  Error saving takeout revenue: {e}")


def insert_daily_data_to_database(data, is_test=False):
    """Insert daily report data directly to database with override capability"""
    try:
        db_manager = get_database_manager(is_test=is_test)

        # Test connection first
        if not db_manager.test_connection():
            print("ERROR: Database connection failed")
            return False

        if not data:
            print("No daily report data to insert")
            return True

        print(f"📊 Processing {len(data)} daily report records...")

        # Use individual inserts with better feedback
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                inserted_count = 0
                updated_count = 0

                for record in data:
                    try:
                        # Use UPSERT with RETURNING to know if it was insert or update
                        query = """
                        INSERT INTO daily_report (
                            store_id, date, is_holiday, tables_served, tables_served_validated,
                            turnover_rate, revenue_tax_not_included, takeout_tables, customers, discount_total
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (store_id, date) DO UPDATE SET
                            is_holiday = EXCLUDED.is_holiday,
                            tables_served = EXCLUDED.tables_served,
                            tables_served_validated = EXCLUDED.tables_served_validated,
                            turnover_rate = EXCLUDED.turnover_rate,
                            revenue_tax_not_included = EXCLUDED.revenue_tax_not_included,
                            takeout_tables = EXCLUDED.takeout_tables,
                            customers = EXCLUDED.customers,
                            discount_total = EXCLUDED.discount_total
                        RETURNING (xmax = 0) AS inserted;
                        """

                        cursor.execute(query, (
                            record['store_id'], record['date'], record['is_holiday'],
                            record['tables_served'], record['tables_served_validated'],
                            record['turnover_rate'], record['revenue_tax_not_included'],
                            record['takeout_tables'], record['customers'], record['discount_total']
                        ))

                        result = cursor.fetchone()
                        if result and result['inserted']:
                            inserted_count += 1
                        else:
                            updated_count += 1
                            print(
                                f"   🔄 Overrode existing data for store {record['store_id']}, date {record['date']}")

                    except Exception as e:
                        print(
                            f"ERROR: Failed to insert/update record for store {record['store_id']}, date {record['date']}: {e}")
                        return False

                conn.commit()

                print(f"✅ Daily report processing completed:")
                print(f"   📈 New records inserted: {inserted_count}")
                print(f"   🔄 Existing records updated: {updated_count}")
                
                # Save discount details
                if any(record.get('discount_total', 0) > 0 for record in data):
                    print("\n📊 Saving discount details...")
                    save_discount_details(data, db_manager)

                # Save takeout revenue (from daily store report)
                if any(record.get('takeout_revenue') is not None for record in data):
                    print("\n📦 Saving takeout revenue...")
                    save_takeout_revenue(data, db_manager)

                return True

    except Exception as e:
        print(f"ERROR: Database insertion failed - {e}")
        return False


def insert_time_data_to_database(data, is_test=False):
    """Insert time segment data directly to database with override capability"""
    try:
        db_manager = get_database_manager(is_test=is_test)

        # Test connection first
        if not db_manager.test_connection():
            print("ERROR: Database connection failed")
            return False

        if not data:
            print("No time segment data to insert")
            return True

        print(f"⏰ Processing {len(data)} time segment records...")

        # Use individual inserts with better feedback
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                inserted_count = 0
                updated_count = 0

                for record in data:
                    try:
                        # Use UPSERT with RETURNING to know if it was insert or update
                        query = """
                        INSERT INTO store_time_report (
                            store_id, date, time_segment_id, is_holiday,
                            tables_served_validated, turnover_rate
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (store_id, date, time_segment_id) DO UPDATE SET
                            is_holiday = EXCLUDED.is_holiday,
                            tables_served_validated = EXCLUDED.tables_served_validated,
                            turnover_rate = EXCLUDED.turnover_rate
                        RETURNING (xmax = 0) AS inserted;
                        """

                        cursor.execute(query, (
                            record['store_id'], record['date'], record['time_segment_id'],
                            record['is_holiday'], record['tables_served_validated'],
                            record['turnover_rate']
                        ))

                        result = cursor.fetchone()
                        if result and result['inserted']:
                            inserted_count += 1
                        else:
                            updated_count += 1
                            print(
                                f"   🔄 Overrode existing data for store {record['store_id']}, date {record['date']}, segment {record['time_segment_id']}")

                    except Exception as e:
                        print(
                            f"ERROR: Failed to insert/update record for store {record['store_id']}, date {record['date']}, segment {record['time_segment_id']}: {e}")
                        return False

                conn.commit()

                print(f"✅ Time segment processing completed:")
                print(f"   📈 New records inserted: {inserted_count}")
                print(f"   🔄 Existing records updated: {updated_count}")

                return True

    except Exception as e:
        print(f"ERROR: Database insertion failed - {e}")
        return False
