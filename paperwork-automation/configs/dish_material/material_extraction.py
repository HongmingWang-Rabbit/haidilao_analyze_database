# Material extraction configuration for export.XLSX file

MATERIAL_COLUMN_MAPPINGS = {
    "start_date": "开始日期",                  # Start date
    "end_date": "结束日期",                    # End date
    "store_code": "工厂",                      # Store code (CA01, CA02, etc.)
    "store_description": "工厂描述",           # Store description
    "material_number": "物料",                 # Material number
    "material_description": "物料描述",        # Material description
    "bun": "Bun",                              # Bun
    "unit_description": "单位描述",            # Unit description
    "category": "大类",                        # Main category
    "unit_price": "系统发出单价",              # System unit price
    "quantity": "数量",                        # Quantity
    "total_amount": "系统发出金额",            # System total amount
    "material_classification": "物料分类",     # Material classification
    "material_class_desc": "物料分类描述",     # Material classification description
    "material_187_class": "187-物料分类",      # 187 material classification
    "material_187_desc": "187-物料分类描述",    # 187 material classification description
    "material_187_level1": "187-一级分类",     # 187 first level classification
    "material_187_level2": "187-二级分类",     # 187 second level classification
    "material_187_flag": "187-标记",           # 187 flag
    "material_187_generic": "187-物料描述(通用)" # 187 generic material description
}

# Store code to ID mapping
STORE_CODE_MAPPING = {
    "CA01": 1,  # 加拿大一店
    "CA02": 2,  # 加拿大二店
    "CA03": 3,  # 加拿大三店
    "CA04": 4,  # 加拿大四店
    "CA05": 5,  # 加拿大五店
    "CA06": 6,  # 加拿大六店
    "CA07": 7,  # 加拿大七店
}

# Material type mapping based on 187-一级分类 (first level classification)
MATERIAL_TYPE_MAPPING = {
    "成本-锅底类": 1,
    "成本-荤菜类": 2,
    "成本-素菜类": 3,
    "成本-酒水类": 4,
    "成本-调料类": 5,
    "成本-其他类": 6,
    "成本-包装类": 7,
    "成本-冰淇淋": 8,
    "成本-零食类": 9,
    "成本-饮料类": 10,
    "成本-服务用品": 11,
    "成本-小料台类": 12,  # Additional type from the data
}