#!/usr/bin/env python3
"""
Inspect ACLED regional file format to understand data types
"""

import pandas as pd

file_path = "data/acled/raw/aggregated-us-canada/2026-01-15/US-and-Canada_aggregated_data_up_to-2026-01-03.xlsx"

print(f"Reading: {file_path}\n")

df = pd.read_excel(file_path, nrows=10)

print(f"Columns: {list(df.columns)}\n")
print(f"Data types:")
for col in df.columns:
    print(f"  {col}: {df[col].dtype}")

print(f"\n\nFirst 5 rows:\n")
print(df.head())

print(f"\n\nSample values for key columns:")
print(f"  year: {df['Year'].iloc[0]} (type: {type(df['Year'].iloc[0])})")
print(f"  month: {df['Month'].iloc[0]} (type: {type(df['Month'].iloc[0])})")
print(f"  week: {df['Week'].iloc[0]} (type: {type(df['Week'].iloc[0])})")
