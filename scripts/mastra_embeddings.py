#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
SOFIA PULSE - MASTRA EMBEDDINGS INTEGRATION
════════════════════════════════════════════════════════════════════════════════

Zero-cost embedding generation using Mastra
Automatically generates and updates embeddings for semantic tables

Features:
- Batch processing for efficiency
- Automatic NULL handling
- Progress tracking
- Error recovery
- Supports title, abstract, and description embeddings

Usage:
    python3 scripts/mastra_embeddings.py --table arxiv_ai_papers
    python3 scripts/mastra_embeddings.py --all
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import time

class MastraEmbeddings:
    """
    Integration with Mastra embedding service
    Generates 384-dimensional embeddings for semantic search
    """
    
    def __init__(self):
        # Database connection
        self.conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            user=os.getenv('POSTGRES_USER', 'sofia'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'sofia_db')
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Mastra API endpoint (update with actual endpoint)
        self.mastra_endpoint = os.getenv('MASTRA_EMBEDDING_ENDPOINT', 'http://localhost:3000/embed')
        
        # Table configuration
        self.tables_config = {
            'arxiv_ai_papers': {
                'text_columns': ['title', 'abstract'],
                'embedding_columns': ['title_embedding', 'abstract_embedding'],
                'batch_size': 50
            },
            'publications': {
                'text_columns': ['title', 'abstract'],
                'embedding_columns': ['title_embedding', 'abstract_embedding'],
                'batch_size': 50
            },
            'openalex_papers': {
                'text_columns': ['title', 'abstract'],
                'embedding_columns': ['title_embedding', 'abstract_embedding'],
                'batch_size': 50
            },
            'stackoverflow_trends': {
                'text_columns': ['tag_name'],
                'embedding_columns': ['title_embedding'],
                'batch_size': 100
            },
            'space_industry': {
                'text_columns': ['company_name', 'description'],
                'embedding_columns': ['title_embedding', 'description_embedding'],
                'batch_size': 50
            },
            'ai_regulation': {
                'text_columns': ['title', 'description'],
                'embedding_columns': ['title_embedding', 'description_embedding'],
                'batch_size': 50
            },
            'patents': {
                'text_columns': ['title', 'abstract'],
                'embedding_columns': ['title_embedding', 'abstract_embedding'],
                'batch_size': 50
            },
            'trends': {
                'text_columns': ['trend_name', 'description'],
                'embedding_columns': ['title_embedding', 'description_embedding'],
                'batch_size': 100
            },
            'world_ngos': {
                'text_columns': ['name', 'description'],
                'embedding_columns': ['title_embedding', 'description_embedding'],
                'batch_size': 50
            }
        }
    
    def generate_embedding_via_mastra(self, text: str) -> Optional[List[float]]:
        """
        Call Mastra API to generate embedding
        Returns 384-dimensional vector
        """
        if not text or len(text.strip()) == 0:
            return None
        
        try:
            # TODO: Replace with actual Mastra API call
            # For now, using a placeholder that returns a mock embedding
            # In production, this should call the real Mastra endpoint
            
            response = requests.post(
                self.mastra_endpoint,
                json={'text': text[:512]},  # Truncate to max length
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding')
            else:
                print(f"  ✗ Mastra API error: {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            # Mastra service not available - fallback to zero vector for now
            # TODO: Implement proper error handling or local embedding model
            print(f"  ⚠ Mastra service unavailable, skipping embedding")
            return None
        except Exception as e:
            print(f"  ✗ Embedding generation error: {e}")
            return None
    
    def process_table(self, table_name: str, force_update: bool = False):
        """
        Generate embeddings for all rows in a table
        """
        if table_name not in self.tables_config:
            print(f"✗ Table {table_name} not configured for embeddings")
            return
        
        config = self.tables_config[table_name]
        text_cols = config['text_columns']
        emb_cols = config['embedding_columns']
        batch_size = config['batch_size']
        
        print(f"\n{'='*80}")
        print(f"Processing: sofia.{table_name}")
        print(f"{'='*80}")
        
        # Get rows that need embeddings
        where_clause = "WHERE " + " OR ".join([
            f"{emb_col} IS NULL" for emb_col in emb_cols
        ])
        
        if force_update:
            where_clause = ""  # Process all rows
        
        # Count total rows
        self.cur.execute(f"SELECT COUNT(*) as total FROM sofia.{table_name} {where_clause}")
        total = self.cur.fetchone()['total']
        
        if total == 0:
            print(f"✓ All embeddings already generated")
            return
        
        print(f"Rows to process: {total:,}")
        print(f"Batch size: {batch_size}")
        
        # Process in batches
        processed = 0
        errors = 0
        
        for offset in range(0, total, batch_size):
            # Fetch batch
            cols_to_fetch = ['id'] + text_cols
            self.cur.execute(f"""
                SELECT {', '.join(cols_to_fetch)}
                FROM sofia.{table_name}
                {where_clause}
                ORDER BY id
                LIMIT {batch_size} OFFSET {offset}
            """)
            
            rows = self.cur.fetchall()
            
            print(f"  Batch {offset//batch_size + 1}/{(total + batch_size - 1)//batch_size}...", end=' ')
            
            batch_start = time.time()
            batch_success = 0
            
            for row in rows:
                row_id = row['id']
                
                # Generate embeddings for each text column
                for text_col, emb_col in zip(text_cols, emb_cols):
                    text = row.get(text_col)
                    
                    if text:
                        embedding = self.generate_embedding_via_mastra(text)
                        
                        if embedding:
                            # Update database
                            self.cur.execute(f"""
                                UPDATE sofia.{table_name}
                                SET {emb_col} = %s
                                WHERE id = %s
                            """, (embedding, row_id))
                            
                            batch_success += 1
                        else:
                            errors += 1
            
            self.conn.commit()
            processed += batch_success
            
            batch_time = time.time() - batch_start
            print(f"{batch_success} embeddings in {batch_time:.2f}s")
        
        print(f"\n{'='*80}")
        print(f"✓ Completed: {processed:,} embeddings generated")
        if errors > 0:
            print(f"⚠ Errors: {errors}")
        print(f"{'='*80}\n")
    
    def process_all_tables(self, force_update: bool = False):
        """
        Process all configured tables
        """
        print("\n" + "="*80)
        print("SOFIA PULSE - MASTRA EMBEDDINGS BATCH PROCESSOR")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tables: {len(self.tables_config)}")
        print(f"Force update: {force_update}")
        print("="*80)
        
        start_time = time.time()
        
        for table_name in self.tables_config.keys():
            try:
                self.process_table(table_name, force_update)
            except Exception as e:
                print(f"✗ Error processing {table_name}: {e}")
        
        total_time = time.time() - start_time
        
        print("\n" + "="*80)
        print(f"ALL TABLES PROCESSED")
        print(f"Total time: {total_time/60:.2f} minutes")
        print("="*80)
    
    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings using Mastra')
    parser.add_argument('--table', type=str, help='Process specific table')
    parser.add_argument('--all', action='store_true', help='Process all tables')
    parser.add_argument('--force', action='store_true', help='Force update existing embeddings')
    
    args = parser.parse_args()
    
    embedder = MastraEmbeddings()
    
    try:
        if args.all:
            embedder.process_all_tables(force_update=args.force)
        elif args.table:
            embedder.process_table(args.table, force_update=args.force)
        else:
            parser.print_help()
    finally:
        embedder.close()

if __name__ == '__main__':
    main()
