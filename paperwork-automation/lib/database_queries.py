#!/usr/bin/env python3
"""
Centralized database query functions for report generation.
All database interactions should go through this module.
"""

from utils.database import DatabaseManager
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


class ReportDataProvider:
    """Centralized data provider for all report generation"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_report_data(self, target_date: str):
        """Get all required data in a single comprehensive query to reduce database load"""
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        year, month, day = target_dt.year, target_dt.month, target_dt.day

        # Calculate date ranges
        prev_year = year - 1
        if month == 1:
            prev_month_year, prev_month = year - 1, 12
        else:
            prev_month_year, prev_month = year, month - 1

        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            dr.date,
            dr.tables_served,
            dr.takeout_tables,
            dr.tables_served_validated,
            dr.revenue_tax_not_included,
            dr.customers,
            dr.discount_total,
            dr.turnover_rate,
            dr.is_holiday,
            EXTRACT(YEAR FROM dr.date) as data_year,
            EXTRACT(MONTH FROM dr.date) as data_month,
            EXTRACT(DAY FROM dr.date) as data_day,
            smt.revenue as target_revenue,
            -- Categorize data by period (order matters - specific conditions first)
            CASE 
                WHEN dr.date = %s THEN 'target_day'
                WHEN EXTRACT(YEAR FROM dr.date) = %s 
                     AND EXTRACT(MONTH FROM dr.date) = %s
                     AND EXTRACT(DAY FROM dr.date) <= %s THEN 'current_year_mtd'
                WHEN EXTRACT(YEAR FROM dr.date) = %s 
                     AND EXTRACT(MONTH FROM dr.date) = %s
                     AND EXTRACT(DAY FROM dr.date) <= %s THEN 'prev_month_mtd'
                WHEN EXTRACT(YEAR FROM dr.date) = %s 
                     AND EXTRACT(MONTH FROM dr.date) = %s
                     AND EXTRACT(DAY FROM dr.date) <= %s THEN 'prev_year_mtd'
                WHEN EXTRACT(YEAR FROM dr.date) = %s 
                     AND EXTRACT(MONTH FROM dr.date) = %s THEN 'current_month'
                WHEN EXTRACT(YEAR FROM dr.date) = %s 
                     AND EXTRACT(MONTH FROM dr.date) = %s THEN 'prev_month'
                ELSE 'other'
            END as period_type
        FROM daily_report dr
        JOIN store s ON dr.store_id = s.id
        LEFT JOIN store_monthly_target smt ON s.id = smt.store_id 
            AND EXTRACT(YEAR FROM smt.month) = %s 
            AND EXTRACT(MONTH FROM smt.month) = %s
        WHERE (
            -- Target day
            dr.date = %s
            OR
            -- Current month
            (EXTRACT(YEAR FROM dr.date) = %s 
             AND EXTRACT(MONTH FROM dr.date) = %s)
            OR
            -- Previous month
            (EXTRACT(YEAR FROM dr.date) = %s 
             AND EXTRACT(MONTH FROM dr.date) = %s)
            OR
            -- Previous month MTD (for comparison)
            (EXTRACT(YEAR FROM dr.date) = %s 
             AND EXTRACT(MONTH FROM dr.date) = %s
             AND EXTRACT(DAY FROM dr.date) <= %s)
            OR
            -- Previous year same period (for yearly comparison)
            (EXTRACT(YEAR FROM dr.date) = %s 
             AND EXTRACT(MONTH FROM dr.date) = %s
             AND EXTRACT(DAY FROM dr.date) <= %s)
        )
        ORDER BY s.id, dr.date
        """

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    target_date,  # target_day comparison
                    year, month, day,  # current_year_mtd
                    prev_month_year, prev_month, day,  # prev_month_mtd
                    prev_year, month, day,  # prev_year_mtd
                    year, month,  # current_month
                    prev_month_year, prev_month,  # prev_month
                    year, month,  # JOIN condition for monthly targets
                    target_date,  # WHERE target day
                    year, month,  # WHERE current month
                    prev_month_year, prev_month,  # WHERE prev month
                    prev_month_year, prev_month, day,  # WHERE prev month MTD
                    prev_year, month, day  # WHERE prev year
                ))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching comprehensive data: {e}")
            return []

    def process_comprehensive_data(self, all_data):
        """Process comprehensive data and calculate all required metrics client-side"""
        if not all_data:
            return [], [], [], [], [], [], [], [], [], [], []

        # Group data by period and store
        data_by_period = {}
        for row in all_data:
            period = row['period_type']
            store_id = row['store_id']

            if period not in data_by_period:
                data_by_period[period] = {}
            if store_id not in data_by_period[period]:
                data_by_period[period][store_id] = []

            data_by_period[period][store_id].append(row)

        # Calculate aggregated metrics for each period and store
        def aggregate_store_data(period_data):
            aggregated = {}
            for store_id, rows in period_data.items():
                if not rows:
                    continue

                # Get first row for static data
                first_row = rows[0]

                # Aggregate metrics
                total_tables_served = sum(
                    float(r['tables_served'] or 0) for r in rows)
                total_tables_validated = sum(
                    float(r['tables_served_validated'] or 0) for r in rows)
                total_takeout = sum(
                    float(r['takeout_tables'] or 0) for r in rows)
                total_revenue = sum(
                    float(r['revenue_tax_not_included'] or 0) for r in rows)
                total_customers = sum(float(r['customers'] or 0) for r in rows)
                total_discount = sum(
                    float(r['discount_total'] or 0) for r in rows)
                # Store seating capacity mapping (from business knowledge)
                # This is consistent with existing code patterns in the codebase
                store_seating_capacity = {
                    1: 53, 2: 36, 3: 48, 4: 70, 5: 55, 6: 56, 7: 57}

                # Calculate proper monthly cumulative turnover rate
                # Method 1: Weighted average by seating capacity (more accurate)
                if first_row['store_id'] in store_seating_capacity:
                    seating_capacity = store_seating_capacity[first_row['store_id']]
                    # Use total tables served divided by total available seats-days
                    avg_turnover = total_tables_validated / \
                        (seating_capacity * len(rows)) if len(rows) > 0 else 0
                else:
                    # Fallback: Use high-precision arithmetic mean (preserve decimal precision)
                    # This avoids precision loss from rounding individual daily rates
                    avg_turnover = sum(float(r['turnover_rate'] or 0)
                                       for r in rows) / len(rows) if rows else 0

                aggregated[store_id] = {
                    'store_id': store_id,
                    'store_name': first_row['store_name'],
                    'tables_served': total_tables_served,
                    'tables_served_validated': total_tables_validated,
                    'takeout_tables': total_takeout,
                    'revenue_tax_not_included': total_revenue,
                    'customers': total_customers,
                    'discount_total': total_discount,
                    'turnover_rate': avg_turnover,
                    'target_revenue': first_row.get('target_revenue', 100000),
                    'days_count': len(rows),
                    # Additional calculated fields
                    'monthly_tables': total_tables_served,
                    'monthly_tables_validated': total_tables_validated,
                    'monthly_revenue': total_revenue,
                    'monthly_discount_total': total_discount,
                    'avg_turnover_rate': avg_turnover,
                    'avg_per_table': total_revenue / total_tables_served if total_tables_validated > 0 else 0,
                    # MTD fields - FIXED: Explicit naming for both validated and non-validated
                    'mtd_tables': total_tables_served,                    # Non-validated MTD tables
                    'mtd_tables_validated': total_tables_validated,      # Validated MTD tables
                    'mtd_revenue': total_revenue,
                    'mtd_discount_total': total_discount,
                    # Previous period fields
                    'prev_monthly_tables': total_tables_served,
                    'prev_monthly_tables_validated': total_tables_validated,
                    'prev_monthly_revenue': total_revenue,
                    'prev_avg_turnover_rate': avg_turnover,
                    # Non-validated prev MTD tables
                    'prev_mtd_tables': total_tables_served,
                    'prev_mtd_tables_validated': total_tables_validated,  # Validated prev MTD tables
                    'prev_mtd_revenue': total_revenue,
                    # Average per table for full month (not MTD)
                    'prev_month_avg_per_table': total_revenue / total_tables_served if total_tables_served > 0 else 0,
                    # Yearly comparison fields - FIXED: Explicit separate fields for clarity
                    # Non-validated tables (for consumption calculations)
                    'total_tables': total_tables_served,
                    # Validated tables (for table count display)
                    'total_tables_validated': total_tables_validated,
                    'total_revenue': total_revenue,
                    'avg_turnover_rate': avg_turnover,
                    'avg_per_table': total_revenue / total_tables_served if total_tables_served > 0 else 0
                }

            return list(aggregated.values())

        # Process each period
        daily_data = aggregate_store_data(data_by_period.get('target_day', {}))

        # Combine current_year_mtd and target_day for complete monthly data
        combined_monthly_data = {}
        for period in ['current_year_mtd', 'target_day']:
            period_data = data_by_period.get(period, {})
            for store_id, rows in period_data.items():
                if store_id not in combined_monthly_data:
                    combined_monthly_data[store_id] = []
                combined_monthly_data[store_id].extend(rows)

        monthly_data = aggregate_store_data(combined_monthly_data)

        # Combine prev_month and prev_month_mtd for complete previous month data
        combined_prev_month_data = {}
        for period in ['prev_month', 'prev_month_mtd']:
            period_data = data_by_period.get(period, {})
            for store_id, rows in period_data.items():
                if store_id not in combined_prev_month_data:
                    combined_prev_month_data[store_id] = []
                combined_prev_month_data[store_id].extend(rows)

        previous_month_data = aggregate_store_data(combined_prev_month_data)
        current_mtd = aggregate_store_data(combined_monthly_data)
        prev_mtd = aggregate_store_data(
            data_by_period.get('prev_month_mtd', {}))
        yearly_current = aggregate_store_data(combined_monthly_data)
        yearly_previous = aggregate_store_data(
            data_by_period.get('prev_year_mtd', {}))

        # Calculate rankings
        daily_ranking_names = []
        monthly_ranking_names = []
        daily_ranking_values = []
        monthly_ranking_values = []

        if daily_data:
            daily_sorted = sorted(
                daily_data, key=lambda x: x['turnover_rate'], reverse=True)
            daily_ranking_names = [row['store_name'] for row in daily_sorted]
            daily_ranking_values = [row['turnover_rate']
                                    for row in daily_sorted]

        if monthly_data:
            monthly_sorted = sorted(
                monthly_data, key=lambda x: x['avg_turnover_rate'], reverse=True)
            monthly_ranking_names = [row['store_name']
                                     for row in monthly_sorted]
            monthly_ranking_values = [row['avg_turnover_rate']
                                      for row in monthly_sorted]

        return (daily_data, monthly_data, previous_month_data, current_mtd, prev_mtd,
                yearly_current, yearly_previous, daily_ranking_names, monthly_ranking_names,
                daily_ranking_values, monthly_ranking_values)

    def get_all_processed_data(self, target_date: str):
        """Get and process all data needed for report generation"""

        # Get all data in single query
        all_data = self.get_all_report_data(target_date)

        if not all_data:
            return None

        # Process all data client-side
        processed_data = self.process_comprehensive_data(all_data)

        if not processed_data[0]:  # daily_data
            return None

        return processed_data

    def get_time_segment_data(self, target_date: str):
        """Get time segment data from store_time_report table"""
        from datetime import datetime

        # Parse target date to get current and previous year/month
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        current_year = target_dt.year
        current_month = target_dt.month
        target_day = target_dt.day

        prev_year = current_year - 1

        # Use separate queries to avoid Cartesian products
        sql_base = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            ts.label as time_segment,
            ts.id as time_segment_id,
            -- Current year target date data
            str_current.tables_served_validated as current_tables,
            str_current.turnover_rate as current_turnover,
            -- Previous year same date data
            str_prev.tables_served_validated as prev_year_tables,
            str_prev.turnover_rate as prev_year_turnover,
            -- Time segment target data
            smtt.turnover_rate as target_turnover
        FROM store s
        CROSS JOIN time_segment ts
        LEFT JOIN store_time_report str_current ON s.id = str_current.store_id 
            AND ts.id = str_current.time_segment_id
            AND str_current.date = %s
        LEFT JOIN store_time_report str_prev ON s.id = str_prev.store_id 
            AND ts.id = str_prev.time_segment_id
            AND str_prev.date = %s
        LEFT JOIN store_monthly_time_target smtt ON s.id = smtt.store_id 
            AND ts.id = smtt.time_segment_id
            AND EXTRACT(YEAR FROM smtt.month) = %s 
            AND EXTRACT(MONTH FROM smtt.month) = %s
        WHERE s.id BETWEEN 1 AND 7
        ORDER BY s.id, ts.id
        """

        # Calculate previous year target date
        prev_year_target_date = f"{prev_year}-{current_month:02d}-{target_day:02d}"

        try:
            # Get base data
            base_results = self.db_manager.fetch_all(sql_base, (
                target_date,  # Current year target date
                prev_year_target_date,  # Previous year same date
                current_year, current_month  # Target data
            ))

            # Get MTD aggregates separately to avoid Cartesian products
            mtd_sql = """
            SELECT 
                store_id, 
                time_segment_id,
                AVG(turnover_rate) as mtd_avg_turnover,
                SUM(tables_served_validated) as mtd_total_tables
            FROM store_time_report 
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
                AND EXTRACT(DAY FROM date) <= %s
            GROUP BY store_id, time_segment_id
            """

            mtd_results = self.db_manager.fetch_all(
                mtd_sql, (current_year, current_month, target_day))

            # Get previous year MTD aggregates (up to target day)
            prev_full_month_sql = """
            SELECT 
                store_id, 
                time_segment_id,
                AVG(turnover_rate) as prev_full_month_avg_turnover
            FROM store_time_report 
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
                AND EXTRACT(DAY FROM date) <= %s
            GROUP BY store_id, time_segment_id
            """

            prev_full_results = self.db_manager.fetch_all(
                prev_full_month_sql, (prev_year, current_month, target_day))

            # Get previous year MTD aggregates
            prev_mtd_sql = """
            SELECT 
                store_id, 
                time_segment_id,
                SUM(tables_served_validated) as prev_mtd_total_tables
            FROM store_time_report 
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
                AND EXTRACT(DAY FROM date) <= %s
            GROUP BY store_id, time_segment_id
            """

            prev_mtd_results = self.db_manager.fetch_all(
                prev_mtd_sql, (prev_year, current_month, target_day))

            # Create lookup dictionaries for aggregated data
            mtd_lookup = {(row['store_id'], row['time_segment_id'])                          : row for row in mtd_results}
            prev_full_lookup = {
                (row['store_id'], row['time_segment_id']): row for row in prev_full_results}
            prev_mtd_lookup = {
                (row['store_id'], row['time_segment_id']): row for row in prev_mtd_results}

            # Combine base results with aggregated data
            results = []
            for base_row in base_results:
                store_id = base_row['store_id']
                time_segment_id = base_row['time_segment_id']

                # Get aggregated data
                mtd_data = mtd_lookup.get((store_id, time_segment_id), {})
                prev_full_data = prev_full_lookup.get(
                    (store_id, time_segment_id), {})
                prev_mtd_data = prev_mtd_lookup.get(
                    (store_id, time_segment_id), {})

                # Combine all data
                combined_row = dict(base_row)
                combined_row.update({
                    'mtd_avg_turnover': mtd_data.get('mtd_avg_turnover'),
                    'mtd_total_tables': mtd_data.get('mtd_total_tables'),
                    'prev_full_month_avg_turnover': prev_full_data.get('prev_full_month_avg_turnover'),
                    'prev_mtd_total_tables': prev_mtd_data.get('prev_mtd_total_tables')
                })

                results.append(combined_row)

            # Process results into the format expected by time segment worksheet
            time_segment_data = {}

            for row in results:
                store_id = row['store_id']
                time_segment = row['time_segment']

                if store_id not in time_segment_data:
                    time_segment_data[store_id] = {}

                # Extract data from the new query structure (preserve Decimal precision)
                time_segment_data[store_id][time_segment] = {
                    # Daily data for target date
                    'turnover_current': row['current_turnover'] or 0,
                    'tables': row['current_tables'] or 0,
                    # Using current day tables as customers
                    'customers': row['current_tables'] or 0,

                    # Previous year data
                    'turnover_prev': row['prev_year_turnover'] or 0,
                    'prev_full_month_avg_turnover': row['prev_full_month_avg_turnover'] or 0,

                    # Target data
                    'target': row['target_turnover'] or 0,

                    # MTD data for current year
                    'mtd_avg_turnover': row['mtd_avg_turnover'] or 0,
                    'mtd_total_tables': row['mtd_total_tables'] or 0,

                    # MTD data for previous year
                    'prev_mtd_total_tables': row['prev_mtd_total_tables'] or 0,
                    'customers_prev_year': row['prev_mtd_total_tables'] or 0
                }

            return time_segment_data

        except Exception as e:
            print(f"❌ Error getting time segment data: {e}")
            return {}

    def get_daily_store_performance(self, target_date: str):
        """
        Get daily store performance data for tracking worksheet.

        Args:
            target_date: Target date in YYYY-MM-DD format

        Returns:
            List of store performance data dictionaries
        """
        from datetime import datetime

        # Parse target date to get previous year equivalent
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        prev_year = target_dt.year - 1
        prev_year_date = f"{prev_year}-{target_dt.month:02d}-{target_dt.day:02d}"

        # Define individual store managers as per reference sheet
        store_managers = {
            1: '张森磊',
            2: '潘幸远',
            3: 'Bao Xiaoyun',
            4: '李俊娟',
            5: '陈浩',
            6: '高新菊',
            7: '潘幸远'
        }

        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            s.seats_total as seating_capacity,
            COALESCE(
                (SELECT AVG(turnover_rate) 
                 FROM daily_report dr2 
                 WHERE dr2.store_id = s.id 
                   AND dr2.date >= '2024-01-01' 
                   AND dr2.date <= '2024-12-31'), 
                5.0
            ) as annual_avg_turnover_2024,
            -- Current year data (2025-06-28)
            dr_current.turnover_rate as current_turnover_rate,
            dr_current.revenue_tax_not_included / 10000.0 as current_revenue,
            -- Previous year data (2024-06-28)
            dr_prev.turnover_rate as prev_turnover_rate,
            dr_prev.revenue_tax_not_included / 10000.0 as prev_revenue
        FROM store s
        LEFT JOIN daily_report dr_current ON s.id = dr_current.store_id 
            AND dr_current.date = %s
        LEFT JOIN daily_report dr_prev ON s.id = dr_prev.store_id 
            AND dr_prev.date = %s
        WHERE s.id BETWEEN 1 AND 7
        ORDER BY s.id
        """

        try:
            results = self.db_manager.fetch_all(
                sql, (target_date, prev_year_date))

            # Convert to expected format
            performance_data = []
            for row in results:
                store_id = row['store_id']
                performance_data.append({
                    'store_id': store_id,
                    'store_name': row['store_name'],
                    # Use individual managers
                    'manager_name': store_managers.get(store_id, '蒋冰遇'),
                    'seating_capacity': row.get('seating_capacity', 0),
                    'annual_avg_turnover_2024': row.get('annual_avg_turnover_2024', 0),
                    # Current year data (preserve Decimal precision)
                    'current_turnover_rate': row.get('current_turnover_rate', 0),
                    'current_revenue': row.get('current_revenue', 0),
                    # Previous year data (preserve Decimal precision)
                    'prev_turnover_rate': row.get('prev_turnover_rate', 0),
                    'prev_revenue': row.get('prev_revenue', 0)
                })

            return performance_data

        except Exception as e:
            print(f"❌ Error getting daily store performance data: {e}")
            return []

    def get_gross_margin_dish_price_data(self, target_date: str):
        """
        Get dish price data for gross margin analysis.

        Args:
            target_date: Target date in YYYY-MM-DD format

        Returns:
            List of dish price data dictionaries
        """
        from datetime import datetime

        # Parse target date to get year and month
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        current_year = target_dt.year
        current_month = target_dt.month

        # Calculate previous month and year
        if current_month == 1:
            prev_month = 12
            prev_month_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_month_year = current_year

        prev_year = current_year - 1

        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            '加拿大' as region,
            d.full_code as dish_code,
            SUBSTRING(d.full_code, 1, 8) as dish_short_code,
            d.name as dish_name,
            d.size as specification,
            CONCAT(s.name, d.full_code) as unique_code,
            '' as combo_code,
            0 as dish_weight_kg,
            '' as dish_unit,
            
            -- Current period sales data (from dish_monthly_sale)
            COALESCE(dms.sale_amount, 0) as current_period_sales,
            COALESCE(dms.sale_amount, 0) as theoretical_usage,
            
            -- Price data from dish_price_history
            COALESCE(dph_current.price, 0) as current_price,
            COALESCE(dph_prev.price, 0) as previous_price,
            COALESCE(dph_prev_year.price, 0) as last_year_price,
            
            -- Aggregated material data: all materials for this dish with material number
            COALESCE(
                STRING_AGG(
                    CASE 
                        WHEN m.name IS NOT NULL AND dm.standard_quantity IS NOT NULL THEN
                            m.material_number || ' - ' || m.name || ' - ' || ROUND(dm.standard_quantity * COALESCE(dms.sale_amount, 0), 2)::text
                        ELSE NULL
                    END, 
                    E'\n' 
                    ORDER BY m.material_number
                ), 
                ''
            ) as material_list_with_usage,
            
            -- Total material cost for this dish: sum(material_price * standard_quantity * dish_sales)
            COALESCE(
                SUM(
                    CASE 
                        WHEN mph.price IS NOT NULL AND dm.standard_quantity IS NOT NULL AND dms.sale_amount IS NOT NULL THEN
                            mph.price * dm.standard_quantity * dms.sale_amount
                        ELSE 0
                    END
                ), 
                0
            ) as total_material_cost,
            
            -- Keep individual material fields for backward compatibility
            '' as material_code,
            '' as material_name,
            0 as material_price_per_kg,
            0 as current_material_usage,
            
            -- Combo data (placeholder)
            0 as combo_usage,
            0 as combo_sales,
            
            -- Additional fields
            '' as price_adjustment_date,
            0 as click_rate,
            0 as actual_gross_margin,
            '' as dish_category,
            
            -- Loss analysis (placeholder)
            0 as theoretical_usage_loss,
            0 as actual_usage_loss,
            0 as current_month_loss_cost,
            0 as previous_month_loss_cost,
            0 as comparable_period_loss_cost
            
        FROM store s
        CROSS JOIN dish d
        LEFT JOIN dish_monthly_sale dms ON d.id = dms.dish_id 
            AND s.id = dms.store_id
            AND dms.year = %s
            AND dms.month = %s
        LEFT JOIN dish_price_history dph_current ON d.id = dph_current.dish_id
            AND s.id = dph_current.store_id
            AND dph_current.is_active = true
            AND EXTRACT(YEAR FROM dph_current.effective_date) = %s
            AND EXTRACT(MONTH FROM dph_current.effective_date) = %s
        LEFT JOIN dish_price_history dph_prev ON d.id = dph_prev.dish_id
            AND s.id = dph_prev.store_id
            AND dph_prev.is_active = true
            AND EXTRACT(YEAR FROM dph_prev.effective_date) = %s
            AND EXTRACT(MONTH FROM dph_prev.effective_date) = %s
        LEFT JOIN dish_price_history dph_prev_year ON d.id = dph_prev_year.dish_id
            AND s.id = dph_prev_year.store_id
            AND dph_prev_year.is_active = true
            AND EXTRACT(YEAR FROM dph_prev_year.effective_date) = %s
            AND EXTRACT(MONTH FROM dph_prev_year.effective_date) = %s
        LEFT JOIN dish_material dm ON d.id = dm.dish_id
        LEFT JOIN material m ON dm.material_id = m.id
        LEFT JOIN material_price_history mph ON m.id = mph.material_id
            AND s.id = mph.store_id
            AND mph.is_active = true
            AND EXTRACT(YEAR FROM mph.effective_date) = %s
            AND EXTRACT(MONTH FROM mph.effective_date) = %s
        WHERE s.id BETWEEN 1 AND 7
            AND (dms.sale_amount > 0 OR dph_current.price > 0)
        GROUP BY s.id, s.name, d.id, d.full_code, d.name, d.size, 
                 dms.sale_amount, dph_current.price, dph_prev.price, dph_prev_year.price
        ORDER BY s.id, d.full_code
        """

        try:
            results = self.db_manager.fetch_all(sql, (
                current_year, current_month,  # mds current period
                current_year, current_month,  # dph_current
                prev_month_year, prev_month,  # dph_prev
                prev_year, current_month,     # dph_prev_year
                current_year, current_month   # mph current
            ))

            return results

        except Exception as e:
            print(f"❌ Error getting gross margin dish price data: {e}")
            return []

    def get_gross_margin_material_cost_data(self, target_date: str):
        """
        Get material cost data for gross margin analysis.

        Args:
            target_date: Target date in YYYY-MM-DD format

        Returns:
            List of material cost data dictionaries
        """
        from datetime import datetime

        # Parse target date
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        current_year = target_dt.year
        current_month = target_dt.month

        # Calculate previous month
        if current_month == 1:
            prev_month = 12
            prev_month_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_month_year = current_year

        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            m.material_number,
            m.name as material_name,
            
            -- Current period price
            COALESCE(mph_current.price, 0) as current_price,
            
            -- Previous period price
            COALESCE(mph_prev.price, 0) as previous_price,
            
            -- Usage data from material_monthly_usage
            COALESCE(mmu.material_used, 0) as current_usage,
            COALESCE(mph_current.price * mmu.material_used, 0) as current_cost,
            
            -- Calculate cost impact
            CASE 
                WHEN mph_prev.price > 0 AND mmu.material_used > 0 THEN
                    (mph_current.price - mph_prev.price) * mmu.material_used
                ELSE 0
            END as cost_impact
            
        FROM store s
        CROSS JOIN material m
        LEFT JOIN material_price_history mph_current ON m.id = mph_current.material_id
            AND s.id = mph_current.store_id
            AND mph_current.is_active = true
            AND EXTRACT(YEAR FROM mph_current.effective_date) = %s
            AND EXTRACT(MONTH FROM mph_current.effective_date) = %s
        LEFT JOIN material_price_history mph_prev ON m.id = mph_prev.material_id
            AND s.id = mph_prev.store_id
            AND mph_prev.is_active = true
            AND EXTRACT(YEAR FROM mph_prev.effective_date) = %s
            AND EXTRACT(MONTH FROM mph_prev.effective_date) = %s
        LEFT JOIN material_monthly_usage mmu ON m.id = mmu.material_id
            AND s.id = mmu.store_id
            AND mmu.year = %s
            AND mmu.month = %s
        WHERE s.id BETWEEN 1 AND 7
            AND (mph_current.price > 0 OR mmu.material_used > 0)
        ORDER BY s.id, m.material_number
        """

        try:
            results = self.db_manager.fetch_all(sql, (
                current_year, current_month,  # mph_current
                prev_month_year, prev_month,  # mph_prev
                current_year, current_month   # mmu current
            ))

            return results

        except Exception as e:
            print(f"❌ Error getting gross margin material cost data: {e}")
            return []

    def get_gross_margin_discount_data(self, target_date: str):
        """
        Get discount data for gross margin analysis.

        Args:
            target_date: Target date in YYYY-MM-DD format

        Returns:
            List of discount data dictionaries
        """
        from datetime import datetime

        # Parse target date
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        current_year = target_dt.year
        current_month = target_dt.month

        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            SUM(dr.discount_total) as total_discount,
            SUM(dr.revenue_tax_not_included) as total_revenue,
            CASE 
                WHEN SUM(dr.revenue_tax_not_included) > 0 THEN
                    SUM(dr.discount_total) / SUM(dr.revenue_tax_not_included) * 100
                ELSE 0
            END as discount_percentage,
            COUNT(*) as days_with_discount
        FROM store s
        LEFT JOIN daily_report dr ON s.id = dr.store_id
            AND EXTRACT(YEAR FROM dr.date) = %s
            AND EXTRACT(MONTH FROM dr.date) = %s
        WHERE s.id BETWEEN 1 AND 7
        GROUP BY s.id, s.name
        ORDER BY s.id
        """

        try:
            results = self.db_manager.fetch_all(
                sql, (current_year, current_month))
            return results

        except Exception as e:
            print(f"❌ Error getting gross margin discount data: {e}")
            return []
