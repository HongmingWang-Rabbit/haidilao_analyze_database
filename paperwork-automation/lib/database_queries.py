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
                    # MTD fields
                    'mtd_tables_served': total_tables_served,
                    'mtd_tables': total_tables_validated,
                    'mtd_revenue': total_revenue,
                    'mtd_discount_total': total_discount,
                    # Previous period fields
                    'prev_monthly_tables': total_tables_served,
                    'prev_monthly_tables_validated': total_tables_validated,
                    'prev_monthly_revenue': total_revenue,
                    'prev_avg_turnover_rate': avg_turnover,
                    'prev_mtd_tables': total_tables_served,
                    'prev_mtd_revenue': total_revenue,
                    # Average per table for full month (not MTD)
                    'prev_month_avg_per_table': total_revenue / total_tables_served if total_tables_served > 0 else 0,
                    # Yearly comparison fields
                    'total_tables': total_tables_validated,
                    'total_revenue': total_revenue,
                    'avg_turnover_rate': avg_turnover,
                    'avg_per_table': total_revenue / total_tables_served if total_tables_validated > 0 else 0
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

            # Get previous year full month aggregates
            prev_full_month_sql = """
            SELECT 
                store_id, 
                time_segment_id,
                AVG(turnover_rate) as prev_full_month_avg_turnover
            FROM store_time_report 
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
            GROUP BY store_id, time_segment_id
            """

            prev_full_results = self.db_manager.fetch_all(
                prev_full_month_sql, (prev_year, current_month))

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
            mtd_lookup = {(row['store_id'], row['time_segment_id'])
                           : row for row in mtd_results}
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
