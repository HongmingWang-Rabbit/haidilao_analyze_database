#!/usr/bin/env python3
"""
Modular extraction library for Haidilao restaurant data processing.
Consolidates common extraction logic used across historical and monthly automation scripts.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class StoreMapping:
    """Centralized store mapping management"""
    
    @staticmethod
    def get_store_name_mapping() -> Dict[str, int]:
        """Get store name to ID mapping for Chinese store names"""
        return {
            '加拿大一店': 1,
            '加拿大二店': 2,
            '加拿大三店': 3,
            '加拿大四店': 4,
            '加拿大五店': 5,
            '加拿大六店': 6,
            '加拿大七店': 7,
            "加拿大八店": 8
        }
    
    @staticmethod
    def get_store_folder_mapping() -> Dict[str, int]:
        """Get store folder name to store ID mapping for numeric folders"""
        return {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7
        }


class DataCleaner:
    """Common data cleaning utilities"""
    
    @staticmethod
    def clean_dish_code(code) -> Optional[str]:
        """Clean and validate dish code"""
        if pd.isna(code):
            return None
        
        # Convert to string and clean
        try:
            if isinstance(code, (int, float)):
                # Remove .0 suffix from float codes
                code_str = str(int(code)) if code == int(code) else str(code)
            else:
                code_str = str(code).strip()
                
            # Remove .0 suffix if present
            if code_str.endswith('.0'):
                code_str = code_str[:-2]
                
            # Validate: should be numeric and reasonable length
            if code_str.isdigit() and 4 <= len(code_str) <= 8:
                return code_str
                
        except (ValueError, TypeError):
            pass
            
        return None
    
    @staticmethod
    def find_dish_name_column(df: pd.DataFrame) -> Optional[str]:
        """Find the appropriate dish name column"""
        possible_columns = [
            '菜品名称',
            '菜品名称(门店pad显示名称)',
            '菜品名称(系统统一名称)'
        ]
        
        for col in possible_columns:
            if col in df.columns:
                return col
        return None
    
    @staticmethod
    def find_dish_code_column(df: pd.DataFrame) -> Optional[str]:
        """Find the appropriate dish code column"""
        possible_columns = ['菜品编码', '菜品短编码', '编码']
        
        for col in possible_columns:
            if col in df.columns:
                return col
        return None
    
    @staticmethod
    def is_valid_dish_row(row, dish_name_col: str) -> bool:
        """Check if a row contains valid dish data (not header row)"""
        try:
            dish_name = str(row[dish_name_col]) if pd.notna(row[dish_name_col]) else ''
            
            # Skip header rows
            header_indicators = ['菜品名称', '菜品名称(门店pad显示名称)', '菜品名称(系统统一名称)']
            if dish_name in header_indicators:
                return False
                
            # Skip empty or very short names
            if len(dish_name.strip()) < 2:
                return False
                
            return True
            
        except Exception:
            return False


class DishTypeExtractor:
    """Handles dish type and child type extraction"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def extract_dish_types(self, df: pd.DataFrame) -> int:
        """Extract and insert dish types"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                count = 0
                
                # Get unique dish types
                dish_types = set()
                if '大类名称' in df.columns:
                    for dish_type in df['大类名称'].dropna().unique():
                        if pd.notna(dish_type) and str(dish_type).strip():
                            dish_types.add(str(dish_type).strip())
                
                # Insert dish types
                for dish_type in dish_types:
                    try:
                        cursor.execute("""
                            INSERT INTO dish_type (name)
                            VALUES (%s)
                            ON CONFLICT (name) DO NOTHING
                        """, (dish_type,))
                        count += cursor.rowcount
                    except Exception as e:
                        logger.debug(f"Error inserting dish type {dish_type}: {e}")
                        continue
                
                conn.commit()
                return count
                
        except Exception as e:
            logger.error(f"Error processing dish types: {e}")
            return 0
    
    def extract_dish_child_types(self, df: pd.DataFrame) -> int:
        """Extract and insert dish child types"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                count = 0
                
                # Get unique parent-child type combinations
                type_combinations = set()
                if '大类名称' in df.columns and '子类名称' in df.columns:
                    for _, row in df.iterrows():
                        if (pd.notna(row['大类名称']) and pd.notna(row['子类名称'])):
                            parent_type = str(row['大类名称']).strip()
                            child_type = str(row['子类名称']).strip()
                            if parent_type and child_type:
                                type_combinations.add((parent_type, child_type))
                
                # Insert child types
                for parent_type, child_type in type_combinations:
                    try:
                        cursor.execute("""
                            INSERT INTO dish_child_type (name, dish_type_id)
                            VALUES (%s, (SELECT id FROM dish_type WHERE name = %s))
                            ON CONFLICT (name, dish_type_id) DO NOTHING
                        """, (child_type, parent_type))
                        count += cursor.rowcount
                    except Exception as e:
                        logger.debug(f"Error inserting dish child type: {e}")
                        continue
                
                conn.commit()
                return count
                
        except Exception as e:
            logger.error(f"Error processing dish child types: {e}")
            return 0


