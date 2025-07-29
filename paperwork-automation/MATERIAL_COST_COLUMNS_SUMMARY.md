# Material Report Cost Columns Enhancement

## Summary

Successfully added two new cost calculation columns to the **物料用量差异分析** sheet in the material report, providing detailed financial analysis of material usage and variances.

## New Columns Added

### **Column N: 本月总消费金额 (Total Money Spent This Month)**
- **Formula**: `(理论用量 + 套餐用量 + 系统记录) × 物料单价`
- **Excel Formula**: `=(G{row}+H{row}+I{row})*{material_price}`
- **Purpose**: Calculate total money spent on each material across all usage types
- **Format**: Currency format with 2 decimal places (`#,##0.00`)

### **Column O: 差异金额 (Variance Cost)**
- **Formula**: `差异数量 × 物料单价`
- **Excel Formula**: `=K{row}*{material_price}`
- **Purpose**: Calculate the financial impact of material usage variance
- **Format**: Currency format with 2 decimal places (`#,##0.00`)

## Technical Implementation

### 1. **Database Enhancement**
Added material price query to `get_material_variance_data()` method:

```sql
SELECT 
    m.id as material_id,
    m.name as material_name,
    mph.store_id,
    s.name as store_name,
    COALESCE(mph.price, 0) as material_price
FROM material m
LEFT JOIN material_price_history mph ON m.id = mph.material_id
LEFT JOIN store s ON mph.store_id = s.id
WHERE m.is_active = TRUE 
    AND mph.is_active = true
    AND mph.effective_date <= (date_trunc('month', make_date(%s, %s, 1)) + interval '1 month - 1 day')::date
ORDER BY s.name, m.id, mph.effective_date DESC
```

### 2. **Data Structure Update**
Extended variance data dictionary to include:
```python
'material_price': material_price  # Added to each variance record
```

### 3. **Worksheet Layout Update**
- **Total Columns**: Expanded from 13 to 15 columns (A-O)
- **Column Widths**: Updated to accommodate new cost columns
- **Title Span**: Extended to cover all 15 columns
- **Headers**: Added "本月总消费金额" and "差异金额"

### 4. **Formatting Enhancements**
- **Numeric Format**: Applied currency formatting (`#,##0.00`) to cost columns
- **Border Styling**: Extended to include new columns
- **Row Highlighting**: Variance-based color coding applies to all 15 columns

## Usage Examples

### **Total Money Spent Calculation**
For a material with:
- 理论用量 (Theoretical): 10.50 kg
- 套餐用量 (Combo): 2.30 kg  
- 系统记录 (System): 13.20 kg
- 物料单价 (Price): $8.50/kg

**Total Cost**: (10.50 + 2.30 + 13.20) × $8.50 = $221.00

### **Variance Cost Calculation**
For the same material with:
- 差异数量 (Variance): -0.40 kg (shortage)
- 物料单价 (Price): $8.50/kg

**Variance Cost**: -0.40 × $8.50 = -$3.40 (cost saving due to shortage)

## Benefits

1. **Financial Visibility**: Store managers can see actual dollar impact of material usage
2. **Cost Control**: Identify materials with highest financial variance impact
3. **Budget Planning**: Use total spending data for future procurement planning
4. **Performance Analysis**: Track cost efficiency across different material categories
5. **Decision Making**: Prioritize variance reduction efforts based on financial impact

## File Changes Made

### Modified Files:
- `lib/monthly_dishes_worksheet.py`
  - Enhanced `get_material_variance_data()` with price query
  - Updated `add_variance_data_section()` with new columns
  - Extended formatting functions for 15 columns
  - Updated column widths and header spans

### Test Results:
- ✅ **Successfully generated**: 15-column worksheet (A-O)
- ✅ **Formulas working**: Both cost calculations implemented correctly
- ✅ **Formatting applied**: Currency format and borders working
- ✅ **Data integration**: Material prices successfully retrieved and applied

## Column Layout Summary

| Col | Header | Content | Formula |
|-----|--------|---------|---------|
| A | 序号 | Row number | - |
| B | 门店 | Store name | - |
| C | 物料名称 | Material name | - |
| D | 物料号 | Material number | - |
| E | 单位 | Unit | - |
| F | 包装规格 | Package spec | - |
| G | 理论用量 | Theoretical usage | - |
| H | 套餐用量 | Combo usage | - |
| I | 系统记录 | System record | - |
| J | 库存盘点 | Inventory count | - |
| K | 差异数量 | Variance quantity | `=I-(G+H+J)` |
| L | 差异率(%) | Variance rate | `=ABS(K/I)*100` |
| M | 状态 | Status | - |
| **N** | **本月总消费金额** | **Total monthly cost** | **=(G+H+I)*price** |
| **O** | **差异金额** | **Variance cost** | **=K*price** |

The enhancement is now complete and ready for production use!