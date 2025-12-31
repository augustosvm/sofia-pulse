#!/usr/bin/env python3
"""
JOBS INTELLIGENCE REPORT - NLP Analysis on 8,600+ Global Jobs

Analyzes:
1. Skills demand by sector/country
2. Salary gaps by region/tech
3. Remote vs On-site trends
4. Seniority demand
5. Tech stack trends
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

# ============================================================================
# TECH SKILLS PATTERNS (NLP Extraction)
# ============================================================================

TECH_SKILLS = {
    # Programming Languages
    'python': r'\b(python|django|flask|fastapi)\b',
    'javascript': r'\b(javascript|js|node\.?js|typescript|ts)\b',
    'java': r'\b(java|spring|springboot)\b',
    'go': r'\b(golang|go)\b',
    'rust': r'\b(rust|cargo)\b',
    'php': r'\b(php|laravel|symfony)\b',
    'ruby': r'\b(ruby|rails|ruby on rails)\b',
    'csharp': r'\b(c#|\.net|dotnet|asp\.net)\b',
    'cpp': r'\b(c\+\+|cpp)\b',
    'kotlin': r'\b(kotlin)\b',
    'swift': r'\b(swift|ios)\b',

    # Frontend
    'react': r'\b(react|reactjs|react\.js|next\.js|nextjs)\b',
    'vue': r'\b(vue|vuejs|vue\.js|nuxt)\b',
    'angular': r'\b(angular|angularjs)\b',
    'svelte': r'\b(svelte)\b',

    # Backend/Frameworks
    'nodejs': r'\b(node|nodejs|node\.js|express)\b',
    'spring': r'\b(spring|springboot|spring boot)\b',
    'django': r'\b(django)\b',

    # Databases
    'postgresql': r'\b(postgres|postgresql|psql)\b',
    'mysql': r'\b(mysql|mariadb)\b',
    'mongodb': r'\b(mongodb|mongo)\b',
    'redis': r'\b(redis)\b',
    'elasticsearch': r'\b(elasticsearch|elastic)\b',

    # Cloud & DevOps
    'aws': r'\b(aws|amazon web services|ec2|s3|lambda)\b',
    'azure': r'\b(azure|microsoft azure)\b',
    'gcp': r'\b(gcp|google cloud|gke)\b',
    'docker': r'\b(docker|container)\b',
    'kubernetes': r'\b(kubernetes|k8s)\b',
    'terraform': r'\b(terraform)\b',
    'jenkins': r'\b(jenkins|ci/cd)\b',

    # AI/ML
    'machine_learning': r'\b(machine learning|ml|deep learning|neural network)\b',
    'ai': r'\b(artificial intelligence|ai|llm|gpt)\b',
    'tensorflow': r'\b(tensorflow|tf)\b',
    'pytorch': r'\b(pytorch)\b',
    'data_science': r'\b(data science|data scientist|data analysis)\b',

    # Other
    'graphql': r'\b(graphql)\b',
    'rest_api': r'\b(rest|restful|api)\b',
    'git': r'\b(git|github|gitlab)\b',
}

SENIORITY_PATTERNS = {
    'junior': r'\b(junior|jr|entry level|associate)\b',
    'mid': r'\b(mid level|mid-level|intermediate|ii|iii)\b',
    'senior': r'\b(senior|sr|lead|principal|staff)\b',
    'manager': r'\b(manager|director|head of|vp|cto|cio)\b',
}

REMOTE_PATTERNS = {
    'remote': r'\b(remote|work from home|wfh|distributed)\b',
    'hybrid': r'\b(hybrid)\b',
    'onsite': r'\b(on-site|onsite|in-person|office)\b',
}

def extract_skills(text):
    """Extract tech skills from job description using regex"""
    if not text:
        return []

    text_lower = text.lower()
    skills = []

    for skill, pattern in TECH_SKILLS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            skills.append(skill)

    return skills

def extract_seniority(title, description):
    """Extract seniority level from title/description"""
    text = f"{title} {description}".lower()

    for level, pattern in SENIORITY_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return level

    return 'mid'  # default

def extract_remote_type(title, description, remote_type_field):
    """Extract remote work type"""
    if remote_type_field and remote_type_field.strip():
        return remote_type_field.lower()

    text = f"{title} {description}".lower()

    for rtype, pattern in REMOTE_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return rtype

    return 'unknown'

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_skills_by_country(conn):
    """Skills demand by country"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            c.common_name as country,
            j.title,
            j.description
        FROM sofia.jobs j
        LEFT JOIN sofia.countries c ON j.country_id = c.id
        WHERE j.country_id IS NOT NULL
            AND j.description IS NOT NULL
            AND j.posted_date >= CURRENT_DATE - INTERVAL '90 days'
    """)

    jobs = cur.fetchall()

    # Extract skills per country
    country_skills = defaultdict(Counter)

    for job in jobs:
        country = job['country']
        skills = extract_skills(job['description'])

        for skill in skills:
            country_skills[country][skill] += 1

    # Top 10 countries by job count
    top_countries = sorted(country_skills.items(), key=lambda x: sum(x[1].values()), reverse=True)[:10]

    result = []
    for country, skills in top_countries:
        top_skills = skills.most_common(10)
        result.append({
            'country': country,
            'total_jobs': sum(skills.values()),
            'top_skills': [{'skill': s, 'count': c} for s, c in top_skills]
        })

    return result

def analyze_remote_trends(conn):
    """Remote vs On-site trends"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            title,
            description,
            remote_type
        FROM sofia.jobs
        WHERE posted_date >= CURRENT_DATE - INTERVAL '90 days'
            AND description IS NOT NULL
    """)

    jobs = cur.fetchall()

    remote_counts = Counter()

    for job in jobs:
        rtype = extract_remote_type(job['title'], job['description'], job.get('remote_type'))
        remote_counts[rtype] += 1

    total = sum(remote_counts.values())

    return [{
        'type': rtype,
        'count': count,
        'percentage': (count / total * 100) if total > 0 else 0
    } for rtype, count in remote_counts.most_common()]

def analyze_seniority_demand(conn):
    """Seniority level demand"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            title,
            description,
            seniority
        FROM sofia.jobs
        WHERE posted_date >= CURRENT_DATE - INTERVAL '90 days'
            AND description IS NOT NULL
    """)

    jobs = cur.fetchall()

    seniority_counts = Counter()

    for job in jobs:
        seniority = job.get('seniority')
        if not seniority:
            seniority = extract_seniority(job['title'], job['description'])
        seniority_counts[seniority] += 1

    total = sum(seniority_counts.values())

    return [{
        'seniority': level,
        'count': count,
        'percentage': (count / total * 100) if total > 0 else 0
    } for level, count in seniority_counts.most_common()]

def analyze_tech_stack_trends(conn):
    """Tech stack trends (co-occurrence)"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            description
        FROM sofia.jobs
        WHERE posted_date >= CURRENT_DATE - INTERVAL '90 days'
            AND description IS NOT NULL
        LIMIT 5000
    """)

    jobs = cur.fetchall()

    # Find common tech stacks (skills that appear together)
    stack_combos = Counter()

    for job in jobs:
        skills = extract_skills(job['description'])

        # Count pairs
        if len(skills) >= 2:
            skills_sorted = sorted(skills)
            for i in range(len(skills_sorted)):
                for j in range(i+1, min(i+3, len(skills_sorted))):  # Max 2 pairs per skill
                    combo = f"{skills_sorted[i]} + {skills_sorted[j]}"
                    stack_combos[combo] += 1

    return [{'stack': stack, 'count': count} for stack, count in stack_combos.most_common(20)]

def analyze_salary_insights(conn):
    """Salary insights (where available)"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            c.common_name as country,
            COUNT(*) as with_salary,
            AVG((salary_min + salary_max) / 2) as avg_salary
        FROM sofia.jobs j
        LEFT JOIN sofia.countries c ON j.country_id = c.id
        WHERE salary_min IS NOT NULL
            AND salary_max IS NOT NULL
            AND posted_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY c.common_name
        HAVING COUNT(*) >= 5
        ORDER BY avg_salary DESC
        LIMIT 10
    """)

    return cur.fetchall()

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(conn):
    report = []

    report.append("=" * 80)
    report.append("JOBS INTELLIGENCE REPORT - NLP Analysis")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Analysis Period: Last 90 days")
    report.append("")

    # 1. Skills by Country
    report.append("=" * 80)
    report.append("🌍 SKILLS DEMAND BY COUNTRY")
    report.append("=" * 80)
    report.append("")

    skills_by_country = analyze_skills_by_country(conn)

    for country_data in skills_by_country[:5]:
        report.append(f"📍 {country_data['country']} ({country_data['total_jobs']} jobs):")
        report.append("")
        for skill_data in country_data['top_skills'][:5]:
            report.append(f"   {skill_data['count']:3d}x {skill_data['skill']}")
        report.append("")

    # 2. Remote Trends
    report.append("=" * 80)
    report.append("🏠 REMOTE vs ON-SITE TRENDS")
    report.append("=" * 80)
    report.append("")

    remote_trends = analyze_remote_trends(conn)

    for trend in remote_trends:
        report.append(f"• {trend['type'].upper()}: {trend['count']} jobs ({trend['percentage']:.1f}%)")
    report.append("")

    # 3. Seniority Demand
    report.append("=" * 80)
    report.append("🎓 SENIORITY LEVEL DEMAND")
    report.append("=" * 80)
    report.append("")

    seniority_data = analyze_seniority_demand(conn)

    for sen in seniority_data:
        report.append(f"• {sen['seniority'].upper()}: {sen['count']} jobs ({sen['percentage']:.1f}%)")
    report.append("")

    # 4. Tech Stack Trends
    report.append("=" * 80)
    report.append("🔥 TECH STACK TRENDS (Co-occurrence)")
    report.append("=" * 80)
    report.append("")

    stacks = analyze_tech_stack_trends(conn)

    report.append("Most common tech combinations:")
    report.append("")
    for stack in stacks[:15]:
        report.append(f"   {stack['count']:3d}x {stack['stack']}")
    report.append("")

    # 5. Salary Insights
    report.append("=" * 80)
    report.append("💰 SALARY INSIGHTS (by Country)")
    report.append("=" * 80)
    report.append("")

    salaries = analyze_salary_insights(conn)

    if salaries:
        for sal in salaries:
            report.append(f"• {sal['country']}: ${sal['avg_salary']:,.0f} avg ({sal['with_salary']} jobs with salary data)")
        report.append("")
    else:
        report.append("(Insufficient salary data in recent jobs)")
        report.append("")

    report.append("=" * 80)
    report.append("✅ Jobs Intelligence Analysis Complete!")
    report.append("")

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        print()

        report = generate_report(conn)

        # Print
        print(report)

        # Save
        with open('analytics/jobs-intelligence.txt', 'w') as f:
            f.write(report)

        print("💾 Saved to: analytics/jobs-intelligence.txt")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
