# Store Configuration

This directory contains centralized configuration for all store-related data and mock data for testing/development.

## Purpose

All hardcoded store information, manager assignments, seating capacities, and mock data have been moved to this centralized location to:

1. **Eliminate code duplication** - Single source of truth for store data
2. **Improve maintainability** - Update store info in one place
3. **Ensure consistency** - All code uses same store data
4. **Simplify testing** - Centralized mock data for development

## Files

### `store_info.py`

Contains all store-related configuration:

- **`STORE_MANAGERS`**: Dictionary mapping store IDs to manager names
- **`STORE_SEATING_CAPACITY`**: Dictionary mapping store IDs to seating capacities
- **`REGIONAL_MANAGER`**: Regional manager name (蒋冰遇)
- **`WESTERN_REGION_STORES`**: List of western region store IDs [1, 2, 7]
- **`EASTERN_REGION_STORES`**: List of eastern region store IDs [3, 4, 5, 6, 8]
- **`ALL_CANADIAN_STORES`**: List of all Canadian store IDs [1-8]
- **`REPORT_STORE_ORDER`**: Display order for reports [1, 2, 7, 3, 4, 5, 6, 8]

**Helper Functions:**
- `get_store_manager(store_id)` - Get manager name for a store
- `get_seating_capacity(store_id)` - Get seating capacity for a store
- `get_region(store_id)` - Get region (西部/东部) for a store

### `mock_data.py`

Contains mock data for testing and development:

- **`DAILY_STORE_MOCK_DATA`**: Mock data for daily store tracking
- **`WEEKLY_STORE_MOCK_DATA`**: Mock data for weekly store tracking

**Helper Functions:**
- `get_daily_mock_data()` - Get mock data for daily store tracking
- `get_weekly_mock_data()` - Get mock data for weekly store tracking
- `get_mock_data_by_store_id(store_id, data_type)` - Get mock data for specific store

### `__init__.py`

Package initialization file that exports all public APIs for easy importing.

## Usage

### Importing Store Information

```python
from configs.store_config import (
    STORE_MANAGERS,
    STORE_SEATING_CAPACITY,
    get_store_manager,
    get_seating_capacity,
    get_region
)

# Get manager for store 1
manager = get_store_manager(1)  # Returns: '张森磊'

# Get seating capacity for store 4
capacity = get_seating_capacity(4)  # Returns: 70

# Get region for store 3
region = get_region(3)  # Returns: '东部'

# Use dictionaries directly
all_managers = STORE_MANAGERS
all_capacities = STORE_SEATING_CAPACITY
```

### Importing Mock Data

```python
from configs.store_config import (
    get_daily_mock_data,
    get_weekly_mock_data,
    get_mock_data_by_store_id
)

# Get all daily mock data
daily_data = get_daily_mock_data()  # Returns list of 8 stores

# Get all weekly mock data
weekly_data = get_weekly_mock_data()  # Returns list of 8 stores

# Get specific store data
store_4_daily = get_mock_data_by_store_id(4, 'daily')
store_4_weekly = get_mock_data_by_store_id(4, 'weekly')
```

## Adding a New Store

To add a new store (e.g., Store 9):

1. **Update `store_info.py`:**
   ```python
   STORE_MANAGERS[9] = 'Manager Name'
   STORE_SEATING_CAPACITY[9] = 60
   # Add to appropriate region
   EASTERN_REGION_STORES.append(9)
   # Update ALL_CANADIAN_STORES (already uses range(1, 9), update to range(1, 10))
   # Update REPORT_STORE_ORDER
   ```

2. **Update `mock_data.py`:**
   ```python
   # Add to DAILY_STORE_MOCK_DATA
   {
       'store_id': 9,
       'store_name': '加拿大九店',
       'manager_name': 'Manager Name',
       'seating_capacity': 60,
       # ... other fields
   }

   # Add to WEEKLY_STORE_MOCK_DATA with similar structure
   ```

3. **Update `lib/config.py`:**
   ```python
   # Update STORE_IDS from range(1, 9) to range(1, 10)
   ```

4. **Update database and reports** to handle the new store

## Files Updated to Use This Config

The following files have been updated to use centralized configuration:

- `lib/database_queries.py` - Uses `STORE_MANAGERS` and `STORE_SEATING_CAPACITY`
- `lib/daily_store_tracking_worksheet.py` - Uses `get_daily_mock_data()`
- `lib/weekly_store_tracking_worksheet.py` - Uses `get_weekly_mock_data()`

## Migration Notes

**Before (Hardcoded):**
```python
# In database_queries.py
store_managers = {
    1: '张森磊',
    2: '潘幸远',
    # ... hardcoded
}

# In daily_store_tracking_worksheet.py
def _get_mock_store_data(self):
    return [
        {'store_id': 1, 'manager_name': '张森磊', ...},
        # ... 100+ lines of hardcoded data
    ]
```

**After (Centralized):**
```python
# In database_queries.py
from configs.store_config import STORE_MANAGERS
store_managers = STORE_MANAGERS

# In daily_store_tracking_worksheet.py
from configs.store_config import get_daily_mock_data

def _get_mock_store_data(self):
    return get_daily_mock_data()
```

## Benefits

✅ **Single Source of Truth**: All store data in one location
✅ **Easy Updates**: Change manager or capacity in one place
✅ **Consistency**: All code uses same data
✅ **Type Safety**: Type hints for all functions
✅ **Testability**: Easy to mock and test
✅ **Maintainability**: Clear structure and documentation

## Future Enhancements

Potential improvements:
- Load from YAML/JSON config files
- Database-backed configuration
- Environment-specific configs (dev/staging/prod)
- Validation and schema checking
