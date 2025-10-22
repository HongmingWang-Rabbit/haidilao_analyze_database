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

# Import centralized store configuration
from configs.store_config import STORE_MANAGERS, STORE_SEATING_CAPACITY


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
                # Store seating capacity from centralized config
                store_seating_capacity = STORE_SEATING_CAPACITY

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

        # Process year-over-year data with proper field mapping
        prev_year_data = aggregate_store_data(
            data_by_period.get('prev_year_mtd', {}))
        prev_year_mtd_data = aggregate_store_data(
            data_by_period.get('prev_year_mtd', {}))

        # Add year-over-year fields to the aggregated data
        def add_yearly_fields(data_list, prev_year_list, prev_year_mtd_list):
            """Add year-over-year comparison fields to each store's data"""
            for store_data in data_list:
                store_id = store_data['store_id']

                # Find corresponding previous year data
                prev_year_store = next(
                    (s for s in prev_year_list if s['store_id'] == store_id), {})
                prev_year_mtd_store = next(
                    (s for s in prev_year_mtd_list if s['store_id'] == store_id), {})

                # Add year-over-year fields
                store_data['prev_yearly_tables'] = prev_year_store.get(
                    'total_tables', 0)
                store_data['prev_yearly_tables_validated'] = prev_year_store.get(
                    'total_tables_validated', 0)
                store_data['prev_yearly_revenue'] = prev_year_store.get(
                    'total_revenue', 0)
                store_data['prev_yearly_mtd_tables'] = prev_year_mtd_store.get(
                    'total_tables', 0)
                store_data['prev_yearly_mtd_tables_validated'] = prev_year_mtd_store.get(
                    'total_tables_validated', 0)
                store_data['prev_yearly_mtd_revenue'] = prev_year_mtd_store.get(
                    'total_revenue', 0)

            return data_list

        # Add year-over-year fields to all relevant datasets
        monthly_data = add_yearly_fields(
            monthly_data, prev_year_data, prev_year_mtd_data)
        current_mtd = add_yearly_fields(
            current_mtd, prev_year_data, prev_year_mtd_data)
        daily_data = add_yearly_fields(
            daily_data, prev_year_data, prev_year_mtd_data)

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
        from datetime import datetime, timedelta

        # Parse target date to get current and previous year/month
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        current_year = target_dt.year
        current_month = target_dt.month
        target_day = target_dt.day

        prev_year = current_year - 1

        # Helper function to find same weekday from previous year
        def find_same_weekday_previous_year(target_dt):
            """Find the nearest future date with same weekday in previous year"""
            # Get the same date in previous year
            same_date_prev_year = target_dt.replace(year=prev_year)

            # Get weekday of target date (0=Monday, 6=Sunday)
            target_weekday = target_dt.weekday()

            # Get weekday of same date in previous year
            prev_year_weekday = same_date_prev_year.weekday()

            # If weekdays are the same, use the same date
            if target_weekday == prev_year_weekday:
                return same_date_prev_year

            # Otherwise, find the nearest future date with same weekday
            days_to_add = (target_weekday - prev_year_weekday) % 7
            if days_to_add == 0:
                days_to_add = 7  # If same weekday, go to next week

            return same_date_prev_year + timedelta(days=days_to_add)

        # Calculate previous year dates
        prev_year_target_date = f"{prev_year}-{current_month:02d}-{target_day:02d}"
        prev_year_same_weekday_dt = find_same_weekday_previous_year(target_dt)
        prev_year_same_weekday_date = prev_year_same_weekday_dt.strftime(
            '%Y-%m-%d')

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
            -- Previous year same weekday data
            str_prev_weekday.tables_served_validated as prev_year_weekday_tables,
            str_prev_weekday.turnover_rate as prev_year_weekday_turnover,
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
        LEFT JOIN store_time_report str_prev_weekday ON s.id = str_prev_weekday.store_id 
            AND ts.id = str_prev_weekday.time_segment_id
            AND str_prev_weekday.date = %s
        LEFT JOIN store_monthly_time_target smtt ON s.id = smtt.store_id 
            AND ts.id = smtt.time_segment_id
            AND EXTRACT(YEAR FROM smtt.month) = %s 
            AND EXTRACT(MONTH FROM smtt.month) = %s
        WHERE s.id BETWEEN 1 AND 8
        ORDER BY s.id, ts.id
        """

        try:
            # Get base data
            base_results = self.db_manager.fetch_all(sql_base, (
                target_date,  # Current year target date
                prev_year_target_date,  # Previous year same date
                prev_year_same_weekday_date,  # Previous year same weekday date
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
            mtd_lookup = {(row['store_id'], row['time_segment_id']): row for row in mtd_results}
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

                    # Previous year same weekday data
                    'turnover_prev_weekday': row['prev_year_weekday_turnover'] or 0,
                    'tables_prev_weekday': row['prev_year_weekday_tables'] or 0,

                    # Target data
                    'target': row['target_turnover'] or 0,

                    # MTD data for current year
                    'mtd_avg_turnover': row['mtd_avg_turnover'] or 0,
                    'mtd_total_tables': row['mtd_total_tables'] or 0,

                    # MTD data for previous year
                    'prev_mtd_total_tables': row['prev_mtd_total_tables'] or 0,
                    'customers_prev_year': row['prev_mtd_total_tables'] or 0,

                    # Store the weekday comparison date for reference
                    'prev_year_weekday_date': prev_year_same_weekday_date
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

        # Store managers from centralized config
        store_managers = STORE_MANAGERS

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
        WHERE s.id BETWEEN 1 AND 8
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

    def get_weekly_store_performance(self, start_date: str, end_date: str):
        """
        Get weekly store performance data for tracking worksheet (7-day aggregation).

        Args:
            start_date: Start date of the 7-day period in YYYY-MM-DD format
            end_date: End date of the 7-day period in YYYY-MM-DD format

        Returns:
            List of store performance data dictionaries with weekly aggregations
        """
        from datetime import datetime, timedelta

        # Parse dates to get previous year equivalent period with same weekday alignment
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Calculate previous year dates with same weekday alignment
        prev_year_base_end = end_dt.replace(year=end_dt.year - 1)
        
        # Find the nearest date with the same weekday as end_dt
        weekday_diff = end_dt.weekday() - prev_year_base_end.weekday()
        if weekday_diff > 3:  # If difference is more than 3 days forward, go back a week
            weekday_diff -= 7
        elif weekday_diff < -3:  # If difference is more than 3 days backward, go forward a week
            weekday_diff += 7
        
        prev_year_end_dt = prev_year_base_end + timedelta(days=weekday_diff)
        prev_year_start_dt = prev_year_end_dt - timedelta(days=6)  # 7 days including end date
        
        prev_year_start = prev_year_start_dt.strftime('%Y-%m-%d')
        prev_year_end = prev_year_end_dt.strftime('%Y-%m-%d')

        # Store managers from centralized config
        store_managers = STORE_MANAGERS

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
            -- Current year weekly data (7-day aggregation)
            COALESCE(AVG(dr_current.turnover_rate), 0) as current_avg_turnover_rate,
            COALESCE(SUM(dr_current.revenue_tax_not_included) / 10000.0, 0) as current_total_revenue,
            -- Previous year weekly data (7-day aggregation)
            COALESCE(AVG(dr_prev.turnover_rate), 0) as prev_avg_turnover_rate,
            COALESCE(SUM(dr_prev.revenue_tax_not_included) / 10000.0, 0) as prev_total_revenue
        FROM store s
        LEFT JOIN daily_report dr_current ON s.id = dr_current.store_id
            AND dr_current.date >= %s AND dr_current.date <= %s
        LEFT JOIN daily_report dr_prev ON s.id = dr_prev.store_id
            AND dr_prev.date >= %s AND dr_prev.date <= %s
        WHERE s.id BETWEEN 1 AND 8
        GROUP BY s.id, s.name, s.seats_total
        ORDER BY s.id
        """

        try:
            results = self.db_manager.fetch_all(
                sql, (start_date, end_date, prev_year_start, prev_year_end))

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
                    # Current year weekly data (preserve Decimal precision)
                    'current_avg_turnover_rate': row.get('current_avg_turnover_rate', 0),
                    'current_total_revenue': row.get('current_total_revenue', 0),
                    # Previous year weekly data (preserve Decimal precision)
                    'prev_avg_turnover_rate': row.get('prev_avg_turnover_rate', 0),
                    'prev_total_revenue': row.get('prev_total_revenue', 0)
                })

            return performance_data

        except Exception as e:
            print(f"❌ Error getting weekly store performance data: {e}")
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
        WITH dish_current_price AS (
            SELECT 
                dish_id, store_id, price,
                MIN(effective_date) as earliest_price_date
            FROM dish_price_history
            WHERE is_active = true
                AND EXTRACT(YEAR FROM effective_date) = %s
                AND EXTRACT(MONTH FROM effective_date) = %s
            GROUP BY dish_id, store_id, price
        ),
        dish_previous_price AS (
            SELECT DISTINCT ON (dish_id, store_id)
                dish_id, store_id, price
            FROM dish_price_history
            WHERE is_active = true
                AND (
                    EXTRACT(YEAR FROM effective_date) < %s
                    OR (EXTRACT(YEAR FROM effective_date) = %s AND EXTRACT(MONTH FROM effective_date) < %s)
                )
            ORDER BY dish_id, store_id, effective_date DESC
        ),
        dish_last_year_price AS (
            -- Get the most recent price before same period last year for each dish (not per store)
            SELECT DISTINCT ON (dish_id)
                dish_id, price, effective_date
            FROM dish_price_history
            WHERE is_active = true
                AND effective_date <= %s
            ORDER BY dish_id, effective_date DESC
        ),
        -- Aggregate dish sales across all sales modes first
        aggregated_dish_sales AS (
            SELECT 
                dish_id,
                store_id,
                SUM(COALESCE(sale_amount, 0)) as total_sale_amount,
                SUM(COALESCE(return_amount, 0)) as total_return_amount,
                SUM(COALESCE(free_meal_amount, 0)) as total_free_meal_amount,
                SUM(COALESCE(gift_amount, 0)) as total_gift_amount
            FROM dish_monthly_sale
            WHERE year = %s AND month = %s
            GROUP BY dish_id, store_id
        ),
        -- Calculate theoretical usage (dish_sales * standard_quantity * loss_rate)
        dish_theoretical_usage AS (
            SELECT 
                d.id as dish_id,
                s.id as store_id,
                -- Regular dish sales theoretical usage (now aggregated across all sales modes)
                COALESCE(
                    SUM((COALESCE(ads.total_sale_amount, 0) - COALESCE(ads.total_return_amount, 0)) * 
                        COALESCE(dm.standard_quantity, 0) * COALESCE(dm.loss_rate, 1.0) / COALESCE(NULLIF(dm.unit_conversion_rate, 0), 1.0)), 
                    0
                ) as regular_theoretical_usage,
                -- Combo dish sales theoretical usage
                COALESCE(
                    SUM(COALESCE(mcds.sale_amount, 0) * 
                        COALESCE(dm.standard_quantity, 0) * COALESCE(dm.loss_rate, 1.0) / COALESCE(NULLIF(dm.unit_conversion_rate, 0), 1.0)), 
                    0
                ) as combo_theoretical_usage
            FROM dish d
            CROSS JOIN store s
            LEFT JOIN aggregated_dish_sales ads ON d.id = ads.dish_id 
                AND s.id = ads.store_id
            LEFT JOIN monthly_combo_dish_sale mcds ON d.id = mcds.dish_id 
                AND s.id = mcds.store_id
                AND mcds.year = %s AND mcds.month = %s
            LEFT JOIN dish_material dm ON d.id = dm.dish_id
            WHERE s.id BETWEEN 1 AND 8
            GROUP BY d.id, s.id
        ),
        -- Get actual usage from material_monthly_usage (current, previous month, last year)
        dish_actual_usage AS (
            SELECT 
                d.id as dish_id,
                s.id as store_id,
                -- Current month actual usage
                COALESCE(SUM(CASE WHEN mmu.year = %s AND mmu.month = %s THEN mmu.material_used ELSE 0 END), 0) as actual_material_usage,
                -- Previous month actual usage
                COALESCE(SUM(CASE WHEN mmu.year = %s AND mmu.month = %s THEN mmu.material_used ELSE 0 END), 0) as prev_actual_usage,
                -- Last year same period actual usage
                COALESCE(SUM(CASE WHEN mmu.year = %s AND mmu.month = %s THEN mmu.material_used ELSE 0 END), 0) as ly_actual_usage
            FROM dish d
            CROSS JOIN store s
            LEFT JOIN dish_material dm ON d.id = dm.dish_id
            LEFT JOIN material_monthly_usage mmu ON dm.material_id = mmu.material_id
                AND s.id = mmu.store_id
                AND (
                    (mmu.year = %s AND mmu.month = %s) OR  -- Current month
                    (mmu.year = %s AND mmu.month = %s) OR  -- Previous month
                    (mmu.year = %s AND mmu.month = %s)     -- Last year same month
                )
            WHERE s.id BETWEEN 1 AND 8
            GROUP BY d.id, s.id
        ),
        -- Get combo sales data
        dish_combo_sales AS (
            SELECT 
                d.id as dish_id,
                s.id as store_id,
                COALESCE(SUM(mcds.sale_amount), 0) as combo_sales_amount
            FROM dish d
            CROSS JOIN store s
            LEFT JOIN monthly_combo_dish_sale mcds ON d.id = mcds.dish_id
                AND s.id = mcds.store_id
                AND mcds.year = %s AND mcds.month = %s
            WHERE s.id BETWEEN 1 AND 8
            GROUP BY d.id, s.id
        )
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
            
            -- Current period sales data (aggregated across all sales modes)
            COALESCE(ads.total_sale_amount, 0) as current_period_sales,
            
            -- Use corrected theoretical usage calculation
            COALESCE(dtu.regular_theoretical_usage, 0) as theoretical_usage,
            COALESCE(dtu.combo_theoretical_usage, 0) as combo_usage,
            
            -- Price data: use current price as fallback for missing historical prices
            COALESCE(dcp.price, 0) as current_price,
            COALESCE(dpp.price, dcp.price, 0) as previous_price,
            COALESCE(dlyp.price, dcp.price, 0) as last_year_price,
            
            -- Price adjustment date: earliest date of current price
            COALESCE(dcp.earliest_price_date, CURRENT_DATE) as price_adjustment_date,
            
            -- Aggregated material data: all materials for this dish with material number
            COALESCE(
                STRING_AGG(
                    CASE 
                        WHEN m.name IS NOT NULL AND dm.standard_quantity IS NOT NULL THEN
                            m.material_number || ' - ' || m.name || ' - ' || ROUND(dm.standard_quantity * COALESCE(ads.total_sale_amount, 0), 2)::text
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
                        WHEN mph.price IS NOT NULL AND dm.standard_quantity IS NOT NULL AND ads.total_sale_amount IS NOT NULL THEN
                            mph.price * dm.standard_quantity * ads.total_sale_amount
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
            
            -- Combo data from theoretical usage calculation
            COALESCE(dcs.combo_sales_amount, 0) as combo_sales,
            
            -- Loss analysis: theoretical vs actual usage
            COALESCE(dtu.regular_theoretical_usage, 0) as theoretical_usage_loss,
            COALESCE(dau.actual_material_usage, 0) as actual_usage_loss,
            
            -- Loss cost calculations: (actual_usage - theoretical_usage) * average_material_cost
            CASE 
                WHEN COALESCE(dau.actual_material_usage, 0) > COALESCE(dtu.regular_theoretical_usage, 0) 
                THEN (COALESCE(dau.actual_material_usage, 0) - COALESCE(dtu.regular_theoretical_usage, 0)) * COALESCE(AVG(mph.price), 5.0)
                ELSE 0
            END as current_month_loss_cost,
            
            -- Previous month loss cost (using current material price as estimate)
            CASE 
                WHEN COALESCE(dau.prev_actual_usage, 0) > COALESCE(dtu.regular_theoretical_usage, 0)
                THEN (COALESCE(dau.prev_actual_usage, 0) - COALESCE(dtu.regular_theoretical_usage, 0)) * COALESCE(AVG(mph.price), 5.0)
                ELSE 0
            END as previous_month_loss_cost,
            
            -- Comparable period (last year) loss cost (using current material price as estimate)
            CASE 
                WHEN COALESCE(dau.ly_actual_usage, 0) > COALESCE(dtu.regular_theoretical_usage, 0)
                THEN (COALESCE(dau.ly_actual_usage, 0) - COALESCE(dtu.regular_theoretical_usage, 0)) * COALESCE(AVG(mph.price), 5.0)
                ELSE 0
            END as comparable_period_loss_cost
            
        FROM store s
        CROSS JOIN dish d
        LEFT JOIN aggregated_dish_sales ads ON d.id = ads.dish_id 
            AND s.id = ads.store_id
        LEFT JOIN dish_current_price dcp ON d.id = dcp.dish_id
            AND s.id = dcp.store_id
        LEFT JOIN dish_previous_price dpp ON d.id = dpp.dish_id
            AND s.id = dpp.store_id
        LEFT JOIN dish_last_year_price dlyp ON d.id = dlyp.dish_id
        LEFT JOIN dish_material dm ON d.id = dm.dish_id
        LEFT JOIN material m ON dm.material_id = m.id
        LEFT JOIN material_price_history mph ON m.id = mph.material_id
            AND s.id = mph.store_id
            AND mph.is_active = true
            AND EXTRACT(YEAR FROM mph.effective_date) = %s
            AND EXTRACT(MONTH FROM mph.effective_date) = %s
        LEFT JOIN dish_theoretical_usage dtu ON d.id = dtu.dish_id
            AND s.id = dtu.store_id
        LEFT JOIN dish_actual_usage dau ON d.id = dau.dish_id
            AND s.id = dau.store_id
        LEFT JOIN dish_combo_sales dcs ON d.id = dcs.dish_id
            AND s.id = dcs.store_id
        WHERE s.id BETWEEN 1 AND 8
            AND (ads.total_sale_amount > 0 OR dcp.price > 0)
        GROUP BY s.id, s.name, d.id, d.full_code, d.name, d.size, 
                 ads.total_sale_amount, dcp.price, dpp.price, dlyp.price, dcp.earliest_price_date,
                 dtu.regular_theoretical_usage, dtu.combo_theoretical_usage, dau.actual_material_usage,
                 dau.prev_actual_usage, dau.ly_actual_usage, dcs.combo_sales_amount
        ORDER BY s.id, d.full_code
        """

        try:
            # Calculate last year same period date
            last_year_same_period = f"{prev_year}-{current_month:02d}-30"

            params = (
                current_year, current_month,  # dish_current_price
                prev_month_year, prev_month_year, prev_month,  # dish_previous_price
                last_year_same_period,  # dish_last_year_price
                current_year, current_month,  # aggregated_dish_sales
                # dish_theoretical_usage (both regular and combo)
                current_year, current_month,
                # dish_actual_usage (current, previous, last year)
                current_year, current_month,  # Current month
                prev_month_year, prev_month,  # Previous month  
                prev_year, current_month,     # Last year same month
                current_year, current_month,  # Current month (for WHERE clause)
                prev_month_year, prev_month,  # Previous month (for WHERE clause)
                prev_year, current_month,     # Last year same month (for WHERE clause)
                current_year, current_month,  # dish_combo_sales
                current_year, current_month   # mph current
            )

            results = self.db_manager.fetch_all(sql, params)

            return results

        except Exception as e:
            print(f"❌ Error getting gross margin dish price data: {e}")
            import traceback
            traceback.print_exc()
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
        WITH material_current_price AS (
            SELECT 
                material_id, store_id, price
            FROM material_price_history
            WHERE is_active = true
                AND EXTRACT(YEAR FROM effective_date) = %s
                AND EXTRACT(MONTH FROM effective_date) = %s
        ),
        material_previous_price AS (
            SELECT DISTINCT ON (material_id, store_id)
                material_id, store_id, price
            FROM material_price_history
            WHERE is_active = true
                AND (
                    EXTRACT(YEAR FROM effective_date) < %s
                    OR (EXTRACT(YEAR FROM effective_date) = %s AND EXTRACT(MONTH FROM effective_date) < %s)
                )
            ORDER BY material_id, store_id, effective_date DESC
        )
        SELECT 
            s.id as store_id,
            s.name as store_name,
            m.material_number,
            m.name as material_name,
            
            -- Current period price
            COALESCE(mcp.price, 0) as current_price,
            
            -- Previous period price: use current price as fallback
            COALESCE(mpp.price, mcp.price, 0) as previous_price,
            
            -- Usage data from material_monthly_usage
            COALESCE(mmu.material_used, 0) as current_usage,
            COALESCE(mcp.price * mmu.material_used, 0) as current_cost,
            
            -- Calculate cost impact using fallback logic
            CASE 
                WHEN COALESCE(mpp.price, mcp.price, 0) > 0 AND mmu.material_used > 0 THEN
                    (mcp.price - COALESCE(mpp.price, mcp.price, 0)) * mmu.material_used
                ELSE 0
            END as cost_impact
            
        FROM store s
        CROSS JOIN material m
        LEFT JOIN material_current_price mcp ON m.id = mcp.material_id
            AND s.id = mcp.store_id
        LEFT JOIN material_previous_price mpp ON m.id = mpp.material_id
            AND s.id = mpp.store_id
        LEFT JOIN material_monthly_usage mmu ON m.id = mmu.material_id
            AND s.id = mmu.store_id
            AND mmu.year = %s
            AND mmu.month = %s
        WHERE s.id BETWEEN 1 AND 8
            AND (mcp.price > 0 OR mmu.material_used > 0)
        ORDER BY s.id, m.material_number
        """

        try:
            results = self.db_manager.fetch_all(sql, (
                current_year, current_month,  # material_current_price
                prev_month_year, prev_month_year, prev_month,  # material_previous_price
                current_year, current_month   # mmu current
            ))

            return results

        except Exception as e:
            print(f"❌ Error getting gross margin material cost data: {e}")
            return []

    def get_store_gross_profit_data(self, target_date: str):
        """
        Get store gross profit data for all stores comparison.

        Args:
            target_date: Target date in YYYY-MM-DD format

        Returns:
            List of store gross profit data dictionaries
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

        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            COALESCE(cr.current_revenue, 0) as current_revenue,
            COALESCE(cc.current_cost, 0) as current_cost,
            COALESCE(pr.previous_revenue, 0) as previous_revenue,
            COALESCE(pc.previous_cost, 0) as previous_cost
        FROM store s
        LEFT JOIN (
            SELECT 
                store_id,
                SUM(sale_amount) as current_revenue
            FROM dish_monthly_sale
            WHERE year = %s AND month = %s
            GROUP BY store_id
        ) cr ON s.id = cr.store_id
        LEFT JOIN (
            SELECT 
                mmu.store_id,
                SUM(mmu.material_used * COALESCE(mph.price, 0)) as current_cost
            FROM material_monthly_usage mmu
            LEFT JOIN LATERAL (
                SELECT price 
                FROM material_price_history 
                WHERE material_id = mmu.material_id 
                    AND store_id = mmu.store_id 
                    AND is_active = true
                    AND effective_date <= (date_trunc('month', make_date(%s, %s, 1)) + interval '1 month - 1 day')::date
                ORDER BY effective_date DESC
                LIMIT 1
            ) mph ON true
            WHERE mmu.year = %s AND mmu.month = %s
            GROUP BY mmu.store_id
        ) cc ON s.id = cc.store_id
        LEFT JOIN (
            SELECT 
                store_id,
                SUM(revenue_tax_not_included) as previous_revenue
            FROM daily_report
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
            GROUP BY store_id
        ) pr ON s.id = pr.store_id
        LEFT JOIN (
            SELECT 
                store_id,
                -- Estimate previous month cost using previous month revenue * 65% (typical restaurant cost ratio)
                ROUND(SUM(revenue_tax_not_included) * 0.65, 2) as previous_cost
            FROM daily_report
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
            GROUP BY store_id
        ) pc ON s.id = pc.store_id
        WHERE s.id BETWEEN 1 AND 7
        ORDER BY s.id
        """

        try:
            # Workaround: Use separate queries instead of complex join due to parameter binding issues
            
            # 1. Get all stores
            stores_sql = "SELECT id as store_id, name as store_name FROM store WHERE id BETWEEN 1 AND 8 ORDER BY id"
            stores = self.db_manager.fetch_all(stores_sql)
            
            # 2. Get current revenue
            current_revenue_sql = """
            SELECT 
                store_id,
                SUM(sale_amount) as current_revenue
            FROM dish_monthly_sale
            WHERE year = %s AND month = %s
            GROUP BY store_id
            """
            current_revenue_data = self.db_manager.fetch_all(current_revenue_sql, (current_year, current_month))
            current_revenue_dict = {row['store_id']: row['current_revenue'] for row in current_revenue_data}
            
            # 3. Get current cost
            current_cost_sql = """
            SELECT 
                mmu.store_id,
                SUM(mmu.material_used * COALESCE(mph.price, 0)) as current_cost
            FROM material_monthly_usage mmu
            LEFT JOIN LATERAL (
                SELECT price 
                FROM material_price_history 
                WHERE material_id = mmu.material_id 
                    AND store_id = mmu.store_id 
                    AND is_active = true
                    AND effective_date <= (date_trunc('month', make_date(%s, %s, 1)) + interval '1 month - 1 day')::date
                ORDER BY effective_date DESC
                LIMIT 1
            ) mph ON true
            WHERE mmu.year = %s AND mmu.month = %s
            GROUP BY mmu.store_id
            """
            current_cost_data = self.db_manager.fetch_all(current_cost_sql, (current_year, current_month, current_year, current_month))
            current_cost_dict = {row['store_id']: row['current_cost'] for row in current_cost_data}
            
            # 4. Get previous revenue
            previous_revenue_sql = """
            SELECT 
                store_id,
                SUM(revenue_tax_not_included) as previous_revenue
            FROM daily_report
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
            GROUP BY store_id
            """
            previous_revenue_data = self.db_manager.fetch_all(previous_revenue_sql, (prev_month_year, prev_month))
            previous_revenue_dict = {row['store_id']: row['previous_revenue'] for row in previous_revenue_data}
            
            # 5. Get previous cost (estimated)
            previous_cost_sql = """
            SELECT 
                store_id,
                ROUND(SUM(revenue_tax_not_included) * 0.65, 2) as previous_cost
            FROM daily_report
            WHERE EXTRACT(YEAR FROM date) = %s 
                AND EXTRACT(MONTH FROM date) = %s
            GROUP BY store_id
            """
            previous_cost_data = self.db_manager.fetch_all(previous_cost_sql, (prev_month_year, prev_month))
            previous_cost_dict = {row['store_id']: row['previous_cost'] for row in previous_cost_data}
            
            # Combine all data
            results = []
            for store in stores:
                store_id = store['store_id']
                results.append({
                    'store_id': store_id,
                    'store_name': store['store_name'],
                    'current_revenue': current_revenue_dict.get(store_id, 0),
                    'current_cost': current_cost_dict.get(store_id, 0),
                    'previous_revenue': previous_revenue_dict.get(store_id, 0),
                    'previous_cost': previous_cost_dict.get(store_id, 0)
                })

            # Results are already in the correct format
            data = results

            print(f"✅ Retrieved {len(data)} store gross profit records")
            return data

        except Exception as e:
            print(f"❌ Error getting store gross profit data: {e}")
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
        WHERE s.id BETWEEN 1 AND 8
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
