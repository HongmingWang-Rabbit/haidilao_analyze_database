import logging
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from decimal import Decimal
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class DishPriceChangeSheet:
    def __init__(self, db_manager, target_date: str):
        self.db_manager = db_manager
        self.target_date = datetime.strptime(target_date, '%Y-%m-%d')
        self.sheet_name = "菜品价格变动表"

    def _get_date_ranges(self):
        """Calculate date ranges for current, last month, and last year same month"""
        current_start = self.target_date.replace(day=1)
        current_end = self.target_date

        last_month_end = current_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        last_year_start = current_start - relativedelta(years=1)
        last_year_end = self.target_date - relativedelta(years=1)

        return {
            'current': (current_start, current_end),
            'last_month': (last_month_start, last_month_end),
            'last_year': (last_year_start, last_year_end)
        }

    def _get_dish_prices_and_sales(self, date_range: tuple, store_id: int) -> Dict[int, Dict[str, Any]]:
        """Get dish prices and sales for a specific date range and store - using dish ID for unique identification"""
        start_date, end_date = date_range
        year = start_date.year
        month = start_date.month

        query = """
            WITH dish_data AS (
                SELECT
                    d.id as dish_id,
                    d.full_code as dish_code,
                    d.name as dish_name,
                    dms.sale_amount as total_quantity,
                    COALESCE(
                        (SELECT dph.price
                         FROM dish_price_history dph
                         WHERE dph.dish_id = d.id
                           AND dph.store_id = %s
                           AND ((dph.effective_year < %s) OR
                                (dph.effective_year = %s AND dph.effective_month <= %s))
                         ORDER BY dph.effective_year DESC, dph.effective_month DESC
                         LIMIT 1),
                        0
                    ) as avg_price
                FROM dish d
                INNER JOIN dish_monthly_sale dms ON d.id = dms.dish_id
                WHERE dms.store_id = %s
                    AND dms.year = %s
                    AND dms.month = %s
            )
            SELECT
                dish_id,
                dish_code,
                dish_name,
                avg_price,
                total_quantity,
                avg_price * total_quantity as total_revenue
            FROM dish_data
            WHERE total_quantity > 0
        """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (store_id, year, year, month, store_id, year, month))
                    results = cursor.fetchall()

                    dish_data = {}
                    for row in results:
                        # Use dish_id as the key instead of dish_code
                        dish_data[row['dish_id']] = {
                            'dish_code': row['dish_code'],
                            'dish_name': row['dish_name'],
                            'avg_price': float(row['avg_price']) if row['avg_price'] else 0,
                            'total_quantity': float(row['total_quantity']) if row['total_quantity'] else 0,
                            'total_revenue': float(row['total_revenue']) if row['total_revenue'] else 0
                        }

                    return dish_data
        except Exception as e:
            logger.error(f"Error getting dish prices and sales: {e}")
            return {}

    def _get_store_data(self, store_id: int, store_name: str) -> list:
        """Get dish price change data for a specific store"""
        date_ranges = self._get_date_ranges()

        current_data = self._get_dish_prices_and_sales(date_ranges['current'], store_id)
        last_month_data = self._get_dish_prices_and_sales(date_ranges['last_month'], store_id)
        last_year_data = self._get_dish_prices_and_sales(date_ranges['last_year'], store_id)

        # Get all dish IDs that appear in any of the three periods
        all_dish_ids = set(current_data.keys()) | set(last_month_data.keys()) | set(last_year_data.keys())

        store_rows = []
        for dish_id in all_dish_ids:
            current = current_data.get(dish_id, {})
            last_month = last_month_data.get(dish_id, {})
            last_year = last_year_data.get(dish_id, {})

            # Skip if no current data
            if not current:
                continue

            current_price = current.get('avg_price', 0)
            last_month_price = last_month.get('avg_price', 0)
            last_year_price = last_year.get('avg_price', 0)
            current_quantity = current.get('total_quantity', 0)
            current_revenue = current.get('total_revenue', 0)

            # Calculate price changes
            # Only include actual price changes, not new dishes
            mom_price_change = current_price - last_month_price if last_month_price else 0
            yoy_price_change = current_price - last_year_price if last_year_price else 0

            # Calculate revenue impact of price changes
            mom_revenue_impact = mom_price_change * current_quantity
            yoy_revenue_impact = yoy_price_change * current_quantity

            # Get dish code and name from whichever period has data
            dish_code = current.get('dish_code', last_month.get('dish_code', last_year.get('dish_code', '')))
            dish_name = current.get('dish_name', last_month.get('dish_name', last_year.get('dish_name', '')))

            row = {
                '门店': store_name,
                '菜品编码': dish_code,
                '菜品名称': dish_name,
                '本期单价': current_price,
                '上期单价': last_month_price,
                '去年同期单价': last_year_price,
                '环比价格变动': mom_price_change,
                '同比价格变动': yoy_price_change,
                '本期销量': current_quantity,
                '本期收入': current_revenue,
                '环比影响收入': mom_revenue_impact,
                '同比影响收入': yoy_revenue_impact
            }

            store_rows.append(row)

        # Sort by absolute revenue impact (descending)
        return sorted(store_rows, key=lambda x: abs(x['环比影响收入']), reverse=True)

    def generate_sheet(self, workbook):
        """Generate the dish price change sheet"""
        ws = workbook.create_sheet(self.sheet_name)

        # Define stores
        stores = [
            (1, '加拿大一店'),
            (2, '加拿大二店'),
            (3, '加拿大三店'),
            (4, '加拿大四店'),
            (5, '加拿大五店'),
            (6, '加拿大六店'),
            (7, '加拿大七店')
        ]

        # Headers
        headers = [
            '门店', '菜品编码', '菜品名称', '本期单价', '上期单价',
            '去年同期单价', '环比价格变动', '同比价格变动', '本期销量',
            '本期收入', '环比影响收入', '同比影响收入'
        ]

        # Style definitions
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=11)
        border = Border(
            left=Side(border_style="thin"),
            right=Side(border_style="thin"),
            top=Side(border_style="thin"),
            bottom=Side(border_style="thin")
        )

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border

        # Collect all data
        all_data = []
        for store_id, store_name in stores:
            logger.info(f"Processing store: {store_name}")
            store_data = self._get_store_data(store_id, store_name)
            all_data.extend(store_data)

        # Write data rows
        row_num = 2
        for data in all_data:
            # Store name
            ws.cell(row=row_num, column=1, value=data['门店']).border = border

            # Dish code
            ws.cell(row=row_num, column=2, value=data['菜品编码']).border = border

            # Dish name
            ws.cell(row=row_num, column=3, value=data['菜品名称']).border = border

            # Current price
            ws.cell(row=row_num, column=4, value=round(data['本期单价'], 2)).border = border
            ws.cell(row=row_num, column=4).number_format = '#,##0.00'

            # Last month price
            ws.cell(row=row_num, column=5, value=round(data['上期单价'], 2)).border = border
            ws.cell(row=row_num, column=5).number_format = '#,##0.00'

            # Last year price
            ws.cell(row=row_num, column=6, value=round(data['去年同期单价'], 2)).border = border
            ws.cell(row=row_num, column=6).number_format = '#,##0.00'

            # MoM price change
            mom_change_cell = ws.cell(row=row_num, column=7, value=round(data['环比价格变动'], 2))
            mom_change_cell.border = border
            mom_change_cell.number_format = '#,##0.00'
            if data['环比价格变动'] > 0:
                mom_change_cell.font = Font(color="FF0000")  # Red for increase
            elif data['环比价格变动'] < 0:
                mom_change_cell.font = Font(color="008000")  # Green for decrease

            # YoY price change
            yoy_change_cell = ws.cell(row=row_num, column=8, value=round(data['同比价格变动'], 2))
            yoy_change_cell.border = border
            yoy_change_cell.number_format = '#,##0.00'
            if data['同比价格变动'] > 0:
                yoy_change_cell.font = Font(color="FF0000")  # Red for increase
            elif data['同比价格变动'] < 0:
                yoy_change_cell.font = Font(color="008000")  # Green for decrease

            # Current quantity
            ws.cell(row=row_num, column=9, value=round(data['本期销量'], 0)).border = border
            ws.cell(row=row_num, column=9).number_format = '#,##0'

            # Current revenue
            ws.cell(row=row_num, column=10, value=round(data['本期收入'], 2)).border = border
            ws.cell(row=row_num, column=10).number_format = '#,##0.00'

            # MoM revenue impact
            mom_impact_cell = ws.cell(row=row_num, column=11, value=round(data['环比影响收入'], 2))
            mom_impact_cell.border = border
            mom_impact_cell.number_format = '#,##0.00'
            if data['环比影响收入'] > 0:
                mom_impact_cell.font = Font(color="FF0000")  # Red for increase
            elif data['环比影响收入'] < 0:
                mom_impact_cell.font = Font(color="008000")  # Green for decrease

            # YoY revenue impact
            yoy_impact_cell = ws.cell(row=row_num, column=12, value=round(data['同比影响收入'], 2))
            yoy_impact_cell.border = border
            yoy_impact_cell.number_format = '#,##0.00'
            if data['同比影响收入'] > 0:
                yoy_impact_cell.font = Font(color="FF0000")  # Red for increase
            elif data['同比影响收入'] < 0:
                yoy_impact_cell.font = Font(color="008000")  # Green for decrease

            row_num += 1

        # Set column widths
        column_widths = [15, 15, 30, 12, 12, 15, 15, 15, 12, 15, 15, 15]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        # Freeze panes (keep header visible)
        ws.freeze_panes = 'A2'

        logger.info(f"Generated {self.sheet_name} with {row_num - 2} rows of data")
        return ws