class DishExtractor:
    """Handles store-specific dish extraction"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.data_cleaner = DataCleaner()
    
    def extract_dishes_batch(self, df: pd.DataFrame, dish_name_col: str, dish_code_col: str, 
                           store_mapping: Dict[str, int], batch_size: int = 20) -> int:
        """Extract dishes in batches with store-specific logic"""
        try:
            total_count = 0
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        batch_count = 0
                        
                        for _, row in batch.iterrows():
                            batch_count += self._process_single_dish(cursor, row, dish_name_col, 
                                                                   dish_code_col, store_mapping)
                        
                        conn.commit()
                        total_count += batch_count
                        
                except Exception as e:
                    logger.error(f"Error processing dish batch: {e}")
                    continue
            
            return total_count
            
        except Exception as e:
            logger.error(f"Error in batch dish extraction: {e}")
            return 0
    
    def _process_single_dish(self, cursor, row, dish_name_col: str, dish_code_col: str, 
                           store_mapping: Dict[str, int]) -> int:
        """Process a single dish row"""
        try:
            # Clean dish code
            full_code = self.data_cleaner.clean_dish_code(row[dish_code_col])
            if not full_code:
                return 0
            
            size = row.get('规格', '') if pd.notna(row.get('规格')) else ''
            dish_name = str(row[dish_name_col]).strip()
            
            # Get type IDs
            dish_child_type_id = self._get_dish_child_type_id(cursor, row)
            
            # Determine which stores this dish should be created for
            stores_to_create = self._determine_target_stores(row, store_mapping)
            
            # Insert dish for each relevant store
            count = 0
            for store_id in stores_to_create:
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
                
                if cursor.rowcount > 0:
                    count += 1
            
            return count
            
        except Exception as e:
            logger.debug(f"Error processing individual dish: {e}")
            return 0
    
    def _get_dish_child_type_id(self, cursor, row) -> Optional[int]:
        """Get dish child type ID from row data"""
        if '大类名称' not in row or '子类名称' not in row:
            return None
            
        if not (pd.notna(row['大类名称']) and pd.notna(row['子类名称'])):
            return None
        
        try:
            cursor.execute("""
                SELECT dct.id FROM dish_child_type dct
                JOIN dish_type dt ON dct.dish_type_id = dt.id
                WHERE dt.name = %s AND dct.name = %s
            """, (str(row['大类名称']).strip(), str(row['子类名称']).strip()))
            
            result = cursor.fetchone()
            return result['id'] if result else None
            
        except Exception:
            return None
    
    def _determine_target_stores(self, row, store_mapping: Dict[str, int]) -> Set[int]:
        """Determine which stores a dish should be created for"""
        stores = set()
        
        # Check if row has store information
        if '门店名称' in row and pd.notna(row['门店名称']):
            store_name = str(row['门店名称']).strip()
            if store_name in store_mapping:
                stores.add(store_mapping[store_name])
        
        # If no specific store info, create for all stores (fallback)
        if not stores:
            stores = set(store_mapping.values())
        
        return stores


class PriceHistoryExtractor:
    """Handles store-specific price history extraction"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.data_cleaner = DataCleaner()
    
    def extract_price_history_batch(self, df: pd.DataFrame, dish_name_col: str, dish_code_col: str,
                                  target_date: str, store_mapping: Dict[str, int], 
                                  batch_size: int = 20) -> int:
        """Extract price history in batches"""
        try:
            total_count = 0
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        batch_count = 0
                        
                        for _, row in batch.iterrows():
                            batch_count += self._process_single_price(cursor, row, dish_name_col,
                                                                    dish_code_col, target_date, store_mapping)
                        
                        conn.commit()
                        total_count += batch_count
                        
                except Exception as e:
                    logger.error(f"Error processing price history batch: {e}")
                    continue
            
            return total_count
            
        except Exception as e:
            logger.error(f"Error in batch price history extraction: {e}")
            return 0
    
    def _process_single_price(self, cursor, row, dish_name_col: str, dish_code_col: str,
                            target_date: str, store_mapping: Dict[str, int]) -> int:
        """Process a single price history row"""
        try:
            # Clean dish code
            full_code = self.data_cleaner.clean_dish_code(row[dish_code_col])
            if not full_code:
                return 0
            
            # Get price
            price = None
            price_columns = ['单价', '菜品单价', '价格']
            for col in price_columns:
                if col in row and pd.notna(row[col]):
                    try:
                        price = float(row[col])
                        break
                    except (ValueError, TypeError):
                        continue
            
            if not price or price <= 0:
                return 0
            
            # Get store
            store_id = None
            if '门店名称' in row and pd.notna(row['门店名称']):
                store_name = str(row['门店名称']).strip()
                if store_name in store_mapping:
                    store_id = store_mapping[store_name]
            
            if not store_id:
                return 0
            
            size = row.get('规格', '') if pd.notna(row.get('规格')) else ''
            
            # Get dish ID (store-specific)
            cursor.execute("""
                SELECT id FROM dish 
                WHERE full_code = %s AND size = %s AND store_id = %s
            """, (full_code, size, store_id))
            
            result = cursor.fetchone()
            if not result:
                return 0
            
            dish_id = result['id']
            
            # Insert price history
            cursor.execute("""
                INSERT INTO dish_price_history (
                    dish_id, store_id, price, effective_date, is_active
                )
                VALUES (%s, %s, %s, %s, true)
                ON CONFLICT (dish_id, store_id, effective_date) DO UPDATE SET
                    price = EXCLUDED.price,
                    is_active = true
            """, (dish_id, store_id, price, target_date))
            
            return cursor.rowcount
            
        except Exception as e:
            logger.debug(f"Error processing individual price: {e}")
            return 0


