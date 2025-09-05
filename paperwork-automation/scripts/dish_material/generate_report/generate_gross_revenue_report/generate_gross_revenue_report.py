#!/usr/bin/env python3
"""
Generate Gross Revenue Report Data for Dishes with Historical Comparisons
Retrieves and calculates profitability data for each dish by store including:
- Dish sale revenue (quantity * price)
- Material used cost (materials used * material price)  
- Net revenue (revenue - cost)
- Revenue percentage (profit margin)
- Historical price comparisons (last month and last year)

Note: This module now only returns data. Excel generation has been removed.
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
from dateutil.relativedelta import relativedelta

# Add parent directory to path for imports - MUST come before local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from lib.config import STORE_ID_TO_NAME_MAPPING
from lib.dish_material_db import DishMaterialDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GrossRevenueReportGenerator:
    """Generate gross revenue report data for dishes by store."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the report generator."""
        self.db_manager = db_manager
        self.dish_material_db = None
        
    def generate_report(self, year: int, month: int, include_history: bool = True) -> Dict:
        """
        Generate the gross revenue report data for all stores.
        
        Args:
            year: Target year
            month: Target month
            include_history: Whether to include historical price comparisons
            
        Returns:
            Dict containing report data for all stores
        """
        logger.info(f"Generating gross revenue report data for {year}-{month:02d}")
        
        # Initialize database module with connection
        with self.db_manager.get_connection() as conn:
            self.dish_material_db = DishMaterialDatabase(conn)
        
        # Calculate comparison periods if including history
        last_month_date = None
        last_year_date = None
        if include_history:
            current_date = datetime(year, month, 1)
            last_month_date = current_date - relativedelta(months=1)
            last_year_date = current_date - relativedelta(years=1)
        
        # Collect data for all stores
        report_data = {
            'year': year,
            'month': month,
            'stores': {},
            'last_month_date': last_month_date,
            'last_year_date': last_year_date
        }
        
        for store_id, store_name in STORE_ID_TO_NAME_MAPPING.items():
            if store_id > 100:  # Skip Hi Bowl for now
                continue
                
            logger.info(f"Processing store {store_id}: {store_name}")
            
            # Get data for this store
            if include_history:
                store_data = self._get_store_dish_revenue_data_with_history(
                    store_id, year, month,
                    last_month_date.year, last_month_date.month,
                    last_year_date.year, last_year_date.month
                )
            else:
                store_data = self._get_store_dish_revenue_data(store_id, year, month)
            
            if not store_data:
                logger.warning(f"No data for store {store_id} in {year}-{month:02d}")
                continue
            
            report_data['stores'][store_id] = {
                'store_name': store_name,
                'dish_data': store_data
            }
        
        if not report_data['stores']:
            logger.warning(f"No data found for any store in {year}-{month:02d}")
        
        logger.info(f"Generated data for {len(report_data['stores'])} stores")
        
        return report_data
    
    def _get_store_dish_revenue_data(self, store_id: int, year: int, month: int) -> List[Dict]:
        """
        Get dish revenue data for a specific store and month.
        
        Returns list of dicts with:
        - dish_name, dish_code
        - sale_quantity, dish_price, dish_revenue
        - material_details (list of material usage)
        - material_cost, net_revenue, profit_margin
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get dish sales with material costs
            query = """
                WITH dish_sales AS (
                    -- Get dish sales for the month
                    SELECT 
                        d.id as dish_id,
                        d.name as dish_name,
                        d.full_code as dish_code,
                        d.size as dish_size,
                        dms.sale_amount - COALESCE(dms.return_amount, 0) as net_quantity,
                        dph.price as dish_price
                    FROM dish_monthly_sale dms
                    JOIN dish d ON d.id = dms.dish_id
                    LEFT JOIN dish_price_history dph ON 
                        dph.dish_id = d.id 
                        AND dph.store_id = dms.store_id
                        AND dph.effective_year = %s
                        AND dph.effective_month = %s
                    WHERE dms.store_id = %s 
                        AND dms.year = %s 
                        AND dms.month = %s
                        AND (dms.sale_amount - COALESCE(dms.return_amount, 0)) > 0
                ),
                material_usage AS (
                    -- Calculate material usage for each dish
                    SELECT 
                        ds.dish_id,
                        m.material_number,
                        m.name as material_name,
                        dm.standard_quantity,
                        dm.loss_rate,
                        -- Formula: net_quantity * standard_quantity / conversion_unit * loss_rate
                        -- Note: conversion_unit is stored in dm.unit_conversion_rate
                        ds.net_quantity * COALESCE(dm.standard_quantity, 0) / COALESCE(dm.unit_conversion_rate, 1.0) * COALESCE(dm.loss_rate, 1.0) as total_usage,
                        mph.price as material_price,
                        (ds.net_quantity * COALESCE(dm.standard_quantity, 0) / COALESCE(dm.unit_conversion_rate, 1.0) * COALESCE(dm.loss_rate, 1.0)) * COALESCE(mph.price, 0) as material_cost
                    FROM dish_sales ds
                    LEFT JOIN dish_material dm ON dm.dish_id = ds.dish_id AND dm.store_id = %s
                    LEFT JOIN material m ON m.id = dm.material_id
                    LEFT JOIN material_price_history mph ON 
                        mph.material_id = m.id 
                        AND mph.store_id = %s
                        AND mph.effective_year = %s
                        AND mph.effective_month = %s
                )
                SELECT 
                    ds.dish_id,
                    ds.dish_name,
                    ds.dish_code,
                    ds.dish_size,
                    ds.net_quantity,
                    COALESCE(ds.dish_price, 0) as dish_price,
                    ds.net_quantity * COALESCE(ds.dish_price, 0) as dish_revenue,
                    COALESCE(STRING_AGG(
                        CASE 
                            WHEN mu.material_number IS NOT NULL 
                            THEN mu.material_name || '-' || mu.material_number || '-' || ROUND(mu.total_usage::numeric, 4)
                            ELSE NULL
                        END, 
                        '; ' ORDER BY mu.material_name
                    ), '') as material_details,
                    COALESCE(SUM(mu.material_cost), 0) as total_material_cost
                FROM dish_sales ds
                LEFT JOIN material_usage mu ON mu.dish_id = ds.dish_id
                GROUP BY 
                    ds.dish_id, ds.dish_name, ds.dish_code, ds.dish_size,
                    ds.net_quantity, ds.dish_price
                ORDER BY ds.dish_name, ds.dish_code
            """
            
            cursor.execute(query, (
                year, month,  # for dish price
                store_id, year, month,  # for dish sales
                store_id,  # for dish_material
                store_id, year, month  # for material price
            ))
            
            results = []
            for row in cursor.fetchall():
                dish_revenue = float(row['dish_revenue'] or 0)
                material_cost = float(row['total_material_cost'] or 0)
                net_revenue = dish_revenue - material_cost
                
                # Calculate profit margin percentage
                if dish_revenue > 0:
                    profit_margin = (net_revenue / dish_revenue) * 100
                else:
                    profit_margin = 0
                
                results.append({
                    'dish_name': row['dish_name'],
                    'dish_code': row['dish_code'],
                    'dish_size': row['dish_size'],
                    'sale_quantity': float(row['net_quantity'] or 0),
                    'dish_price': float(row['dish_price'] or 0),
                    'dish_revenue': dish_revenue,
                    'material_details': row['material_details'] or 'No materials',
                    'material_cost': material_cost,
                    'net_revenue': net_revenue,
                    'profit_margin': profit_margin
                })
            
            return results
    

    def _get_store_dish_revenue_data_with_history(
        self, store_id: int, year: int, month: int,
        last_month_year: int, last_month_month: int,
        last_year_year: int, last_year_month: int
    ) -> List[Dict]:
        """
        Get dish revenue data with historical price comparisons.
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Complex query to get current and historical prices
            query = """
                WITH dish_sales AS (
                    -- Get dish sales for the current month
                    SELECT 
                        d.id as dish_id,
                        d.name as dish_name,
                        d.full_code as dish_code,
                        d.size as dish_size,
                        dms.sale_amount - COALESCE(dms.return_amount, 0) as net_quantity,
                        -- Current month price
                        dph_current.price as dish_price_current,
                        -- Last month price
                        dph_last_month.price as dish_price_last_month,
                        -- Last year price
                        dph_last_year.price as dish_price_last_year
                    FROM dish_monthly_sale dms
                    JOIN dish d ON d.id = dms.dish_id
                    -- Current month price
                    LEFT JOIN dish_price_history dph_current ON 
                        dph_current.dish_id = d.id 
                        AND dph_current.store_id = dms.store_id
                        AND dph_current.effective_year = %s
                        AND dph_current.effective_month = %s
                    -- Last month price (don't check is_active for historical prices)
                    LEFT JOIN dish_price_history dph_last_month ON 
                        dph_last_month.dish_id = d.id 
                        AND dph_last_month.store_id = dms.store_id
                        AND dph_last_month.effective_year = %s
                        AND dph_last_month.effective_month = %s
                    -- Last year price (don't check is_active for historical prices)
                    LEFT JOIN dish_price_history dph_last_year ON 
                        dph_last_year.dish_id = d.id 
                        AND dph_last_year.store_id = dms.store_id
                        AND dph_last_year.effective_year = %s
                        AND dph_last_year.effective_month = %s
                    WHERE dms.store_id = %s 
                        AND dms.year = %s 
                        AND dms.month = %s
                        AND (dms.sale_amount - COALESCE(dms.return_amount, 0)) > 0
                ),
                material_usage AS (
                    -- Calculate material usage with price history
                    SELECT 
                        ds.dish_id,
                        m.material_number,
                        m.name as material_name,
                        dm.standard_quantity,
                        dm.loss_rate,
                        dm.unit_conversion_rate,
                        -- Calculate material usage using correct formula
                        ds.net_quantity * COALESCE(dm.standard_quantity, 0) / 
                        COALESCE(dm.unit_conversion_rate, 1.0) * COALESCE(dm.loss_rate, 1.0) as total_usage,
                        -- Current prices
                        mph_current.price as material_price_current,
                        -- Last month prices
                        mph_last_month.price as material_price_last_month,
                        -- Last year prices
                        mph_last_year.price as material_price_last_year,
                        -- Calculate costs
                        (ds.net_quantity * COALESCE(dm.standard_quantity, 0) / 
                         COALESCE(dm.unit_conversion_rate, 1.0) * COALESCE(dm.loss_rate, 1.0)) * 
                         COALESCE(mph_current.price, 0) as material_cost_current
                    FROM dish_sales ds
                    LEFT JOIN dish_material dm ON dm.dish_id = ds.dish_id AND dm.store_id = %s
                    LEFT JOIN material m ON m.id = dm.material_id
                    -- Current month material price
                    LEFT JOIN material_price_history mph_current ON 
                        mph_current.material_id = m.id 
                        AND mph_current.store_id = %s
                        AND mph_current.effective_year = %s
                        AND mph_current.effective_month = %s
                    -- Last month material price (don't check is_active for historical prices)
                    LEFT JOIN material_price_history mph_last_month ON 
                        mph_last_month.material_id = m.id 
                        AND mph_last_month.store_id = %s
                        AND mph_last_month.effective_year = %s
                        AND mph_last_month.effective_month = %s
                    -- Last year material price (don't check is_active for historical prices)
                    LEFT JOIN material_price_history mph_last_year ON 
                        mph_last_year.material_id = m.id 
                        AND mph_last_year.store_id = %s
                        AND mph_last_year.effective_year = %s
                        AND mph_last_year.effective_month = %s
                )
                SELECT 
                    ds.dish_id,
                    ds.dish_name,
                    ds.dish_code,
                    ds.dish_size,
                    ds.net_quantity,
                    -- Dish prices
                    COALESCE(ds.dish_price_current, 0) as dish_price_current,
                    COALESCE(ds.dish_price_last_month, 0) as dish_price_last_month,
                    COALESCE(ds.dish_price_last_year, 0) as dish_price_last_year,
                    -- Dish revenue
                    ds.net_quantity * COALESCE(ds.dish_price_current, 0) as dish_revenue,
                    -- Material details
                    COALESCE(STRING_AGG(
                        CASE 
                            WHEN mu.material_number IS NOT NULL 
                            THEN mu.material_name || '-' || mu.material_number || 
                                 '-Qty:' || ROUND(mu.total_usage::numeric, 2) ||
                                 '-$' || ROUND(mu.material_price_current::numeric, 2) ||
                                 '(LM:$' || COALESCE(ROUND(mu.material_price_last_month::numeric, 2)::text, 'N/A') ||
                                 ',LY:$' || COALESCE(ROUND(mu.material_price_last_year::numeric, 2)::text, 'N/A') || ')'
                            ELSE NULL
                        END, 
                        '; ' ORDER BY mu.material_name
                    ), 'No materials') as material_details,
                    -- Material costs
                    COALESCE(SUM(mu.material_cost_current), 0) as total_material_cost,
                    -- Average material price changes
                    AVG(CASE 
                        WHEN mu.material_price_last_month > 0 AND mu.material_price_current > 0
                        THEN ((mu.material_price_current - mu.material_price_last_month) / mu.material_price_last_month) * 100
                        ELSE NULL
                    END) as avg_material_price_change_last_month,
                    AVG(CASE 
                        WHEN mu.material_price_last_year > 0 AND mu.material_price_current > 0
                        THEN ((mu.material_price_current - mu.material_price_last_year) / mu.material_price_last_year) * 100
                        ELSE NULL
                    END) as avg_material_price_change_last_year
                FROM dish_sales ds
                LEFT JOIN material_usage mu ON mu.dish_id = ds.dish_id
                GROUP BY 
                    ds.dish_id, ds.dish_name, ds.dish_code, ds.dish_size,
                    ds.net_quantity, ds.dish_price_current, ds.dish_price_last_month, 
                    ds.dish_price_last_year
                ORDER BY ds.dish_name, ds.dish_code
            """
            
            cursor.execute(query, (
                # Dish price parameters
                year, month,  # current
                last_month_year, last_month_month,  # last month
                last_year_year, last_year_month,  # last year
                store_id, year, month,  # for dish sales
                # Material price parameters
                store_id,  # for dish_material
                store_id, year, month,  # current material price
                store_id, last_month_year, last_month_month,  # last month material price
                store_id, last_year_year, last_year_month  # last year material price
            ))
            
            results = []
            for row in cursor.fetchall():
                dish_revenue = float(row['dish_revenue'] or 0)
                material_cost = float(row['total_material_cost'] or 0)
                net_revenue = dish_revenue - material_cost
                
                # Calculate profit margin percentage
                if dish_revenue > 0:
                    profit_margin = (net_revenue / dish_revenue) * 100
                else:
                    profit_margin = 0
                
                # Calculate dish price changes
                dish_price_current = float(row['dish_price_current'] or 0)
                dish_price_last_month = float(row['dish_price_last_month'] or 0)
                dish_price_last_year = float(row['dish_price_last_year'] or 0)
                
                dish_price_change_last_month = None
                if dish_price_last_month > 0 and dish_price_current > 0:
                    dish_price_change_last_month = ((dish_price_current - dish_price_last_month) / dish_price_last_month) * 100
                
                dish_price_change_last_year = None
                if dish_price_last_year > 0 and dish_price_current > 0:
                    dish_price_change_last_year = ((dish_price_current - dish_price_last_year) / dish_price_last_year) * 100
                
                results.append({
                    'dish_name': row['dish_name'],
                    'dish_code': row['dish_code'],
                    'dish_size': row['dish_size'],
                    'sale_quantity': float(row['net_quantity'] or 0),
                    # Dish prices
                    'dish_price': dish_price_current,  # Keep backward compatibility
                    'dish_price_current': dish_price_current,
                    'dish_price_last_month': dish_price_last_month,
                    'dish_price_last_year': dish_price_last_year,
                    'dish_price_change_last_month': dish_price_change_last_month,
                    'dish_price_change_last_year': dish_price_change_last_year,
                    # Revenue and costs
                    'dish_revenue': dish_revenue,
                    'material_details': row['material_details'] or 'No materials',
                    'material_cost': material_cost,
                    'net_revenue': net_revenue,
                    'profit_margin': profit_margin,
                    # Material price changes
                    'avg_material_price_change_last_month': row['avg_material_price_change_last_month'],
                    'avg_material_price_change_last_year': row['avg_material_price_change_last_year']
                })
            
            return results

    def _get_theory_vs_actual_data(self, store_id: int, year: int, month: int) -> List[Dict]:
        """
        Get theory vs actual usage comparison data.
        
        Returns:
            List of dicts with material comparison data
        """
        with self.db_manager.get_connection() as conn:
            self.dish_material_db = DishMaterialDatabase(conn)
            
            # Get theoretical vs actual comparison
            comparison_data = self.dish_material_db.get_theoretical_vs_actual_usage(store_id, year, month)
            
            # Get material prices
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    m.material_number,
                    COALESCE(mph.price, 0) as price
                FROM material m
                LEFT JOIN material_price_history mph ON 
                    mph.material_id = m.id 
                    AND mph.store_id = %s
                    AND mph.effective_year = %s
                    AND mph.effective_month = %s
                WHERE m.material_number IN %s
            """, (store_id, year, month, 
                  tuple([d['material_number'] for d in comparison_data]) if comparison_data else ('',)))
            
            prices = {row['material_number']: float(row['price']) for row in cursor.fetchall()}
        
        # Add price and variance value to comparison data
        for item in comparison_data:
            material_num = item['material_number']
            price = prices.get(material_num, 0)
            variance = float(item['variance'])
            item['price'] = price
            item['variance_value'] = variance * price
        
        return comparison_data

    def _get_profit_summary_data(self, year: int, month: int) -> Dict:
        """
        Get profit summary data comparing current month with previous periods.
        Shows breakdown by actual dish types from database.
        
        Args:
            year: Target year
            month: Target month
            
        Returns:
            Dict containing profit summary data
        """
        from datetime import date
        from dateutil.relativedelta import relativedelta
        from decimal import Decimal
        
        # Calculate dates
        current_date = date(year, month, 1)
        last_month = current_date - relativedelta(months=1)
        last_year = current_date - relativedelta(years=1)
        
        # Get dish types from database
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name 
                FROM dish_type 
                WHERE id IN (3, 5, 6, 7, 8, 9)  -- Main dish types to show
                ORDER BY id
            """)
            dish_types = cursor.fetchall()
        
        summary_data = {
            'year': year,
            'month': month,
            'last_month': {'year': last_month.year, 'month': last_month.month},
            'last_year': {'year': last_year.year, 'month': last_year.month},
            'dish_types': dish_types,
            'stores': {}
        }
        
        # Get data for each store
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            for store_id, store_name in STORE_ID_TO_NAME_MAPPING.items():
                if store_id > 100:  # Skip Hi Bowl
                    continue
                
                # Query to get revenue by dish type and total
                dish_type_query = """
                    SELECT 
                        dt.id as dish_type_id,
                        dt.name as dish_type_name,
                        COALESCE(SUM(dms.sale_amount - COALESCE(dms.return_amount, 0)), 0) as revenue
                    FROM dish_type dt
                    LEFT JOIN dish_child_type dct ON dt.id = dct.dish_type_id
                    LEFT JOIN dish d ON d.dish_child_type_id = dct.id
                    LEFT JOIN dish_monthly_sale dms ON dms.dish_id = d.id 
                        AND dms.store_id = %s 
                        AND dms.year = %s 
                        AND dms.month = %s
                    WHERE dt.id IN (3, 5, 6, 7, 8, 9)
                    GROUP BY dt.id, dt.name
                    ORDER BY dt.id
                """
                
                # Get total revenue for percentage calculation
                total_query = """
                    SELECT COALESCE(SUM(sale_amount - COALESCE(return_amount, 0)), 0) as total_revenue
                    FROM dish_monthly_sale
                    WHERE store_id = %s AND year = %s AND month = %s
                """
                
                # Get current month total
                cursor.execute(total_query, [store_id, year, month])
                current_total = float(cursor.fetchone()['total_revenue'] or 0)
                
                # Get last month total
                cursor.execute(total_query, [store_id, last_month.year, last_month.month])
                last_total = float(cursor.fetchone()['total_revenue'] or 0)
                
                # Get current month data by dish type
                cursor.execute(dish_type_query, [store_id, year, month])
                current_data = {row['dish_type_id']: float(row['revenue'] or 0) 
                               for row in cursor.fetchall()}
                
                # Get last month data by dish type
                cursor.execute(dish_type_query, [store_id, last_month.year, last_month.month])
                last_data = {row['dish_type_id']: float(row['revenue'] or 0) 
                            for row in cursor.fetchall()}
                
                store_summary = {
                    'store_name': store_name,
                    'current_total': current_total,
                    'last_total': last_total,
                    'dish_type_data': {}
                }
                
                # Calculate data for each dish type
                for dish_type in dish_types:
                    type_id = dish_type['id']
                    current_revenue = current_data.get(type_id, 0)
                    last_revenue = last_data.get(type_id, 0)
                    
                    # Calculate percentages of total revenue
                    current_pct = (current_revenue / current_total * 100) if current_total > 0 else 0
                    last_pct = (last_revenue / last_total * 100) if last_total > 0 else 0
                    
                    # Calculate change in percentage points
                    change = current_pct - last_pct
                    
                    store_summary['dish_type_data'][type_id] = {
                        'current_revenue': current_revenue,
                        'last_revenue': last_revenue,
                        'current_percentage': current_pct,
                        'last_percentage': last_pct,
                        'change': change
                    }
                
                summary_data['stores'][store_id] = store_summary
        
        return summary_data
    
    def get_theory_vs_actual_comparison(self, store_id: int, year: int, month: int) -> List[Dict]:
        """
        Public method to get theory vs actual usage comparison for a store.
        
        Args:
            store_id: Store ID
            year: Year
            month: Month
            
        Returns:
            List of dicts with material comparison data
        """
        return self._get_theory_vs_actual_data(store_id, year, month)
    
    def get_profit_summary(self, year: int, month: int) -> Dict:
        """
        Public method to get profit summary data.
        
        Args:
            year: Year
            month: Month
            
        Returns:
            Dict containing profit summary data
        """
        return self._get_profit_summary_data(year, month)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Generate gross revenue report data for dishes by store'
    )
    parser.add_argument(
        '--year',
        type=int,
        required=True,
        help='Target year (e.g., 2025)'
    )
    parser.add_argument(
        '--month',
        type=int,
        required=True,
        help='Target month (1-12)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Use test database'
    )
    parser.add_argument(
        '--no-history',
        action='store_true',
        help='Generate report without historical price comparisons'
    )
    
    args = parser.parse_args()
    
    # Validate month
    if not 1 <= args.month <= 12:
        logger.error("Month must be between 1 and 12")
        sys.exit(1)
    
    # Initialize database connection
    db_config = DatabaseConfig(is_test=args.test)
    db_manager = DatabaseManager(db_config)
    
    # Test database connection
    if not db_manager.test_connection():
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    logger.info(f"Connected to {'test' if args.test else 'production'} database")
    
    # Generate report data
    generator = GrossRevenueReportGenerator(db_manager)
    report_data = generator.generate_report(
        args.year, args.month,
        include_history=not args.no_history
    )
    
    print("\n" + "="*50)
    print("GROSS REVENUE REPORT DATA GENERATION COMPLETE")
    print("="*50)
    print(f"Generated data for {len(report_data.get('stores', {}))} stores")
    print("="*50)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())