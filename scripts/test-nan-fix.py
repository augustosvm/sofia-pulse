#!/usr/bin/env python3
"""Test NaN handling"""

import pandas as pd
import json

file_path = "data/acled/raw/aggregated-us-canada/2026-01-15/US-and-Canada_aggregated_data_up_to-2026-01-03.xlsx"

df = pd.read_excel(file_path, nrows=5)

print("Original dtypes:")
for col in df.columns:
    print(f"  {col}: {df[col].dtype}")

print("\nOriginal first row (raw):")
print(df.iloc[0].to_dict())

# Method 1: df.where()
df1 = df.where(pd.notna(df), None)
print("\nMethod 1 (df.where) first row:")
row_dict = df1.iloc[0].to_dict()
print(row_dict)

# Try to serialize to JSON
try:
    json_str = json.dumps(row_dict)
    print("\n✅ JSON serialization SUCCESS")
except Exception as e:
    print(f"\n❌ JSON serialization FAILED: {e}")

# Method 2: fillna()
df2 = df.fillna(value=None)
print("\nMethod 2 (fillna) first row:")
row_dict2 = df2.iloc[0].to_dict()
print(row_dict2)

try:
    json_str2 = json.dumps(row_dict2)
    print("\n✅ JSON serialization SUCCESS")
except Exception as e:
    print(f"\n❌ JSON serialization FAILED: {e}")
