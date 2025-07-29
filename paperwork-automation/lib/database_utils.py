#!/usr/bin/env python3
"""
Enhanced database utilities for Haidilao paperwork automation.
Consolidates common database operation patterns from 50+ files.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import pandas as pd
from datetime import datetime

from .config import (
    STORE_NAME_MAPPING, STORE_ID_TO_NAME_MAPPING, 
    DEFAULT_BATCH_SIZE, RETRY_CONFIG
)


class DatabaseOperations:
    """
    High-level database operations for common patterns.
    Consolidates duplicate database logic from multiple extraction scripts.
    """
    
    def __init__(self, database_manager):
        """
        Initialize database operations.
        
        Args:
            database_manager: Database manager instance
        """
        self.db_manager = database_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with proper cleanup.
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def safe_insert_with_conflict_handling(
        self, 
        table: str, 
        data: Dict[str, Any], 
        conflict_columns: List[str],
        update_columns: Optional[List[str]] = None
    ) -> bool:
        """
        Standardized insert with conflict resolution (upsert).
        
        Args:
            table: Target table name
            data: Dictionary with column -> value mappings
            conflict_columns: Columns to check for conflicts
            update_columns: Columns to update on conflict (default: all except conflict columns)
            
        Returns:
            True if operation succeeded
        """
        if not data:
            return True
        
        # Prepare column lists
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['%s'] * len(values))
        
        # Prepare conflict resolution
        conflict_clause = ', '.join(conflict_columns)
        
        if update_columns is None:
            update_columns = [col for col in columns if col not in conflict_columns]
        
        update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
        
        sql = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_clause})
        DO UPDATE SET {update_clause}
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
                self.logger.debug(f"Upserted 1 record into {table}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to upsert into {table}: {e}")
            return False
    
    def batch_upsert(
        self, 
        table: str, 
        data_list: List[Dict[str, Any]], 
        conflict_columns: List[str],
        batch_size: int = None,
        update_columns: Optional[List[str]] = None
    ) -> int:
        """
        Optimized batch upsert operations.
        
        Args:
            table: Target table name
            data_list: List of dictionaries with data to insert
            conflict_columns: Columns to check for conflicts
            batch_size: Number of records per batch
            update_columns: Columns to update on conflict
            
        Returns:
            Number of records successfully processed
        """
        if not data_list:
            return 0
        
        batch_size = batch_size or DEFAULT_BATCH_SIZE
        total_processed = 0
        
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            
            try:
                # Prepare batch insert SQL
                if not batch:
                    continue
                
                columns = list(batch[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                
                # Prepare conflict resolution
                conflict_clause = ', '.join(conflict_columns)
                
                if update_columns is None:
                    update_columns = [col for col in columns if col not in conflict_columns]
                
                update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
                
                sql = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT ({conflict_clause})
                DO UPDATE SET {update_clause}
                """
                
                # Prepare batch data
                batch_values = []
                for record in batch:
                    batch_values.append([record.get(col) for col in columns])
                
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(sql, batch_values)
                    conn.commit()
                    total_processed += len(batch)
                    
                    self.logger.info(f"Processed batch of {len(batch)} records for {table}")
                    
            except Exception as e:
                self.logger.error(f"Failed to process batch for {table}: {e}")
                continue
        
        self.logger.info(f"Successfully processed {total_processed} total records for {table}")
        return total_processed
    
    def get_or_create_lookup(
        self, 
        table: str, 
        lookup_data: Dict[str, Any], 
        return_column: str = 'id'
    ) -> Optional[Any]:
        """
        Common lookup pattern with creation if not exists.
        
        Args:
            table: Target table name
            lookup_data: Data to look up / create
            return_column: Column to return (usually 'id')
            
        Returns:
            Value from return_column or None if failed
        """
        # First try to find existing record
        where_clause = ' AND '.join([f"{k} = %s" for k in lookup_data.keys()])
        select_sql = f"SELECT {return_column} FROM {table} WHERE {where_clause}"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql, list(lookup_data.values()))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                
                # Record doesn't exist, create it
                columns = list(lookup_data.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                
                insert_sql = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({placeholders})
                RETURNING {return_column}
                """
                
                cursor.execute(insert_sql, list(lookup_data.values()))
                result = cursor.fetchone()
                conn.commit()
                
                if result:
                    self.logger.debug(f"Created new {table} record with {return_column}={result[0]}")
                    return result[0]
                
        except Exception as e:
            self.logger.error(f"Failed get_or_create for {table}: {e}")
        
        return None
    
    def execute_query_to_dataframe(
        self, 
        query: str, 
        params: Optional[List] = None
    ) -> Optional[pd.DataFrame]:
        """
        Execute query and return results as DataFrame.
        Common pattern for report generation queries.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            DataFrame with query results or None if failed
        """
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                self.logger.debug(f"Query returned {len(df)} rows")
                return df
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
            return None
    
    def get_store_data_summary(self, target_date: str) -> Dict[str, int]:
        """
        Get summary of data availability by store for a target date.
        Common validation pattern used across multiple scripts.
        
        Args:
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping store names to record counts
        """
        query = """
        SELECT s.store_name, COUNT(dr.id) as record_count
        FROM store s
        LEFT JOIN daily_report dr ON s.id = dr.store_id 
            AND dr.report_date = %s
        GROUP BY s.id, s.store_name
        ORDER BY s.id
        """
        
        try:
            df = self.execute_query_to_dataframe(query, [target_date])
            if df is not None:
                return dict(zip(df['store_name'], df['record_count']))
        except Exception as e:
            self.logger.error(f"Failed to get store data summary: {e}")
        
        return {}
    
    def deactivate_previous_records(
        self, 
        table: str, 
        filter_conditions: Dict[str, Any],
        active_column: str = 'is_active'
    ) -> int:
        """
        Deactivate previous records matching conditions.
        Common pattern for price history and other temporal data.
        
        Args:
            table: Target table name
            filter_conditions: Conditions to identify records to deactivate
            active_column: Column name for active flag
            
        Returns:
            Number of records deactivated
        """
        where_clause = ' AND '.join([f"{k} = %s" for k in filter_conditions.keys()])
        sql = f"""
        UPDATE {table} 
        SET {active_column} = false, updated_at = CURRENT_TIMESTAMP
        WHERE {where_clause} AND {active_column} = true
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, list(filter_conditions.values()))
                affected_rows = cursor.rowcount
                conn.commit()
                
                if affected_rows > 0:
                    self.logger.info(f"Deactivated {affected_rows} records in {table}")
                
                return affected_rows
                
        except Exception as e:
            self.logger.error(f"Failed to deactivate records in {table}: {e}")
            return 0
    
    def get_max_effective_date(
        self, 
        table: str, 
        filter_conditions: Dict[str, Any],
        date_column: str = 'effective_date'
    ) -> Optional[datetime]:
        """
        Get maximum effective date for records matching conditions.
        Common pattern for temporal data queries.
        
        Args:
            table: Target table name
            filter_conditions: Conditions to filter records
            date_column: Column name for date comparison
            
        Returns:
            Maximum date or None if no records found
        """
        where_clause = ' AND '.join([f"{k} = %s" for k in filter_conditions.keys()])
        sql = f"SELECT MAX({date_column}) FROM {table} WHERE {where_clause}"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, list(filter_conditions.values()))
                result = cursor.fetchone()
                
                if result and result[0]:
                    return result[0]
                    
        except Exception as e:
            self.logger.error(f"Failed to get max date from {table}: {e}")
        
        return None
    
    def validate_data_completeness(
        self, 
        table: str, 
        required_stores: List[int],
        target_date: str,
        date_column: str = 'report_date'
    ) -> Tuple[bool, List[int]]:
        """
        Validate that data exists for all required stores on target date.
        Common validation pattern across extraction scripts.
        
        Args:
            table: Table to check
            required_stores: List of store IDs that must have data
            target_date: Target date to check
            date_column: Column name for date filtering
            
        Returns:
            Tuple of (is_complete, missing_store_ids)
        """
        query = f"""
        SELECT DISTINCT store_id 
        FROM {table} 
        WHERE {date_column} = %s
        """
        
        try:
            df = self.execute_query_to_dataframe(query, [target_date])
            if df is not None:
                present_stores = set(df['store_id'].tolist())
                required_stores_set = set(required_stores)
                missing_stores = list(required_stores_set - present_stores)
                
                is_complete = len(missing_stores) == 0
                return is_complete, missing_stores
                
        except Exception as e:
            self.logger.error(f"Failed to validate data completeness: {e}")
        
        return False, required_stores


