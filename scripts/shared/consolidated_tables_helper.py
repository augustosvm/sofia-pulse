"""
Consolidated Tables Helper - Python Version

Centraliza INSERTs para tabelas consolidadas:
- tech_trends (github, stackoverflow, npm, pypi)
- community_posts (hackernews, reddit, producthunt)
- patents (epo, wipo, uspto)
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


class ConsolidatedTablesHelper:
    """Helper para gerenciar INSERTs em tabelas consolidadas"""
    
    def __init__(self, conn):
        """
        Args:
            conn: Conexão psycopg2
        """
        self.conn = conn
    
    def insert_tech_trend(
        self,
        source: str,
        name: str,
        category: Optional[str] = None,
        trend_type: Optional[str] = None,
        score: Optional[float] = None,
        rank: Optional[int] = None,
        stars: Optional[int] = None,
        forks: Optional[int] = None,
        views: Optional[int] = None,
        mentions: Optional[int] = None,
        growth_rate: Optional[float] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Insert/Update tech trend"""
        
        query = """
        INSERT INTO sofia.tech_trends (
            source, name, category, trend_type,
            score, rank, stars, forks, views, mentions, growth_rate,
            period_start, period_end, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, name, period_start) DO UPDATE SET
            score = EXCLUDED.score,
            rank = EXCLUDED.rank,
            stars = EXCLUDED.stars,
            forks = EXCLUDED.forks,
            views = EXCLUDED.views,
            mentions = EXCLUDED.mentions,
            growth_rate = EXCLUDED.growth_rate,
            metadata = EXCLUDED.metadata,
            collected_at = NOW()
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (
                source, name, category, trend_type,
                score, rank, stars, forks, views, mentions, growth_rate,
                period_start, period_end,
                json.dumps(metadata) if metadata else None
            ))
        self.conn.commit()
    
    def insert_community_post(
        self,
        source: str,
        external_id: str,
        title: str,
        url: Optional[str] = None,
        content: Optional[str] = None,
        author: Optional[str] = None,
        score: Optional[int] = None,
        comments_count: Optional[int] = None,
        upvotes: Optional[int] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        posted_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Insert/Update community post"""
        
        query = """
        INSERT INTO sofia.community_posts (
            source, external_id, title, url, content,
            author, score, comments_count, upvotes,
            category, tags, posted_at, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, external_id) DO UPDATE SET
            title = EXCLUDED.title,
            score = EXCLUDED.score,
            comments_count = EXCLUDED.comments_count,
            upvotes = EXCLUDED.upvotes,
            metadata = EXCLUDED.metadata,
            collected_at = NOW()
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (
                source, external_id, title, url, content,
                author, score, comments_count, upvotes,
                category,
                json.dumps(tags) if tags else None,
                posted_at,
                json.dumps(metadata) if metadata else None
            ))
        self.conn.commit()
    
    def insert_patent(
        self,
        source: str,
        patent_number: str,
        title: Optional[str] = None,
        abstract: Optional[str] = None,
        applicant: Optional[str] = None,
        inventor: Optional[str] = None,
        ipc_classification: Optional[List[str]] = None,
        technology_field: Optional[str] = None,
        country_id: Optional[int] = None,
        applicant_country: Optional[str] = None,
        filing_date: Optional[datetime] = None,
        publication_date: Optional[datetime] = None,
        grant_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Insert/Update patent"""
        
        query = """
        INSERT INTO sofia.patents (
            source, patent_number, title, abstract,
            applicant, inventor,
            ipc_classification, technology_field,
            country_id, applicant_country,
            filing_date, publication_date, grant_date,
            metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, patent_number) DO UPDATE SET
            title = EXCLUDED.title,
            abstract = EXCLUDED.abstract,
            metadata = EXCLUDED.metadata,
            collected_at = NOW()
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (
                source, patent_number, title, abstract,
                applicant, inventor,
                ipc_classification, technology_field,
                country_id, applicant_country,
                filing_date, publication_date, grant_date,
                json.dumps(metadata) if metadata else None
            ))
        self.conn.commit()
    
    def batch_insert_tech_trends(self, trends: List[Dict[str, Any]]):
        """Batch insert tech trends"""
        for trend in trends:
            self.insert_tech_trend(**trend)
    
    def batch_insert_community_posts(self, posts: List[Dict[str, Any]]):
        """Batch insert community posts"""
        for post in posts:
            self.insert_community_post(**post)
    
    def batch_insert_patents(self, patents: List[Dict[str, Any]]):
        """Batch insert patents"""
        for patent in patents:
            self.insert_patent(**patent)
