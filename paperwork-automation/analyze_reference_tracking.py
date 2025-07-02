#!/usr/bin/env python3
"""
Analyze the reference tracking worksheet to understand correct values
"""

import pandas as pd
import sys
from pathlib import Path


def analyze_reference_file():
    """Read and analyze the reference tracking worksheet"""

    reference_file = "data/dishes_related/跟踪表-加拿大.xlsx"

    try:
        print("🔍 ANALYZING REFERENCE TRACKING WORKSHEET")
        print("=" * 60)

        # Read Excel file - try different sheet names
        try:
            # Try reading the first sheet
            df = pd.read_excel(reference_file, sheet_name=0)
            print(f"✅ Successfully read reference file")
            print(f"   Shape: {df.shape}")
            print()
        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")
            return

        # Display the structure
        print("📋 FILE STRUCTURE:")
        print("-" * 30)
        print("Column names:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
        print()

        # Display first few rows
        print("📊 FIRST 15 ROWS:")
        print("-" * 30)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 20)

        print(df.head(15).to_string(index=True))
        print()

        # Look for store data
        print("🏪 ANALYZING STORE DATA:")
        print("-" * 30)

        # Try to identify store rows
        store_keywords = ['加拿大一店', '加拿大二店', '加拿大三店',
                          '加拿大四店', '加拿大五店', '加拿大六店', '加拿大七店']

        for idx, row in df.iterrows():
            row_str = str(row.values)
            for store in store_keywords:
                if store in row_str:
                    print(f"Found {store} at row {idx}:")
                    print(f"  {row.values}")
                    break

        # Try to identify date patterns (2025-06-28 or similar)
        print("\n📅 LOOKING FOR DATE REFERENCES:")
        print("-" * 30)

        for idx, row in df.iterrows():
            row_str = str(row.values).lower()
            if '2025' in row_str or '06-28' in row_str or '6-28' in row_str or '28' in row_str:
                print(f"Date-related content at row {idx}:")
                print(f"  {row.values}")

        # Look for revenue patterns (numbers like 3.14, 4.31, etc.)
        print("\n💰 LOOKING FOR REVENUE PATTERNS:")
        print("-" * 30)

        revenue_patterns = ['3.14', '4.31',
                            '4.40', '4.26', '4.54', '3.79', '1.59']

        for idx, row in df.iterrows():
            row_str = str(row.values)
            for pattern in revenue_patterns:
                if pattern in row_str:
                    print(f"Found revenue {pattern} at row {idx}:")
                    print(f"  {row.values}")
                    break

        return df

    except Exception as e:
        print(f"❌ Error analyzing reference file: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_worksheet_structure(df):
    """Try to understand the worksheet structure better"""

    print("\n🔍 DETAILED STRUCTURE ANALYSIS:")
    print("=" * 60)

    # Check each row for patterns
    for idx in range(min(20, len(df))):
        row = df.iloc[idx]
        row_data = []

        for val in row.values:
            if pd.isna(val):
                row_data.append("NaN")
            elif isinstance(val, (int, float)):
                row_data.append(f"{val}")
            else:
                row_data.append(str(val)[:15])  # Truncate long strings

        print(f"Row {idx:2d}: {' | '.join(row_data)}")


if __name__ == "__main__":
    df = analyze_reference_file()

    if df is not None:
        analyze_worksheet_structure(df)

        print("\n✅ Reference file analysis complete!")
        print("Use this information to understand the correct worksheet structure.")
