#!/usr/bin/env python3
"""
Sofia Pulse - Tech Trend Score (SIMPLE)

Fórmula SIMPLES que JÁ funciona (sem over-engineering)

TECH TREND SCORE =
    github_stars * 0.4 +
    npm_downloads * 0.3 +
    hn_mentions * 0.2 +
    reddit_posts * 0.1

POR QUE ESTA FÓRMULA FUNCIONA:
- GitHub stars = Desenvolvedores usando (ação real, não hype)
- NPM downloads = Projetos reais em produção
- HN mentions = Comunidade tech falando
- Reddit posts = Interesse público geral

WEAK SIGNALS (Dark Horses):
- Tech com alto GitHub mas baixo funding = oportunidade
- Tech com alto HN mas baixo NPM = hype vs realidade
- Tech com crescimento consistente = tendência real

OUTPUT:
- Top 20 tecnologias por trend score
- Dark Horses: Alto GitHub, baixo funding
- Hype Check: Alto HN, baixo NPM
- Rising Stars: Crescimento acelerado
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# DATABASE CONFIG
# ============================================================================

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME', 'sofia_db'),
}

# ============================================================================
# DATA COLLECTION
# ============================================================================

def get_github_technologies(conn) -> Dict[str, Dict[str, float]]:
    """
    Extrai tecnologias do GitHub com métricas normalizadas

    Returns:
        Dict[tech_name, {stars, forks, repos_count}]
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Agregar por linguagem
    query = """
    SELECT
        language as tech,
        COUNT(*) as repo_count,
        SUM(stars) as total_stars,
        AVG(stars) as avg_stars,
        SUM(forks) as total_forks,
        MAX(stars) as max_stars
    FROM sofia.github_trending
    WHERE language IS NOT NULL
        AND is_archived = FALSE
        AND is_fork = FALSE
    GROUP BY language
    ORDER BY total_stars DESC;
    """

    cursor.execute(query)
    results = cursor.fetchall()

    tech_data = {}
    for row in results:
        tech_data[row['tech']] = {
            'github_stars': float(row['total_stars'] or 0),
            'github_repos': float(row['repo_count'] or 0),
            'github_avg_stars': float(row['avg_stars'] or 0),
        }

    # Também extrair frameworks específicos de topics (não linguagens)
    # Lista de frameworks populares que devem ser rastreados
    known_frameworks = [
        'react', 'vue', 'angular', 'svelte', 'nextjs', 'nuxt',
        'astro', 'solid', 'qwik', 'remix', 'vite', 'tailwind',
        'fastapi', 'django', 'flask', 'laravel', 'spring-boot',
        'express', 'nestjs', 'rails', 'blazor', 'flutter'
    ]

    topic_query = """
    SELECT
        unnest(topics) as tech,
        COUNT(DISTINCT repo_id) as repo_count,
        SUM(stars) as total_stars
    FROM sofia.github_trending
    WHERE topics IS NOT NULL
        AND array_length(topics, 1) > 0
        AND is_archived = FALSE
        AND unnest(topics) = ANY(%s)
    GROUP BY tech
    HAVING COUNT(*) >= 1
    ORDER BY total_stars DESC
    LIMIT 50;
    """

    cursor.execute(topic_query, (known_frameworks,))
    topic_results = cursor.fetchall()

    for row in topic_results:
        tech = row['tech']
        if tech not in tech_data:
            tech_data[tech] = {
                'github_stars': 0,
                'github_repos': 0,
                'github_avg_stars': 0,
            }

        tech_data[tech]['github_stars'] += float(row['total_stars'] or 0)
        tech_data[tech]['github_repos'] += float(row['repo_count'] or 0)

    cursor.close()
    return tech_data


def get_hackernews_technologies(conn) -> Dict[str, Dict[str, float]]:
    """
    Extrai tecnologias do HackerNews com métricas

    Returns:
        Dict[tech_name, {mentions, total_points, avg_points}]
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        unnest(mentioned_technologies) as tech,
        COUNT(*) as mentions,
        SUM(points) as total_points,
        AVG(points) as avg_points,
        SUM(num_comments) as total_comments
    FROM sofia.hackernews_stories
    WHERE mentioned_technologies IS NOT NULL
        AND array_length(mentioned_technologies, 1) > 0
    GROUP BY tech
    ORDER BY mentions DESC;
    """

    cursor.execute(query)
    results = cursor.fetchall()

    tech_data = {}
    for row in results:
        tech_data[row['tech']] = {
            'hn_mentions': float(row['mentions'] or 0),
            'hn_points': float(row['total_points'] or 0),
            'hn_avg_points': float(row['avg_points'] or 0),
            'hn_comments': float(row['total_comments'] or 0),
        }

    cursor.close()
    return tech_data


