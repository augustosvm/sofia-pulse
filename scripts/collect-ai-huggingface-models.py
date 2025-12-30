#!/usr/bin/env python3
"""
AI Technology HuggingFace Models Collector

Tracks HuggingFace model downloads, likes, and popularity for AI technologies.

Data source: HuggingFace Hub API
Storage: sofia.ai_huggingface_models table
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.logger import setup_logger
from scripts.utils.retry import safe_request

load_dotenv()

logger = setup_logger("ai-huggingface-collector")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "sofia"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "sofia_db"),
}

# HuggingFace API token (optional, but recommended for higher rate limits)
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Model searches by technology
# Format: (search_query, tech_key, category)
MODEL_SEARCHES = [
    # LLMs
    ("meta-llama/Llama", "llama-3", "llm"),
    ("deepseek", "deepseek", "llm"),
    ("mistralai", "mistral", "llm"),
    ("microsoft/phi", "phi-4", "llm"),
    ("google/gemma", "gemma", "llm"),
    ("Qwen/Qwen", "qwen", "llm"),
    # Image Generation
    ("stabilityai/stable-diffusion", "stable-diffusion", "image-gen"),
    ("black-forest-labs/FLUX", "flux", "image-gen"),
    # Multimodal
    ("liuhaotian/llava", "llava", "multimodal"),
    ("Qwen/Qwen2-VL", "qwen-vl", "multimodal"),
    ("deepseek-ai/deepseek-vl", "deepseek-vl", "multimodal"),
    ("openai/clip", "clip", "multimodal"),
    # Audio
    ("openai/whisper", "whisper", "audio"),
    ("suno/bark", "bark", "audio"),
    ("myshell-ai/OpenVoice", "openvoice", "audio"),
    # Embeddings
    ("sentence-transformers", "sentence-transformers", "rag"),
    ("BAAI/bge", "bge", "rag"),
]


def search_huggingface_models(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search HuggingFace models API

    API Docs: https://huggingface.co/docs/hub/api
    """
    url = "https://huggingface.co/api/models"
    params = {
        "search": query,
        "sort": "downloads",
        "direction": -1,
        "limit": limit,
    }

    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    try:
        response = safe_request(url, params=params, headers=headers, timeout=15)

        if response and response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"HF API returned status {response.status_code if response else 'None'}")
            return []

    except Exception as e:
        logger.error(f"Failed to search HF for '{query}': {e}")
        return []


def get_model_details(model_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific model"""
    url = f"https://huggingface.co/api/models/{model_id}"

    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    try:
        response = safe_request(url, headers=headers, timeout=15)

        if response and response.status_code == 200:
            return response.json()
        return None

    except Exception as e:
        logger.error(f"Failed to get details for {model_id}: {e}")
        return None


def extract_model_data(model: Dict[str, Any], tech_key: str, category: str) -> Dict[str, Any]:
    """Extract relevant data from HuggingFace model object"""

    # Extract parameters size (e.g., "7B", "70B")
    model_id = model.get("id", "")
    parameters = None

    # Try to extract from model ID (e.g., "llama-3-70B")
    for size in ["1B", "3B", "7B", "8B", "13B", "14B", "30B", "34B", "70B", "72B", "405B"]:
        if size.lower() in model_id.lower():
            parameters = size
            break

    # Extract tags
    tags = model.get("tags", [])

    return {
        "model_id": model_id,
        "tech_key": tech_key,
        "category": category,
        "likes": model.get("likes", 0),
        "downloads_30d": model.get("downloads", 0),  # Note: HF API doesn't provide exact 30d downloads
        "downloads_total": model.get("downloads", 0),
        "model_type": tags[0] if tags else None,
        "pipeline_tag": model.get("pipeline_tag"),
        "library_name": model.get("library_name"),
        "description": model.get("description", "")[:500] if model.get("description") else None,
        "author": model.get("author"),
        "created_at_source": model.get("createdAt"),
        "last_modified": model.get("lastModified"),
        "parameters": parameters,
        "tags": tags,
    }


def insert_to_db(records: List[Dict[str, Any]]) -> int:
    """Insert model data into database"""
    if not records:
        return 0

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        insert_query = """
            INSERT INTO sofia.ai_huggingface_models (
                model_id, tech_key, category,
                downloads_30d, downloads_total, likes,
                model_type, pipeline_tag, library_name,
                description, author, created_at_source, last_modified,
                parameters, tags,
                date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
            ON CONFLICT (model_id, date) DO UPDATE SET
                tech_key = EXCLUDED.tech_key,
                category = EXCLUDED.category,
                downloads_30d = EXCLUDED.downloads_30d,
                downloads_total = EXCLUDED.downloads_total,
                likes = EXCLUDED.likes,
                model_type = EXCLUDED.model_type,
                pipeline_tag = EXCLUDED.pipeline_tag,
                library_name = EXCLUDED.library_name,
                description = EXCLUDED.description,
                author = EXCLUDED.author,
                last_modified = EXCLUDED.last_modified,
                parameters = EXCLUDED.parameters,
                tags = EXCLUDED.tags,
                collected_at = NOW()
        """

        batch_data = [
            (
                r["model_id"],
                r["tech_key"],
                r["category"],
                r["downloads_30d"],
                r["downloads_total"],
                r["likes"],
                r["model_type"],
                r["pipeline_tag"],
                r["library_name"],
                r["description"],
                r["author"],
                r["created_at_source"],
                r["last_modified"],
                r["parameters"],
                r["tags"],
            )
            for r in records
        ]

        execute_batch(cur, insert_query, batch_data, page_size=50)
        conn.commit()

        logger.info(f"✅ Inserted {len(batch_data)} HuggingFace model records")
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
    print("🚀 AI HUGGINGFACE MODELS COLLECTOR")
    print("=" * 80)

    try:
        if not HF_TOKEN:
            logger.warning("⚠️  No HF_TOKEN found - API will have lower rate limits")

        logger.info(f"📦 Searching {len(MODEL_SEARCHES)} model categories...")

        all_models = []
        total_found = 0

        for query, tech_key, category in MODEL_SEARCHES:
            logger.info(f"\n  🔍 Searching: {query} ({tech_key})")

            models = search_huggingface_models(query, limit=10)

            if models:
                logger.info(f"    ✅ Found {len(models)} models")

                for model in models:
                    model_data = extract_model_data(model, tech_key, category)
                    all_models.append(model_data)
                    total_found += 1

                    logger.info(
                        f"      • {model_data['model_id']}: {model_data['likes']} likes, {model_data['downloads_total']:,} downloads"
                    )
            else:
                logger.warning(f"    ⚠️  No models found for {query}")

            # Rate limiting
            time.sleep(1)

        # Insert to database
        if all_models:
            insert_to_db(all_models)

        # Summary
        print("\n" + "=" * 80)
        print("✅ AI HUGGINGFACE COLLECTION COMPLETE")
        print("=" * 80)
        print(f"📊 Total models collected: {total_found}")
        print(f"✅ Inserted into database: {len(all_models)}")

        # Top models by likes
        if all_models:
            print("\n⭐ TOP 10 MODELS BY LIKES:")
            sorted_models = sorted(all_models, key=lambda x: x["likes"], reverse=True)[:10]
            for i, model in enumerate(sorted_models, 1):
                print(f"  {i}. {model['model_id']}: {model['likes']:,} likes")

        print("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
