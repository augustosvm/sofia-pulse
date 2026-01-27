#!/usr/bin/env python3
"""
Docker Hub + Cybersecurity Cross-Check
Identifica plataformas Docker com falhas de segurança conhecidas

Cruza:
- sofia.tech_trends (source='docker_hub') - Tecnologias usadas
- sofia.cybersecurity_events - CVEs e vulnerabilidades
"""

import os
import sys
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'dbname': os.getenv('DB_NAME', 'sofia'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def analyze_docker_security():
    """
    Analisa cruzamento entre Docker Hub e CVEs
    """
    conn = get_connection()
    cur = conn.cursor()

    print("=" * 80)
    print("🐳🔒 DOCKER HUB + CYBERSECURITY CROSS-CHECK")
    print("=" * 80)
    print()

    # Get Docker images with recent activity
    cur.execute("""
        SELECT
            name as tech,
            views as pulls,
            stars,
            collected_at,
            metadata
        FROM sofia.tech_trends
        WHERE source = 'docker_hub'
          AND collected_at >= NOW() - INTERVAL '7 days'
        ORDER BY views DESC
        LIMIT 50
    """)
    docker_images = cur.fetchall()

    print(f"📊 Analyzing {len(docker_images)} Docker images...")
    print()

    # Get recent CVEs
    cur.execute("""
        SELECT
            cve_id,
            title,
            description,
            severity,
            published_date,
            affected_products
        FROM sofia.cybersecurity_events
        WHERE event_type = 'vulnerability'
          AND published_date >= NOW() - INTERVAL '30 days'
        ORDER BY published_date DESC
    """)
    cves = cur.fetchall()

    print(f"🔒 Found {len(cves)} recent CVEs (last 30 days)")
    print()

    # Cross-check
    vulnerabilities_found = []

    for img in docker_images:
        tech = img['tech'].lower()

        for cve in cves:
            # Check if tech is mentioned in CVE
            title_lower = (cve['title'] or '').lower()
            desc_lower = (cve['description'] or '').lower()
            products = (cve['affected_products'] or [])
            products_str = ' '.join(products).lower() if isinstance(products, list) else str(products).lower()

            if (tech in title_lower or
                tech in desc_lower or
                tech in products_str):

                vulnerabilities_found.append({
                    'tech': img['tech'],
                    'pulls': img['pulls'],
                    'cve_id': cve['cve_id'],
                    'severity': cve['severity'],
                    'title': cve['title'],
                    'published': cve['published_date']
                })

    # Report
    print("=" * 80)
    print("⚠️  VULNERABILITIES FOUND")
    print("=" * 80)
    print()

    if not vulnerabilities_found:
        print("✅ No critical vulnerabilities found in top Docker images")
        print()
    else:
        # Group by tech
        by_tech = {}
        for v in vulnerabilities_found:
            tech = v['tech']
            if tech not in by_tech:
                by_tech[tech] = []
            by_tech[tech].append(v)

        for tech, vulns in sorted(by_tech.items(), key=lambda x: -len(x[1])):
            pulls = vulns[0]['pulls']
            print(f"🐳 {tech.upper()}")
            print(f"   Pulls: {pulls:,}")
            print(f"   Vulnerabilities: {len(vulns)}")
            print()

            for v in vulns[:3]:  # Top 3 per tech
                severity_emoji = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }.get(v['severity'], '⚪')

                print(f"   {severity_emoji} {v['severity']} - {v['cve_id']}")
                print(f"      {v['title'][:70]}...")
                print(f"      Published: {v['published']}")
                print()

            if len(vulns) > 3:
                print(f"   ... and {len(vulns) - 3} more vulnerabilities")
                print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"   Docker images analyzed: {len(docker_images)}")
    print(f"   Recent CVEs checked: {len(cves)}")
    print(f"   Vulnerable platforms found: {len(set(v['tech'] for v in vulnerabilities_found))}")
    print(f"   Total vulnerabilities: {len(vulnerabilities_found)}")
    print()

    # Save to file
    output_file = "analytics/docker-security-crosscheck-latest.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("🐳🔒 DOCKER HUB + CYBERSECURITY CROSS-CHECK\n")
        f.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write("=" * 80 + "\n\n")

        if vulnerabilities_found:
            for tech, vulns in sorted(by_tech.items(), key=lambda x: -len(x[1])):
                f.write(f"\n🐳 {tech.upper()}\n")
                f.write(f"   Pulls: {vulns[0]['pulls']:,}\n")
                f.write(f"   Vulnerabilities: {len(vulns)}\n\n")

                for v in vulns:
                    f.write(f"   [{v['severity']}] {v['cve_id']}\n")
                    f.write(f"   {v['title']}\n")
                    f.write(f"   Published: {v['published']}\n\n")
        else:
            f.write("✅ No critical vulnerabilities found in top Docker images\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Summary: {len(set(v['tech'] for v in vulnerabilities_found))} vulnerable platforms, ")
        f.write(f"{len(vulnerabilities_found)} total vulnerabilities\n")

    print(f"📄 Report saved: {output_file}")
    print()

    cur.close()
    conn.close()

    return {
        'docker_images': len(docker_images),
        'cves_checked': len(cves),
        'vulnerable_platforms': len(set(v['tech'] for v in vulnerabilities_found)),
        'total_vulnerabilities': len(vulnerabilities_found)
    }

if __name__ == '__main__':
    try:
        result = analyze_docker_security()

        # Send WhatsApp notification if vulnerabilities found
        if result['vulnerable_platforms'] > 0:
            try:
                from scripts.utils.whatsapp_notifier import send_whatsapp

                message = f"""🚨 *Docker Security Alert*

⚠️  {result['vulnerable_platforms']} vulnerable platforms found
🔒 {result['total_vulnerabilities']} total vulnerabilities
📊 {result['docker_images']} images analyzed

Check: analytics/docker-security-crosscheck-latest.txt"""

                send_whatsapp(message)
            except:
                pass

        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
