#!/usr/bin/env python3
"""
AI Technology ArXiv Papers Collector

Tracks ArXiv paper counts by AI technology keywords over time.

Data source: ArXiv API
Storage: sofia.ai_arxiv_keywords table
"""

import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Dict, List

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.logger import setup_logger
from scripts.utils.retry import safe_request

load_dotenv()

logger = setup_logger("ai-arxiv-collector")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "sofia"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "sofia_db"),
}

# Keywords to search by technology
# Format: (keyword, tech_key, category)
ARXIV_KEYWORDS = [
    # LLMs
    ("llama language model", "llama-3", "llm"),
    ("deepseek", "deepseek", "llm"),
    ("mistral llm", "mistral", "llm"),
    ("phi-3", "phi-4", "llm"),
    ("gemma model", "gemma", "llm"),
    ("qwen", "qwen", "llm"),
    ("GPT-4", "gpt-4", "llm"),
    ("claude", "claude", "llm"),
    ("gemini", "gemini", "llm"),
    # Agent Frameworks
    ("langgraph", "langgraph", "agents"),
    ("langchain", "langchain", "agents"),
    ("autogen agent", "autogen", "agents"),
    ("multi-agent", "agents", "agents"),
    # Inference
    ("vllm", "vllm", "inference"),
    ("quantization llm", "gptq", "inference"),
    ("gguf", "gguf", "inference"),
    # RAG
    ("graphrag", "graphrag", "rag"),
    ("retrieval augmented generation", "llamaindex", "rag"),
    ("RAG", "rag-island", "rag"),
    ("ColBERT", "colbert", "rag"),
    ("vector database", "chromadb", "rag"),
    # Multimodal
    ("llava", "llava", "multimodal"),
    ("vision language model", "qwen-vl", "multimodal"),
    ("CLIP", "clip", "multimodal"),
    # Audio
    ("whisper speech", "whisper", "audio"),
    ("text-to-speech", "xtts", "audio"),
    ("voice cloning", "openvoice", "audio"),
    # Image Generation
    ("stable diffusion", "stable-diffusion", "image-gen"),
    ("FLUX diffusion", "flux", "image-gen"),
    # Safety
    ("guardrails llm", "guardrails", "safety"),
    ("RLHF", "rlhf", "safety"),
    # Fine-tuning
    ("LoRA", "peft", "framework"),
    ("QLoRA", "peft", "framework"),
]


def search_arxiv(keyword: str, year: int, month: int) -> Dict[str, Any]:
    """
    Search ArXiv for papers matching keyword in a specific month

    API: http://export.arxiv.org/api/query
    """
    # Build date range for the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Format dates for ArXiv API (YYYYMMDD)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # Build query
    # Search in title, abstract, and keywords
    # Category: cs.AI, cs.CL, cs.LG (AI, Computation and Language, Machine Learning)
    query = f"(ti:{keyword} OR abs:{keyword}) AND submittedDate:[{start_str}0000 TO {end_str}2359]"

    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "max_results": 100,
        "sortBy": "relevance",
    }

    try:
        response = safe_request(url, params=params, timeout=20)

        if response and response.status_code == 200:
            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entries = root.findall("atom:entry", ns)
            paper_count = len(entries)

            # Extract paper IDs and titles
            paper_ids = []
            paper_titles = []

            for entry in entries[:10]:  # Top 10 papers
                id_elem = entry.find("atom:id", ns)
                title_elem = entry.find("atom:title", ns)

                if id_elem is not None:
                    paper_id = id_elem.text.split("/")[-1]  # Extract arXiv ID
                    paper_ids.append(paper_id)

                if title_elem is not None:
                    title = title_elem.text.replace("\n", " ").strip()
                    paper_titles.append(title)

            return {
                "paper_count": paper_count,
                "paper_ids": paper_ids,
                "paper_titles": paper_titles,
            }
        else:
            logger.warning(f"ArXiv API returned status {response.status_code if response else 'None'}")
            return {"paper_count": 0, "paper_ids": [], "paper_titles": []}

    except Exception as e:
        logger.error(f"Failed to search ArXiv for '{keyword}': {e}")
        return {"paper_count": 0, "paper_ids": [], "paper_titles": []}


def insert_to_db(records: List[Dict[str, Any]]) -> int:
    """Insert keyword stats into database"""
    if not records:
        return 0

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        insert_query = """
            INSERT INTO sofia.ai_arxiv_keywords (
                keyword, tech_key, category,
                paper_count, year, month,
                top_paper_ids, top_paper_titles
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (keyword, year, month) DO UPDATE SET
                tech_key = EXCLUDED.tech_key,
                category = EXCLUDED.category,
                paper_count = EXCLUDED.paper_count,
                top_paper_ids = EXCLUDED.top_paper_ids,
                top_paper_titles = EXCLUDED.top_paper_titles,
                collected_at = NOW()
        """

        batch_data = [
            (
                r["keyword"],
                r["tech_key"],
                r["category"],
                r["paper_count"],
                r["year"],
                r["month"],
                r["paper_ids"],
                r["paper_titles"],
            )
            for r in records
        ]

        execute_batch(cur, insert_query, batch_data, page_size=50)
        conn.commit()

        logger.info(f"✅ Inserted {len(batch_data)} ArXiv keyword records")
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
    print("🚀 AI ARXIV KEYWORDS COLLECTOR")
    print("=" * 80)

    try:
        # Collect data for last 12 months
        now = datetime.now()
        months_to_collect = 12

        logger.info(f"📦 Collecting ArXiv papers for {len(ARXIV_KEYWORDS)} keywords x {months_to_collect} months...")

        all_records = []
        total_papers = 0

        for keyword, tech_key, category in ARXIV_KEYWORDS:
            logger.info(f"\n  🔍 Keyword: '{keyword}' ({tech_key})")

            for i in range(months_to_collect):
                # Calculate year/month
                target_date = now - timedelta(days=30 * i)
                year = target_date.year
                month = target_date.month

                logger.info(f"    📅 {year}-{month:02d}...")

                result = search_arxiv(keyword, year, month)

                if result["paper_count"] > 0:
                    all_records.append(
                        {
                            "keyword": keyword,
                            "tech_key": tech_key,
                            "category": category,
                            "paper_count": result["paper_count"],
                            "year": year,
                            "month": month,
                            "paper_ids": result["paper_ids"],
                            "paper_titles": result["paper_titles"],
                        }
                    )

                    total_papers += result["paper_count"]
                    logger.info(f"      ✅ Found {result['paper_count']} papers")
                else:
                    logger.info(f"      ⚠️  No papers found")

                # Rate limiting - ArXiv has strict limits
                time.sleep(3)

        # Insert to database
        if all_records:
            insert_to_db(all_records)

        # Summary
        print("\n" + "=" * 80)
        print("✅ AI ARXIV COLLECTION COMPLETE")
        print("=" * 80)
        print(f"📊 Total records: {len(all_records)}")
        print(f"📝 Total papers found: {total_papers}")

        # Top keywords by paper count
        if all_records:
            # Aggregate by keyword
            keyword_totals = {}
            for record in all_records:
                kw = record["keyword"]
                if kw not in keyword_totals:
                    keyword_totals[kw] = 0
                keyword_totals[kw] += record["paper_count"]

            print("\n📈 TOP 10 KEYWORDS BY TOTAL PAPERS (12 months):")
            sorted_keywords = sorted(keyword_totals.items(), key=lambda x: x[1], reverse=True)[:10]
            for i, (keyword, count) in enumerate(sorted_keywords, 1):
                print(f"  {i}. '{keyword}': {count} papers")

        print("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
