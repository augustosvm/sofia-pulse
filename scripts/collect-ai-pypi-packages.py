#!/usr/bin/env python3
"""
AI Technology PyPI Packages Collector

Tracks PyPI download statistics for AI/ML packages across:
- LLMs (torch, transformers, etc.)
- Agents (langchain, autogen, etc.)
- RAG (chromadb, llama-index, etc.)
- Inference (vllm, onnxruntime, etc.)

Data source: PyPI Stats API + pypistats.org
Storage: sofia.ai_pypi_packages table
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

# Add parent to path for utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.logger import setup_logger
from scripts.utils.retry import safe_request

load_dotenv()

# Setup logger
logger = setup_logger("ai-pypi-collector")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "sofia"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "sofia_db"),
}

# PyPI package mappings to AI technologies
# Format: (package_name, tech_key, category)
PYPI_PACKAGES = [
    # Core AI Frameworks
    ("torch", "pytorch", "framework"),
    ("tensorflow", "tensorflow", "framework"),
    ("jax", "jax", "framework"),
    ("transformers", "transformers", "framework"),
    ("diffusers", "diffusers", "framework"),
    ("accelerate", "accelerate", "framework"),
    ("peft", "peft", "framework"),
    ("bitsandbytes", "bitsandbytes", "inference"),
    # LLM Libraries
    ("openai", "gpt-4", "llm"),
    ("anthropic", "claude", "llm"),
    ("google-generativeai", "gemini", "llm"),
    ("cohere", "command-r", "llm"),
    # Agent Frameworks
    ("langchain", "langchain", "agents"),
    ("langchain-core", "langchain", "agents"),
    ("langchain-community", "langchain", "agents"),
    ("langgraph", "langgraph", "agents"),
    ("autogen", "autogen", "agents"),
    ("pyautogen", "autogen", "agents"),
    ("crewai", "crewai", "agents"),
    ("pydantic-ai", "pydantic-ai", "agents"),
    ("llama-index", "llamaindex", "rag"),
    ("llama-index-core", "llamaindex", "rag"),
    ("haystack-ai", "haystack", "agents"),
    ("semantic-kernel", "semantic-kernel", "agents"),
    # Inference & Optimization
    ("vllm", "vllm", "inference"),
    ("tensorrt-llm", "tensorrt-llm", "inference"),
    ("onnxruntime", "onnxruntime", "inference"),
    ("onnxruntime-gpu", "onnxruntime", "inference"),
    ("ctransformers", "ctransformers", "inference"),
    ("auto-gptq", "gptq", "inference"),
    ("autoawq", "awq", "inference"),
    ("deepspeed", "deepspeed", "inference"),
    ("axolotl", "axolotl", "framework"),
    ("unsloth", "unsloth", "framework"),
    # RAG & Embeddings
    ("sentence-transformers", "sentence-transformers", "rag"),
    # Vector Databases
    ("chromadb", "chromadb", "rag"),
    ("pymilvus", "milvus", "rag"),
    ("pgvector", "pgvector", "rag"),
    ("lancedb", "lancedb", "rag"),
    ("qdrant-client", "qdrant", "rag"),
    ("weaviate-client", "weaviate", "rag"),
    ("pinecone-client", "pinecone", "rag"),
    ("faiss-cpu", "faiss", "rag"),
    ("faiss-gpu", "faiss", "rag"),
    # Data & Analytics
    ("duckdb", "duckdb", "data"),
    ("polars", "polars", "data"),
    ("deltalake", "delta-lake", "data"),
    # Multimodal
    ("clip", "clip", "multimodal"),
    # Audio
    ("openai-whisper", "whisper", "audio"),
    ("TTS", "xtts", "audio"),
    # Safety & Monitoring
    ("guardrails-ai", "guardrails", "safety"),
    ("nemoguardrails", "nemo-guardrails", "safety"),
    ("langfuse", "langfuse", "observability"),
    ("arize-phoenix", "phoenix", "observability"),
    # Testing
    ("ragas", "ragas", "testing"),
    # Edge
    ("mlx", "mlx", "edge"),
    ("tensorflow-lite", "tensorflow-lite", "edge"),
    ("mediapipe", "mediapipe", "edge"),
]


def get_pypi_stats(package_name: str) -> Optional[Dict[str, Any]]:
    """
    Get package statistics from PyPI

    Uses multiple sources:
    1. pypistats.org API (download stats)
    2. pypi.org JSON API (package metadata)
    """
    stats = {
        "package_name": package_name,
        "downloads_7d": 0,
        "downloads_30d": 0,
        "downloads_90d": 0,
        "version": None,
        "description": None,
        "homepage_url": None,
        "repository_url": None,
    }

    try:
        # 1. Get download stats from pypistats.org
        # Endpoint: https://pypistats.org/api/packages/{package}/recent
        stats_url = f"https://pypistats.org/api/packages/{package_name}/recent"
        response = safe_request(stats_url, timeout=10)

        if response and response.status_code == 200:
            data = response.json()
            if "data" in data:
                # pypistats returns last_day, last_week, last_month
                recent = data["data"]
                stats["downloads_7d"] = recent.get("last_week", 0)
                stats["downloads_30d"] = recent.get("last_month", 0)
                # Estimate 90d as 3x monthly (rough approximation)
                stats["downloads_90d"] = stats["downloads_30d"] * 3

        # 2. Get package metadata from PyPI JSON API
        metadata_url = f"https://pypi.org/pypi/{package_name}/json"
        response = safe_request(metadata_url, timeout=10)

        if response and response.status_code == 200:
            data = response.json()
            info = data.get("info", {})

            stats["version"] = info.get("version")
            stats["description"] = info.get("summary") or info.get("description", "")[:500]
            stats["homepage_url"] = info.get("home_page")

            # Try to extract GitHub repo URL
            project_urls = info.get("project_urls", {})
            for key in ["Repository", "Source", "Code", "GitHub"]:
                if key in project_urls:
                    stats["repository_url"] = project_urls[key]
                    break

            # Fallback to home_page if it's a GitHub URL
            if not stats["repository_url"] and stats["homepage_url"]:
                if "github.com" in stats["homepage_url"]:
                    stats["repository_url"] = stats["homepage_url"]

        logger.info(f"  ✅ {package_name}: {stats['downloads_30d']:,} downloads/month")
        return stats

    except Exception as e:
        logger.error(f"  ❌ Failed to get stats for {package_name}: {e}")
        return None


def insert_to_db(records: List[Dict[str, Any]]) -> int:
    """Insert package stats into database"""
    if not records:
        return 0

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Batch insert query
        insert_query = """
            INSERT INTO sofia.ai_pypi_packages (
                package_name, tech_key, category,
                downloads_7d, downloads_30d, downloads_90d,
                version, description, homepage_url, repository_url,
                date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
            ON CONFLICT (package_name, date) DO UPDATE SET
                tech_key = EXCLUDED.tech_key,
                category = EXCLUDED.category,
                downloads_7d = EXCLUDED.downloads_7d,
                downloads_30d = EXCLUDED.downloads_30d,
                downloads_90d = EXCLUDED.downloads_90d,
                version = EXCLUDED.version,
                description = EXCLUDED.description,
                homepage_url = EXCLUDED.homepage_url,
                repository_url = EXCLUDED.repository_url,
                collected_at = NOW()
        """

        batch_data = [
            (
                r["package_name"],
                r["tech_key"],
                r["category"],
                r["downloads_7d"],
                r["downloads_30d"],
                r["downloads_90d"],
                r["version"],
                r["description"],
                r["homepage_url"],
                r["repository_url"],
            )
            for r in records
        ]

        execute_batch(cur, insert_query, batch_data, page_size=50)
        conn.commit()

        logger.info(f"✅ Inserted {len(batch_data)} PyPI package records")
        return len(batch_data)

    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()


def main():
    print("=" * 80)
    print("🚀 AI PYPI PACKAGES COLLECTOR")
    print("=" * 80)

    try:
        logger.info(f"📦 Collecting stats for {len(PYPI_PACKAGES)} Python packages...")

        records = []
        success_count = 0
        fail_count = 0

        for package_name, tech_key, category in PYPI_PACKAGES:
            stats = get_pypi_stats(package_name)

            if stats:
                records.append(
                    {
                        "package_name": package_name,
                        "tech_key": tech_key,
                        "category": category,
                        "downloads_7d": stats["downloads_7d"],
                        "downloads_30d": stats["downloads_30d"],
                        "downloads_90d": stats["downloads_90d"],
                        "version": stats["version"],
                        "description": stats["description"],
                        "homepage_url": stats["homepage_url"],
                        "repository_url": stats["repository_url"],
                    }
                )
                success_count += 1
            else:
                fail_count += 1

            # Rate limiting - be respectful to PyPI
            time.sleep(1)

        # Insert to database
        if records:
            insert_to_db(records)

        # Summary
        print("\n" + "=" * 80)
        print("✅ AI PYPI COLLECTION COMPLETE")
        print("=" * 80)
        print(f"✅ Success: {success_count} packages")
        print(f"❌ Failed: {fail_count} packages")
        print(f"📊 Total: {len(PYPI_PACKAGES)} packages")

        # Top packages by downloads
        if records:
            print("\n📈 TOP 10 PACKAGES BY DOWNLOADS (30d):")
            sorted_records = sorted(records, key=lambda x: x["downloads_30d"], reverse=True)[:10]
            for i, record in enumerate(sorted_records, 1):
                print(f"  {i}. {record['package_name']}: {record['downloads_30d']:,} downloads/month")

        print("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
