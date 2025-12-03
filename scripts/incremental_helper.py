#!/usr/bin/env python3
"""
Incremental Import Helper for Sofia Pulse Collectors
Provides utilities for tracking collector runs and enabling incremental imports
"""

import psycopg2
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from contextlib import contextmanager

class IncrementalCollector:
    """
    Helper class for incremental data collection
    
    Usage:
        with IncrementalCollector('my-collector', conn) as tracker:
            # Your collection logic here
            for record in fetch_data():
                tracker.record_processed()
                if insert_record(record):
                    tracker.record_inserted()
                else:
                    tracker.record_updated()
    """
    
    def __init__(self, collector_name: str, conn):
        self.collector_name = collector_name
        self.conn = conn
        self.run_id = None
        self.records_processed = 0
        self.records_inserted = 0
        self.records_updated = 0
        self.last_run_time = None
        
    def __enter__(self):
        """Start tracking a collector run"""
        cursor = self.conn.cursor()
        try:
            # Get last successful run time
            cursor.execute(
                "SELECT sofia.get_last_successful_run(%s)",
                (self.collector_name,)
            )
            result = cursor.fetchone()
            self.last_run_time = result[0] if result else None
            
            # Start new run
            cursor.execute(
                "SELECT sofia.start_collector_run(%s)",
                (self.collector_name,)
            )
            self.run_id = cursor.fetchone()[0]
            self.conn.commit()
            
            print(f"✅ Started collector run #{self.run_id}")
            if self.last_run_time:
                print(f"📅 Last successful run: {self.last_run_time}")
            else:
                print(f"📅 First run (no previous data)")
                
        finally:
            cursor.close()
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete tracking a collector run"""
        cursor = self.conn.cursor()
        try:
            status = 'success' if exc_type is None else 'failed'
            error_msg = str(exc_val) if exc_val else None
            
            cursor.execute("""
                SELECT sofia.complete_collector_run(%s, %s, %s, %s, %s, %s)
            """, (
                self.run_id,
                status,
                self.records_processed,
                self.records_inserted,
                self.records_updated,
                error_msg
            ))
            self.conn.commit()
            
            print(f"\n{'✅' if status == 'success' else '❌'} Collector run #{self.run_id} {status}")
            print(f"   Processed: {self.records_processed}")
            print(f"   Inserted: {self.records_inserted}")
            print(f"   Updated: {self.records_updated}")
            
        finally:
            cursor.close()
            
        return False  # Don't suppress exceptions
        
    def record_processed(self, count: int = 1):
        """Increment processed record counter"""
        self.records_processed += count
        
    def record_inserted(self, count: int = 1):
        """Increment inserted record counter"""
        self.records_inserted += count
        
    def record_updated(self, count: int = 1):
        """Increment updated record counter"""
        self.records_updated += count
        
    def should_fetch_year(self, year: int, max_age_days: int = 365) -> bool:
        """
        Check if data for a given year should be fetched
        
        Args:
            year: The year to check
            max_age_days: Maximum age in days before refetching (default: 365)
            
        Returns:
            True if data should be fetched, False to skip
        """
        # Always fetch current and previous year
        current_year = datetime.now(timezone.utc).year
        if year >= current_year - 1:
            return True
            
        # If no last run, fetch everything
        if not self.last_run_time:
            return True
            
        # Check if data is older than max_age_days
        age = datetime.now(timezone.utc) - self.last_run_time
        if age.days > max_age_days:
            return True
            
        # Skip old years that were recently fetched
        return False

def get_years_to_fetch(
    start_year: int,
    end_year: int,
    last_run: Optional[datetime] = None,
    max_age_days: int = 365
) -> list:
    """
    Get list of years that should be fetched based on last run time
    
    Args:
        start_year: Earliest year to consider
        end_year: Latest year to consider  
        last_run: Timestamp of last successful run
        max_age_days: How many days before refetching old data
        
    Returns:
        List of years to fetch
    """
    current_year = datetime.now(timezone.utc).year
    years_to_fetch = []
    
    for year in range(start_year, end_year + 1):
        # Always fetch recent years (current + previous)
        if year >= current_year - 1:
            years_to_fetch.append(year)
            continue
            
        # If no last run, fetch all years
        if not last_run:
            years_to_fetch.append(year)
            continue
            
        # Check if data is too old and needs refresh
        age = datetime.now(timezone.utc) - last_run
        if age.days > max_age_days:
            years_to_fetch.append(year)
            
    return years_to_fetch

# Example usage
if __name__ == '__main__':
    import os
    
    # Example connection
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        database=os.getenv('POSTGRES_DB', 'sofia_db'),
        user=os.getenv('POSTGRES_USER', 'sofia'),
        password=os.getenv('POSTGRES_PASSWORD', '')
    )
    
    # Example collector
    with IncrementalCollector('example-collector', conn) as tracker:
        # Simulate processing 100 records
        for i in range(100):
            tracker.record_processed()
            if i % 3 == 0:
                tracker.record_inserted()
            else:
                tracker.record_updated()
                
    conn.close()
