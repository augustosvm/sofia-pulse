#!/usr/bin/env python3
"""
Sofia Skills Kit - Test Normalization & Aggregation
Testa a camada de normalização e agregação com o domínio research.
"""

import sys
import json
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.skill_runner import run


def print_result(title, result):
    """Pretty print result."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, default=str))


def test_dry_run():
    """Test normalization in dry run mode."""
    print("\n[test] === TEST 1: Dry Run (research domain) ===")
    
    result = run("data.normalize", {
        "domain": "research",
        "mode": "full",
        "dry_run": True
    })
    
    if result["ok"]:
        print(f"✅ Dry run successful!")
        print(f"  Sources processed: {result['data']['sources_processed']}")
        print(f"  Queries generated: {len(result['data'].get('queries', []))}")
        for query in result['data'].get('queries', []):
            print(f"\n  Source: {query['source']}")
            print(f"  Query preview (first 200 chars):")
            print(f"    {query['query'][:200]}...")
    else:
        print(f"❌ Dry run failed: {result['errors']}")
    
    return result["ok"]


def test_normalize_incremental():
    """Test incremental normalization."""
    print("\n[test] === TEST 2: Incremental Normalization (research) ===")
    
    result = run("data.normalize", {
        "domain": "research",
        "mode": "incremental"
    })
    
    if result["ok"]:
        print(f"✅ Normalization successful!")
        print(f"  Domain: {result['data']['domain']}")
        print(f"  Mode: {result['data']['mode']}")
        print(f"  Total processed: {result['data']['total_processed']}")
        print(f"  Inserted: {result['data']['inserted']}")
        print(f"  Updated: {result['data']['updated']}")
        print(f"  Duration: {result['data']['duration_ms']}ms")
    else:
        print(f"❌ Normalization failed: {result['errors']}")
    
    return result["ok"]


def test_aggregate_incremental():
    """Test incremental aggregation."""
    print("\n[test] === TEST 3: Incremental Aggregation (research_monthly_summary) ===")
    
    result = run("facts.aggregate", {
        "aggregation": "research_monthly_summary",
        "mode": "incremental"
    })
    
    if result["ok"]:
        print(f"✅ Aggregation successful!")
        print(f"  Aggregation: {result['data']['aggregation']}")
        print(f"  Mode: {result['data']['mode']}")
        print(f"  Total records: {result['data']['total_records']}")
        print(f"  Grain count: {result['data']['grain_count']}")
        print(f"  Duration: {result['data']['duration_ms']}ms")
    else:
        print(f"❌ Aggregation failed: {result['errors']}")
    
    return result["ok"]


def test_normalize_source_filter():
    """Test normalization with source filter."""
    print("\n[test] === TEST 4: Normalization with Source Filter (arxiv only) ===")
    
    result = run("data.normalize", {
        "domain": "research",
        "mode": "incremental",
        "source_filter": "arxiv"
    })
    
    if result["ok"]:
        print(f"✅ Filtered normalization successful!")
        print(f"  Sources processed: {result['data']['sources_processed']}")
        print(f"  Total processed: {result['data']['total_processed']}")
        print(f"  Inserted: {result['data']['inserted']}")
    else:
        print(f"❌ Filtered normalization failed: {result['errors']}")
    
    return result["ok"]


def test_verify_data():
    """Verify normalized data in database."""
    print("\n[test] === TEST 5: Verify Data in Database ===")
    
    # Count research_papers by source
    import os
    import psycopg2
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print(f"❌ DATABASE_URL not set")
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Count by source
        cur.execute("""
            SELECT source, COUNT(*) as count
            FROM sofia.research_papers
            GROUP BY source
            ORDER BY count DESC
        """)
        
        print(f"✅ Database verification:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} papers")
        
        # Count facts
        cur.execute("SELECT COUNT(*) FROM sofia.facts_research_monthly")
        facts_count = cur.fetchone()[0]
        print(f"\n  Facts (monthly): {facts_count} records")
        
        cur.close()
        conn.close()
        
        return True
    
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False


def main():
    print("[test] Starting Normalization & Aggregation Tests")
    print("[test] Testing PASSO 7.13 implementation")
    
    results = []
    
    # Test 1: Dry run
    results.append(("Dry Run", test_dry_run()))
    
    # Test 2: Incremental normalization
    results.append(("Normalization (incremental)", test_normalize_incremental()))
    
    # Test 3: Incremental aggregation
    results.append(("Aggregation (incremental)", test_aggregate_incremental()))
    
    # Test 4: Source filter
    results.append(("Source Filter", test_normalize_source_filter()))
    
    # Test 5: Verify data
    results.append(("Database Verification", test_verify_data()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for test_name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
