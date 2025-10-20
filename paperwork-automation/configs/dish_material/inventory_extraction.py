# Inventory checking result extraction configuration

INVENTORY_COLUMN_MAPPINGS = {
    "row_number": "行号",           # Row number
    "material_code": "物料编码",    # Material code
    "material_name": "物料名称",    # Material name
    "stock_quantity": "库存数量",   # Stock quantity (system)
    "count_quantity": "盘点数量",   # Count quantity (physical)
    "unit": "单位",                 # Unit
    "unit_code": "单位编码",        # Unit code
    "unit_desc": "单位描述"         # Unit description
}

# Store folder to store ID mapping
# The folder structure is /1/, /2/, etc. for each store
INVENTORY_STORE_MAPPING = {
    "1": 1,  # CA01 - 加拿大一店
    "2": 2,  # CA02 - 加拿大二店
    "3": 3,  # CA03 - 加拿大三店
    "4": 4,  # CA04 - 加拿大四店
    "5": 5,  # CA05 - 加拿大五店
    "6": 6,  # CA06 - 加拿大六店
    "7": 7,  # CA07 - 加拿大七店
    "8": 8,
}

# File name pattern to extract store code
# Example: CA01-7月-盘点结果.xls -> CA01
INVENTORY_FILE_PATTERN = r'^(CA\d{2})-.*盘点结果\.xls$'

# Store code to ID mapping (alternative)
INVENTORY_STORE_CODE_MAPPING = {
    "CA01": 1,
    "CA02": 2,
    "CA03": 3,
    "CA04": 4,
    "CA05": 5,
    "CA06": 6,
    "CA07": 7,
}