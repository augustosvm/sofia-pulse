#!/usr/bin/env python3
"""
Master Normalizer - Run all normalizers in sequence
"""
import subprocess
import sys
from pathlib import Path

normalizers = [
    ("ACLED", "normalize-acled-to-observations.py"),
    ("GDELT", "normalize-gdelt-to-observations.py"),
    ("World Bank", "normalize-worldbank-to-observations.py"),
    ("Brasil", "normalize-brasil-to-observations.py"),
]

print("="*70)
print("MASTER NORMALIZER - Security Hybrid Model")
print("="*70)

for name, script in normalizers:
    print(f"\n{'='*70}")
    print(f"Running: {name}")
    print(f"{'='*70}")
    
    result = subprocess.run(
        [sys.executable, f"scripts/{script}"],
        cwd=Path(__file__).parent.parent,
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"\nWARNING: {name} normalizer failed")
        print("Continuing with next normalizer...")
    else:
        print(f"\nOK: {name} normalization complete")

print("\n" + "="*70)
print("ALL NORMALIZERS COMPLETE")
print("="*70)
