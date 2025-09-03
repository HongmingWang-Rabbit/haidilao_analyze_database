# Inventory Views Guide

This document describes the SQL views created for easier querying of inventory data with material names and other details.

## Available Views

### 1. `inventory_count_with_materials`
**Purpose**: Main view that joins inventory counts with material details and store names.

**Columns**:
- `id`, `year`, `month`, `store_id`, `store_name`
- `material_id`, `material_number`, `material_name`, `material_description`
- `unit`, `material_type`, `material_child_type`
- `counted_quantity`, `created_at`, `created_by`

**Sample Query**:
```sql
-- Get inventory for specific store and month
SELECT material_number, material_name, counted_quantity, unit
FROM inventory_count_with_materials
WHERE year = 2025 AND month = 7 AND store_id = 1
ORDER BY material_name;
```

### 2. `inventory_summary_by_month`
**Purpose**: Monthly summary showing total materials and quantities per store.

**Columns**:
- `year`, `month`, `store_id`, `store_name`
- `material_count` (number of distinct materials)
- `total_quantity` (sum of all counted quantities)
- `first_entry`, `last_entry` (timestamps)

**Sample Query**:
```sql
-- Get monthly summary for all stores
SELECT year, month, store_name, material_count, total_quantity
FROM inventory_summary_by_month
WHERE year = 2025
ORDER BY year DESC, month DESC;
```

### 3. `inventory_quantity_changes`
**Purpose**: Shows month-over-month quantity changes for materials.

**Columns**:
- `store_id`, `store_name`, `material_id`, `material_number`, `material_name`
- `year`, `month`, `unit`
- `counted_quantity`, `previous_quantity`
- `quantity_change` (absolute change)
- `percentage_change` (percent change)

**Sample Query**:
```sql
-- Find materials with big changes (>50%)
SELECT store_name, material_name, 
       previous_quantity, counted_quantity, percentage_change
FROM inventory_quantity_changes
WHERE year = 2025 AND month = 7
  AND ABS(percentage_change) > 50
ORDER BY ABS(percentage_change) DESC;
```

### 4. `materials_not_in_inventory`
**Purpose**: Lists active materials that have never been counted in inventory.

**Columns**:
- `store_id`, `store_name`
- `material_id`, `material_number`, `material_name`
- `unit`, `material_type`, `material_child_type`

**Sample Query**:
```sql
-- Find materials never counted for a store
SELECT material_number, material_name, material_type
FROM materials_not_in_inventory
WHERE store_id = 1;
```

## Common Use Cases

### Search for Specific Materials
```sql
-- Find all beef-related materials
SELECT DISTINCT material_number, material_name, unit
FROM inventory_count_with_materials
WHERE material_name ILIKE '%beef%' 
   OR material_name ILIKE '%牛%';
```

### Compare Stores
```sql
-- Compare total inventory value across stores for a month
SELECT store_name, 
       COUNT(DISTINCT material_id) as unique_materials,
       SUM(counted_quantity) as total_units
FROM inventory_count_with_materials
WHERE year = 2025 AND month = 7
GROUP BY store_id, store_name
ORDER BY total_units DESC;
```

### Track Material Over Time
```sql
-- Track a specific material's quantity over months
SELECT year, month, store_name, counted_quantity
FROM inventory_count_with_materials
WHERE material_number = '4021526'
ORDER BY year, month, store_id;
```

### Export to Excel
```sql
-- Export full inventory for a month
COPY (
    SELECT store_name, material_number, material_name, 
           counted_quantity, unit, material_type
    FROM inventory_count_with_materials
    WHERE year = 2025 AND month = 7
    ORDER BY store_id, material_name
) TO '/tmp/inventory_july_2025.csv' WITH CSV HEADER;
```

## Python Usage Example

```python
from utils.database import DatabaseManager, DatabaseConfig

db_config = DatabaseConfig()
db_manager = DatabaseManager(db_config)

with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    
    # Query using the view
    cursor.execute("""
        SELECT material_number, material_name, counted_quantity, unit
        FROM inventory_count_with_materials
        WHERE year = %s AND month = %s AND store_id = %s
        ORDER BY counted_quantity DESC
        LIMIT 10
    """, (2025, 7, 1))
    
    for row in cursor.fetchall():
        print(f"{row['material_number']}: {row['material_name']} - {row['counted_quantity']} {row['unit']}")
```

## Notes
- All views are read-only (cannot INSERT/UPDATE/DELETE through views)
- Views automatically reflect any changes in underlying tables
- Use indexes on year, month, and store_id for best performance
- Material names may contain Chinese characters - ensure proper encoding when displaying