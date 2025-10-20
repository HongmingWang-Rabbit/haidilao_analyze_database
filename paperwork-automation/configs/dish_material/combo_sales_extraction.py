# Combo sales extraction configuration

COMBO_SALES_COLUMN_MAPPINGS = {
    "month": "月份",                      # Month (202507)
    "country": "国家",                    # Country
    "store_name": "门店名称",             # Store name
    "sales_mode": "销售模式",             # Sales mode (堂食, 外卖, etc.)
    "category": "大类名称",               # Main category
    "subcategory": "小类名称",            # Subcategory
    "combo_code": "套餐编码",             # Combo code
    "combo_name": "套餐名称",             # Combo name
    "combo_size": "套餐规格",             # Combo size/spec
    "combo_price": "套餐单价",            # Combo unit price
    "dish_code": "菜品编码",              # Dish code
    "dish_name": "菜品名称",              # Dish name
    "dish_size": "菜品规格名称",          # Dish size/spec name
    "dish_price": "菜品单价",             # Dish unit price
    "dish_unit": "菜品单位",              # Dish unit
    "sale_quantity": "出品数量",          # Sales quantity
    "sale_amount": "出品金额",            # Sales amount
    "return_quantity": "退菜数量",        # Return quantity
    "return_amount": "退菜金额",          # Return amount
    "net_quantity": "应收数量",           # Net quantity (sale - return)
    "net_amount": "应收金额",             # Net amount
    "combo_discount": "套餐折扣",         # Combo discount rate
    "actual_revenue": "实收金额",         # Actual revenue
    "net_revenue": "销售产品净收入",      # Net revenue
    "tax": "税额",                        # Tax amount
    "net_after_tax": "净额"              # Net after tax
}

# Store name to ID mapping (same as dish extraction)
COMBO_STORE_MAPPING = {
    "加拿大一店": 1,
    "加拿大二店": 2,
    "加拿大三店": 3,
    "加拿大四店": 4,
    "加拿大五店": 5,
    "加拿大六店": 6,
    "加拿大七店": 7,
    "加拿大八店": 8,
}

# Default sheet name for combo sales
COMBO_SALES_SHEET_NAME = "套餐销售汇总"