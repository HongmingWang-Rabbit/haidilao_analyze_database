
DISH_COLUMN_MAPPINGS = {
    "store_name": "门店名称",  # Add store name column
    "name": "菜品名称(门店pad显示名称)",
    "full_code": "菜品编码",
    "system_name": "菜品名称(系统统一名称)",
    "size": "规格",
    "short_code": "菜品短编码",
    "dish_type_name": "大类名称",
    "dish_child_type_name": "子类名称",
    "dish_price_this_month": "菜品单价",
    "sale_amount": "出品数量",
    "return_amount": "退菜数量",
    "free_amount": "免单数量",
    "gift_amount": "赠菜数量",
    "tax_amount": "税额",  # Tax amount column
}

# Alternative column mappings for folder-based exports (one file per store)
DISH_COLUMN_MAPPINGS_ALT = {
    "store_name": "门店名称",  # Store name is in the data itself
    "name": "菜品名称",  # Simplified column name (required field)
    "full_code": "菜品编码",
    # Note: system_name is not mapped in this format - will default to name value
    "size": "规格",
    "short_code": "菜品短编码",
    "dish_type_name": "大类名称",
    "dish_child_type_name": "子类名称",
    "dish_price_this_month": "菜品单价",
    "sale_amount": "出品数量",
    "return_amount": "退菜数量",
    "free_amount": "免单数量",
    "gift_amount": "赠菜数量",
    "tax_amount": "税额",  # Tax amount column
}

DISH_FILE_STOREID_MAPPING = {
    "加拿大一店": 1,
    "加拿大二店": 2,
    "加拿大三店": 3,
    "加拿大四店": 4,
    "加拿大五店": 5,
    "加拿大六店": 6,
    "加拿大七店": 7,
}
