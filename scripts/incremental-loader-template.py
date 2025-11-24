#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
SOFIA PULSE - INCREMENTAL LOADER TEMPLATE
════════════════════════════════════════════════════════════════════════════════

Template for creating incremental data collectors
Supports: GitHub, Hacker News, Reddit, NPM, PyPI, GDELT

Features:
- Automatic deduplication (source_id + collected_at)
- Incremental updates (only new data since last run)
- Progress tracking with collector_runs table
- Error recovery
- Idempotent operations
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
import time
import hashlib

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.incremental_helper import IncrementalCollector

class IncrementalLoader:
    """
    Base class for incremental data loading
    Extend this for specific sources (GitHub, HN, Reddit, etc.)
    """
    
    def __init__(self, source_name: str, table_name: str):
        self.source_name = source_name
        self.table_name = table_name
        
        # Database connection
        self.conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            user=os.getenv('POSTGRES_USER', 'sofia'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'sofia_db')
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        self.records_processed = 0
        self.records_inserted = 0
        self.records_updated = 0
    
    def get_last_collected_time(self) -> Optional[datetime]:
        """Get timestamp of last successful collection"""
        self.cur.execute(f"""
            SELECT MAX(collected_at) as last_time
            FROM sofia.{self.table_name}
        """)
        result = self.cur.fetchone()
        return result['last_time'] if result else None
    
    def generate_record_hash(self, record: Dict) -> str:
        """Generate unique hash for deduplication"""
        # Customize this based on your data structure
        key_data = f"{record.get('source_id', '')}_{record.get('title', '')}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def fetch_new_data(self, since: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch new data from source API
        Override this method in subclasses
        """
        raise NotImplementedError("Subclasses must implement fetch_new_data()")
    
    def transform_record(self, raw_record: Dict) -> Dict:
        """
        Transform raw API data to database schema
        Override this method in subclasses
        """
        raise NotImplementedError("Subclasses must implement transform_record()")
    
    def upsert_records(self, records: List[Dict]):
        """Insert or update records with deduplication"""
        if not records:
            return
        
        # Customize columns based on your schema
        columns = records[0].keys()
        
        query = f"""
            INSERT INTO sofia.{self.table_name} ({', '.join(columns)})
            VALUES %s
            ON CONFLICT (source_id, collected_at) 
            DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                data = EXCLUDED.data
        """
        
        values = [[r[col] for col in columns] for r in records]
        execute_values(self.cur, query, values)
        self.conn.commit()
    
    def run(self):
        """Main collection loop"""
        print(f"\n{'='*80}")
        print(f"{self.source_name.upper()} - INCREMENTAL COLLECTOR")
        print(f"{'='*80}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Table: sofia.{self.table_name}")
        
        # Get last collection time
        last_time = self.get_last_collected_time()
        if last_time:
            print(f"Last collection: {last_time}")
        else:
            print(f"First run - collecting all available data")
        
        # Use incremental helper for tracking
        with IncrementalCollector(self.source_name, self.conn) as collector:
            try:
                # Fetch new data
                print(f"\nFetching new data...")
                raw_data = self.fetch_new_data(since=last_time)
                
                if not raw_data:
                    print(f"✓ No new data available")
                    collector.records_processed = 0
                    return
                
                print(f"Fetched: {len(raw_data)} records")
                
                # Transform and insert
                print(f"Transforming and inserting...")
                batch_size = 100
                
                for i in range(0, len(raw_data), batch_size):
                    batch = raw_data[i:i+batch_size]
                    transformed = [self.transform_record(r) for r in batch]
                    
                    self.upsert_records(transformed)
                    
                    self.records_processed += len(batch)
                    print(f"  Processed: {self.records_processed}/{len(raw_data)}", end='\r')
                
                print(f"\n\n{'='*80}")
                print(f"✓ COLLECTION COMPLETE")
                print(f"  Processed: {self.records_processed}")
                print(f"  Table: sofia.{self.table_name}")
                print(f"{'='*80}\n")
                
                # Update collector stats
                collector.records_processed = self.records_processed
                collector.records_inserted = self.records_inserted
                collector.records_updated = self.records_updated
                
            except Exception as e:
                print(f"\n✗ Error: {e}")
                raise
    
    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


# ============================================================================
# GITHUB TRENDING COLLECTOR
# ============================================================================

class GitHubTrendingLoader(IncrementalLoader):
    """Collect GitHub trending repositories"""
    
    def __init__(self):
        super().__init__('github_trending', 'github_trending')
        self.api_url = 'https://api.github.com/search/repositories'
        self.headers = {
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'Sofia-Pulse-Collector'
        }
        
        # Add token if available
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            self.headers['Authorization'] = f'Bearer {github_token}'
    
    def fetch_new_data(self, since: Optional[datetime] = None) -> List[Dict]:
        """Fetch trending repos from GitHub"""
        # Query for repos created/updated recently
        if since:
            date_str = since.strftime('%Y-%m-%d')
            query = f'pushed:>{date_str} stars:>100'
        else:
            query = 'stars:>1000'  # First run: get top repos
        
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': 100
        }
        
        try:
            response = requests.get(self.api_url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('items', [])
            
        except Exception as e:
            print(f"  ✗ GitHub API error: {e}")
            return []
    
    def transform_record(self, raw_record: Dict) -> Dict:
        """Transform GitHub API response to database schema"""
        return {
            'source_id': str(raw_record['id']),
            'name': raw_record['name'],
            'full_name': raw_record['full_name'],
            'description': raw_record.get('description', ''),
            'language': raw_record.get('language', ''),
            'stars': raw_record['stargazers_count'],
            'forks': raw_record['forks_count'],
            'watchers': raw_record['watchers_count'],
            'topics': raw_record.get('topics', []),
            'created_at_source': raw_record['created_at'],
            'updated_at_source': raw_record['updated_at'],
            'collected_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'data': raw_record  # Store full response as JSONB
        }


# ============================================================================
# HACKER NEWS COLLECTOR
# ============================================================================

class HackerNewsLoader(IncrementalLoader):
    """Collect Hacker News top stories"""
    
    def __init__(self):
        super().__init__('hacker_news', 'hacker_news_stories')
        self.api_url = 'https://hacker-news.firebaseio.com/v0'
    
    def fetch_new_data(self, since: Optional[datetime] = None) -> List[Dict]:
        """Fetch top stories from HN"""
        try:
            # Get top story IDs
            response = requests.get(f"{self.api_url}/topstories.json", timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:100]  # Top 100
            
            # Fetch each story
            stories = []
            for story_id in story_ids:
                try:
                    resp = requests.get(f"{self.api_url}/item/{story_id}.json", timeout=5)
                    if resp.status_code == 200:
                        stories.append(resp.json())
                    time.sleep(0.1)  # Rate limiting
                except:
                    continue
            
            return stories
            
        except Exception as e:
            print(f"  ✗ HN API error: {e}")
            return []
    
    def transform_record(self, raw_record: Dict) -> Dict:
        """Transform HN API response to database schema"""
        return {
            'source_id': str(raw_record['id']),
            'title': raw_record.get('title', ''),
            'url': raw_record.get('url', ''),
            'score': raw_record.get('score', 0),
            'by_user': raw_record.get('by', ''),
            'descendants': raw_record.get('descendants', 0),
            'created_at_source': datetime.fromtimestamp(raw_record['time'], tz=timezone.utc),
            'collected_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'data': raw_record
        }


# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Incremental data collector')
    parser.add_argument('source', choices=['github', 'hn', 'reddit', 'npm', 'pypi', 'gdelt'],
                       help='Data source to collect')
    
    args = parser.parse_args()
    
    loaders = {
        'github': GitHubTrendingLoader,
        'hn': HackerNewsLoader,
        # Add more as needed
    }
    
    if args.source in loaders:
        loader = loaders[args.source]()
        try:
            loader.run()
        finally:
            loader.close()
    else:
        print(f"✗ Loader for {args.source} not implemented yet")

if __name__ == '__main__':
    main()