class CommonQueries:
    """
    Common database queries used across multiple modules.
    Consolidates duplicate query patterns.
    """
    
    @staticmethod
    def get_store_mapping_query() -> str:
        """Get query for store ID to name mapping."""
        return "SELECT id, store_name FROM store ORDER BY id"
    
    @staticmethod
    def get_material_types_query() -> str:
        """Get query for material type mappings."""
        return "SELECT id, type_name FROM material_type ORDER BY id"
    
    @staticmethod
    def get_active_prices_query(target_date: str) -> str:
        """Get query for active prices on target date."""
        return f"""
        SELECT material_id, store_id, price, effective_date
        FROM material_price_history
        WHERE effective_date <= '{target_date}'
        AND is_active = true
        ORDER BY material_id, store_id, effective_date DESC
        """
    
    @staticmethod
    def get_monthly_summary_query(year: int, month: int) -> str:
        """Get query for monthly data summary."""
        return f"""
        SELECT 
            s.store_name,
            COUNT(dr.id) as day_count,
            SUM(dr.revenue) as total_revenue,
            AVG(dr.table_count) as avg_tables
        FROM store s
        LEFT JOIN daily_report dr ON s.id = dr.store_id
        WHERE EXTRACT(YEAR FROM dr.report_date) = {year}
        AND EXTRACT(MONTH FROM dr.report_date) = {month}
        GROUP BY s.id, s.store_name
        ORDER BY s.id
        """


# Export database utilities
__all__ = [
    'DatabaseOperations',
    'CommonQueries'
]