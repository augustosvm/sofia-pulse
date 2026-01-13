#!/usr/bin/env python3
"""
CATHO JOBS INTELLIGENCE REPORT - NLP Analysis on 1,400+ Brazilian Jobs

Analyzes Catho.com.br data:
1. Skills demand by city/state
2. Salary insights
3. Remote vs On-site trends
4. Seniority demand
5. Tech stack trends
6. Regional patterns (Brazilian states)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

def get_catho_jobs():
    """Get all Catho jobs from last 90 days"""
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Connected to database")

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    j.*,
                    c.name as city_name,
                    s.name as state_name,
                    s.code as state_code
                FROM sofia.jobs j
                LEFT JOIN sofia.cities c ON j.city_id = c.id
                LEFT JOIN sofia.states s ON j.state_id = s.id
                WHERE j.platform = 'catho'
                  AND j.collected_at >= NOW() - INTERVAL '90 days'
                ORDER BY j.collected_at DESC
            """)
            jobs = cursor.fetchall()
            print(f"📊 Loaded {len(jobs)} Catho jobs from last 90 days\n")
            return jobs
    finally:
        conn.close()

def analyze_skills_by_location(jobs):
    """Analyze skills demand by state"""
    print("="*80)
    print("🗺️  SKILLS DEMAND BY BRAZILIAN STATE")
    print("="*80)
    print()

    state_skills = defaultdict(lambda: defaultdict(int))
    state_totals = defaultdict(int)

    for job in jobs:
        state = job.get('state_name') or job.get('state') or 'Unknown'
        state_totals[state] += 1

        if job.get('skills_required'):
            for skill in job['skills_required']:
                state_skills[state][skill.lower()] += 1

    # Sort by total jobs
    top_states = sorted(state_totals.items(), key=lambda x: x[1], reverse=True)[:10]

    for state, total in top_states:
        print(f"📍 {state} ({total} jobs):\n")

        skills = state_skills[state]
        if skills:
            top_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:5]
            for skill, count in top_skills:
                print(f"    {count:3d}x {skill}")
        else:
            print("    (No skills data)")
        print()

def analyze_remote_trends(jobs):
    """Analyze remote work trends"""
    print("="*80)
    print("🏠 REMOTE vs ON-SITE TRENDS")
    print("="*80)
    print()

    remote_counts = Counter()
    for job in jobs:
        remote_type = job.get('remote_type') or 'unknown'
        remote_counts[remote_type.upper()] += 1

    total = sum(remote_counts.values())
    for remote_type, count in sorted(remote_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total * 100) if total > 0 else 0
        print(f"• {remote_type}: {count} jobs ({pct:.1f}%)")
    print()

def analyze_seniority(jobs):
    """Analyze seniority level demand"""
    print("="*80)
    print("🎓 SENIORITY LEVEL DEMAND")
    print("="*80)
    print()

    seniority_counts = Counter()
    for job in jobs:
        seniority = job.get('seniority_level') or 'unknown'
        seniority_counts[seniority.upper()] += 1

    total = sum(seniority_counts.values())
    for seniority, count in sorted(seniority_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total * 100) if total > 0 else 0
        print(f"• {seniority}: {count} jobs ({pct:.1f}%)")
    print()

def analyze_tech_stack(jobs):
    """Analyze tech stack co-occurrence"""
    print("="*80)
    print("🔥 TECH STACK TRENDS (Co-occurrence)")
    print("="*80)
    print()

    # Track skill pairs
    skill_pairs = Counter()

    for job in jobs:
        if job.get('skills_required'):
            skills = [s.lower() for s in job['skills_required']]
            # Generate all pairs
            for i, skill1 in enumerate(skills):
                for skill2 in skills[i+1:]:
                    pair = tuple(sorted([skill1, skill2]))
                    skill_pairs[pair] += 1

    print("Most common tech combinations:\n")
    for (skill1, skill2), count in skill_pairs.most_common(15):
        print(f"    {count:3d}x {skill1} + {skill2}")
    print()