class MonthlySalesExtractor:
    """Handles monthly sales data extraction"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.data_cleaner = DataCleaner()
    
    def extract_monthly_sales_batch(self, df: pd.DataFrame, dish_name_col: str, dish_code_col: str,
                                  target_date: str, store_mapping: Dict[str, int],
                                  batch_size: int = 20) -> int:
        """Extract monthly sales data with aggregation"""
        try:
            # Parse target date
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            year, month = target_dt.year, target_dt.month
            
            # Pre-aggregate data to handle multiple Excel rows
            aggregated_data = self._aggregate_sales_data(df, dish_code_col, store_mapping)
            
            total_count = 0
            
            for i in range(0, len(aggregated_data), batch_size):
                batch = aggregated_data[i:i + batch_size]
                
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        batch_count = 0
                        
                        for sales_record in batch:
                            batch_count += self._process_single_sales(cursor, sales_record, year, month)
                        
                        conn.commit()
                        total_count += batch_count
                        
                except Exception as e:
                    logger.error(f"Error processing sales batch: {e}")
                    continue
            
            return total_count
            
        except Exception as e:
            logger.error(f"Error in batch sales extraction: {e}")
            return 0
    
    def _aggregate_sales_data(self, df: pd.DataFrame, dish_code_col: str, 
                            store_mapping: Dict[str, int]) -> List[Dict]:
        """Aggregate sales data by dish code, size, and store"""
        aggregated = {}
        
        for _, row in df.iterrows():
            # Clean dish code
            full_code = self.data_cleaner.clean_dish_code(row[dish_code_col])
            if not full_code:
                continue
            
            # Get store
            if '门店名称' not in row or not pd.notna(row['门店名称']):
                continue
                
            store_name = str(row['门店名称']).strip()
            if store_name not in store_mapping:
                continue
                
            store_id = store_mapping[store_name]
            size = row.get('规格', '') if pd.notna(row.get('规格')) else ''
            
            # Get quantity
            quantity = 0
            quantity_columns = ['数量', '销售数量', '销量']
            for col in quantity_columns:
                if col in row and pd.notna(row[col]):
                    try:
                        quantity = float(row[col])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Create aggregation key
            key = (full_code, size, store_id)
            
            # Aggregate
            if key not in aggregated:
                aggregated[key] = {
                    'full_code': full_code,
                    'size': size,
                    'store_id': store_id,
                    'total_quantity': 0
                }
            
            aggregated[key]['total_quantity'] += quantity
        
        return list(aggregated.values())
    
    def _process_single_sales(self, cursor, sales_record: Dict, year: int, month: int) -> int:
        """Process a single aggregated sales record"""
        try:
            # Get dish ID (store-specific)
            cursor.execute("""
                SELECT id FROM dish 
                WHERE full_code = %s AND size = %s AND store_id = %s
            """, (sales_record['full_code'], sales_record['size'], sales_record['store_id']))
            
            result = cursor.fetchone()
            if not result:
                return 0
            
            dish_id = result['id']
            
            # Insert monthly sales
            cursor.execute("""
                INSERT INTO dish_monthly_sale (
                    dish_id, store_id, year, month, sale_amount, sales_mode
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (dish_id, store_id, year, month) DO UPDATE SET
                    sale_amount = EXCLUDED.sale_amount,
                    updated_at = CURRENT_TIMESTAMP
            """, (dish_id, sales_record['store_id'], year, month, 
                  sales_record['total_quantity'], 'dine-in'))
            
            return cursor.rowcount
            
        except Exception as e:
            logger.debug(f"Error processing individual sales record: {e}")
            return 0


class ExtractionOrchestrator:
    """Orchestrates the complete extraction process"""
    
    def __init__(self, db_manager, debug: bool = False):
        self.db_manager = db_manager
        self.debug = debug
        
        # Initialize extractors
        self.data_cleaner = DataCleaner()
        self.dish_type_extractor = DishTypeExtractor(db_manager)
        self.dish_extractor = DishExtractor(db_manager)
        self.price_extractor = PriceHistoryExtractor(db_manager)
        self.sales_extractor = MonthlySalesExtractor(db_manager)
    
    def extract_dishes_complete(self, file_path: Path, target_date: str) -> Tuple[int, int, int, int, int]:
        """Complete dish extraction process (types, dishes, prices, sales)"""
        logger.info(f"🍽️ Starting complete dish extraction from: {file_path.name}")
        
        try:
            # Read Excel file
            max_rows = 1000 if not self.debug else 5000
            df = pd.read_excel(file_path, engine='openpyxl', nrows=max_rows)
            logger.info(f"Loaded {len(df)} rows from file (limited to {max_rows})")
            
            # Validate columns
            dish_name_col = self.data_cleaner.find_dish_name_column(df)
            dish_code_col = self.data_cleaner.find_dish_code_column(df)
            
            if not dish_name_col or not dish_code_col:
                logger.error(f"Required columns not found. Name col: {dish_name_col}, Code col: {dish_code_col}")
                return 0, 0, 0, 0, 0
            
            # Clean data
            df_clean = df[df.apply(lambda row: self.data_cleaner.is_valid_dish_row(row, dish_name_col), axis=1)]
            logger.info(f"Cleaned data: {len(df_clean)} valid rows")
            
            store_mapping = StoreMapping.get_store_name_mapping()
            
            # Execute extraction steps
            dish_type_count = self.dish_type_extractor.extract_dish_types(df_clean)
            logger.info(f"Processed {dish_type_count} dish types")
            
            dish_child_type_count = self.dish_type_extractor.extract_dish_child_types(df_clean)
            logger.info(f"Processed {dish_child_type_count} dish child types")
            
            dish_count = self.dish_extractor.extract_dishes_batch(df_clean, dish_name_col, dish_code_col, store_mapping)
            logger.info(f"Processed {dish_count} dishes")
            
            price_history_count = self.price_extractor.extract_price_history_batch(
                df_clean, dish_name_col, dish_code_col, target_date, store_mapping)
            logger.info(f"Processed {price_history_count} price history records")
            
            monthly_sales_count = self.sales_extractor.extract_monthly_sales_batch(
                df_clean, dish_name_col, dish_code_col, target_date, store_mapping)
            logger.info(f"Processed {monthly_sales_count} monthly sales records")
            
            return dish_type_count, dish_child_type_count, dish_count, price_history_count, monthly_sales_count
            
        except Exception as e:
            logger.error(f"Error in complete dish extraction: {e}")
            return 0, 0, 0, 0, 0