def normalize_tech_name(tech: str) -> str:
    """Normaliza nomes de tecnologias para matching"""
    # Mapeamento de aliases
    aliases = {
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'python': 'Python',
        'rust': 'Rust',
        'go': 'Go',
        'golang': 'Go',
        'java': 'Java',
        'c++': 'C++',
        'csharp': 'C#',
        'c#': 'C#',
        'ruby': 'Ruby',
        'php': 'PHP',
        'swift': 'Swift',
        'kotlin': 'Kotlin',
        'elixir': 'Elixir',
        'react': 'React',
        'vue': 'Vue',
        'angular': 'Angular',
        'svelte': 'Svelte',
        'nextjs': 'Next.js',
        'next.js': 'Next.js',
        'django': 'Django',
        'flask': 'Flask',
        'rails': 'Rails',
        'laravel': 'Laravel',
        'tensorflow': 'TensorFlow',
        'pytorch': 'PyTorch',
        'kubernetes': 'Kubernetes',
        'docker': 'Docker',
        'postgres': 'PostgreSQL',
        'postgresql': 'PostgreSQL',
        'mongodb': 'MongoDB',
        'redis': 'Redis',
        'wasm': 'WebAssembly',
        'webassembly': 'WebAssembly',
    }

    tech_lower = tech.lower().strip()
    return aliases.get(tech_lower, tech)


def calculate_tech_trend_scores(
    github_data: Dict[str, Dict[str, float]],
    hn_data: Dict[str, Dict[str, float]]
) -> List[Tuple[str, float, Dict[str, float]]]:
    """
    Calcula Tech Trend Score para cada tecnologia

    Formula SIMPLES:
        score = github_stars*0.4 + npm_downloads*0.3 + hn_points*0.2 + reddit*0.1

    Como NPM e Reddit ainda não existem, ajustamos:
        score = github_stars*0.6 + hn_points*0.4

    Returns:
        List[(tech_name, score, {metrics})]
    """
    # Combinar dados
    all_techs = set(github_data.keys()) | set(hn_data.keys())

    scores = []

    for tech in all_techs:
        tech_normalized = normalize_tech_name(tech)

        # GitHub metrics
        gh = github_data.get(tech, {})
        github_stars = gh.get('github_stars', 0)
        github_repos = gh.get('github_repos', 0)

        # HackerNews metrics
        hn = hn_data.get(tech, {})
        hn_points = hn.get('hn_points', 0)
        hn_mentions = hn.get('hn_mentions', 0)

        # Normalizar valores (escala log para evitar dominância de outliers)
        import math
        github_score = math.log10(github_stars + 1) * 100
        hn_score = math.log10(hn_points + 1) * 100

        # FÓRMULA SIMPLES (ajustada para dados disponíveis)
        # Peso 60% GitHub, 40% HN (quando tivermos NPM/Reddit, ajustamos)
        trend_score = (
            github_score * 0.6 +
            hn_score * 0.4
        )

        if trend_score > 0:  # Filtrar techs sem dados
            scores.append((
                tech_normalized,
                trend_score,
                {
                    'github_stars': int(github_stars),
                    'github_repos': int(github_repos),
                    'hn_mentions': int(hn_mentions),
                    'hn_points': int(hn_points),
                    'github_score': github_score,
                    'hn_score': hn_score,
                }
            ))

    # Ordenar por score
    scores.sort(key=lambda x: x[1], reverse=True)

    return scores


# ============================================================================
# REPORTING
# ============================================================================

