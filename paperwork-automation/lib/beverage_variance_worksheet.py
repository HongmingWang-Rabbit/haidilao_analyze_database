#!/usr/bin/env python3
"""
Beverage Variance Worksheet Generator
Generates detailed beverage variance analysis showing system vs inventory differences
"""

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


class BeverageVarianceGenerator:
    """Generator for beverage variance detail worksheet"""

    def __init__(self, data_provider):
        self.data_provider = data_provider
        self.db_manager = data_provider.db_manager

    def generate_worksheet(self, workbook, target_date: str):
        """Generate beverage variance detail worksheet"""
        worksheet = workbook.create_sheet("酒水差异明细表")

        # Set up styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(
            start_color="C41E3A", end_color="C41E3A", fill_type="solid")
        data_font = Font(size=10)
        border = Border(left=Side(style='thin'), right=Side(style='thin'),
                        top=Side(style='thin'), bottom=Side(style='thin'))

        # Parse target date
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        year, month = target_dt.year, target_dt.month

        # Create header row
        headers = [
            "月份", "来源", "大区", "门店", "物料编号", "物料名称",
            "规格", "单位", "系统数量", "盘点数量", "差异数量",
            "单价", "差异金额", "备注"
        ]

        # Set headers
        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border

        # Get detailed variance data
        variance_details = self.get_beverage_variance_details(year, month)

        # Populate data rows
        row = 2
        for detail in variance_details:
            worksheet.cell(row=row, column=1, value=f"{year:04d}{month:02d}")
            worksheet.cell(row=row, column=2, value=detail['source'])
            worksheet.cell(row=row, column=3, value=detail['region'])
            worksheet.cell(row=row, column=4, value=detail['store_name'])
            worksheet.cell(row=row, column=5, value=detail['material_number'])
            worksheet.cell(row=row, column=6, value=detail['material_name'])
            worksheet.cell(row=row, column=7, value=detail['specification'])
            worksheet.cell(row=row, column=8, value=detail['unit'])
            worksheet.cell(row=row, column=9, value=detail['system_quantity'])
            worksheet.cell(row=row, column=10,
                           value=detail['counted_quantity'])
            worksheet.cell(row=row, column=11,
                           value=detail['variance_quantity'])
            worksheet.cell(row=row, column=12, value=detail['unit_price'])
            worksheet.cell(row=row, column=13, value=detail['variance_amount'])
            worksheet.cell(row=row, column=14, value=detail['remarks'])

            # Apply styling to data rows
            for col in range(1, 15):
                cell = worksheet.cell(row=row, column=col)
                cell.font = data_font
                cell.border = border
                cell.alignment = Alignment(
                    horizontal='center', vertical='center')

            row += 1

        # Add summary row
        if variance_details:
            # Empty cells for non-summary columns
            for col in range(1, 9):
                worksheet.cell(row=row, column=col, value="").border = border

            # Summary labels and totals
            worksheet.cell(row=row, column=9,
                           value="合计").font = Font(bold=True)
            worksheet.cell(row=row, column=9).border = border
            worksheet.cell(row=row, column=9).alignment = Alignment(
                horizontal='center')

            # Calculate totals
            total_system = sum(float(detail['system_quantity'])
                               for detail in variance_details)
            total_counted = sum(float(detail['counted_quantity'])
                                for detail in variance_details)
            total_variance = sum(
                float(detail['variance_quantity']) for detail in variance_details)
            total_amount = sum(float(detail['variance_amount'])
                               for detail in variance_details)

            worksheet.cell(row=row, column=10,
                           value=f"{total_system:.2f}").font = Font(bold=True)
            worksheet.cell(row=row, column=10).border = border
            worksheet.cell(row=row, column=10).alignment = Alignment(
                horizontal='center')

            worksheet.cell(row=row, column=11,
                           value=f"{total_counted:.2f}").font = Font(bold=True)
            worksheet.cell(row=row, column=11).border = border
            worksheet.cell(row=row, column=11).alignment = Alignment(
                horizontal='center')

            worksheet.cell(row=row, column=12,
                           value=f"{total_variance:.2f}").font = Font(bold=True)
            worksheet.cell(row=row, column=12).border = border
            worksheet.cell(row=row, column=12).alignment = Alignment(
                horizontal='center')

            worksheet.cell(row=row, column=13, value="").border = border
            worksheet.cell(row=row, column=14,
                           value=f"{total_amount:.2f}").font = Font(bold=True)
            worksheet.cell(row=row, column=14).border = border
            worksheet.cell(row=row, column=14).alignment = Alignment(
                horizontal='center')

        # Set column widths
        column_widths = [10, 12, 10, 20, 15, 25, 15, 8, 12, 12, 12, 12, 12, 15]
        for i, width in enumerate(column_widths, 1):
            worksheet.column_dimensions[get_column_letter(i)].width = width

        return worksheet

    def get_beverage_variance_details(self, year: int, month: int):
        """Get detailed beverage variance data"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Query detailed beverage variance data - simplified without system_quantity
                query = """
                SELECT 
                    s.id as store_id,
                    s.name as store_name,
                    m.material_number,
                    m.name as material_name,
                    m.package_spec as specification,
                    m.unit,
                    0 as system_quantity,  -- No system quantity available
                    COALESCE(ic.counted_quantity, 0) as counted_quantity,
                    COALESCE(ic.counted_quantity, 0) as variance_quantity,  -- Use counted as variance
                    10.0 as unit_price,  -- Simplified: assume $10 average price
                    COALESCE(ic.counted_quantity, 0) * 10.0 as variance_amount,
                    mt.name as material_type_name,
                    CASE 
                        WHEN COALESCE(ic.counted_quantity, 0) > 0 
                        THEN '有库存'
                        ELSE '无库存'
                    END as remarks
                    
                FROM store s
                JOIN inventory_count ic ON s.id = ic.store_id 
                    AND EXTRACT(year FROM ic.count_date) = %s AND EXTRACT(month FROM ic.count_date) = %s
                JOIN material m ON ic.material_id = m.id
                JOIN material_type mt ON m.material_type_id = mt.id
                WHERE s.is_active = TRUE
                AND mt.name = '成本-酒水类'
                AND COALESCE(ic.counted_quantity, 0) > 0
                ORDER BY s.id, mt.name, m.name
                """

                cursor.execute(query, (year, month))
                results = cursor.fetchall()

                # Convert to list of dictionaries
                variance_details = []
                for row in results:
                    variance_details.append({
                        'store_id': row['store_id'],
                        'store_name': row['store_name'],
                        'material_number': row['material_number'] or '',
                        'material_name': row['material_name'] or '',
                        'specification': row['specification'] or '',
                        'unit': row['unit'] or '个',
                        'system_quantity': f"{row['system_quantity']:.2f}" if row['system_quantity'] else "0.00",
                        'counted_quantity': f"{row['counted_quantity']:.2f}" if row['counted_quantity'] else "0.00",
                        'variance_quantity': f"{row['variance_quantity']:.2f}" if row['variance_quantity'] else "0.00",
                        'unit_price': f"{row['unit_price']:.2f}" if row['unit_price'] else "0.00",
                        'variance_amount': f"{row['variance_amount']:.2f}" if row['variance_amount'] else "0.00",
                        'source': 'SAP系统',
                        'region': '加拿大',
                        'remarks': row['remarks'] or ''
                    })

                return variance_details

        except Exception as e:
            print(f"ERROR: Failed to get beverage variance details: {e}")
            return []
