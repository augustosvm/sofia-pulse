#!/usr/bin/env npx tsx
/**
 * Docker Hub Stats Collector
 * Métrica: "Deployment Signal" / Infraestrutura
 * 
 * Coleta estatísticas de imagens oficiais e populares:
 * - Pull Count (Total deploys/downloads)
 * - Star Count
 * - Last Updated (Freshness)
 * 
 * Fonte: Docker Hub API v2 (Public)
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

// Mapeamento: Tech -> Docker Image (Namespace/Repo)
// Maioria são imagens oficiais ("library/__")
const DOCKER_IMAGES: Record<string, string | null> = {
    'python': 'library/python',
    'node': 'library/node',
    'postgres': 'library/postgres',
    'mongo': 'library/mongo',
    'redis': 'library/redis',
    'nginx': 'library/nginx',
    'httpd': 'library/httpd', // Apache
    'traefik': 'library/traefik',
    'golang': 'library/golang',
    'rust': 'library/rust',
    'ruby': 'library/ruby',
    'php': 'library/php',
    'java': 'library/openjdk', // OpenJDK como proxy principal de Java
    'jenkins': 'jenkins/jenkins', // Non-library official
    'gitlab': 'gitlab/gitlab-ce',
    'ubuntu': 'library/ubuntu',
    'alpine': 'library/alpine',
    'mysql': 'library/mysql',
    'mariadb': 'library/mariadb',
    'elasticsearch': 'library/elasticsearch',
    'kibana': 'library/kibana',
    'logstash': 'library/logstash',
    'rabbitmq': 'library/rabbitmq',
    'wordpress': 'library/wordpress',
    'memcached': 'library/memcached',
    'influxdb': 'library/influxdb',
    'cassandra': 'library/cassandra',
    'consul': 'library/consul',
    'vault': 'library/vault',
    'terraform': 'hashicorp/terraform',
    'docker': 'library/docker', // Docker-in-Docker
    'kubernetes': 'rancher/k3s', // Proxy razoável para k8s leve, já que k8s vanilla é complexo
    'react': null, // Não é tecnologia de container/backend (geralmente buildado em node)
    'vue': null,
};

async function collectDockerStats() {
    console.log('🐳 Docker Hub Stats Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);
    let totalUpdated = 0;
    const today = new Date().toISOString().split('T')[0] + ' 12:00:00+00';

    try {
        for (const [tech, imageName] of Object.entries(DOCKER_IMAGES)) {
            if (!imageName) continue; // Skip frontend-only libs

            console.log(`\n🔍 Fetching stats for image: ${imageName}...`);

            try {
                // https://hub.docker.com/v2/repositories/library/python/
                const url = `https://hub.docker.com/v2/repositories/${imageName}/`;

                const response = await axios.get(url, { timeout: 10000 });
                const data = response.data;

                // Extrair métricas
                const pullCount = data.pull_count;
                const starCount = data.star_count;
                const lastUpdated = data.last_updated;

                console.log(`   ✅ Pulls: ${pullCount.toLocaleString()} | Stars: ${starCount} | Updated: ${lastUpdated}`);

                // Unified Insert into tech_trends
                await pool.query(`
                    INSERT INTO sofia.tech_trends (
                        source, name, category, trend_type,
                        views, stars, metadata, collected_at,
                        period_start, period_end
                    ) VALUES (
                        'docker_hub', $1, 'infrastructure', 'daily_stats',
                        $2, $3, $4, $5,
                        $5, $5
                    )
                    ON CONFLICT (source, name, collected_at) 
                    DO UPDATE SET 
                        views = EXCLUDED.views,
                        stars = EXCLUDED.stars,
                        metadata = EXCLUDED.metadata;
                `, [
                    tech,
                    pullCount,
                    starCount,
                    JSON.stringify({ last_updated: lastUpdated, image_name: imageName }),
                    today
                ]);

                totalUpdated++;

            } catch (error: any) {
                if (error.response?.status === 404) {
                    console.error(`   ❌ Image not found: ${imageName}`);
                } else {
                    console.error(`   ❌ API Error:`, error.message);
                }
            }

            // Polite rate limiting
            await new Promise(r => setTimeout(r, 1000));
        }

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Collection complete. Updated ${totalUpdated} metrics.`);
        console.log('='.repeat(60));

        // Get total records count
        const countResult = await pool.query(`
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT name) as unique_images,
                   MAX(collected_at) as last_collected
            FROM sofia.tech_trends
            WHERE source = 'docker_hub'
        `);
        const stats = countResult.rows[0];

        console.log('\n📊 DATABASE STATS:');
        console.log(`   Total records: ${stats.total}`);
        console.log(`   Unique images: ${stats.unique_images}`);
        console.log(`   Last collected: ${stats.last_collected}`);
        console.log('='.repeat(60));

        // Return stats for notification
        return {
            success: true,
            inserted: totalUpdated,
            total_records: parseInt(stats.total),
            unique_images: parseInt(stats.unique_images),
            last_collected: stats.last_collected
        };

    } catch (err: any) {
        console.error('❌ Fatal error:', err.message);
        return {
            success: false,
            error: err.message,
            inserted: totalUpdated
        };
    } finally {
        await pool.end();
    }
}

// Run standalone
if (require.main === module) {
    collectDockerStats()
        .then(result => {
            if (result && result.success) {
                console.log(`\n🎉 SUCCESS: ${result.inserted} images updated`);
                process.exit(0);
            } else {
                console.error(`\n❌ FAILED: ${result?.error || 'Unknown error'}`);
                process.exit(1);
            }
        })
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectDockerStats };
