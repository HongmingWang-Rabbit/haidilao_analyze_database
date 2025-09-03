"""
Database operations module for dish-material related queries.
Provides modular, reusable database functions for the dish-material system.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class DishMaterialDatabase:
    """Centralized database operations for dish-material system."""
    
    def __init__(self, connection):
        """Initialize with database connection."""
        self.connection = connection
        
    def get_dish_sales_with_material_usage(self, target_date: date, store_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Get dish sales with calculated material usage for a specific date.
        
        Args:
            target_date: Date to query
            store_ids: Optional list of store IDs to filter
            
        Returns:
            List of dish sales with material usage calculations
        """
        query = """
        WITH dish_sales AS (
            SELECT 
                store_id,
                dish_code,
                dish_name,
                category,
                SUM(net_quantity) as net_quantity,
                AVG(selling_price) as selling_price,
                SUM(net_quantity * selling_price) as revenue
            FROM daily_dishes
            WHERE date = %s
            {store_filter}
            GROUP BY store_id, dish_code, dish_name, category
        ),
        material_usage AS (
            SELECT 
                ds.store_id,
                ds.dish_code,
                ds.dish_name,
                ds.category,
                ds.net_quantity,
                ds.selling_price,
                ds.revenue,
                dm.material_number,
                dm.material_name,
                dm.standard_quantity,
                dm.unit_conversion_rate,
                dm.loss_rate,
                ds.net_quantity * COALESCE(dm.standard_quantity, 0) / 
                    COALESCE(dm.unit_conversion_rate, 1.0) * 
                    COALESCE(dm.loss_rate, 1.0) as total_usage
            FROM dish_sales ds
            LEFT JOIN dish_material_mapping dm ON ds.dish_code = dm.dish_code
        )
        SELECT * FROM material_usage
        ORDER BY store_id, dish_code, material_number
        """
        
        params = [target_date]
        if store_ids:
            store_filter = "AND store_id = ANY(%s)"
            params.append(store_ids)
        else:
            store_filter = ""
            
        query = query.format(store_filter=store_filter)
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_material_prices(self, material_numbers: List[str], target_date: date) -> Dict[str, Decimal]:
        """
        Get material prices for specific materials on a target date.
        
        Args:
            material_numbers: List of material numbers
            target_date: Date to get prices for
            
        Returns:
            Dictionary mapping material_number to price
        """
        if not material_numbers:
            return {}
            
        query = """
        SELECT DISTINCT ON (material_number)
            material_number,
            unit_price
        FROM material_price_history
        WHERE material_number = ANY(%s)
            AND effective_date <= %s
        ORDER BY material_number, effective_date DESC
        """
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, [material_numbers, target_date])
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_historical_material_prices(self, material_numbers: List[str], 
                                      target_date: date, 
                                      comparison_dates: List[date]) -> Dict[str, Dict[str, Decimal]]:
        """
        Get material prices for multiple dates for comparison.
        
        Args:
            material_numbers: List of material numbers
            target_date: Current date
            comparison_dates: List of dates to compare against
            
        Returns:
            Nested dictionary: {material_number: {date_str: price}}
        """
        if not material_numbers:
            return {}
            
        all_dates = [target_date] + comparison_dates
        
        query = """
        WITH price_data AS (
            SELECT DISTINCT ON (material_number, target_date)
                material_number,
                %s::date as target_date,
                unit_price
            FROM material_price_history
            WHERE material_number = ANY(%s)
                AND effective_date <= %s
            ORDER BY material_number, target_date, effective_date DESC
        )
        """
        
        union_parts = []
        params = []
        
        for check_date in all_dates:
            union_parts.append("""
            SELECT DISTINCT ON (material_number)
                material_number,
                %s::date as target_date,
                unit_price
            FROM material_price_history
            WHERE material_number = ANY(%s)
                AND effective_date <= %s
            ORDER BY material_number, effective_date DESC
            """)
            params.extend([check_date, material_numbers, check_date])
        
        full_query = " UNION ALL ".join(union_parts)
        
        result = {}
        with self.connection.cursor() as cursor:
            cursor.execute(full_query, params)
            for row in cursor.fetchall():
                material_num = row[0]
                date_val = row[1]
                price = row[2]
                
                if material_num not in result:
                    result[material_num] = {}
                result[material_num][date_val.strftime('%Y-%m-%d')] = price
                
        return result
    
    def get_dish_prices(self, dish_codes: List[str], target_date: date) -> Dict[str, Decimal]:
        """
        Get dish prices for specific dishes on a target date.
        
        Args:
            dish_codes: List of dish codes
            target_date: Date to get prices for
            
        Returns:
            Dictionary mapping dish_code to price
        """
        if not dish_codes:
            return {}
            
        query = """
        SELECT DISTINCT ON (dish_code)
            dish_code,
            unit_price
        FROM dish_price_history
        WHERE dish_code = ANY(%s)
            AND effective_date <= %s
        ORDER BY dish_code, effective_date DESC
        """
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, [dish_codes, target_date])
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_historical_dish_prices(self, dish_codes: List[str], 
                                  target_date: date,
                                  comparison_dates: List[date]) -> Dict[str, Dict[str, Decimal]]:
        """
        Get dish prices for multiple dates for comparison.
        
        Args:
            dish_codes: List of dish codes
            target_date: Current date
            comparison_dates: List of dates to compare against
            
        Returns:
            Nested dictionary: {dish_code: {date_str: price}}
        """
        if not dish_codes:
            return {}
            
        union_parts = []
        params = []
        
        for check_date in [target_date] + comparison_dates:
            union_parts.append("""
            SELECT DISTINCT ON (dish_code)
                dish_code,
                %s::date as target_date,
                unit_price
            FROM dish_price_history
            WHERE dish_code = ANY(%s)
                AND effective_date <= %s
            ORDER BY dish_code, effective_date DESC
            """)
            params.extend([check_date, dish_codes, check_date])
        
        full_query = " UNION ALL ".join(union_parts)
        
        result = {}
        with self.connection.cursor() as cursor:
            cursor.execute(full_query, params)
            for row in cursor.fetchall():
                dish_code = row[0]
                date_val = row[1]
                price = row[2]
                
                if dish_code not in result:
                    result[dish_code] = {}
                result[dish_code][date_val.strftime('%Y-%m-%d')] = price
                
        return result
    
    def get_store_profit_summary(self, target_date: date, comparison_dates: List[date]) -> List[Dict[str, Any]]:
        """
        Get profit summary for all stores comparing multiple dates.
        
        Args:
            target_date: Current date to analyze
            comparison_dates: List of dates to compare against
            
        Returns:
            List of store profit summaries with comparisons
        """
        query = """
        WITH store_summary AS (
            SELECT 
                s.store_id,
                s.store_name,
                %s::date as report_date,
                COALESCE(SUM(dd.net_quantity * dd.selling_price), 0) as total_revenue,
                COALESCE(SUM(
                    dd.net_quantity * dmm.standard_quantity / 
                    COALESCE(dmm.unit_conversion_rate, 1.0) * 
                    COALESCE(dmm.loss_rate, 1.0) * 
                    COALESCE(mph.unit_price, 0)
                ), 0) as total_material_cost
            FROM stores s
            LEFT JOIN daily_dishes dd ON s.store_id = dd.store_id AND dd.date = %s
            LEFT JOIN dish_material_mapping dmm ON dd.dish_code = dmm.dish_code
            LEFT JOIN LATERAL (
                SELECT unit_price 
                FROM material_price_history 
                WHERE material_number = dmm.material_number 
                    AND effective_date <= %s
                ORDER BY effective_date DESC 
                LIMIT 1
            ) mph ON true
            WHERE s.store_id <= 7
            GROUP BY s.store_id, s.store_name
        )
        SELECT 
            store_id,
            store_name,
            report_date,
            total_revenue,
            total_material_cost,
            total_revenue - total_material_cost as gross_profit,
            CASE 
                WHEN total_revenue > 0 
                THEN ((total_revenue - total_material_cost) / total_revenue * 100)
                ELSE 0 
            END as profit_margin_percent
        FROM store_summary
        ORDER BY store_id
        """
        
        all_results = []
        
        for check_date in [target_date] + comparison_dates:
            with self.connection.cursor() as cursor:
                cursor.execute(query, [check_date, check_date, check_date])
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    all_results.append(result)
        
        return all_results
    
    def get_overall_profit_summary(self, target_date: date, comparison_dates: List[date]) -> Dict[str, Any]:
        """
        Get overall profit summary across all stores for multiple dates.
        
        Args:
            target_date: Current date to analyze
            comparison_dates: List of dates to compare against
            
        Returns:
            Dictionary with overall profit metrics and comparisons
        """
        store_summaries = self.get_store_profit_summary(target_date, comparison_dates)
        
        result = {
            'current': {'date': target_date},
            'comparisons': []
        }
        
        for summary in store_summaries:
            if summary['report_date'] == target_date:
                if 'total_revenue' not in result['current']:
                    result['current']['total_revenue'] = Decimal('0')
                    result['current']['total_material_cost'] = Decimal('0')
                    result['current']['gross_profit'] = Decimal('0')
                    
                result['current']['total_revenue'] += summary['total_revenue']
                result['current']['total_material_cost'] += summary['total_material_cost']
                result['current']['gross_profit'] += summary['gross_profit']
            else:
                date_key = summary['report_date'].strftime('%Y-%m-%d')
                if date_key not in [c['date'] for c in result['comparisons']]:
                    result['comparisons'].append({
                        'date': date_key,
                        'total_revenue': Decimal('0'),
                        'total_material_cost': Decimal('0'),
                        'gross_profit': Decimal('0')
                    })
                
                for comp in result['comparisons']:
                    if comp['date'] == date_key:
                        comp['total_revenue'] += summary['total_revenue']
                        comp['total_material_cost'] += summary['total_material_cost']
                        comp['gross_profit'] += summary['gross_profit']
        
        if result['current'].get('total_revenue', 0) > 0:
            result['current']['profit_margin'] = (
                result['current']['gross_profit'] / result['current']['total_revenue'] * 100
            )
        else:
            result['current']['profit_margin'] = Decimal('0')
            
        for comp in result['comparisons']:
            if comp.get('total_revenue', 0) > 0:
                comp['profit_margin'] = comp['gross_profit'] / comp['total_revenue'] * 100
            else:
                comp['profit_margin'] = Decimal('0')
        
        return result
    
    def get_actual_material_usage(self, store_id: int, year: int, month: int) -> Dict[str, Decimal]:
        """
        Get actual material usage from inventory data.
        Formula: Beginning + Purchases + Transfers In - Ending - Transfers Out = Actual Usage
        
        Args:
            store_id: Store ID
            year: Year
            month: Month
            
        Returns:
            Dictionary mapping material_number to actual usage quantity
        """
        query = """
        SELECT 
            mi.material_number,
            mi.beginning_inventory,
            mi.purchase_amount,
            mi.transfer_in_amount,
            mi.ending_inventory,
            mi.transfer_out_amount,
            -- Actual usage calculation
            COALESCE(mi.beginning_inventory, 0) + 
            COALESCE(mi.purchase_amount, 0) + 
            COALESCE(mi.transfer_in_amount, 0) - 
            COALESCE(mi.ending_inventory, 0) - 
            COALESCE(mi.transfer_out_amount, 0) as actual_usage
        FROM monthly_inventory mi
        WHERE mi.store_id = %s
            AND mi.year = %s
            AND mi.month = %s
        """
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, [store_id, year, month])
            return {row['material_number']: Decimal(str(row['actual_usage'])) 
                   for row in cursor.fetchall() if row['actual_usage']}
    
    def get_theoretical_vs_actual_usage(self, store_id: int, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Compare theoretical usage (from dish sales) vs actual usage (from inventory).
        
        Args:
            store_id: Store ID
            year: Year
            month: Month
            
        Returns:
            List of materials with theoretical vs actual usage comparison
        """
        query = """
        WITH theoretical_usage AS (
            -- Calculate theoretical usage from dish sales
            SELECT 
                m.material_number,
                m.name as material_name,
                SUM(
                    (dms.sale_amount - COALESCE(dms.return_amount, 0)) * 
                    COALESCE(dm.standard_quantity, 0) / 
                    COALESCE(dm.unit_conversion_rate, 1.0) * 
                    COALESCE(dm.loss_rate, 1.0)
                ) as theory_usage
            FROM dish_monthly_sale dms
            JOIN dish d ON d.id = dms.dish_id
            JOIN dish_material dm ON dm.dish_id = d.id AND dm.store_id = dms.store_id
            JOIN material m ON m.id = dm.material_id
            WHERE dms.store_id = %s
                AND dms.year = %s
                AND dms.month = %s
            GROUP BY m.material_number, m.name
        ),
        actual_usage AS (
            -- Get actual usage from inventory count
            -- For now, we'll use the counted quantity as a proxy for actual usage
            -- In a real system, this would be: beginning + purchases - ending = usage
            SELECT 
                m.material_number,
                COALESCE(ic.counted_quantity, 0) as actual_usage
            FROM material m
            LEFT JOIN inventory_count ic ON 
                ic.material_id = m.id
                AND ic.store_id = %s
                AND ic.year = %s
                AND ic.month = %s
        )
        SELECT 
            COALESCE(t.material_number, a.material_number) as material_number,
            t.material_name,
            COALESCE(t.theory_usage, 0) as theoretical_usage,
            COALESCE(a.actual_usage, 0) as actual_usage,
            COALESCE(a.actual_usage, 0) - COALESCE(t.theory_usage, 0) as variance,
            CASE 
                WHEN COALESCE(t.theory_usage, 0) > 0 
                THEN ((COALESCE(a.actual_usage, 0) - COALESCE(t.theory_usage, 0)) / t.theory_usage * 100)
                ELSE NULL
            END as variance_percentage
        FROM theoretical_usage t
        FULL OUTER JOIN actual_usage a ON t.material_number = a.material_number
        WHERE COALESCE(t.theory_usage, 0) > 0 OR COALESCE(a.actual_usage, 0) > 0
        ORDER BY ABS(COALESCE(a.actual_usage, 0) - COALESCE(t.theory_usage, 0)) DESC
        """
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, [
                store_id, year, month,  # for theoretical
                store_id, year, month   # for actual
            ])
            return [dict(row) for row in cursor.fetchall()]