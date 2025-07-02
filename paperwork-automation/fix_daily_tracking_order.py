#!/usr/bin/env python3
"""
Extract correct mapping from reference file and fix daily tracking worksheet
"""

import pandas as pd
from utils.database import get_database_manager


def extract_reference_mapping():
    """Extract the correct store order and values from reference file"""

    reference_file = "data/dishes_related/跟踪表-加拿大.xlsx"

    try:
        # Read the reference file
        df = pd.read_excel(reference_file, sheet_name=0)

        print("🔍 EXTRACTING CORRECT MAPPING FROM REFERENCE FILE")
        print("=" * 60)

        # Extract the correct store order and values
        reference_stores = []

        # Process store rows (rows 2-8 based on analysis)
        store_rows = [
            (2, "加拿大五店", 5),  # Row 2 = Store 5
            (3, "加拿大六店", 6),  # Row 3 = Store 6
            (4, "加拿大三店", 3),  # Row 4 = Store 3
            (5, "加拿大四店", 4),  # Row 5 = Store 4
            (6, "加拿大一店", 1),  # Row 6 = Store 1
            (7, "加拿大七店", 7),  # Row 7 = Store 7
            (8, "加拿大二店", 2),  # Row 8 = Store 2
        ]

        print("📊 CORRECT STORE ORDER AND VALUES:")
        print("-" * 60)
        print(
            f"{'Row':<3} {'Store':<10} {'Store Name':<12} {'Turnover':<10} {'Revenue':<10}")
        print("-" * 60)

        for row_idx, store_name, store_id in store_rows:
            if row_idx < len(df):
                row_data = df.iloc[row_idx]

                # Extract values from the row
                # Based on analysis: column 5 = turnover 2025, column 10 = revenue 2025
                turnover_2025 = row_data.iloc[5] if len(row_data) > 5 else 0
                revenue_2025 = row_data.iloc[10] if len(row_data) > 10 else 0

                reference_stores.append({
                    'display_order': len(reference_stores) + 1,
                    'store_id': store_id,
                    'store_name': store_name,
                    'turnover_2025': round(float(turnover_2025), 2),
                    'revenue_2025': round(float(revenue_2025), 2)
                })

                print(
                    f"{len(reference_stores):<3} {store_id:<10} {store_name:<12} {turnover_2025:<10.2f} {revenue_2025:<10.2f}")

        # Extract regional totals from row 1
        regional_row = df.iloc[1]
        regional_turnover = round(float(regional_row.iloc[5]), 2) if len(
            regional_row) > 5 else 0
        regional_revenue = round(float(regional_row.iloc[10]), 2) if len(
            regional_row) > 10 else 0

        print("-" * 60)
        print(
            f"{'REG':<3} {'TOTAL':<10} {'区域':<12} {regional_turnover:<10.2f} {regional_revenue:<10.2f}")

        return reference_stores, regional_turnover, regional_revenue

    except Exception as e:
        print(f"❌ Error extracting reference mapping: {e}")
        import traceback
        traceback.print_exc()
        return [], 0, 0


def compare_with_database(reference_stores):
    """Compare reference values with database values"""

    try:
        db_manager = get_database_manager()

        # Query database for 2025-06-28
        query = """
        SELECT 
            dr.store_id,
            s.name as store_name,
            dr.revenue_tax_not_included,
            dr.turnover_rate
        FROM daily_report dr
        JOIN store s ON dr.store_id = s.id
        WHERE dr.date = '2025-06-28'
        ORDER BY dr.store_id
        """

        db_results = db_manager.fetch_all(query)

        print("\n🔍 COMPARING REFERENCE VS DATABASE:")
        print("=" * 80)
        print(f"{'Order':<5} {'Store':<12} {'Ref Rev':<8} {'DB Rev':<8} {'Rev Diff':<8} {'Ref Turn':<8} {'DB Turn':<8} {'Turn Diff':<8}")
        print("-" * 80)

        # Create database lookup
        db_lookup = {row['store_id']: row for row in db_results}

        total_ref_revenue = 0
        total_db_revenue = 0
        discrepancies = []

        for ref_store in reference_stores:
            store_id = ref_store['store_id']
            ref_revenue = ref_store['revenue_2025']
            ref_turnover = ref_store['turnover_2025']

            total_ref_revenue += ref_revenue

            if store_id in db_lookup:
                db_data = db_lookup[store_id]
                db_revenue = float(db_data['revenue_tax_not_included']) / 10000
                db_turnover = float(db_data['turnover_rate'])

                total_db_revenue += db_revenue

                revenue_diff = db_revenue - ref_revenue
                turnover_diff = db_turnover - ref_turnover

                print(f"{ref_store['display_order']:<5} {ref_store['store_name']:<12} {ref_revenue:<8.2f} {db_revenue:<8.2f} {revenue_diff:<8.2f} {ref_turnover:<8.2f} {db_turnover:<8.2f} {turnover_diff:<8.2f}")

                if abs(revenue_diff) > 0.01:
                    discrepancies.append(
                        f"Store {store_id}: Revenue diff {revenue_diff:.2f}")
                if abs(turnover_diff) > 0.01:
                    discrepancies.append(
                        f"Store {store_id}: Turnover diff {turnover_diff:.2f}")
            else:
                print(
                    f"{ref_store['display_order']:<5} {ref_store['store_name']:<12} {ref_revenue:<8.2f} {'MISSING':<8} {'--':<8} {ref_turnover:<8.2f} {'MISSING':<8} {'--':<8}")
                discrepancies.append(
                    f"Store {store_id}: Missing from database")

        print("-" * 80)
        total_revenue_diff = total_db_revenue - total_ref_revenue
        print(f"{'TOTAL':<18} {total_ref_revenue:<8.2f} {total_db_revenue:<8.2f} {total_revenue_diff:<8.2f}")

        print(f"\n📋 SUMMARY:")
        print(f"   Reference total: {total_ref_revenue:.2f} 万加元")
        print(f"   Database total: {total_db_revenue:.2f} 万加元")
        print(f"   Total difference: {total_revenue_diff:.2f} 万加元")

        if discrepancies:
            print(f"\n❌ Found {len(discrepancies)} discrepancies:")
            for disc in discrepancies:
                print(f"   - {disc}")
        else:
            print("\n✅ All values match!")

        return reference_stores, discrepancies

    except Exception as e:
        print(f"❌ Error comparing with database: {e}")
        import traceback
        traceback.print_exc()
        return reference_stores, ["Comparison failed"]


if __name__ == "__main__":
    # Extract reference mapping
    reference_stores, regional_turnover, regional_revenue = extract_reference_mapping()

    if reference_stores:
        # Compare with database
        reference_stores, discrepancies = compare_with_database(
            reference_stores)

        print(f"\n🎯 NEXT STEPS:")
        print("1. Update daily tracking worksheet generator to use correct store order")
        print("2. Fix any database discrepancies identified")
        print("3. Ensure generated worksheet matches reference structure exactly")
    else:
        print("❌ Failed to extract reference mapping")
