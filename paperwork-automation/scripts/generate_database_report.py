#!/usr/bin/env python3
"""
Generate comparison report (对比上月表) from actual database data.
All values are calculated from database, not hardcoded.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import DatabaseConfig, DatabaseManager

# Load environment variables
load_dotenv()

class BaseWorksheetGenerator:
    """Base class for worksheet generators"""
    
    def __init__(self, db_manager, store_names, target_date):
        self.db_manager = db_manager
        self.store_names = store_names
        self.target_date = target_date
    
    def create_worksheet(self, wb, sheet_name):
        """Create and configure a new worksheet"""
        ws = wb.create_sheet(sheet_name)
        return ws
    
    def apply_common_formatting(self, ws, current_row):
        """Apply common formatting to worksheet"""
        # Apply borders
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        for row in range(1, current_row):
            for col in range(1, 11):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                
                # Apply number formatting for numeric values
                if isinstance(cell.value, (int, float)) and col > 2:
                    cell.number_format = '0.00'
                elif isinstance(cell.value, str) and col > 2:
                    # Check if it's a percentage
                    if cell.value.endswith('%'):
                        cell.number_format = '0.00%'
        
        # Set column widths
        column_widths = [20, 20, 12, 12, 12, 12, 12, 12, 12, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Set row height for title
        ws.row_dimensions[1].height = 25
    
    def generate_worksheet(self, wb):
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement generate_worksheet")


class ComparisonWorksheetGenerator(BaseWorksheetGenerator):
    """Generate comparison worksheet (对比上月表)"""
    
    def generate_worksheet(self, wb, daily_data, monthly_data, previous_month_data, 
                          monthly_targets, current_mtd, prev_mtd, 
                          daily_ranking, monthly_ranking, daily_ranking_values, monthly_ranking_values):
        """Generate the comparison worksheet"""
        ws = self.create_worksheet(wb, "对比上月表")
        
        # Parse target date for calculations
        target_dt = datetime.strptime(self.target_date, '%Y-%m-%d')
        year, month, day = target_dt.year, target_dt.month, target_dt.day
        time_progress = self.calculate_time_progress(self.target_date)
        
        # Convert to dictionaries for easier access
        daily_dict = {row['store_id']: row for row in daily_data}
        monthly_dict = {row['store_id']: row for row in monthly_data}
        prev_month_dict = {row['store_id']: row for row in previous_month_data}
        targets_dict = {row['store_id']: row for row in monthly_targets}
        current_mtd_dict = {row['store_id']: row for row in current_mtd}
        prev_mtd_dict = {row['store_id']: row for row in prev_mtd}
        
        # Get weekday in Chinese
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekdays[target_dt.weekday()]
        
        # Title
        title = f"加拿大-各门店{self.target_date.replace('-', '年', 1).replace('-', '月', 1)}日环比数据-{weekday}"
        ws.merge_cells('A1:J1')
        ws['A1'] = title
        ws['A1'].font = Font(bold=True, size=12)
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws['A1'].fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
        
        # Headers
        headers = ["项目", "内容"] + list(self.store_names.values()) + ["加拿大片区"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=2, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Data rows with exact structure from screenshots
        data_rows = [
            # 桌数(考核) section
            ("桌数\n(考核)", "今日总桌数", "FFFF99"),
            ("", "今日外卖桌数", "FFFF99"),
            ("", "今日未计入考核桌数", "FFFF99"),
            ("", f"{target_dt.month}月总桌数", "FFFF99"),
            ("", "上月同期总桌数", "FFFF99"),
            ("", "对比上月同期总桌数", "FFFF00"),  # Highlighted
            
            # 收入 section
            ("收入\n(不含税-万加元)", "今日营业收入(万)", "E6F3FF"),
            ("", "本月截止目前营业收入(万)", "E6F3FF"),
            ("", "上月截止目前营业收入(万)", "E6F3FF"),
            ("", "环比营业收入变化(万)", "E6F3FF"),
            ("", "本月营业收入目标(万)", "E6F3FF"),
            ("", "本月截止目标完成率", "FFFF00"),  # Highlighted
            ("", "标准时间进度", "E6F3FF"),
            ("", "当月累计优惠总金额(万)", "E6F3FF"),
            ("", "当月累计优惠占比", "E6F3FF"),
            
            # 单桌消费 section
            ("单桌消费\n(不含税)", "今日人均消费", "FFFF99"),
            ("", "今日消费客数", "FFFF99"),
            ("", "今日单桌消费", "FFFF99"),
            ("", "截止今日单桌消费", "FFFF99"),  # Highlighted
            ("", "上月单桌消费", "FFFF99"),
            ("", "环比上月变化", "FFFF99"),
            
            # 翻台率 section
            ("翻台率", "名次", "FFFF00"),  # Highlighted
            ("", f"{target_dt.month}月{target_dt.day}日翻台率排名店铺", "E6F3FF"),
            ("", f"{target_dt.month}月{target_dt.day}日翻台率排名", "FFFF00"),
            ("", f"{target_dt.month}月平均翻台率排名店铺", "E6F3FF"),
            ("", f"{target_dt.month}月平均翻台率排名", "FFFF00"),
        ]
        
        # Add data to worksheet
        current_row = 3
        
        for category, content, color in data_rows:
            # Add category (column A)
            if category:
                ws.cell(row=current_row, column=1, value=category)
            
            # Add content (column B)
            ws.cell(row=current_row, column=2, value=content)
            
            # Add data for each store (columns C-I) and total (column J)
            for col, store_name in enumerate(list(self.store_names.values()) + ["加拿大片区"], 3):
                value = self.get_cell_value(content, category, store_name, col, 
                                          daily_dict, monthly_dict, prev_month_dict, targets_dict, 
                                          current_mtd_dict, prev_mtd_dict, daily_ranking, monthly_ranking,
                                          daily_ranking_values, monthly_ranking_values,
                                          time_progress, target_dt)
                
                cell = ws.cell(row=current_row, column=col, value=value)
                cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            
            # Apply background color to category and content cells
            ws.cell(row=current_row, column=1).fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            ws.cell(row=current_row, column=2).fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            
            current_row += 1
        
        # Merge category cells
        merge_ranges = [
            (3, 8),   # 桌数(考核) - 6 rows
            (9, 17),  # 收入 - 11 rows
            (18, 23), # 单桌消费 - 4 rows
            (24, 28), # 翻台率 - 2 rows
        ]
        
        for start_row, end_row in merge_ranges:
            if start_row < end_row:
                ws.merge_cells(f'A{start_row}:A{end_row}')
                cell = ws[f'A{start_row}']
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.font = Font(bold=True)
        
        # Apply common formatting
        self.apply_common_formatting(ws, current_row)
        
        # Manual modify for display
        ws['J25'].value = ws["J26"].value
        ws.merge_cells(f'B{25}:B{26}')
        ws.merge_cells(f'B{27}:B{28}')
        ws.merge_cells(f'J{25}:J{28}')
        
        return ws
    
    def calculate_time_progress(self, target_date: str):
        """Calculate actual time progress through the month"""
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        
        # Get last day of the month
        if target_dt.month == 12:
            next_month = target_dt.replace(year=target_dt.year + 1, month=1, day=1)
        else:
            next_month = target_dt.replace(month=target_dt.month + 1, day=1)
        
        last_day = (next_month - timedelta(days=1)).day
        current_day = target_dt.day
        
        progress = (current_day / last_day) * 100
        return round(progress, 2)
    
    def get_cell_value(self, content, category, store_name, col, daily_dict, monthly_dict, 
                      prev_month_dict, targets_dict, current_mtd_dict, prev_mtd_dict, 
                      daily_ranking, monthly_ranking, daily_ranking_values, monthly_ranking_values,
                      time_progress, target_dt):
        """Calculate cell value directly from database data"""
        
        # Handle 加拿大片区 (totals) vs individual stores
        if store_name == "加拿大片区":
            # Calculate totals from all stores
            tables_served = sum(float(row['tables_served']) for row in daily_dict.values())
            tables_served_validated = sum(float(row['tables_served_validated']) for row in daily_dict.values())
            takeout_tables = sum(float(row['takeout_tables']) for row in daily_dict.values())
            tables_validated = sum(float(row['tables_served_validated']) for row in daily_dict.values())
            revenue = sum(float(row['revenue_tax_included']) for row in daily_dict.values())
            customers = sum(float(row['customers']) for row in daily_dict.values())
            discount = sum(float(row['discount_total']) for row in daily_dict.values())
            turnover_rate = sum(float(row['turnover_rate']) for row in daily_dict.values()) / len(daily_dict)
            
            monthly_discount = sum(float(row['monthly_discount_total']) for row in monthly_dict.values())
            monthly_tables = sum(float(row['monthly_tables']) for row in monthly_dict.values())
            monthly_tables_validated = sum(float(row['monthly_tables_validated']) for row in monthly_dict.values())
            monthly_revenue = sum(float(row['monthly_revenue']) for row in monthly_dict.values())
            avg_monthly_turnover = sum(float(row['avg_turnover_rate']) for row in monthly_dict.values()) / len(monthly_dict) if monthly_dict else 0
            
            # Previous month totals
            prev_month_tables = sum(float(row['prev_monthly_tables']) for row in prev_month_dict.values()) if prev_month_dict else 0
            prev_month_tables_validated = sum(float(row['prev_monthly_tables_validated']) for row in prev_month_dict.values()) if prev_month_dict else 0
            prev_month_revenue = sum(float(row['prev_monthly_revenue']) for row in prev_month_dict.values()) if prev_month_dict else 0
            
            # Month-to-date totals
            current_mtd_tables = sum(float(row['mtd_tables_served']) for row in current_mtd_dict.values()) if current_mtd_dict else monthly_tables
            current_mtd_revenue = sum(float(row['mtd_revenue']) for row in current_mtd_dict.values()) if current_mtd_dict else monthly_revenue
            current_mtd_tables_validated = sum(float(row['mtd_tables']) for row in current_mtd_dict.values()) if current_mtd_dict else monthly_tables_validated
            current_mtd_discount = sum(float(row['mtd_discount_total']) for row in current_mtd_dict.values()) if current_mtd_dict else monthly_discount
            prev_mtd_tables = sum(float(row['prev_mtd_tables']) for row in prev_mtd_dict.values()) if prev_mtd_dict else prev_month_tables
            prev_mtd_tables_validated = sum(float(row['prev_mtd_tables']) for row in prev_mtd_dict.values()) if prev_mtd_dict else prev_month_tables_validated
            prev_mtd_revenue = sum(float(row['prev_mtd_revenue']) for row in prev_mtd_dict.values()) if prev_mtd_dict else 0

            # Target totals
            target_revenue = sum(float(row['target_revenue']) for row in targets_dict.values())
            
        else:
            # Get store_id from store_name
            store_id = None
            for sid, sname in self.store_names.items():
                if sname == store_name:
                    store_id = sid
                    break
            
            if not store_id or store_id not in daily_dict:
                return ""
            
            # Get data for this individual store
            daily_row = daily_dict[store_id]
            monthly_row = monthly_dict.get(store_id, {})
            prev_month_row = prev_month_dict.get(store_id, {})
            target_row = targets_dict.get(store_id, {})
            current_mtd_row = current_mtd_dict.get(store_id, {})
            prev_mtd_row = prev_mtd_dict.get(store_id, {})
            
            # Extract individual store values
            tables_served = float(daily_row.get('tables_served', 0))
            tables_served_validated = float(daily_row.get('tables_served_validated', 0))
            takeout_tables = float(daily_row.get('takeout_tables', 0))
            tables_validated = float(daily_row.get('tables_served_validated', 0))
            revenue = float(daily_row.get('revenue_tax_included', 0))
            customers = float(daily_row.get('customers', 0))
            discount = float(daily_row.get('discount_total', 0))
            turnover_rate = float(daily_row.get('turnover_rate', 0))
            
            # Monthly data
            monthly_discount = float(monthly_row.get('monthly_discount_total', 0)) if monthly_row else 0
            monthly_tables = float(monthly_row.get('monthly_tables', 0)) if monthly_row else 0
            monthly_tables_validated = float(monthly_row.get('monthly_tables_validated', 0)) if monthly_row else 0
            monthly_revenue = float(monthly_row.get('monthly_revenue', 0)) if monthly_row else 0
            avg_monthly_turnover = float(monthly_row.get('avg_turnover_rate', 0)) if monthly_row else 0
            
            # Previous month data
            prev_month_tables = float(prev_month_row.get('prev_monthly_tables', 0)) if prev_month_row else 0
            prev_month_tables_validated = float(prev_month_row.get('prev_monthly_tables_validated', 0)) if prev_month_row else 0
            prev_month_revenue = float(prev_month_row.get('prev_monthly_revenue', 0)) if prev_month_row else 0
            
            # Month-to-date data
            current_mtd_tables = float(current_mtd_row.get('mtd_tables_served', 0)) if current_mtd_row else monthly_tables
            current_mtd_tables_validated = float(current_mtd_row.get('mtd_tables', 0)) if current_mtd_row else monthly_tables_validated
            current_mtd_discount = float(current_mtd_row.get('mtd_discount_total', 0)) if current_mtd_row else monthly_discount
            current_mtd_revenue = float(current_mtd_row.get('mtd_revenue', 0)) if current_mtd_row else monthly_revenue
            prev_mtd_revenue = float(prev_mtd_row.get('prev_mtd_revenue', 0)) if prev_mtd_row else prev_month_revenue
            prev_mtd_tables = float(prev_mtd_row.get('prev_mtd_tables', 0)) if prev_mtd_row else prev_month_tables
            prev_mtd_tables_validated = float(prev_mtd_row.get('prev_mtd_tables', 0)) if prev_mtd_row else prev_month_tables_validated
 
            # Target data
            target_revenue = float(target_row.get('target_revenue', 100)) if target_row else 100
        
        # Calculate derived values (same logic for both totals and individual stores)
        excluded_customers = tables_served - tables_validated
        avg_per_table = revenue / tables_served if tables_served > 0 else 0
        per_capita = revenue / customers if customers > 0 else 0
        discount_pct = discount / revenue * 100 if revenue > 0 else 0
        mtd_discount_pct = current_mtd_discount / current_mtd_revenue * 100 if current_mtd_revenue > 0 else 0
        completion_rate = monthly_revenue / target_revenue * 100 if target_revenue > 0 else 0
        table_change = monthly_tables_validated - prev_month_tables_validated
        revenue_change = current_mtd_revenue - prev_mtd_revenue
        current_mtd_avg_table = current_mtd_revenue / current_mtd_tables if current_mtd_tables > 0 else 0
        prev_month_avg_table = prev_mtd_revenue / prev_mtd_tables if prev_mtd_tables > 0 else 0
        avg_table_change = current_mtd_avg_table - prev_month_avg_table
        
        # Return value based on content (unified logic for both totals and individual stores)
        if content == "今日总桌数":
            return round(tables_validated, 2)
        elif content == "今日外卖桌数":
            return round(takeout_tables, 2)
        elif content == "今日未计入考核桌数":
            return round(excluded_customers, 2)
        elif content == f"{target_dt.month}月总桌数":
            return round(monthly_tables_validated, 2)
        elif content == "上月同期总桌数":
            return round(prev_month_tables_validated, 2)
        elif content == "对比上月同期总桌数":
            return f"{'上升' if table_change >= 0 else '下降'}{abs(table_change):.2f}桌"
        elif content == "今日营业收入(万)":
            return round(revenue/10000, 2)
        elif content == "本月截止目前营业收入(万)":
            return round(current_mtd_revenue/10000, 2)
        elif content == "上月截止目前营业收入(万)":
            return round(prev_mtd_revenue/10000, 2)
        elif content == "环比营业收入变化(万)":
            return round(revenue_change/10000, 2)
        elif content == "本月营业收入目标(万)":
            return round(target_revenue/10000, 2)
        elif content == "本月截止目标完成率":
            return f"{completion_rate:.2f}%"
        elif content == "标准时间进度":
            return f"{time_progress:.2f}%"
        elif content == "当月累计优惠总金额(万)":
            return round(current_mtd_discount/10000, 2)
        elif content == "当月累计优惠占比":
            return f"{mtd_discount_pct:.2f}%"
        elif content == "今日人均消费":
            return round(per_capita, 2)
        elif content == "今日消费客数":
            return round(customers, 2)
        elif content == "今日单桌消费":
            return round(avg_per_table, 2)
        elif content == "截止今日单桌消费":
            return round(current_mtd_avg_table, 2)
        elif content == "上月单桌消费":
            return round(prev_month_avg_table, 2)
        elif content == "环比上月变化":
            return round(avg_table_change, 2)
        elif content == "名次":
            if "翻台率排名" in category:
                if store_name == "加拿大片区":
                    return "当月累计平均翻台率"
                else:
                    col_index = col - 3
                    if col_index < 7:
                        return f"第{col_index + 1}名"
            else:
                if store_name == "加拿大片区":
                    return "当月累计平均翻台率"
                else:
                    store_id = next(k for k, v in self.store_names.items() if v == store_name)
                    return f"第{store_id}名"
        elif content == f"{target_dt.month}月{target_dt.day}日翻台率排名店铺":
            if store_name == "加拿大片区":
                return ""
            else:
                col_index = col - 3
                if col_index < len(daily_ranking):
                    return daily_ranking[col_index]
                return ""
        elif content == f"{target_dt.month}月{target_dt.day}日翻台率排名":
            if store_name == "加拿大片区":
                return round(turnover_rate, 2)
            else:
                col_index = col - 3
                if col_index < len(daily_ranking_values):
                    return round(daily_ranking_values[col_index], 2)
                return ""
        elif content == f"{target_dt.month}月平均翻台率排名店铺":
            if store_name == "加拿大片区":
                return ""
            else:
                col_index = col - 3
                if col_index < len(monthly_ranking):
                    return monthly_ranking[col_index]
                return ""
        elif content == f"{target_dt.month}月平均翻台率排名":
            if store_name == "加拿大片区":
                return ""
            else:
                col_index = col - 3
                if col_index < len(monthly_ranking_values):
                    return round(monthly_ranking_values[col_index], 2)
                return ""
        
        return ""


class DatabaseReportGenerator:
    """Generate comparison report from database data"""
    
    def __init__(self, target_date: str, is_test: bool = False):
        self.target_date = target_date
        self.is_test = is_test
        self.config = DatabaseConfig(is_test=is_test)
        self.db_manager = DatabaseManager(self.config)
        self.output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Store mapping
        self.store_names = {
            1: "加拿大一店", 2: "加拿大二店", 3: "加拿大三店", 4: "加拿大四店",
            5: "加拿大五店", 6: "加拿大六店", 7: "加拿大七店"
        }
        
        # Initialize worksheet generators
        self.worksheet_generators = {
            'comparison': ComparisonWorksheetGenerator(self.db_manager, self.store_names, self.target_date)
        }
    
    def get_daily_data(self, date: str):
        """Get daily report data for a specific date"""
        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            dr.date,
            dr.tables_served,
            dr.takeout_tables,
            dr.tables_served_validated,
            dr.revenue_tax_included,
            dr.customers,
            dr.discount_total,
            dr.turnover_rate,
            dr.is_holiday
        FROM daily_report dr
        JOIN store s ON dr.store_id = s.id
        WHERE dr.date = %s
        ORDER BY s.id
        """
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (date,))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching daily data: {e}")
            return []
    
    def get_monthly_data(self, year: int, month: int):
        """Get monthly aggregated data"""
        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            COUNT(*) as days_count,
            SUM(dr.tables_served) as monthly_tables,
            SUM(dr.tables_served_validated) as monthly_tables_validated,
            SUM(dr.revenue_tax_included) as monthly_revenue,
            AVG(dr.revenue_tax_included / NULLIF(dr.tables_served_validated, 0)) as avg_per_table,
            SUM(dr.discount_total) as monthly_discount_total,
            AVG(dr.turnover_rate) as avg_turnover_rate
        FROM daily_report dr
        JOIN store s ON dr.store_id = s.id
        WHERE EXTRACT(YEAR FROM dr.date) = %s 
        AND EXTRACT(MONTH FROM dr.date) = %s
        GROUP BY s.id, s.name
        ORDER BY s.id
        """
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (year, month))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching monthly data: {e}")
            return []
    
    def get_monthly_targets(self):
        """Get monthly revenue targets"""
        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            smt.revenue as target_revenue
        FROM store_monthly_target smt
        JOIN store s ON smt.store_id = s.id
        ORDER BY s.id
        """
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching monthly targets: {e}")
            return []
    
    def get_time_segment_data(self, date: str):
        """Get time segment data for turnover rate calculation"""
        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            ts.label as time_segment,
            str.tables_served_validated,
            str.turnover_rate
        FROM store_time_report str
        JOIN store s ON str.store_id = s.id
        JOIN time_segment ts ON str.time_segment_id = ts.id
        WHERE str.date = %s
        ORDER BY s.id, ts.id
        """
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (date,))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching time segment data: {e}")
            return []
    
    def get_previous_month_data(self, year: int, month: int):
        """Get previous month data for comparison"""
        # Calculate previous month
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
            
        sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            COUNT(*) as days_count,
            SUM(dr.tables_served) as prev_monthly_tables,
            SUM(dr.tables_served_validated) as prev_monthly_tables_validated,
            SUM(dr.revenue_tax_included) as prev_monthly_revenue,
            AVG(dr.turnover_rate) as prev_avg_turnover_rate
        FROM daily_report dr
        JOIN store s ON dr.store_id = s.id
        WHERE EXTRACT(YEAR FROM dr.date) = %s 
        AND EXTRACT(MONTH FROM dr.date) = %s
        GROUP BY s.id, s.name
        ORDER BY s.id
        """
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (prev_year, prev_month))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching previous month data: {e}")
            return []
    
    def get_month_to_date_data(self, year: int, month: int, current_day: int):
        """Get month-to-date data for current and previous month comparison"""
        # Current month to date
        current_sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            SUM(dr.tables_served) as mtd_tables_served,
            SUM(dr.tables_served_validated) as mtd_tables,
            SUM(dr.revenue_tax_included) as mtd_revenue,
            SUM(dr.discount_total) as mtd_discount_total
        FROM daily_report dr
        JOIN store s ON dr.store_id = s.id
        WHERE EXTRACT(YEAR FROM dr.date) = %s 
        AND EXTRACT(MONTH FROM dr.date) = %s
        AND EXTRACT(DAY FROM dr.date) <= %s
        GROUP BY s.id, s.name
        ORDER BY s.id
        """
        
        # Previous month same period
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
            
        prev_sql = """
        SELECT 
            s.id as store_id,
            s.name as store_name,
            SUM(dr.tables_served) as prev_mtd_tables,
            SUM(dr.tables_served_validated) as prev_mtd_tables_validated,
            SUM(dr.revenue_tax_included) as prev_mtd_revenue,
            SUM(dr.discount_total) as prev_mtd_discount
        FROM daily_report dr
        JOIN store s ON dr.store_id = s.id
        WHERE EXTRACT(YEAR FROM dr.date) = %s 
        AND EXTRACT(MONTH FROM dr.date) = %s
        AND EXTRACT(DAY FROM dr.date) <= %s
        GROUP BY s.id, s.name
        ORDER BY s.id
        """
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current month-to-date
                cursor.execute(current_sql, (year, month, current_day))
                current_mtd = cursor.fetchall()
                
                # Get previous month same period
                cursor.execute(prev_sql, (prev_year, prev_month, current_day))
                prev_mtd = cursor.fetchall()
                
                return current_mtd, prev_mtd
        except Exception as e:
            print(f"❌ Error fetching month-to-date data: {e}")
            return [], []
    
    def calculate_rankings(self, daily_data, monthly_data):
        """Calculate store rankings based on turnover rates"""
        # Daily ranking based on daily turnover rate (highest to lowest)
        daily_ranking_sorted = sorted(daily_data, key=lambda x: float(x['turnover_rate']) if x['turnover_rate'] else 0, reverse=True)
        daily_ranking_names = [self.store_names[row['store_id']] for row in daily_ranking_sorted]
        daily_ranking_values = [float(row['turnover_rate']) if row['turnover_rate'] else 0 for row in daily_ranking_sorted]
        
        # Monthly ranking based on average monthly turnover rate (highest to lowest)
        monthly_ranking_sorted = sorted(monthly_data, key=lambda x: float(x['avg_turnover_rate']) if x['avg_turnover_rate'] else 0, reverse=True)
        monthly_ranking_names = [self.store_names[row['store_id']] for row in monthly_ranking_sorted]
        monthly_ranking_values = [float(row['avg_turnover_rate']) if row['avg_turnover_rate'] else 0 for row in monthly_ranking_sorted]
        
        return daily_ranking_names, monthly_ranking_names, daily_ranking_values, monthly_ranking_values
    
    def generate_report(self):
        """Generate the complete report"""
        print(f"🔄 Generating database-driven report for {self.target_date}...")
        
        # Get all database data
        target_dt = datetime.strptime(self.target_date, '%Y-%m-%d')
        year, month, day = target_dt.year, target_dt.month, target_dt.day
        
        daily_data = self.get_daily_data(self.target_date)
        monthly_data = self.get_monthly_data(year, month)
        
        if not daily_data:
            print("❌ No daily data found")
            return None
        
        print(f"✅ Found data for {len(daily_data)} stores")
        
        # Get remaining database data
        previous_month_data = self.get_previous_month_data(year, month)
        monthly_targets = self.get_monthly_targets()
        current_mtd, prev_mtd = self.get_month_to_date_data(year, month, day)
        
        # Calculate rankings
        daily_ranking, monthly_ranking, daily_ranking_values, monthly_ranking_values = self.calculate_rankings(daily_data, monthly_data)
        
        # Create Excel workbook with multiple worksheets
        wb = Workbook()
        # Remove default sheet
        if wb.active:
            wb.remove(wb.active)
        
        # Generate comparison worksheet
        comparison_ws = self.worksheet_generators['comparison'].generate_worksheet(
            wb, daily_data, monthly_data, previous_month_data, 
            monthly_targets, current_mtd, prev_mtd, 
            daily_ranking, monthly_ranking, daily_ranking_values, monthly_ranking_values
        )
        
        if not wb.worksheets:
            print("❌ No worksheets generated")
            return None
        
        # Save the report
        output_path = self.save_report(wb)
        if output_path:
            print(f"✅ Database-driven report generated successfully!")
            print(f"📁 Saved to: {output_path}")
            print(f"📊 All data calculated from database for {len(daily_data)} stores")
            return output_path
        else:
            print("❌ Failed to save report")
            return None
    
    
    def save_report(self, wb):
        """Save the Excel workbook to file"""
        try:
            filename = f"report_{self.target_date.replace('-', '_')}.xlsx"
            output_path = self.output_dir / filename
            wb.save(output_path)
            return output_path
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate database-driven comparison report")
    parser.add_argument("--date", default="2025-06-10", help="Target date (YYYY-MM-DD)")
    parser.add_argument("--test", action="store_true", help="Use test database")
    
    args = parser.parse_args()
    
    try:
        generator = DatabaseReportGenerator(args.date, is_test=args.test)
        output_path = generator.generate_report()
        
        if output_path:
            print(f"\n🎯 Success! Database-driven file created: {output_path}")
            print(f"📁 Located in OUTPUT_DIR: {os.getenv('OUTPUT_DIR', './output')}")
            print(f"📊 All data calculated from database for {args.date}")
        else:
            print("\n❌ Failed to generate report")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 