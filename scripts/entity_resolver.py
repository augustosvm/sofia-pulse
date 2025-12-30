#!/usr/bin/env python3
"""
================================================================================
ENTITY RESOLVER - Universal Entity Resolution & Deduplication
================================================================================

Extracts and resolves entities across all Sofia data sources:
  - GitHub repos → 'repository'
  - ArXiv papers → 'paper'
  - Companies in funding/NGO data → 'company'
  - Researchers/authors → 'person'
  - Technologies/frameworks → 'technology'

Matching strategies:
  1. Exact match (normalized name)
  2. Fuzzy match (Levenshtein distance)
  3. Embedding similarity (Mastra vectors)
  4. Manual verification (low confidence cases)

Usage:
  from entity_resolver import EntityResolver

  resolver = EntityResolver()

  # Extract entities from GitHub
  resolver.extract_github_repos()

  # Extract entities from ArXiv
  resolver.extract_arxiv_papers()

  # Find similar entities
  similar = resolver.find_similar('OpenAI GPT-4', entity_type='technology')

================================================================================
"""

import os
import re
from typing import Dict, List, Optional, Tuple

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()


class EntityResolver:
    """
    Universal entity resolver for Sofia Pulse.
    Extracts, normalizes, and deduplicates entities across all data sources.
    """

    def __init__(self):
        """Initialize database connection and Mastra client."""
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            user=os.getenv("POSTGRES_USER", "sofia"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB", "sofia_db"),
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Mastra endpoint for embeddings
        self.mastra_endpoint = os.getenv("MASTRA_ENDPOINT", "http://localhost:3000/api/embed")

        print("✅ EntityResolver initialized")
        print(f"   Database: {os.getenv('POSTGRES_DB', 'sofia_db')}")
        print(f"   Mastra: {self.mastra_endpoint}")

    # ========================================================================
    # CORE ENTITY RESOLUTION
    # ========================================================================

    def normalize_name(self, name: str) -> str:
        """
        Normalize entity name for fuzzy matching.

        Examples:
          "OpenAI, Inc." → "openai inc"
          "São Paulo" → "sao paulo"
          "GitHub (Microsoft)" → "github microsoft"
        """
        if not name:
            return ""

        # Convert to lowercase
        normalized = name.lower()

        # Remove accents and special characters
        normalized = re.sub(r"[àáâãäå]", "a", normalized)
        normalized = re.sub(r"[èéêë]", "e", normalized)
        normalized = re.sub(r"[ìíîï]", "i", normalized)
        normalized = re.sub(r"[òóôõö]", "o", normalized)
        normalized = re.sub(r"[ùúûü]", "u", normalized)
        normalized = re.sub(r"[ýÿ]", "y", normalized)
        normalized = re.sub(r"[ñ]", "n", normalized)
        normalized = re.sub(r"[ç]", "c", normalized)

        # Remove special characters except spaces
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)

        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def fuzzy_match(self, s1: str, s2: str, threshold: float = 0.8) -> Tuple[bool, float]:
        """
        Fuzzy match two strings using normalized Levenshtein distance.

        Returns:
          (is_match, similarity_score)

        Examples:
          fuzzy_match("OpenAI", "Open AI") → (True, 0.85)
          fuzzy_match("GitHub", "GitLab") → (False, 0.67)
        """
        norm_s1 = self.normalize_name(s1)
        norm_s2 = self.normalize_name(s2)

        if not norm_s1 or not norm_s2:
            return False, 0.0

        max_len = max(len(norm_s1), len(norm_s2))
        distance = self.levenshtein_distance(norm_s1, norm_s2)
        similarity = 1 - (distance / max_len)

        return similarity >= threshold, similarity

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding via Mastra endpoint.

        Returns:
          List of 384 floats or None if error
        """
        if not text or len(text.strip()) == 0:
            return None

        try:
            # Truncate to 512 chars for embedding
            truncated = text[:512]

            response = requests.post(self.mastra_endpoint, json={"text": truncated}, timeout=5)

            if response.status_code == 200:
                data = response.json()
                return data.get("embedding")
            else:
                print(f"⚠️ Mastra error: {response.status_code}")
                return None

        except Exception as e:
            print(f"⚠️ Embedding error: {e}")
            return None

    def find_or_create_entity(
        self,
        name: str,
        entity_type: str,
        source: str,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Find existing canonical entity or create new one.

        Args:
          name: Entity name (e.g., "OpenAI", "GPT-4", "arxiv:2301.00001")
          entity_type: One of: company, person, technology, paper, repository, etc.
          source: Data source (e.g., 'github', 'arxiv', 'crunchbase')
          description: Optional description
          aliases: Optional list of alternative names
          metadata: Optional metadata dict

        Returns:
          entity_id (UUID as string)
        """
        aliases = aliases or []
        metadata = metadata or {}

        # Use PostgreSQL function
        self.cur.execute(
            """
            SELECT sofia.find_or_create_entity(
                %s::TEXT,
                %s::sofia.entity_type,
                %s::TEXT,
                %s::TEXT,
                %s::TEXT[],
                %s::JSONB
            ) as entity_id
        """,
            (name, entity_type, source, description, aliases, metadata),
        )

        result = self.cur.fetchone()
        self.conn.commit()

        return str(result["entity_id"])

    def link_entity_to_source(
        self,
        entity_id: str,
        source_name: str,
        source_table: str,
        source_id: str,
        source_pk: Optional[int] = None,
        match_method: str = "exact",
        match_confidence: float = 1.0,
        source_name_raw: Optional[str] = None,
        source_data: Optional[Dict] = None,
    ) -> int:
        """
        Link canonical entity to source record.

        Args:
          entity_id: UUID of canonical entity
          source_name: Source system (e.g., 'github', 'arxiv')
          source_table: Table name (e.g., 'github_trending')
          source_id: ID in source system
          source_pk: Primary key in source table
          match_method: 'exact', 'fuzzy', 'embedding', 'manual'
          match_confidence: 0.0-1.0
          source_name_raw: Original name in source
          source_data: Full source record (for debugging)

        Returns:
          mapping_id
        """
        source_data = source_data or {}

        self.cur.execute(
            """
            SELECT sofia.link_entity_to_source(
                %s::UUID,
                %s::TEXT,
                %s::TEXT,
                %s::TEXT,
                %s::INTEGER,
                %s::TEXT,
                %s::FLOAT,
                %s::TEXT,
                %s::JSONB
            ) as mapping_id
        """,
            (
                entity_id,
                source_name,
                source_table,
                source_id,
                source_pk,
                match_method,
                match_confidence,
                source_name_raw,
                source_data,
            ),
        )

        result = self.cur.fetchone()
        self.conn.commit()

        return result["mapping_id"]

    def find_similar_entities(
        self, text: str, entity_type: Optional[str] = None, limit: int = 10, min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Find canonical entities similar to given text using embeddings.

        Args:
          text: Text to search for
          entity_type: Optional filter by entity type
          limit: Max results
          min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
          List of dicts with: entity_id, entity_type, canonical_name, similarity
        """
        # Generate embedding
        embedding = self.generate_embedding(text)
        if not embedding:
            return []

        # Convert to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        self.cur.execute(
            """
            SELECT * FROM sofia.find_similar_entities(
                %s::vector(384),
                %s::sofia.entity_type,
                %s::INTEGER,
                %s::FLOAT
            )
        """,
            (embedding_str, entity_type, limit, min_similarity),
        )

        return [dict(row) for row in self.cur.fetchall()]

    # ========================================================================
    # ENTITY EXTRACTION FROM SOURCES
    # ========================================================================

    def extract_github_repos(self, limit: int = 1000):
        """
        Extract GitHub repositories as canonical entities.

        Creates entities of type 'repository' and links to github_trending table.
        """
        print("\n" + "=" * 80)
        print("EXTRACTING GITHUB REPOS AS CANONICAL ENTITIES")
        print("=" * 80)

        # Fetch GitHub repos
        self.cur.execute(
            """
            SELECT id, source_id, name, full_name, description, language, stars, topics, data
            FROM sofia.github_trending
            ORDER BY stars DESC
            LIMIT %s
        """,
            (limit,),
        )

        repos = self.cur.fetchall()
        print(f"Found {len(repos)} GitHub repos")

        created = 0
        linked = 0

        for repo in repos:
            # Create canonical entity
            entity_id = self.find_or_create_entity(
                name=repo["full_name"] or repo["name"],
                entity_type="repository",
                source="github",
                description=repo.get("description"),
                aliases=[repo["name"]] if repo["name"] != repo["full_name"] else [],
                metadata={
                    "language": repo.get("language"),
                    "stars": repo.get("stars"),
                    "topics": repo.get("topics", []),
                },
            )
            created += 1

            # Link to source
            mapping_id = self.link_entity_to_source(
                entity_id=entity_id,
                source_name="github",
                source_table="github_trending",
                source_id=repo["source_id"],
                source_pk=repo["id"],
                match_method="exact",
                match_confidence=1.0,
                source_name_raw=repo["full_name"],
                source_data=repo.get("data", {}),
            )
            linked += 1

            if created % 100 == 0:
                print(f"  Processed {created} repos...")

        print(f"\n✅ GitHub extraction complete:")
        print(f"   Canonical entities created: {created}")
        print(f"   Source mappings created: {linked}")

    def extract_arxiv_papers(self, limit: int = 1000):
        """
        Extract ArXiv papers as canonical entities.

        Creates entities of type 'paper' and links to arxiv_ai_papers table.
        """
        print("\n" + "=" * 80)
        print("EXTRACTING ARXIV PAPERS AS CANONICAL ENTITIES")
        print("=" * 80)

        # Fetch ArXiv papers
        self.cur.execute(
            """
            SELECT id, arxiv_id, title, authors, abstract, categories, published
            FROM sofia.arxiv_ai_papers
            ORDER BY published DESC
            LIMIT %s
        """,
            (limit,),
        )

        papers = self.cur.fetchall()
        print(f"Found {len(papers)} ArXiv papers")

        created = 0
        linked = 0

        for paper in papers:
            # Create canonical entity for paper
            entity_id = self.find_or_create_entity(
                name=paper["title"],
                entity_type="paper",
                source="arxiv",
                description=paper.get("abstract", "")[:500],  # Truncate abstract
                aliases=[paper["arxiv_id"]],
                metadata={
                    "arxiv_id": paper["arxiv_id"],
                    "authors": paper.get("authors", []),
                    "categories": paper.get("categories", []),
                    "published": str(paper.get("published", "")),
                },
            )
            created += 1

            # Link to source
            mapping_id = self.link_entity_to_source(
                entity_id=entity_id,
                source_name="arxiv",
                source_table="arxiv_ai_papers",
                source_id=paper["arxiv_id"],
                source_pk=paper["id"],
                match_method="exact",
                match_confidence=1.0,
                source_name_raw=paper["title"],
            )
            linked += 1

            if created % 100 == 0:
                print(f"  Processed {created} papers...")

        print(f"\n✅ ArXiv extraction complete:")
        print(f"   Canonical entities created: {created}")
        print(f"   Source mappings created: {linked}")

    def extract_ngos(self, limit: int = 200):
        """
        Extract NGOs as canonical entities.

        Creates entities of type 'organization' and links to world_ngos table.
        """
        print("\n" + "=" * 80)
        print("EXTRACTING NGOS AS CANONICAL ENTITIES")
        print("=" * 80)

        # Fetch NGOs
        self.cur.execute(
            """
            SELECT id, name, sector, country, budget_usd, employees, founded, website
            FROM sofia.world_ngos
            ORDER BY budget_usd DESC NULLS LAST
            LIMIT %s
        """,
            (limit,),
        )

        ngos = self.cur.fetchall()
        print(f"Found {len(ngos)} NGOs")

        created = 0
        linked = 0

        for ngo in ngos:
            # Create canonical entity
            entity_id = self.find_or_create_entity(
                name=ngo["name"],
                entity_type="organization",
                source="world_ngos",
                description=f"{ngo.get('sector', 'Unknown')} organization in {ngo.get('country', 'Unknown')}",
                metadata={
                    "sector": ngo.get("sector"),
                    "country": ngo.get("country"),
                    "budget_usd": ngo.get("budget_usd"),
                    "employees": ngo.get("employees"),
                    "founded": ngo.get("founded"),
                    "website": ngo.get("website"),
                },
            )
            created += 1

            # Link to source
            mapping_id = self.link_entity_to_source(
                entity_id=entity_id,
                source_name="world_ngos",
                source_table="world_ngos",
                source_id=str(ngo["id"]),
                source_pk=ngo["id"],
                match_method="exact",
                match_confidence=1.0,
                source_name_raw=ngo["name"],
            )
            linked += 1

            if created % 50 == 0:
                print(f"  Processed {created} NGOs...")

        print(f"\n✅ NGO extraction complete:")
        print(f"   Canonical entities created: {created}")
        print(f"   Source mappings created: {linked}")

    def extract_all_sources(self):
        """Extract entities from all available sources."""
        print("\n" + "=" * 80)
        print("🚀 EXTRACTING ENTITIES FROM ALL SOURCES")
        print("=" * 80)

        # GitHub
        try:
            self.extract_github_repos(limit=500)
        except Exception as e:
            print(f"⚠️ GitHub extraction failed: {e}")

        # ArXiv
        try:
            self.extract_arxiv_papers(limit=500)
        except Exception as e:
            print(f"⚠️ ArXiv extraction failed: {e}")

        # NGOs
        try:
            self.extract_ngos(limit=200)
        except Exception as e:
            print(f"⚠️ NGO extraction failed: {e}")

        print("\n" + "=" * 80)
        print("✅ ALL ENTITY EXTRACTION COMPLETE")
        print("=" * 80)

    def generate_embeddings_for_entities(self, batch_size: int = 50):
        """
        Generate embeddings for canonical entities that don't have them.

        Uses Mastra to generate embeddings for name + description.
        """
        print("\n" + "=" * 80)
        print("GENERATING EMBEDDINGS FOR CANONICAL ENTITIES")
        print("=" * 80)

        # Count entities without embeddings
        self.cur.execute(
            """
            SELECT COUNT(*) as total
            FROM sofia.canonical_entities
            WHERE name_embedding IS NULL
        """
        )
        total = self.cur.fetchone()["total"]
        print(f"Found {total} entities without embeddings")

        if total == 0:
            print("✅ All entities already have embeddings")
            return

        # Process in batches
        processed = 0

        for offset in range(0, total, batch_size):
            self.cur.execute(
                """
                SELECT entity_id, canonical_name, description
                FROM sofia.canonical_entities
                WHERE name_embedding IS NULL
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """,
                (batch_size, offset),
            )

            entities = self.cur.fetchall()

            for entity in entities:
                # Generate embedding for name
                name_embedding = self.generate_embedding(entity["canonical_name"])

                # Generate embedding for description (if exists)
                desc_embedding = None
                if entity.get("description"):
                    desc_embedding = self.generate_embedding(entity["description"])

                # Update entity
                if name_embedding:
                    embedding_str = "[" + ",".join(map(str, name_embedding)) + "]"
                    desc_embedding_str = None
                    if desc_embedding:
                        desc_embedding_str = "[" + ",".join(map(str, desc_embedding)) + "]"

                    self.cur.execute(
                        """
                        UPDATE sofia.canonical_entities
                        SET name_embedding = %s::vector(384),
                            description_embedding = %s::vector(384),
                            updated_at = NOW()
                        WHERE entity_id = %s
                    """,
                        (embedding_str, desc_embedding_str, entity["entity_id"]),
                    )

                    processed += 1

            self.conn.commit()
            print(f"  Processed {processed}/{total} entities...")

        print(f"\n✅ Embedding generation complete: {processed} entities updated")

    def close(self):
        """Close database connection."""
        self.cur.close()
        self.conn.close()
        print("✅ EntityResolver closed")


# ============================================================================
# CLI
# ============================================================================


def main():
    """CLI for entity extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Sofia Entity Resolver")
    parser.add_argument("--extract-github", action="store_true", help="Extract GitHub repos")
    parser.add_argument("--extract-arxiv", action="store_true", help="Extract ArXiv papers")
    parser.add_argument("--extract-ngos", action="store_true", help="Extract NGOs")
    parser.add_argument("--extract-all", action="store_true", help="Extract from all sources")
    parser.add_argument("--generate-embeddings", action="store_true", help="Generate embeddings")
    parser.add_argument("--limit", type=int, default=1000, help="Limit per source")

    args = parser.parse_args()

    resolver = EntityResolver()

    try:
        if args.extract_github:
            resolver.extract_github_repos(limit=args.limit)

        if args.extract_arxiv:
            resolver.extract_arxiv_papers(limit=args.limit)

        if args.extract_ngos:
            resolver.extract_ngos(limit=args.limit)

        if args.extract_all:
            resolver.extract_all_sources()

        if args.generate_embeddings:
            resolver.generate_embeddings_for_entities()

        if not any(
            [args.extract_github, args.extract_arxiv, args.extract_ngos, args.extract_all, args.generate_embeddings]
        ):
            parser.print_help()

    finally:
        resolver.close()


if __name__ == "__main__":
    main()
