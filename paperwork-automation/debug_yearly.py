#!/usr/bin/env python3
from utils.database import DatabaseConfig, DatabaseManager
from scripts.generate_database_report import YearlyComparisonWorksheetGenerator

config = DatabaseConfig(is_test=True)
db_manager = DatabaseManager(config)

# Store mapping
store_names = {
    1: "加拿大一店", 2: "加拿大二店", 3: "加拿大三店", 4: "加拿大四店",
    5: "加拿大五店", 6: "加拿大六店", 7: "加拿大七店"
}

# Create the generator
generator = YearlyComparisonWorksheetGenerator(db_manager, store_names, "2025-06-10")

print("Testing yearly comparison data generation...")

# Get current year data (month-to-date)
current_mtd_data = generator.get_monthly_data_up_to_date(2025, 6, 10)
print(f"\nCurrent year data (2025): {len(current_mtd_data)} records")
if current_mtd_data:
    print("First record:", current_mtd_data[0])
    print("Keys:", list(current_mtd_data[0].keys()))

# Get previous year data (same period)
previous_mtd_data = generator.get_monthly_data_up_to_date(2024, 6, 10)
print(f"\nPrevious year data (2024): {len(previous_mtd_data)} records")
if previous_mtd_data:
    print("First record:", previous_mtd_data[0])

# Test the data processing
if current_mtd_data and previous_mtd_data:
    current_dict = {row['store_id']: row for row in current_mtd_data}
    previous_dict = {row['store_id']: row for row in previous_mtd_data}
    
    store_id = 1
    current = current_dict.get(store_id, {})
    previous = previous_dict.get(store_id, {})
    
    print(f"\nStore {store_id} current data:")
    print(f"  total_tables: {current.get('total_tables')} (type: {type(current.get('total_tables'))})")
    print(f"  avg_turnover_rate: {current.get('avg_turnover_rate')} (type: {type(current.get('avg_turnover_rate'))})")
    
    print(f"\nStore {store_id} previous data:")
    print(f"  total_tables: {previous.get('total_tables')} (type: {type(previous.get('total_tables'))})")
    print(f"  avg_turnover_rate: {previous.get('avg_turnover_rate')} (type: {type(previous.get('avg_turnover_rate'))})")
    
    # Test conversion
    try:
        current_tables = float(current.get('total_tables', 0))
        current_turnover = float(current.get('avg_turnover_rate', 0))
        previous_tables = float(previous.get('total_tables', 0)) if previous else 0
        previous_turnover = float(previous.get('avg_turnover_rate', 0)) if previous else 0
        
        print(f"\nAfter conversion:")
        print(f"  current_tables: {current_tables}")
        print(f"  current_turnover: {current_turnover}")
        print(f"  previous_tables: {previous_tables}")
        print(f"  previous_turnover: {previous_turnover}")
        
    except Exception as e:
        print(f"Conversion error: {e}")
        import traceback
        traceback.print_exc() 