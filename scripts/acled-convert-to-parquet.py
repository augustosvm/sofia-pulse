#!/usr/bin/env python3
"""
ACLED Parquet Converter
=======================
Optional utility to convert collected XLSX files to Parquet format
with standardized column names (snake_case).

This does NOT modify values or infer new columns.
"""

import pandas as pd
from pathlib import Path
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/acled/raw")


def to_snake_case(name: str) -> str:
    """Convert column name to snake_case."""
    return name.lower().replace(' ', '_').replace('-', '_')


def convert_file_to_parquet(xlsx_path: Path) -> bool:
    """Convert a single XLSX file to Parquet."""
    try:
        logger.info(f"Converting: {xlsx_path}")
        
        # Read XLSX
        df = pd.read_excel(xlsx_path)
        
        # Standardize column names
        df.columns = [to_snake_case(col) for col in df.columns]
        
        # Create parquet path
        parquet_path = xlsx_path.with_suffix('.parquet')
        
        # Save as parquet
        df.to_parquet(parquet_path, index=False, compression='snappy')
        
        original_size = xlsx_path.stat().st_size
        parquet_size = parquet_path.stat().st_size
        reduction = (1 - parquet_size / original_size) * 100
        
        logger.info(f"✅ Saved: {parquet_path}")
        logger.info(f"   Size: {original_size:,} → {parquet_size:,} bytes ({reduction:.1f}% reduction)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to convert {xlsx_path}: {e}")
        return False


def main():
    """Convert all XLSX files to Parquet."""
    if not RAW_DIR.exists():
        logger.error(f"Raw data directory not found: {RAW_DIR}")
        return
    
    xlsx_files = list(RAW_DIR.rglob("*.xlsx"))
    
    if not xlsx_files:
        logger.warning("No XLSX files found")
        return
    
    logger.info(f"Found {len(xlsx_files)} XLSX files")
    
    success = 0
    failed = 0
    
    for xlsx_file in xlsx_files:
        if convert_file_to_parquet(xlsx_file):
            success += 1
        else:
            failed += 1
    
    logger.info(f"\nConversion complete:")
    logger.info(f"✅ Successful: {success}")
    logger.info(f"❌ Failed: {failed}")


if __name__ == "__main__":
    main()
