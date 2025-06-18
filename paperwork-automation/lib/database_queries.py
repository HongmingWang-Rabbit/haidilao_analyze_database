#!/usr/bin/env python3
"""
Centralized database query functions for report generation.
All database interactions should go through this module.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import DatabaseManager

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
                total_tables_served = sum(float(r['tables_served'] or 0) for r in rows)
                total_tables_validated = sum(float(r['tables_served_validated'] or 0) for r in rows)
                total_takeout = sum(float(r['takeout_tables'] or 0) for r in rows)
                total_revenue = sum(float(r['revenue_tax_not_included'] or 0) for r in rows)
                total_customers = sum(float(r['customers'] or 0) for r in rows)
                total_discount = sum(float(r['discount_total'] or 0) for r in rows)
                avg_turnover = sum(float(r['turnover_rate'] or 0) for r in rows) / len(rows) if rows else 0
                
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
        prev_mtd = aggregate_store_data(data_by_period.get('prev_month_mtd', {}))
        yearly_current = aggregate_store_data(combined_monthly_data)
        yearly_previous = aggregate_store_data(data_by_period.get('prev_year_mtd', {}))
        
        # Calculate rankings
        daily_ranking_names = []
        monthly_ranking_names = []
        daily_ranking_values = []
        monthly_ranking_values = []
        
        if daily_data:
            daily_sorted = sorted(daily_data, key=lambda x: x['turnover_rate'], reverse=True)
            daily_ranking_names = [row['store_name'] for row in daily_sorted]
            daily_ranking_values = [row['turnover_rate'] for row in daily_sorted]
        
        if monthly_data:
            monthly_sorted = sorted(monthly_data, key=lambda x: x['avg_turnover_rate'], reverse=True)
            monthly_ranking_names = [row['store_name'] for row in monthly_sorted]
            monthly_ranking_values = [row['avg_turnover_rate'] for row in monthly_sorted]
        
        return (daily_data, monthly_data, previous_month_data, current_mtd, prev_mtd, 
                yearly_current, yearly_previous, daily_ranking_names, monthly_ranking_names, 
                daily_ranking_values, monthly_ranking_values)
    
    def get_all_processed_data(self, target_date: str):
        """Get and process all data needed for report generation"""
        print(f"🔄 Fetching all report data for {target_date}...")
        
        # Get all data in single query
        all_data = self.get_all_report_data(target_date)
        
        if not all_data:
            print("❌ No data found")
            return None
        
        print(f"✅ Found {len(all_data)} data records from optimized query")
        
        # Process all data client-side
        processed_data = self.process_comprehensive_data(all_data)
        
        if not processed_data[0]:  # daily_data
            print("❌ No daily data processed")
            return None
        
        print(f"✅ Processed data for {len(processed_data[0])} stores")
        
        return processed_data 