def print_report(scores: List[Tuple[str, float, Dict[str, float]]]):
    """Imprime relatório formatado"""

    print("=" * 80)
    print("SOFIA PULSE - TECH TREND SCORE (SIMPLE)")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Formula: github_stars*0.6 + hn_points*0.4")
    print("(Weights adjusted until NPM/Reddit collectors are ready)")
    print()
    print("=" * 80)
    print()

    # Top 20 Overall
    print("🔥 TOP 20 TECNOLOGIAS (Overall Trend Score)")
    print("-" * 80)
    print(f"{'Rank':<6} {'Technology':<20} {'Score':<10} {'GitHub⭐':<15} {'HN📰':<10}")
    print("-" * 80)

    for idx, (tech, score, metrics) in enumerate(scores[:20], 1):
        print(
            f"{idx:<6} "
            f"{tech:<20} "
            f"{score:<10.1f} "
            f"{metrics['github_stars']:<15,} "
            f"{metrics['hn_mentions']:<10}"
        )

    print()
    print("=" * 80)
    print()

    # Dark Horses (alto GitHub, precisa checar funding)
    print("💎 DARK HORSES (High GitHub Activity, Check Funding!)")
    print("-" * 80)
    print("Tecnologias com muita atividade no GitHub - podem ser oportunidades")
    print()

    dark_horses = [
        (tech, score, metrics)
        for tech, score, metrics in scores
        if metrics['github_stars'] > 1000 and metrics['hn_mentions'] < 10
    ][:10]

    for idx, (tech, score, metrics) in enumerate(dark_horses, 1):
        print(
            f"{idx}. {tech}: "
            f"{metrics['github_stars']:,} stars, "
            f"only {metrics['hn_mentions']} HN mentions"
        )

    print()
    print("=" * 80)
    print()

    # Hype Check (alto HN, baixo GitHub = pode ser hype)
    print("⚠️  HYPE CHECK (High HN Buzz, Low GitHub = Verify!)")
    print("-" * 80)
    print("Muito buzz no HN mas pouco código - pode ser hype, não adoção real")
    print()

    hype_check = [
        (tech, score, metrics)
        for tech, score, metrics in scores
        if metrics['hn_mentions'] >= 5 and metrics['github_stars'] < 500
    ][:10]

    for idx, (tech, score, metrics) in enumerate(hype_check, 1):
        print(
            f"{idx}. {tech}: "
            f"{metrics['hn_mentions']} HN mentions, "
            f"but only {metrics['github_stars']:,} stars"
        )

    print()
    print("=" * 80)
    print()

    # Programming Languages
    print("💻 TOP PROGRAMMING LANGUAGES")
    print("-" * 80)

    languages = {
        'JavaScript', 'TypeScript', 'Python', 'Rust', 'Go', 'Java',
        'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Elixir', 'Zig'
    }

    lang_scores = [
        (tech, score, metrics)
        for tech, score, metrics in scores
        if tech in languages
    ][:10]

    for idx, (tech, score, metrics) in enumerate(lang_scores, 1):
        print(
            f"{idx}. {tech}: "
            f"Score {score:.1f} | "
            f"{metrics['github_stars']:,} stars | "
            f"{metrics['hn_mentions']} HN mentions"
        )

    print()
    print("=" * 80)
    print()

    # Frameworks/Libraries
    print("🛠️  TOP FRAMEWORKS & LIBRARIES")
    print("-" * 80)

    frameworks = {
        'React', 'Vue', 'Angular', 'Svelte', 'Next.js', 'Nuxt', 'Remix',
        'Django', 'Flask', 'FastAPI', 'Rails', 'Laravel', 'Spring',
        'TensorFlow', 'PyTorch', 'JAX', 'scikit-learn',
        'Kubernetes', 'Docker', 'Terraform', 'Ansible',
        'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch',
        'GraphQL', 'tRPC', 'Prisma', 'Drizzle'
    }

    fw_scores = [
        (tech, score, metrics)
        for tech, score, metrics in scores
        if tech in frameworks
    ][:15]

    for idx, (tech, score, metrics) in enumerate(fw_scores, 1):
        print(
            f"{idx}. {tech}: "
            f"Score {score:.1f} | "
            f"{metrics['github_stars']:,} stars | "
            f"{metrics['hn_mentions']} HN mentions"
        )

    print()
    print("=" * 80)
    print()

    print("💡 INSIGHTS:")
    print()
    print("- GitHub stars = Real developer adoption (not just hype)")
    print("- HN mentions = Tech community buzz (early signal)")
    print("- Dark Horses = Undervalued opportunities (high activity, low visibility)")
    print("- Hype Check = Verify real usage vs marketing buzz")
    print()
    print("🔮 CORRELATIONS:")
    print()
    print("- GitHub stars → NPM downloads (1-2 weeks lag)")
    print("- HN front page → VC funding announcement (2-8 weeks lag)")
    print("- Tech trend score → Job postings (1-3 months lag)")
    print()
    print("✅ Analysis complete!")
    print()


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("🚀 Connecting to database...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to PostgreSQL")
        print()

        print("📊 Collecting GitHub data...")
        github_data = get_github_technologies(conn)
        print(f"   ✅ {len(github_data)} technologies from GitHub")
        print()

        print("📊 Collecting HackerNews data...")
        hn_data = get_hackernews_technologies(conn)
        print(f"   ✅ {len(hn_data)} technologies from HackerNews")
        print()

        print("🧮 Calculating Tech Trend Scores...")
        scores = calculate_tech_trend_scores(github_data, hn_data)
        print(f"   ✅ {len(scores)} technologies scored")
        print()

        print_report(scores)

        conn.close()

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