def analyze_salary(jobs):
    """Analyze salary by state"""
    print("="*80)
    print("💰 SALARY INSIGHTS (by State)")
    print("="*80)
    print()

    state_salaries = defaultdict(list)

    for job in jobs:
        if job.get('salary_min'):
            state = job.get('state_name') or job.get('state') or 'Unknown'
            # Convert to USD (assuming BRL, using ~5:1 ratio)
            salary_min = float(job['salary_min'])
            salary_usd = salary_min / 5.0 if job.get('salary_currency') == 'BRL' else salary_min
            state_salaries[state].append(salary_usd)

    if not state_salaries:
        print("(No salary data available)")
        print()
        return

    # Calculate averages
    state_avgs = []
    for state, salaries in state_salaries.items():
        if len(salaries) >= 3:  # At least 3 jobs
            avg = sum(salaries) / len(salaries)
            state_avgs.append((state, avg, len(salaries)))

    # Sort by average salary
    state_avgs.sort(key=lambda x: x[1], reverse=True)

    for state, avg, count in state_avgs[:15]:
        print(f"• {state}: ${avg:,.0f} avg ({count} jobs with salary data)")
    print()

def analyze_cities(jobs):
    """Analyze top cities with tech jobs"""
    print("="*80)
    print("🏙️  TOP CITIES FOR TECH JOBS")
    print("="*80)
    print()

    city_counts = Counter()
    for job in jobs:
        city = job.get('city_name') or job.get('city') or 'Unknown'
        if city != 'Unknown':
            city_counts[city] += 1

    print("Top 20 cities:\n")
    for city, count in city_counts.most_common(20):
        print(f"    {count:3d}x {city}")
    print()

def analyze_top_skills(jobs):
    """Analyze overall top skills"""
    print("="*80)
    print("🔥 TOP 30 SKILLS IN DEMAND")
    print("="*80)
    print()

    skill_counts = Counter()
    for job in jobs:
        if job.get('skills_required'):
            for skill in job['skills_required']:
                skill_counts[skill.lower()] += 1

    for skill, count in skill_counts.most_common(30):
        print(f"    {count:3d}x {skill}")
    print()

def analyze_sectors(jobs):
    """Analyze job sectors"""
    print("="*80)
    print("📊 TECH SECTORS")
    print("="*80)
    print()

    sector_counts = Counter()
    for job in jobs:
        sector = job.get('sector') or 'Unknown'
        sector_counts[sector] += 1

    for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(jobs) * 100) if len(jobs) > 0 else 0
        print(f"• {sector}: {count} jobs ({pct:.1f}%)")
    print()

def main():
    import sys
    from io import StringIO

    # Capture output
    output = StringIO()
    sys.stdout = output

    print()
    print("="*80)
    print("CATHO JOBS INTELLIGENCE REPORT - NLP Analysis")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Analysis Period: Last 90 days")
    print("Platform: Catho.com.br (Brazilian jobs)")
    print()

    # Get jobs
    jobs = get_catho_jobs()

    if not jobs:
        print("❌ No Catho jobs found")
        sys.stdout = sys.__stdout__
        print(output.getvalue())
        return

    # Run analyses
    analyze_top_skills(jobs)
    analyze_skills_by_location(jobs)
    analyze_cities(jobs)
    analyze_remote_trends(jobs)
    analyze_seniority(jobs)
    analyze_sectors(jobs)
    analyze_tech_stack(jobs)
    analyze_salary(jobs)

    print("="*80)
    print("✅ Catho Jobs Intelligence Analysis Complete!")
    print()

    # Get output
    report_content = output.getvalue()
    sys.stdout = sys.__stdout__

    # Print to console
    print(report_content)

    # Save to file
    output_path = 'analytics/catho-jobs-intelligence.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"💾 Saved to: {output_path}")
    print()

if __name__ == "__main__":
    main()
