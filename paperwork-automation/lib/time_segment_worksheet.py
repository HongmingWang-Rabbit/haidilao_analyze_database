#!/usr/bin/env python3
"""
Time segment report worksheet generator (分时段-上报).
Only handles worksheet creation - receives data from main report generator.
"""

from datetime import datetime
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class TimeSegmentWorksheetGenerator:
    """Generate time segment report worksheet (分时段-上报) from provided data"""
    
    def __init__(self, store_names, target_date):
        self.store_names = store_names
        self.target_date = target_date
        # Time segments in the specific order
        self.time_segments = [
            '08:00-13:59',
            '14:00-16:59', 
            '17:00-21:59',
            '22:00-(次)07:59'
        ]
        
    def get_time_segment_data_for_date(self, target_date):
        """Get time segment data for the specific target date from database"""
        # This would normally query the database, but for now we'll use test data
        # In a real implementation, this would use ReportDataProvider to get time segment data
        
        # Test data for 2025-06-10
        test_data = {
            # Store 1 (加拿大一店)
            1: {
                '08:00-13:59': {'turnover_current': 0.72, 'turnover_prev': 0.82, 'target': 0.85, 'tables': 32.6, 'customers': 382.9, 'customers_prev_year': 433.0},
                '14:00-16:59': {'turnover_current': 0.46, 'turnover_prev': 0.57, 'target': 0.60, 'tables': 26.3, 'customers': 245.5, 'customers_prev_year': 304.0},
                '17:00-21:59': {'turnover_current': 1.85, 'turnover_prev': 2.14, 'target': 1.97, 'tables': 86.1, 'customers': 980.8, 'customers_prev_year': 1135.0},
                '22:00-(次)07:59': {'turnover_current': 0.76, 'turnover_prev': 0.96, 'target': 0.78, 'tables': 43.8, 'customers': 400.7, 'customers_prev_year': 510.0}
            },
            # Store 2 (加拿大二店)
            2: {
                '08:00-13:59': {'turnover_current': 0.52, 'turnover_prev': 0.69, 'target': 0.50, 'tables': 11.8, 'customers': 185.7, 'customers_prev_year': 250.0},
                '14:00-16:59': {'turnover_current': 0.41, 'turnover_prev': 0.45, 'target': 0.50, 'tables': 16.4, 'customers': 147.1, 'customers_prev_year': 162.0},
                '17:00-21:59': {'turnover_current': 1.58, 'turnover_prev': 1.87, 'target': 1.80, 'tables': 44.2, 'customers': 551.3, 'customers_prev_year': 673.0},
                '22:00-(次)07:59': {'turnover_current': 0.41, 'turnover_prev': 0.39, 'target': 0.70, 'tables': 3.6, 'customers': 148.6, 'customers_prev_year': 139.0}
            },
            # Store 3 (加拿大三店)
            3: {
                '08:00-13:59': {'turnover_current': 1.06, 'turnover_prev': 1.59, 'target': 1.20, 'tables': 36.7, 'customers': 506.7, 'customers_prev_year': 761.0},
                '14:00-16:59': {'turnover_current': 0.80, 'turnover_prev': 1.28, 'target': 1.00, 'tables': 31.8, 'customers': 385.4, 'customers_prev_year': 615.0},
                '17:00-21:59': {'turnover_current': 2.21, 'turnover_prev': 2.45, 'target': 2.20, 'tables': 99.4, 'customers': 1060.9, 'customers_prev_year': 1175.0},
                '22:00-(次)07:59': {'turnover_current': 0.80, 'turnover_prev': 0.64, 'target': 0.80, 'tables': 22.9, 'customers': 386, 'customers_prev_year': 305.0}
            },
            # Store 4 (加拿大四店)
            4: {
                '08:00-13:59': {'turnover_current': 0.51, 'turnover_prev': 0.92, 'target': 0.51, 'tables': 39.4, 'customers': 426.8, 'customers_prev_year': 641.0},
                '14:00-16:59': {'turnover_current': 0.44, 'turnover_prev': 0.69, 'target': 0.53, 'tables': 24.7, 'customers': 306.3, 'customers_prev_year': 485.0},
                '17:00-21:59': {'turnover_current': 1.54, 'turnover_prev': 1.84, 'target': 1.85, 'tables': 59.1, 'customers': 1075.9, 'customers_prev_year': 1291.0},
                '22:00-(次)07:59': {'turnover_current': 0.79, 'turnover_prev': 0.99, 'target': 1.01, 'tables': 42.8, 'customers': 552.5, 'customers_prev_year': 694.0}
            },
            # Store 5 (加拿大五店)
            5: {
                '08:00-13:59': {'turnover_current': 0.67, 'turnover_prev': 0.86, 'target': 0.85, 'tables': 36.4, 'customers': 368.6, 'customers_prev_year': 475.0},
                '14:00-16:59': {'turnover_current': 0.67, 'turnover_prev': 0.86, 'target': 0.75, 'tables': 32, 'customers': 367.7, 'customers_prev_year': 475.0},
                '17:00-21:59': {'turnover_current': 2.23, 'turnover_prev': 2.53, 'target': 2.40, 'tables': 135.7, 'customers': 1227.9, 'customers_prev_year': 1390.0},
                '22:00-(次)07:59': {'turnover_current': 0.84, 'turnover_prev': 0.86, 'target': 1.10, 'tables': 44.8, 'customers': 460.8, 'customers_prev_year': 473.0}
            },
            # Store 6 (加拿大六店)
            6: {
                '08:00-13:59': {'turnover_current': 0.60, 'turnover_prev': 0.60, 'target': 0.60, 'tables': 35.7, 'customers': 335.3, 'customers_prev_year': 288.0},
                '14:00-16:59': {'turnover_current': 0.35, 'turnover_prev': 0.39, 'target': 0.50, 'tables': 18.7, 'customers': 195.3, 'customers_prev_year': 191.0},
                '17:00-21:59': {'turnover_current': 1.49, 'turnover_prev': 1.65, 'target': 1.80, 'tables': 58.6, 'customers': 833.3, 'customers_prev_year': 800.0},
                '22:00-(次)07:59': {'turnover_current': 0.54, 'turnover_prev': 0.42, 'target': 0.70, 'tables': 23.4, 'customers': 303.9, 'customers_prev_year': 203.0}
            },
            # Store 7 (加拿大七店)
            7: {
                '08:00-13:59': {'turnover_current': 0.74, 'turnover_prev': 0.68, 'target': 0.65, 'tables': 48.5, 'customers': 423.5, 'customers_prev_year': 387.0},
                '14:00-16:59': {'turnover_current': 0.45, 'turnover_prev': 0.61, 'target': 0.65, 'tables': 17.9, 'customers': 253.9, 'customers_prev_year': 348.0},
                '17:00-21:59': {'turnover_current': 1.62, 'turnover_prev': 1.93, 'target': 1.85, 'tables': 88.3, 'customers': 924.6, 'customers_prev_year': 1100.0},
                '22:00-(次)07:59': {'turnover_current': 0.55, 'turnover_prev': 0.22, 'target': 0.70, 'tables': 22.5, 'customers': 313.8, 'customers_prev_year': 127.0}
            }
        }
        
        return test_data
    
    def calculate_differences(self, current, previous, target):
        """Calculate the difference columns"""
        target_diff = current - target
        prev_diff = current - previous
        return target_diff, prev_diff
    
    def generate_worksheet(self, wb, time_segment_data=None):
        """Generate the time segment worksheet from provided data"""
        
        ws = wb.create_sheet("分时段-上报")
        
        # Parse target date for title
        target_dt = datetime.strptime(self.target_date, '%Y-%m-%d')
        year, month, day = target_dt.year, target_dt.month, target_dt.day
        
        # Get weekday in Chinese
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekdays[target_dt.weekday()]
        
        # Title
        title = f"门店分时段营数据2025年6月vs2024年6月截至10日-星期二（考核）"
        ws.merge_cells('A1:L1')
        ws['A1'] = title
        ws['A1'].font = Font(bold=True, size=12)
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws['A1'].fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
        
        # Headers row 1
        headers_row1 = ["门店名称", "分时段", "翻台率（考核）", "", "", "", "", f"10/06/2025", f"10/06/2025", "桌数（考核）", "", "同比差异"]
        for col, header in enumerate(headers_row1, 1):
            cell = ws.cell(row=2, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Headers row 2
        headers_row2 = ["", "", "今年", "去年", "本月目标", "目标差异", "同比差异", "翻台率（考核）", "桌数（考核）", "今年", "去年", "同比差异"]
        for col, header in enumerate(headers_row2, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Merge header cells
        ws.merge_cells('A2:A3')  # 门店名称
        ws.merge_cells('B2:B3')  # 分时段
        ws.merge_cells('C2:G2')  # 翻台率（考核）
        ws.merge_cells('H2:I2')  # 10/06/2025
        ws.merge_cells('J2:K2')  # 桌数（考核）
        ws.merge_cells('L2:L3')  # 同比差异
        
        # Get time segment data (using test data for now)
        if time_segment_data is None:
            time_segment_data = self.get_time_segment_data_for_date(self.target_date)
        
        # Add data rows
        current_row = 4
        
        # Colors for different stores
        store_colors = [
            "FFFF99",  # Light yellow
            "E6F3FF",  # Light blue
            "FFE6E6",  # Light pink
            "E6FFE6",  # Light green
            "FFE6CC",  # Light orange
            "F0E6FF",  # Light purple
            "E6FFFF"   # Light cyan
        ]
        
        for store_id, store_name in self.store_names.items():
            store_data = time_segment_data.get(store_id, {})
            color = store_colors[(store_id - 1) % len(store_colors)]
            
            # Add rows for each time segment
            for i, time_segment in enumerate(self.time_segments):
                segment_data = store_data.get(time_segment, {
                    'turnover_current': 0, 'turnover_prev': 0, 'target': 0, 'tables': 0, 'customers': 0, 'customers_prev_year': 0
                })
                
                # Calculate differences
                target_diff, prev_diff = self.calculate_differences(
                    segment_data['turnover_current'],
                    segment_data['turnover_prev'],
                    segment_data['target']
                )
                
                # Store name (only on first row of each store)
                if i == 0:
                    ws.cell(row=current_row, column=1, value=store_name)
                    # Merge store name across all time segments for this store
                    if len(self.time_segments) > 1:
                        ws.merge_cells(f'A{current_row}:A{current_row + len(self.time_segments) - 1}')
                        ws[f'A{current_row}'].alignment = Alignment(horizontal='center', vertical='center')
                
                # Time segment
                ws.cell(row=current_row, column=2, value=time_segment)
                
                # Turnover data
                ws.cell(row=current_row, column=3, value=round(segment_data['turnover_current'], 2))
                ws.cell(row=current_row, column=4, value=round(segment_data['turnover_prev'], 2))
                ws.cell(row=current_row, column=5, value=round(segment_data['target'], 2))
                ws.cell(row=current_row, column=6, value=round(target_diff, 2))
                ws.cell(row=current_row, column=7, value=round(prev_diff, 2))
                
                # Daily data
                ws.cell(row=current_row, column=8, value=round(segment_data['turnover_current'], 2))
                ws.cell(row=current_row, column=9, value=round(segment_data['tables'], 1))
                
                # Tables and customers
                ws.cell(row=current_row, column=10, value=round(segment_data['customers'], 1))
                ws.cell(row=current_row, column=11, value=round(segment_data['customers'], 0))  # Same as customers for now
                
                # Column L: 同比差异 (Year-over-year difference for table count)
                yoy_table_diff = segment_data['customers'] - segment_data.get('customers_prev_year', 0)
                ws.cell(row=current_row, column=12, value=round(yoy_table_diff, 1))
                
                # Apply background colors
                for col in range(1, 13):
                    cell = ws.cell(row=current_row, column=col)
                    cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
                    
                    # Special formatting for difference columns
                    if col in [6, 7, 12]:  # Difference columns (including new column L)
                        value = cell.value
                        if isinstance(value, (int, float)):
                            if value < 0:
                                cell.font = Font(color="FF0000")  # Red for negative
                            elif value > 0:
                                cell.font = Font(color="008000")  # Green for positive
                
                current_row += 1
            
            # Add store total row
            store_totals = self.calculate_store_totals(store_data)
            
            ws.cell(row=current_row, column=2, value=f"{store_name}汇总")
            ws.cell(row=current_row, column=3, value=round(store_totals['total_turnover_current'], 2))
            ws.cell(row=current_row, column=4, value=round(store_totals['total_turnover_prev'], 2))
            ws.cell(row=current_row, column=5, value=round(store_totals['total_target'], 2))
            ws.cell(row=current_row, column=6, value=round(store_totals['total_target_diff'], 2))
            ws.cell(row=current_row, column=7, value=round(store_totals['total_prev_diff'], 2))
            ws.cell(row=current_row, column=8, value=round(store_totals['total_turnover_current'], 2))
            ws.cell(row=current_row, column=9, value=round(store_totals['total_tables'], 1))
            ws.cell(row=current_row, column=10, value=round(store_totals['total_customers'], 1))
            ws.cell(row=current_row, column=11, value=round(store_totals['total_customers'], 0))
            ws.cell(row=current_row, column=12, value=round(store_totals.get('total_yoy_diff', 0), 1))
            
            # Apply bold formatting and different color for totals
            for col in range(1, 13):
                cell = ws.cell(row=current_row, column=col)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D0D0D0", end_color="D0D0D0", fill_type="solid")
            
            current_row += 1
        
        # Add overall total row
        overall_totals = self.calculate_overall_totals(time_segment_data)
        
        ws.cell(row=current_row, column=1, value="区域整体")
        ws.cell(row=current_row, column=3, value=round(overall_totals['overall_turnover_current'], 2))
        ws.cell(row=current_row, column=4, value=round(overall_totals['overall_turnover_prev'], 2))
        ws.cell(row=current_row, column=5, value=round(overall_totals['overall_target'], 2))
        ws.cell(row=current_row, column=6, value=round(overall_totals['overall_target_diff'], 2))
        ws.cell(row=current_row, column=7, value=round(overall_totals['overall_prev_diff'], 2))
        ws.cell(row=current_row, column=8, value=round(overall_totals['overall_turnover_current'], 2))
        ws.cell(row=current_row, column=9, value=round(overall_totals['overall_tables'], 1))
        ws.cell(row=current_row, column=10, value=round(overall_totals['overall_customers'], 1))
        ws.cell(row=current_row, column=11, value=round(overall_totals['overall_customers'], 0))
        ws.cell(row=current_row, column=12, value=round(overall_totals.get('overall_yoy_diff', 0), 1))
        
        # Apply bold formatting and special color for overall totals
        for col in range(1, 13):
            cell = ws.cell(row=current_row, column=col)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="000080", end_color="000080", fill_type="solid")
        
        # Apply common formatting
        self.apply_common_formatting(ws, current_row + 1)
        
        return ws
    
    def calculate_store_totals(self, store_data):
        """Calculate totals for a single store"""
        total_turnover_current = sum(data['turnover_current'] for data in store_data.values())
        total_turnover_prev = sum(data['turnover_prev'] for data in store_data.values())
        total_target = sum(data['target'] for data in store_data.values())
        total_tables = sum(data['tables'] for data in store_data.values())
        total_customers = sum(data['customers'] for data in store_data.values())
        
        total_target_diff = total_turnover_current - total_target
        total_prev_diff = total_turnover_current - total_turnover_prev
        # Year-over-year difference for table count (current year customers - previous year customers)
        total_customers_prev_year = sum(data.get('customers_prev_year', 0) for data in store_data.values())
        total_yoy_diff = total_customers - total_customers_prev_year
        
        return {
            'total_turnover_current': total_turnover_current,
            'total_turnover_prev': total_turnover_prev,
            'total_target': total_target,
            'total_tables': total_tables,
            'total_customers': total_customers,
            'total_target_diff': total_target_diff,
            'total_prev_diff': total_prev_diff,
            'total_yoy_diff': total_yoy_diff
        }
    
    def calculate_overall_totals(self, time_segment_data):
        """Calculate overall totals across all stores"""
        overall_turnover_current = 0
        overall_turnover_prev = 0
        overall_target = 0
        overall_tables = 0
        overall_customers = 0
        
        for store_id, store_data in time_segment_data.items():
            store_totals = self.calculate_store_totals(store_data)
            overall_turnover_current += store_totals['total_turnover_current']
            overall_turnover_prev += store_totals['total_turnover_prev']
            overall_target += store_totals['total_target']
            overall_tables += store_totals['total_tables']
            overall_customers += store_totals['total_customers']
        
        overall_target_diff = overall_turnover_current - overall_target
        overall_prev_diff = overall_turnover_current - overall_turnover_prev
        # Sum of all store year-over-year differences
        overall_yoy_diff = sum(self.calculate_store_totals(store_data)['total_yoy_diff'] 
                              for store_data in time_segment_data.values())
        
        return {
            'overall_turnover_current': overall_turnover_current,
            'overall_turnover_prev': overall_turnover_prev,
            'overall_target': overall_target,
            'overall_tables': overall_tables,
            'overall_customers': overall_customers,
            'overall_target_diff': overall_target_diff,
            'overall_prev_diff': overall_prev_diff,
            'overall_yoy_diff': overall_yoy_diff
        }
    
    def apply_common_formatting(self, ws, max_row):
        """Apply common formatting to worksheet"""
        # Apply borders
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        for row in range(1, max_row):
            for col in range(1, 13):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                
                # Apply number formatting for numeric values
                if isinstance(cell.value, (int, float)) and row > 3:
                    if col in [3, 4, 5, 6, 7, 8]:  # Turnover columns
                        cell.number_format = '0.00'
                    elif col in [9, 10, 11, 12]:  # Count columns including new column L
                        cell.number_format = '0.0'
        
        # Set column widths
        column_widths = [15, 15, 10, 10, 10, 10, 10, 12, 12, 12, 12, 12]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Set row heights
        ws.row_dimensions[1].height = 25
        ws.row_dimensions[2].height = 20
        ws.row_dimensions[3].height = 20 