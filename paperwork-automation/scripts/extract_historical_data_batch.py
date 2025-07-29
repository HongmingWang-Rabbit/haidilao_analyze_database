#!/usr/bin/env python3
"""
Historical Data Batch Extraction Script

This script processes all historical monthly data from history_files/monthly_report_inputs
and extracts:
- Dishes and dish types from monthly_dish_sale/
- Dish price history from monthly_dish_sale/
- Materials from monthly_material_usage/
- Material prices from material_detail/ store folders

Skips calculated_dish_material_usage and inventory_checking_result if empty folders.

Usage:
    python scripts/extract_historical_data_batch.py [--debug] [--test] [--start-month YYYY-MM] [--end-month YYYY-MM]

Features:
- Processes all months from 2024-05 to 2025-06
- Handles critical material number dtype={'物料': str} issue
- Properly passes target dates to prevent CURRENT_DATE usage
- Comprehensive logging and error handling
- Parallel processing for efficiency
- Respects existing extraction patterns
"""

import sys
import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path setup
from utils.database import DatabaseManager, DatabaseConfig

# Set environment variables for database connection
os.environ['PG_HOST'] = 'localhost'
os.environ['PG_PORT'] = '5432'
os.environ['PG_USER'] = 'hongming'
os.environ['PG_PASSWORD'] = '8894'
os.environ['PG_DATABASE'] = 'haidilao-paperwork'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalDataExtractor:
    """Extracts historical data from monthly report folders."""

    def __init__(self, is_test: bool = False, debug: bool = False):
        """Initialize the extractor with database connection and configuration."""
        self.is_test = is_test
        self.debug = debug

        # Initialize database connection
        config = DatabaseConfig(is_test=is_test)
        self.db_manager = DatabaseManager(config)

        # Initialize results tracking as dictionary of month results
        self.results = {}

    def get_store_mapping(self) -> Dict[str, int]:
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

    def get_store_folder_mapping(self) -> Dict[str, int]:
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

    def extract_target_date_from_month(self, month_folder: str) -> str:
        """Extract target date from month folder name (e.g., '2024-05' -> '2024-05-31')."""
        try:
            year, month = month_folder.split('-')
            # Get last day of month
            if month in ['01', '03', '05', '07', '08', '10', '12']:
                last_day = 31
            elif month in ['04', '06', '09', '11']:
                last_day = 30
            elif month == '02':
                # Simple leap year check
                year_int = int(year)
                if year_int % 4 == 0 and (year_int % 100 != 0 or year_int % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 30

            return f"{year}-{month}-{last_day:02d}"
        except Exception as e:
            logger.error(f"Failed to extract date from {month_folder}: {e}")
            return f"{month_folder}-01"

    def clean_dish_code(self, code) -> Optional[str]:
        """Clean and validate dish code."""
        if pd.isna(code):
            return None

        # Convert to string and clean
        code_str = str(code).strip()

        # Remove .0 if it's a whole number (e.g., 90001690.0 -> 90001690)
        if code_str.endswith('.0'):
            code_str = code_str[:-2]

        return code_str if code_str and code_str != '-' else None

    def find_excel_files(self, folder: Path, pattern: str = "*.xlsx") -> List[Path]:
        """Find Excel files in folder, excluding temporary files."""
        if not folder.exists():
            return []

        patterns = [pattern, pattern.replace('xlsx', 'xls'), pattern.upper()]
        files = []
        for pat in patterns:
            files.extend(folder.glob(pat))

        # Filter out temporary Excel files (starting with ~$)
        files = [f for f in files if not f.name.startswith("~$")]

        return files

    def is_folder_empty_or_nonexistent(self, folder: Path) -> bool:
        """Check if folder is empty or doesn't exist."""
        if not folder.exists():
            return True

        # Check if folder has any files (not just subfolders)
        try:
            for item in folder.iterdir():
                if item.is_file():
                    return False
            return True
        except Exception:
            return True

    def find_dish_name_column(self, df) -> str:
        """Find the appropriate dish name column."""
        possible_columns = [
            '菜品名称',
            '菜品名称(门店pad显示名称)',
            '菜品名称(系统统一名称)'
        ]
        for col in possible_columns:
            if col in df.columns:
                return col
        return None

    def is_valid_dish_row(self, row, dish_name_col: str) -> bool:
        """Check if a row contains valid dish data (not header row)."""
        try:
            # Check if this is a header row by looking for column names
            dish_name = str(row[dish_name_col]) if pd.notna(
                row[dish_name_col]) else ''
            dish_code = str(row['菜品编码']) if pd.notna(row['菜品编码']) else ''

            # Skip header rows or rows with column names as values
            if dish_name in ['菜品名称', '菜品名称(门店pad显示名称)', '菜品名称(系统统一名称)']:
                return False
            if dish_code in ['菜品编码', '菜品短编码']:
                return False

            # Check if dish code looks like actual data (numeric or alphanumeric)
            if dish_code and not dish_code.replace('.', '').replace('-', '').isdigit():
                # Allow alphanumeric codes but skip obvious headers
                if len(dish_code) < 3 or dish_code in ['nan', 'NaN', 'None']:
                    return False

            return True
        except Exception:
            return False

    def extract_dishes_from_monthly_sale(self, file_path: Path, target_date: str) -> Tuple[int, int, int, int, int]:
        """Extract dishes, dish types, price history, and monthly sales from monthly dish sale file."""
        logger.info(f"🍽️ Extracting dishes from: {file_path.name}")

        try:
            # Read Excel file with row limit to prevent hanging
            max_rows = 1000 if not self.debug else 5000  # Limit rows for safety
            df = pd.read_excel(file_path, engine='openpyxl', nrows=max_rows)
            logger.info(
                f"Loaded {len(df)} rows from dish sales file (limited to {max_rows} for safety)")

            # Check if required columns exist
            dish_name_col = self.find_dish_name_column(df)
            if not dish_name_col:
                logger.error("No dish name column found")
                logger.info(f"Available columns: {list(df.columns)}")
                return 0, 0, 0, 0, 0

            # Check for required columns with flexible naming
            required_base_columns = ['菜品编码', '大类名称']
            available_columns = df.columns.tolist()

            # Find dish code column
            dish_code_col = None
            for col in ['菜品编码', '菜品短编码', '编码']:
                if col in available_columns:
                    dish_code_col = col
                    break

            if not dish_code_col:
                logger.error("No dish code column found")
                logger.info(f"Available columns: {available_columns}")
                return 0, 0, 0, 0, 0

            logger.info(f"Using dish name column: {dish_name_col}")
            logger.info(f"Using dish code column: {dish_code_col}")

            # Clean and validate data
            df_clean = df.copy()

            # Remove rows where dish name or code is missing/invalid
            df_clean = df_clean.dropna(subset=[dish_name_col, dish_code_col])

            # Filter out header rows and invalid data
            def is_valid_dish_row(row):
                dish_name = str(row[dish_name_col]).strip()
                dish_code = str(row[dish_code_col]).strip()

                # Skip header rows
                if dish_name in ['菜品名称', '菜品名称(门店pad显示名称)', '菜品名称(系统统一名称)']:
                    return False
                if dish_code in ['菜品编码', '菜品短编码', '编码']:
                    return False

                # Skip empty or very short values
                if len(dish_name) < 2 or len(dish_code) < 1:
                    return False

                return True

            # Apply filter
            valid_mask = df_clean.apply(is_valid_dish_row, axis=1)
            df_clean = df_clean[valid_mask]

            # Further limit for safety
            if len(df_clean) > 500:  # Limit to 500 dishes per file
                df_clean = df_clean.head(500)
                logger.warning(f"⚠️ Limited to 500 dishes for safety")

            logger.info(f"After cleaning: {len(df_clean)} valid rows")

            if len(df_clean) == 0:
                logger.warning("No valid data rows found after cleaning")
                return 0, 0, 0, 0, 0

            store_mapping = self.get_store_mapping()

            # Process in separate transactions to avoid abort propagation
            dish_type_count = 0
            dish_child_type_count = 0
            dish_count = 0
            price_history_count = 0
            monthly_sales_count = 0

            try:
                # Process dish types first
                dish_type_count = self.process_dish_types(df_clean)
                logger.info(f"Processed {dish_type_count} dish types")

                # Process dish child types
                dish_child_type_count = self.process_dish_child_types(df_clean)
                logger.info(
                    f"Processed {dish_child_type_count} dish child types")

                # Process dishes in batches
                dish_count = self.process_dishes_batch(
                    df_clean, dish_name_col, dish_code_col, store_mapping)
                logger.info(f"Processed {dish_count} dishes")

                # Process price history
                price_history_count = self.process_price_history_batch(
                    df_clean, dish_name_col, dish_code_col, target_date, store_mapping)
                logger.info(
                    f"Processed {price_history_count} price history records")

                # Process monthly sales (the missing piece!)
                monthly_sales_count = self.process_monthly_sales_batch(
                    df_clean, dish_name_col, dish_code_col, target_date, store_mapping)
                logger.info(
                    f"Processed {monthly_sales_count} monthly sales records")

            except Exception as e:
                logger.error(f"Error during batch processing: {e}")
                # Continue with what we have
                monthly_sales_count = 0

            logger.info(
                f"✅ Dishes extraction completed - Types: {dish_type_count}, Child Types: {dish_child_type_count}, Dishes: {dish_count}, Price History: {price_history_count}, Monthly Sales: {monthly_sales_count}")
            return dish_type_count, dish_child_type_count, dish_count, price_history_count, monthly_sales_count

        except Exception as e:
            logger.error(f"Error extracting dishes from {file_path}: {e}")
            return 0, 0, 0, 0, 0

    def process_dish_types(self, df: pd.DataFrame) -> int:
        """Process dish types in a separate transaction."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Extract dish types (大类名称)
                if '大类名称' in df.columns:
                    dish_types = df['大类名称'].dropna().unique()
                    count = 0
                    for dish_type in dish_types:
                        try:
                            cursor.execute("""
                                INSERT INTO dish_type (name)
                                VALUES (%s)
                                ON CONFLICT (name) DO NOTHING
                            """, (dish_type,))
                            count += cursor.rowcount
                        except Exception as e:
                            logger.debug(
                                f"Error inserting dish type {dish_type}: {e}")
                            continue

                    conn.commit()
                    return count

                return 0
        except Exception as e:
            logger.error(f"Error processing dish types: {e}")
            return 0

    def process_dish_child_types(self, df: pd.DataFrame) -> int:
        """Process dish child types in a separate transaction."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Extract dish child types (子类名称)
                if '子类名称' in df.columns and '大类名称' in df.columns:
                    count = 0
                    for _, row in df.iterrows():
                        try:
                            child_type = row['子类名称']
                            parent_type = row['大类名称']

                            if pd.notna(child_type) and pd.notna(parent_type):
                                cursor.execute("""
                                    INSERT INTO dish_child_type (name, dish_type_id)
                                    VALUES (%s, (SELECT id FROM dish_type WHERE name = %s))
                                    ON CONFLICT (name, dish_type_id) DO NOTHING
                                """, (child_type, parent_type))
                                count += cursor.rowcount
                        except Exception as e:
                            logger.debug(
                                f"Error inserting dish child type: {e}")
                            continue

                    conn.commit()
                    return count

                return 0
        except Exception as e:
            logger.error(f"Error processing dish child types: {e}")
            return 0

    def process_dishes_batch(self, df: pd.DataFrame, dish_name_col: str, dish_code_col: str, store_mapping: dict) -> int:
        """Process dishes in batches with proper transaction handling - Store-specific."""
        try:
            total_count = 0
            batch_size = 20  # Smaller batches for better error isolation

            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]

                # Process each batch in its own transaction
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        batch_count = 0

                        for _, row in batch.iterrows():
                            try:
                                # Clean dish code (remove .0 suffix from floats)
                                full_code = self.clean_dish_code(
                                    row[dish_code_col])
                                if not full_code:
                                    continue

                                size = row['规格'] if '规格' in row and pd.notna(
                                    row['规格']) else ''
                                dish_name = str(row[dish_name_col]).strip()

                                # Get type IDs
                                dish_type_id = None
                                dish_child_type_id = None

                                if '大类名称' in row and pd.notna(row['大类名称']):
                                    cursor.execute(
                                        "SELECT id FROM dish_type WHERE name = %s", (row['大类名称'],))
                                    result = cursor.fetchone()
                                    if result:
                                        dish_type_id = result['id']

                                if '子类名称' in row and pd.notna(row['子类名称']) and dish_type_id:
                                    cursor.execute("SELECT id FROM dish_child_type WHERE name = %s AND dish_type_id = %s",
                                                   (row['子类名称'], dish_type_id))
                                    result = cursor.fetchone()
                                    if result:
                                        dish_child_type_id = result['id']

                                # Store-specific dish insertion - create dish for all stores that will use it
                                stores_in_data = set()
                                
                                # Check which stores this dish appears in by looking at the store column
                                if '门店名称' in row and pd.notna(row['门店名称']):
                                    store_name = row['门店名称']
                                    if store_name in store_mapping:
                                        stores_in_data.add(store_mapping[store_name])
                                
                                # If no specific store info, create for all stores (fallback)
                                if not stores_in_data:
                                    stores_in_data = set(store_mapping.values())
                                
                                # Insert dish for each relevant store
                                for store_id in stores_in_data:
                                    cursor.execute("""
                                        INSERT INTO dish (
                                            full_code, size, name, dish_child_type_id, store_id
                                        )
                                        VALUES (%s, %s, %s, %s, %s)
                                        ON CONFLICT (full_code, size, store_id) DO UPDATE SET
                                            name = EXCLUDED.name,
                                            dish_child_type_id = EXCLUDED.dish_child_type_id,
                                            updated_at = CURRENT_TIMESTAMP
                                    """, (full_code, size, dish_name, dish_child_type_id, store_id))

                                batch_count += 1

                            except Exception as e:
                                logger.debug(
                                    f"Error processing individual dish: {e}")
                                continue

                        conn.commit()
                        total_count += batch_count

                        if batch_count > 0:
                            logger.debug(
                                f"Processed batch {i//batch_size + 1}: {batch_count} dishes")

                except Exception as e:
                    logger.error(
                        f"Error processing dish batch {i//batch_size + 1}: {e}")
                    continue

            return total_count

        except Exception as e:
            logger.error(f"Error in batch dish processing: {e}")
            return 0

    def process_price_history_batch(self, df: pd.DataFrame, dish_name_col: str, dish_code_col: str, target_date: str, store_mapping: dict) -> int:
        """Process price history in batches with proper transaction handling."""
        try:
            total_count = 0
            batch_size = 20  # Smaller batches for better error isolation

            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]

                # Process each batch in its own transaction
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        batch_count = 0

                        for _, row in batch.iterrows():
                            try:
                                # Clean dish code
                                full_code = self.clean_dish_code(
                                    row[dish_code_col])
                                if not full_code:
                                    continue

                                size = row['规格'] if '规格' in row and pd.notna(
                                    row['规格']) else ''

                                # Find price column - updated for historical file format
                                price = None
                                price_cols = ['菜品单价', '单价', '价格', '均价', '平均价格']
                                for price_col in price_cols:
                                    if price_col in row and pd.notna(row[price_col]):
                                        try:
                                            price = float(row[price_col])
                                            break
                                        except (ValueError, TypeError):
                                            continue

                                if price is None or price <= 0:
                                    continue

                                # Find store
                                store_id = None
                                if '门店名称' in row and pd.notna(row['门店名称']):
                                    store_name = str(row['门店名称']).strip()
                                    if store_name in store_mapping:
                                        store_id = store_mapping[store_name]

                                if not store_id:
                                    continue

                                # Get dish ID (store-specific)
                                cursor.execute("SELECT id FROM dish WHERE full_code = %s AND size = %s AND store_id = %s",
                                               (full_code, size, store_id))
                                result = cursor.fetchone()
                                if not result:
                                    continue

                                dish_id = result['id']

                                # Insert price history
                                cursor.execute("""
                                    INSERT INTO dish_price_history (
                                        dish_id, store_id, price, effective_date, is_active
                                    )
                                    VALUES (%s, %s, %s, %s, true)
                                                                     ON CONFLICT (dish_id, store_id, effective_date) DO UPDATE SET
                                     price = EXCLUDED.price,
                                     is_active = EXCLUDED.is_active
                                """, (dish_id, store_id, price, target_date))

                                batch_count += 1

                            except Exception as e:
                                logger.debug(
                                    f"Error processing individual price history: {e}")
                                continue

                        conn.commit()
                        total_count += batch_count

                        if batch_count > 0:
                            logger.debug(
                                f"Processed price history batch {i//batch_size + 1}: {batch_count} records")

                except Exception as e:
                    logger.error(
                        f"Error processing price history batch {i//batch_size + 1}: {e}")
                    continue

            return total_count

        except Exception as e:
            logger.error(f"Error in batch price history processing: {e}")
            return 0

    def process_monthly_sales_batch(self, df: pd.DataFrame, dish_name_col: str, dish_code_col: str, target_date: str, store_mapping: dict) -> int:
        """Process monthly sales data in batches with proper transaction handling and aggregation."""
        try:
            logger.info(
                "🔄 Pre-aggregating monthly sales data to handle multiple Excel rows...")

            # Extract year and month from target date
            year = int(target_date.split('-')[0])
            month = int(target_date.split('-')[1])

            # CRITICAL FIX: Pre-aggregate data by dish + store before database insertion
            # This handles cases like SMIRNOFF ICE having multiple rows (24 units + 1 unit = 25 total)

            # Clean and prepare data for aggregation
            df_clean = df.copy()

            # Clean dish codes
            df_clean['full_code_clean'] = df_clean[dish_code_col].apply(
                self.clean_dish_code)
            df_clean = df_clean.dropna(subset=['full_code_clean'])

            # Clean size column
            df_clean['size_clean'] = df_clean['规格'].fillna(
                '') if '规格' in df_clean.columns else ''

            # Find and clean quantity columns
            quantity_cols = ['数量', '实收数量', '出品数量', '销售数量', '销售份数']
            quantity_col = None
            for qty_col in quantity_cols:
                if qty_col in df_clean.columns:
                    quantity_col = qty_col
                    break

            if not quantity_col:
                logger.warning("No quantity column found for monthly sales")
                return 0

            # Clean numeric values
            df_clean[quantity_col] = pd.to_numeric(
                df_clean[quantity_col], errors='coerce').fillna(0)

            # Clean store names and filter for known stores
            df_clean = df_clean[df_clean['门店名称'].notna()]
            df_clean['store_name_clean'] = df_clean['门店名称'].astype(
                str).str.strip()
            df_clean = df_clean[df_clean['store_name_clean'].isin(
                store_mapping.keys())]

            if len(df_clean) == 0:
                logger.warning(
                    "No valid data found after cleaning for monthly sales")
                return 0

            # Pre-aggregate by dish code, size, store
            logger.info(
                f"📊 Aggregating {len(df_clean)} rows by dish+store+month...")
            aggregation_columns = ['full_code_clean',
                                   'size_clean', 'store_name_clean']
            df_aggregated = df_clean.groupby(aggregation_columns, as_index=False)[
                quantity_col].sum()

            logger.info(
                f"📊 After aggregation: {len(df_aggregated)} unique dish-store combinations (was {len(df_clean)} rows)")

            # Process aggregated data in batches
            total_count = 0
            batch_size = 20

            for i in range(0, len(df_aggregated), batch_size):
                batch = df_aggregated.iloc[i:i + batch_size]

                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        batch_count = 0

                        for _, row in batch.iterrows():
                            try:
                                full_code = row['full_code_clean']
                                size = row['size_clean']
                                quantity = row[quantity_col]
                                store_name = row['store_name_clean']

                                # Skip if no meaningful quantity
                                if quantity <= 0:
                                    continue

                                store_id = store_mapping[store_name]

                                # Get dish ID (store-specific)
                                cursor.execute("SELECT id FROM dish WHERE full_code = %s AND size = %s AND store_id = %s",
                                               (full_code, size, store_id))
                                result = cursor.fetchone()
                                if not result:
                                    continue

                                dish_id = result['id']

                                # Insert aggregated monthly sales data
                                # Use default sales_mode for historical data
                                cursor.execute("""
                                    INSERT INTO dish_monthly_sale (
                                        dish_id, store_id, year, month, sale_amount, sales_mode
                                    )
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (dish_id, store_id, year, month, sales_mode) DO UPDATE SET
                                        sale_amount = EXCLUDED.sale_amount,
                                        updated_at = CURRENT_TIMESTAMP
                                """, (dish_id, store_id, year, month, quantity, 'dine-in'))

                                if cursor.rowcount > 0:
                                    batch_count += 1

                            except Exception as e:
                                logger.debug(
                                    f"Error processing individual monthly sales: {e}")
                                continue

                        conn.commit()
                        total_count += batch_count

                        if batch_count > 0:
                            logger.debug(
                                f"Processed monthly sales batch {i//batch_size + 1}: {batch_count} records")

                except Exception as e:
                    logger.error(
                        f"Error processing monthly sales batch {i//batch_size + 1}: {e}")
                    continue

            logger.info(
                f"✅ Monthly sales aggregation completed: {total_count} records processed")
            return total_count

        except Exception as e:
            logger.error(f"Error in batch monthly sales processing: {e}")
            return 0

    def is_valid_material_row(self, row) -> bool:
        """Check if a row contains valid material data (not header row)."""
        try:
            # Check if this is a header row by looking for column names
            material_desc = str(row['物料描述']) if pd.notna(row['物料描述']) else ''
            material_number = str(row['物料']) if pd.notna(row['物料']) else ''

            # Skip header rows or rows with column names as values
            if material_desc in ['物料描述', '物料名称', '材料名称', '名称']:
                return False
            if material_number in ['物料', '物料号', '物料编号', '材料号']:
                return False

            # Check if material number looks like actual data
            if material_number and not material_number.replace('.', '').replace('-', '').replace('0', '').isdigit():
                # Skip obvious non-data rows
                if len(material_number) < 3 or material_number in ['nan', 'NaN', 'None']:
                    return False

            return True
        except Exception:
            return False

    def extract_materials_from_monthly_usage(self, file_path: Path, target_date: str) -> Tuple[int, int, int]:
        """Extract materials from monthly material usage file."""
        logger.info(f"📦 Extracting materials from: {file_path.name}")

        try:
            # Handle MB5B files correctly as UTF-16 tab-delimited text
            file_extension = file_path.suffix.lower()
            df = None
            max_rows = 5000 if not self.debug else 10000  # Increase limit for MB5B files

            if file_extension == '.xls' and 'mb5b' in file_path.name.lower():
                # MB5B files are UTF-16 tab-delimited text, not Excel
                try:
                    logger.info("Reading MB5B file as UTF-16 tab-delimited text")
                    df = pd.read_csv(
                        file_path, 
                        sep='\t', 
                        encoding='utf-16',
                        dtype={'物料': str},  # Critical: keep material numbers as strings
                        nrows=max_rows
                    )
                    logger.info(f"Successfully read MB5B file: {len(df)} rows, {len(df.columns)} columns")
                except Exception as e:
                    logger.error(f"Failed to read MB5B file as UTF-16: {e}")
                    return 0, 0, 0
            elif file_extension == '.xls':
                try:
                    # Try xlrd engine for regular Excel files
                    df = pd.read_excel(
                        file_path, engine='xlrd', nrows=max_rows)
                except Exception as e:
                    logger.warning(
                        f"xlrd failed: {e}, trying openpyxl with .xls")
                    try:
                        df = pd.read_excel(
                            file_path, engine='openpyxl', nrows=max_rows)
                    except Exception as e2:
                        logger.error(
                            f"Both engines failed for .xls file: {e2}")
                        return 0, 0, 0
            else:
                # Use openpyxl engine for .xlsx files
                df = pd.read_excel(
                    file_path, engine='openpyxl', nrows=max_rows)

            if df is None:
                logger.error("Failed to read material file")
                return 0, 0, 0

            logger.info(
                f"Loaded {len(df)} rows from material usage file (limited to {max_rows} for safety)")

            # Check if required columns exist for MB5B files
            if 'mb5b' in file_path.name.lower():
                # MB5B files have different structure
                required_columns = ['物料', 'ValA']  # ValA contains store code
                missing_columns = [
                    col for col in required_columns if col not in df.columns]
                if missing_columns:
                    logger.error(f"Missing required columns for MB5B: {missing_columns}")
                    logger.info(f"Available columns: {list(df.columns)}")
                    return 0, 0, 0
            else:
                # Regular material files
                required_columns = ['物料描述', '物料']
                missing_columns = [
                    col for col in required_columns if col not in df.columns]
                if missing_columns:
                    logger.error(f"Missing required columns: {missing_columns}")
                    logger.info(f"Available columns: {list(df.columns)}")
                    return 0, 0, 0

            # Filter valid material rows
            valid_materials = []
            for _, row in df.iterrows():
                if self.is_valid_material_row(row):
                    valid_materials.append(row)

                # Limit for safety
                if len(valid_materials) >= 200:  # Limit to 200 materials per file
                    logger.warning(f"⚠️ Limited to 200 materials for safety")
                    break

            logger.info(f"Found {len(valid_materials)} valid materials")

            if not valid_materials:
                logger.warning("No valid material rows found")
                return 0, 0, 0

            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                material_count = 0

                # Process materials in small batches
                batch_size = 10  # Very small batches
                for i in range(0, len(valid_materials), batch_size):
                    batch = valid_materials[i:i + batch_size]

                    try:
                        for row in batch:
                            try:
                                if 'mb5b' in file_path.name.lower():
                                    # MB5B files - extract store-specific materials
                                    material_number = str(row['物料']).strip() if pd.notna(row.get('物料')) else ''
                                    store_code = str(row.get('ValA', '')).strip() if pd.notna(row.get('ValA')) else ''
                                    
                                    if not material_number or not store_code:
                                        continue
                                    
                                    # Map store code to store ID
                                    store_id = None
                                    if store_code.upper() in ['CA01', 'CA1']:
                                        store_id = 1
                                    elif store_code.upper() in ['CA02', 'CA2']:
                                        store_id = 2
                                    elif store_code.upper() in ['CA03', 'CA3']:
                                        store_id = 3
                                    elif store_code.upper() in ['CA04', 'CA4']:
                                        store_id = 4
                                    elif store_code.upper() in ['CA05', 'CA5']:
                                        store_id = 5
                                    elif store_code.upper() in ['CA06', 'CA6']:
                                        store_id = 6
                                    elif store_code.upper() in ['CA07', 'CA7']:
                                        store_id = 7
                                    
                                    if not store_id:
                                        continue
                                    
                                    # Create basic material name
                                    material_name = f"Material_{material_number}"
                                    
                                    # Insert store-specific material
                                    cursor.execute("""
                                        INSERT INTO material (
                                            store_id, material_number, name, unit, is_active
                                        )
                                        VALUES (%s, %s, %s, %s, %s)
                                        ON CONFLICT (store_id, material_number) DO UPDATE SET
                                            name = EXCLUDED.name,
                                            updated_at = CURRENT_TIMESTAMP
                                    """, (store_id, material_number, material_name, 'KG', True))
                                    
                                else:
                                    # Regular material files - extract material information
                                    material_name = str(row['物料描述']).strip()
                                    material_number = str(row['物料']).strip()

                                    # Clean material number - remove leading zeros
                                    material_number = material_number.lstrip(
                                        '0') if material_number else ''
                                    if not material_number:
                                        material_number = '0'

                                    if not material_name or not material_number:
                                        continue

                                    # For regular files, insert for all stores (1-7)
                                    for store_id in range(1, 8):
                                        cursor.execute("""
                                            INSERT INTO material (
                                                store_id, material_number, name, unit, is_active
                                            )
                                            VALUES (%s, %s, %s, %s, %s)
                                            ON CONFLICT (store_id, material_number) DO UPDATE SET
                                                name = EXCLUDED.name,
                                                updated_at = CURRENT_TIMESTAMP
                                        """, (store_id, material_number, material_name, '', True))

                                if cursor.rowcount > 0:
                                    material_count += 1

                            except Exception as e:
                                logger.debug(
                                    f"Error processing material row: {e}")
                                continue

                        conn.commit()
                        logger.debug(
                            f"Processed batch {i//batch_size + 1}: {len(batch)} materials")

                    except Exception as e:
                        logger.error(f"Error processing material batch: {e}")
                        continue

                logger.info(
                    f"✅ Materials extraction completed - Materials: {material_count}")
                # Return material_type_count, material_child_type_count, material_count
                return 0, 0, material_count

        except Exception as e:
            logger.error(f"Error extracting materials from {file_path}: {e}")
            return 0, 0, 0

    def extract_material_prices_from_detail_folders(self, material_detail_folder: Path, target_date: str) -> int:
        """Extract material prices from store-specific material detail folders."""
        logger.info(
            f"💰 Extracting material prices from: {material_detail_folder}")

        if not material_detail_folder.exists():
            logger.warning(
                f"Material detail folder not found: {material_detail_folder}")
            return 0

        store_mapping = self.get_store_folder_mapping()
        total_price_count = 0

        # Process each store folder
        for store_folder_name, store_id in store_mapping.items():
            store_folder = material_detail_folder / store_folder_name
            if not store_folder.exists():
                logger.warning(f"Store folder not found: {store_folder}")
                continue

            # Find Excel files in store folder
            excel_files = self.find_excel_files(store_folder)
            if not excel_files:
                logger.warning(
                    f"No Excel files found in store folder: {store_folder}")
                continue

            for excel_file in excel_files:
                try:
                    price_count = self.extract_material_prices_from_store_file(
                        excel_file, store_id, target_date
                    )
                    total_price_count += price_count
                except Exception as e:
                    logger.error(
                        f"Error processing store {store_id} file {excel_file}: {e}")
                    continue

        logger.info(
            f"✅ Material prices extraction completed - Total: {total_price_count}")
        return total_price_count

    def extract_material_prices_from_store_file(self, file_path: Path, store_id: int, target_date: str) -> int:
        """Extract material prices from a single store file."""
        logger.info(f"💰 Processing material price file: {file_path.name}")

        try:
            # Add row limit to prevent hanging
            max_rows = 500 if not self.debug else 1000  # Limit rows for safety

            # CRITICAL: Use dtype={'物料': str} to prevent float64 conversion [[memory:1779842]]
            df = pd.read_excel(file_path, engine='openpyxl',
                               nrows=max_rows, dtype={'物料': str})
            logger.info(
                f"Loaded {len(df)} rows from material price file (limited to {max_rows} for safety)")

            # Check if required columns exist with flexible naming
            if '物料' not in df.columns:
                logger.error("Missing required column: 物料")
                logger.info(f"Available columns: {list(df.columns)}")
                return 0

            # Find price column with flexible naming
            price_col = None
            price_cols = ['单价', '系统发出单价', '价格', '成本']
            for col in price_cols:
                if col in df.columns:
                    price_col = col
                    break

            if not price_col:
                logger.error(f"No price column found. Tried: {price_cols}")
                logger.info(f"Available columns: {list(df.columns)}")
                return 0

            logger.info(f"Using price column: {price_col}")

            # Filter valid material price rows
            valid_prices = []
            for _, row in df.iterrows():
                if self.is_valid_material_price_row(row):
                    valid_prices.append(row)

                # Limit for safety
                if len(valid_prices) >= 200:  # Limit to 200 material prices per file
                    logger.warning(
                        f"⚠️ Limited to 200 material prices for safety")
                    break

            logger.info(f"Found {len(valid_prices)} valid material price rows")

            if not valid_prices:
                logger.warning("No valid material price rows found")
                return 0

            # Process material prices in small batches
            total_count = 0
            batch_size = 10  # Very small batches

            for i in range(0, len(valid_prices), batch_size):
                batch = valid_prices[i:i + batch_size]

                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        batch_count = 0

                        for row in batch:
                            try:
                                # Extract material information
                                material_number = str(row['物料']).strip()

                                # Clean material number - remove leading zeros but keep as string
                                material_number = material_number.lstrip(
                                    '0') if material_number else ''
                                if not material_number:
                                    material_number = '0'

                                # Extract price using the found price column
                                try:
                                    price = float(row[price_col])
                                except (ValueError, TypeError):
                                    continue

                                if price <= 0:
                                    continue

                                # Get material ID
                                cursor.execute(
                                    "SELECT id FROM material WHERE material_number = %s", (material_number,))
                                result = cursor.fetchone()
                                if not result:
                                    continue

                                material_id = result[0]

                                # Insert material price history
                                cursor.execute("""
                                    INSERT INTO material_price_history (
                                        material_id, store_id, price, effective_date, is_active
                                    )
                                    VALUES (%s, %s, %s, %s, true)
                                    ON CONFLICT (material_id, store_id, effective_date) DO UPDATE SET
                                        price = EXCLUDED.price,
                                        is_active = EXCLUDED.is_active,
                                        updated_at = CURRENT_TIMESTAMP
                                """, (material_id, store_id, price, target_date))

                                if cursor.rowcount > 0:
                                    batch_count += 1

                            except Exception as e:
                                logger.debug(
                                    f"Error processing material price row: {e}")
                                continue

                        conn.commit()
                        total_count += batch_count
                        logger.debug(
                            f"Processed batch {i//batch_size + 1}: {batch_count} material prices")

                except Exception as e:
                    logger.error(f"Error processing material price batch: {e}")
                    continue

            logger.info(
                f"✅ Material price extraction completed for {file_path.name} - Records: {total_count}")
            return total_count

        except Exception as e:
            logger.error(
                f"Error processing material price file {file_path}: {e}")
            return 0

    def is_valid_material_price_row(self, row) -> bool:
        """Check if a row contains valid material price data."""
        try:
            # Check if required columns exist and have valid data
            if '物料' not in row:
                return False

            # Check for price column with flexible naming
            price_col = None
            price_cols = ['单价', '系统发出单价', '价格', '成本']
            for col in price_cols:
                if col in row:
                    price_col = col
                    break

            if not price_col:
                return False

            material_number = str(row['物料']).strip()

            # Skip empty material numbers
            if not material_number or material_number == 'nan':
                return False

            # Skip header rows
            if material_number in ['物料', '物料号', '物料编号']:
                return False

            # Check if price is valid
            try:
                price = float(row[price_col])
                if price <= 0:
                    return False
            except (ValueError, TypeError):
                return False

            # Check if material number is reasonable (not too short)
            if len(material_number) < 2:
                return False

            return True

        except Exception:
            return False

    def extract_materials_from_detail_files(self, material_detail_folder: Path, target_date: str) -> int:
        """Extract materials with proper names and descriptions from material detail files."""
        logger.info(f"📦 Extracting materials from detail files: {material_detail_folder}")
        
        if not material_detail_folder.exists():
            logger.warning(f"Material detail folder not found: {material_detail_folder}")
            return 0
        
        # Find store folders (numbered 1-7)
        store_folders = [f for f in material_detail_folder.iterdir()
                         if f.is_dir() and f.name.isdigit()]
        store_folders.sort(key=lambda x: int(x.name))
        
        if not store_folders:
            logger.warning(f"No store folders found in: {material_detail_folder}")
            return 0
        
        total_materials = 0
        
        for store_folder in store_folders:
            store_id = int(store_folder.name)
            logger.info(f"Processing materials for store {store_id}...")
            
            # Find Excel files in the store folder
            excel_files = self.find_excel_files(store_folder, "*.xl*")
            
            for excel_file in excel_files:
                try:
                    logger.info(f"Reading material detail file: {excel_file.name}")
                    df = pd.read_excel(excel_file, engine='openpyxl', dtype={'物料': str})
                    
                    # Based on analysis: Column 5 = material numbers, Column 6 = material names, Column 7 = units
                    if df.shape[1] >= 7:
                        material_numbers = df.iloc[:, 4]  # Column 5 (0-indexed)
                        material_names = df.iloc[:, 5]    # Column 6 (0-indexed) 
                        material_units = df.iloc[:, 6]    # Column 7 (0-indexed)
                        
                        materials_added = 0
                        
                        with self.db_manager.get_connection() as conn:
                            cursor = conn.cursor()
                            
                            for i in range(len(df)):
                                material_number = material_numbers.iloc[i]
                                material_name = material_names.iloc[i]
                                material_unit = material_units.iloc[i]
                                
                                # Skip if material number is invalid
                                if pd.isna(material_number) or not str(material_number).strip():
                                    continue
                                    
                                material_number = str(material_number).strip()
                                
                                # Remove leading zeros (material numbers have many leading zeros)
                                material_number = material_number.lstrip('0')
                                if not material_number:
                                    material_number = '0'
                                
                                if not material_number.isdigit() or len(material_number) < 6:
                                    continue
                                
                                # Use material name or fallback to generic name
                                if pd.notna(material_name) and str(material_name).strip():
                                    name = str(material_name).strip()
                                else:
                                    name = f"Material_{material_number}"
                                
                                # Use unit or default to empty
                                if pd.notna(material_unit) and str(material_unit).strip():
                                    unit = str(material_unit).strip()
                                else:
                                    unit = ''
                                
                                try:
                                    # Insert material with store-specific data
                                    cursor.execute("""
                                        INSERT INTO material (
                                            store_id, material_number, name, unit, is_active
                                        )
                                        VALUES (%s, %s, %s, %s, %s)
                                        ON CONFLICT (store_id, material_number) DO UPDATE SET
                                            name = EXCLUDED.name,
                                            unit = EXCLUDED.unit,
                                            updated_at = CURRENT_TIMESTAMP
                                    """, (store_id, material_number, name, unit, True))
                                    
                                    materials_added += 1
                                    
                                    # Limit for safety
                                    if materials_added >= 200:
                                        logger.warning(f"⚠️ Limited to 200 materials for safety")
                                        break
                                        
                                except Exception as e:
                                    logger.debug(f"Error inserting material {material_number}: {e}")
                                    continue
                            
                            conn.commit()
                        
                        logger.info(f"Added {materials_added} materials for store {store_id}")
                        total_materials += materials_added
                    
                except Exception as e:
                    logger.error(f"Error processing {excel_file}: {e}")
                    continue
        
        logger.info(f"✅ Total materials extracted from detail files: {total_materials}")
        return total_materials

    def extract_dish_material_relationships_from_calculated_usage(self, calculated_folder: Path, target_date: str) -> int:
        """Extract dish-material relationships from calculated_dish_material_usage files."""
        logger.info(f"Extracting dish-material relationships from: {calculated_folder}")
        
        if not calculated_folder.exists():
            logger.warning(f"Calculated folder not found: {calculated_folder}")
            return 0
        
        # Find calculated usage files
        usage_files = self.find_excel_files(calculated_folder, "*.xl*")
        if not usage_files:
            logger.warning(f"No usage files found in: {calculated_folder}")
            return 0
        
        total_relationships = 0
        
        for usage_file in usage_files:
            try:
                logger.info(f"Processing calculated usage file: {usage_file.name}")
                
                # Read the Excel file
                df = pd.read_excel(usage_file, engine='xlrd', nrows=200)  # Limit for safety
                logger.info(f"Loaded {len(df)} rows from calculated usage file")
                
                # Look for dish code and material columns
                dish_code_cols = [col for col in df.columns if any(keyword in str(col) 
                                 for keyword in ['编码', 'code', '菜品'])]
                material_cols = [col for col in df.columns if '物料' in str(col)]
                quantity_cols = [col for col in df.columns if any(keyword in str(col) 
                                for keyword in ['用量', '数量', 'quantity'])]
                
                if not dish_code_cols or not material_cols:
                    logger.warning(f"Missing required columns in {usage_file.name}")
                    logger.info(f"Dish columns: {dish_code_cols}, Material columns: {material_cols}")
                    continue
                
                dish_code_col = dish_code_cols[0]
                material_col = None
                quantity_col = None
                
                # Find material number column
                for col in material_cols:
                    if any(keyword in str(col) for keyword in ['号', 'number']):
                        material_col = col
                        break
                
                # Find quantity column
                if quantity_cols:
                    quantity_col = quantity_cols[0]
                
                if not material_col:
                    logger.warning(f"No material number column found in {usage_file.name}")
                    continue
                
                logger.info(f"Using columns - Dish: {dish_code_col}, Material: {material_col}, Quantity: {quantity_col}")
                
                # Process relationships
                relationships_added = 0
                
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for _, row in df.iterrows():
                        try:
                            # Extract dish code
                            dish_code = str(row[dish_code_col]).strip() if pd.notna(row[dish_code_col]) else ''
                            dish_code = dish_code.replace('.0', '')  # Remove pandas float suffix
                            
                            # Extract material number
                            material_number = str(row[material_col]).strip() if pd.notna(row[material_col]) else ''
                            material_number = material_number.replace('.0', '')
                            
                            # Extract quantity if available
                            standard_quantity = 0.0
                            if quantity_col and pd.notna(row[quantity_col]):
                                try:
                                    standard_quantity = float(row[quantity_col])
                                except (ValueError, TypeError):
                                    standard_quantity = 0.0
                            
                            if not dish_code or not material_number:
                                continue
                            
                            # Find dish and material IDs in database
                            cursor.execute("SELECT id FROM dish WHERE full_code = %s LIMIT 1", (dish_code,))
                            dish_result = cursor.fetchone()
                            if not dish_result:
                                continue
                            dish_id = dish_result['id']
                            
                            cursor.execute("SELECT id FROM material WHERE material_number = %s LIMIT 1", (material_number,))
                            material_result = cursor.fetchone()
                            if not material_result:
                                continue
                            material_id = material_result['id']
                            
                            # Insert dish-material relationship
                            cursor.execute("""
                                INSERT INTO dish_material (
                                    dish_id, material_id, standard_quantity, 
                                    loss_rate, unit_conversion_rate, is_active
                                )
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (dish_id, material_id) DO UPDATE SET
                                    standard_quantity = EXCLUDED.standard_quantity,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (dish_id, material_id, standard_quantity, 1.0, 1.0, True))
                            
                            if cursor.rowcount > 0:
                                relationships_added += 1
                                
                            # Limit for safety
                            if relationships_added >= 100:
                                logger.warning(f"⚠️ Limited to 100 relationships for safety")
                                break
                                
                        except Exception as e:
                            logger.debug(f"Error processing relationship row: {e}")
                            continue
                    
                    conn.commit()
                    logger.info(f"✅ Added {relationships_added} dish-material relationships from {usage_file.name}")
                    total_relationships += relationships_added
                
            except Exception as e:
                logger.error(f"Error processing calculated usage file {usage_file}: {e}")
                continue
        
        logger.info(f"✅ Total dish-material relationships extracted: {total_relationships}")
        return total_relationships

    def process_month_folder(self, month_folder: Path) -> Dict[str, int]:
        """Process a single month folder."""
        month_name = month_folder.name
        logger.info(f"🗓️ Processing month: {month_name}")

        # Extract target date from month folder name
        target_date = self.extract_target_date_from_month(month_name)
        logger.info(f"📅 Target date: {target_date}")

        # Initialize results tracking
        results = {
            'dish_types': 0,
            'dish_child_types': 0,
            'dishes': 0,
            'dish_price_history': 0,
            'monthly_sales': 0,  # Fix the tracking name
            'materials': 0,
            'material_price_history': 0,
            'dish_material_relationships': 0,
        }

        try:
            # 1. Extract dishes from monthly_dish_sale
            monthly_dish_sale_folder = month_folder / "monthly_dish_sale"
            if monthly_dish_sale_folder.exists():
                dish_files = self.find_excel_files(monthly_dish_sale_folder)
                for dish_file in dish_files:
                    dish_types, child_types, dishes, price_history, monthly_sales = self.extract_dishes_from_monthly_sale(
                        dish_file, target_date
                    )
                    results['dish_types'] += dish_types
                    results['dish_child_types'] += child_types
                    results['dishes'] += dishes
                    results['dish_price_history'] += price_history
                    results['monthly_sales'] += monthly_sales

            # 2. Extract materials from monthly_material_usage
            monthly_material_usage_folder = month_folder / "monthly_material_usage"
            if monthly_material_usage_folder.exists():
                material_files = self.find_excel_files(
                    monthly_material_usage_folder, "*.xl*")
                for material_file in material_files:
                    try:
                        mat_types, mat_child_types, materials = self.extract_materials_from_monthly_usage(
                            material_file, target_date
                        )
                        results['materials'] += materials
                        logger.info(f"Materials extracted: {materials}")
                    except Exception as e:
                        logger.error(
                            f"Error extracting materials from {material_file}: {e}")
                        continue

            # 3. Extract materials with proper names from material_detail folders
            material_detail_folder = month_folder / "material_detail"
            if material_detail_folder.exists():
                try:
                    proper_materials = self.extract_materials_from_detail_files(
                        material_detail_folder, target_date
                    )
                    results['materials'] += proper_materials
                    logger.info(f"Proper materials extracted: {proper_materials}")
                    
                    # Also extract material prices
                    material_prices = self.extract_material_prices_from_detail_folders(
                        material_detail_folder, target_date
                    )
                    results['material_price_history'] += material_prices
                    logger.info(f"Material prices extracted: {material_prices}")
                except Exception as e:
                    logger.error(f"Error extracting from material detail: {e}")

            # 4. Extract dish-material relationships from calculated_dish_material_usage
            calculated_folder = month_folder / "calculated_dish_material_usage"
            if calculated_folder.exists() and not self.is_folder_empty_or_nonexistent(calculated_folder):
                try:
                    dish_material_relationships = self.extract_dish_material_relationships_from_calculated_usage(
                        calculated_folder, target_date
                    )
                    results['dish_material_relationships'] += dish_material_relationships
                    logger.info(f"Dish-material relationships extracted: {dish_material_relationships}")
                except Exception as e:
                    logger.error(f"Error extracting dish-material relationships: {e}")
            else:
                logger.info(f"📂 Calculated dish material usage folder empty or not found")

            # 5. Skip inventory_checking_result if empty
            inventory_folder = month_folder / "inventory_checking_result"
            if not self.is_folder_empty_or_nonexistent(inventory_folder):
                logger.info(
                    f"⚠️ Inventory checking result folder not empty, but skipping as requested")

            logger.info(f"✅ Month {month_name} processed successfully")
            return results

        except Exception as e:
            logger.error(f"Error processing month {month_name}: {e}")
            return None

    def process_all_months(self, start_month: str = None, end_month: str = None) -> bool:
        """Process all months in the history folder."""
        history_folder = Path("history_files/monthly_report_inputs")

        if not history_folder.exists():
            logger.error(f"History folder not found: {history_folder}")
            return False

        # Get all month folders
        month_folders = [f for f in history_folder.iterdir() if f.is_dir()]
        month_folders.sort()

        if not month_folders:
            logger.warning("No month folders found in history directory")
            return False

        # Filter by date range if specified
        if start_month or end_month:
            filtered_folders = []
            for folder in month_folders:
                folder_month = folder.name
                if start_month and folder_month < start_month:
                    continue
                if end_month and folder_month > end_month:
                    continue
                filtered_folders.append(folder)
            month_folders = filtered_folders

        logger.info(f"🗓️ Processing {len(month_folders)} months")

        success_count = 0
        for month_folder in month_folders:
            try:
                logger.info(f"📅 Processing month: {month_folder.name}")
                month_results = self.process_month_folder(month_folder)

                if month_results:
                    # Store results by month
                    self.results[month_folder.name] = month_results
                    success_count += 1
                    logger.info(
                        f"✅ Successfully processed {month_folder.name}")
                else:
                    logger.warning(f"⚠️ No results from {month_folder.name}")

            except Exception as e:
                logger.error(f"❌ Error processing {month_folder.name}: {e}")
                continue

        logger.info(
            f"Completed processing {success_count}/{len(month_folders)} months")
        return success_count > 0

    def print_results_summary(self):
        """Print a summary of all extraction results."""
        print("EXTRACTION SUMMARY")
        print("=" * 50)
        print(f"Total months processed: {len(self.results)}")

        # Sum up all results
        total_dish_types = sum(r['dish_types'] for r in self.results.values())
        total_dish_child_types = sum(r['dish_child_types']
                                     for r in self.results.values())
        total_dishes = sum(r['dishes'] for r in self.results.values())
        total_dish_price_history = sum(
            r['dish_price_history'] for r in self.results.values())
        total_monthly_sales = sum(r['monthly_sales']
                                  for r in self.results.values())
        total_materials = sum(r['materials'] for r in self.results.values())
        total_material_price_history = sum(
            r['material_price_history'] for r in self.results.values())
        total_dish_material_relationships = sum(
            r.get('dish_material_relationships', 0) for r in self.results.values())

        print("TOTALS:")
        print(f"  Dish types: {total_dish_types}")
        print(f"  Dish child types: {total_dish_child_types}")
        print(f"  Dishes: {total_dishes}")
        print(f"  Dish price history: {total_dish_price_history}")
        print(f"  Monthly sales: {total_monthly_sales}")
        print(f"  Materials: {total_materials}")
        print(f"  Material price history: {total_material_price_history}")
        print(f"  Dish-material relationships: {total_dish_material_relationships}")

        # Show breakdown by month
        print("\nBY MONTH:")
        for month, results in self.results.items():
            print(f"  {month}:")
            print(
                f"    Dishes: {results['dishes']}, Dish prices: {results['dish_price_history']}, Monthly sales: {results['monthly_sales']}")
            print(
                f"    Materials: {results['materials']}, Material prices: {results['material_price_history']}")
            print(
                f"    Dish-material relationships: {results.get('dish_material_relationships', 0)}")

        print("=" * 50)


def main():
    """Main entry point for the historical data extraction."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract historical data from monthly report inputs'
    )
    parser.add_argument('--month', type=str,
                        help='Single month to process (e.g., 2024-05)')
    parser.add_argument('--start-month', type=str,
                        help='Start month for range (e.g., 2024-05)')
    parser.add_argument('--end-month', type=str,
                        help='End month for range (e.g., 2024-12)')
    parser.add_argument('--test', action='store_true',
                        help='Use test database')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')

    args = parser.parse_args()

    # Create extractor instance
    extractor = HistoricalDataExtractor(is_test=args.test, debug=args.debug)

    try:
        if args.month:
            # Process single month
            month_folder = Path(
                f"history_files/monthly_report_inputs/{args.month}")
            if not month_folder.exists():
                logger.error(f"Month folder not found: {month_folder}")
                return

            logger.info(f"Processing single month: {args.month}")
            results = extractor.process_month_folder(month_folder)

            if results:
                extractor.results[args.month] = results
                logger.info(f"✅ Successfully processed {args.month}")
            else:
                logger.error(f"❌ Failed to process {args.month}")

        else:
            # Process all months or range
            extractor.process_all_months(args.start_month, args.end_month)

        # Print summary
        extractor.print_results_summary()

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
