#!/usr/bin/env npx tsx
/**
 * GitGuardian API - Detecção de Vulnerabilidades
 * Onde a governança está quebrando
 * Monitora exposição de secrets e vulnerabilidades em repositórios
 */

import axios from 'axios';
import { Client } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

const GITGUARDIAN_API_KEY = process.env.GITGUARDIAN_API_KEY;
const GITGUARDIAN_BASE_URL = 'https://api.gitguardian.com/v1';

interface GitGuardianIncident {
    id: number;
    date: string;
    detector: {
        name: string;
        display_name: string;
    };
    secret_hash: string;
    gitguardian_url: string;
    regression: boolean;
    status: string;
    assignee_email?: string;
    occurrences_count: number;
    secret_revoked: boolean;
    severity: string;
    validity: string;
    ignore_reason?: string;
    triggered_at: string;
}

async function collectGitGuardianIncidents() {
    console.log('🔒 GitGuardian - Monitoramento de Segurança');
    console.log('='.repeat(60));

    if (!GITGUARDIAN_API_KEY) {
        console.error('❌ GITGUARDIAN_API_KEY é obrigatória!');
        console.log('\n📝 Obtenha sua API key em: https://dashboard.gitguardian.com/');
        process.exit(1);
    }

    const client = new Client(dbConfig);
    await client.connect();

    try {
        // Criar tabela de incidentes de segurança
        await client.query(`
            CREATE TABLE IF NOT EXISTS sofia.gitguardian_incidents (
                id SERIAL PRIMARY KEY,
                incident_id INTEGER UNIQUE,
                incident_date TIMESTAMPTZ,
                detector_name VARCHAR(200),
                detector_display_name VARCHAR(200),
                secret_hash VARCHAR(200),
                gitguardian_url TEXT,
                regression BOOLEAN,
                status VARCHAR(50),
                assignee_email VARCHAR(200),
                occurrences_count INTEGER,
                secret_revoked BOOLEAN,
                severity VARCHAR(50),
                validity VARCHAR(50),
                ignore_reason TEXT,
                triggered_at TIMESTAMPTZ,
                collected_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_incidents_date 
            ON sofia.gitguardian_incidents(incident_date);
            
            CREATE INDEX IF NOT EXISTS idx_incidents_severity 
            ON sofia.gitguardian_incidents(severity);
            
            CREATE INDEX IF NOT EXISTS idx_incidents_status 
            ON sofia.gitguardian_incidents(status);
        `);

        console.log('\n🔍 Buscando incidentes de segurança...');

        let page = 1;
        let totalCollected = 0;
        let hasMore = true;

        while (hasMore && page <= 5) { // Limitar a 5 páginas
            try {
                const response = await axios.get(`${GITGUARDIAN_BASE_URL}/incidents`, {
                    params: {
                        page: page,
                        per_page: 100
                    },
                    headers: {
                        'Authorization': `Token ${GITGUARDIAN_API_KEY}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 15000
                });

                const incidents: GitGuardianIncident[] = response.data.results || [];

                if (incidents.length === 0) {
                    hasMore = false;
                    break;
                }

                console.log(`\n📄 Página ${page}: ${incidents.length} incidentes`);

                for (const incident of incidents) {
                    try {
                        await client.query(`
                            INSERT INTO sofia.gitguardian_incidents (
                                incident_id, incident_date, detector_name, detector_display_name,
                                secret_hash, gitguardian_url, regression, status,
                                assignee_email, occurrences_count, secret_revoked,
                                severity, validity, ignore_reason, triggered_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                            ON CONFLICT (incident_id) DO UPDATE SET
                                status = EXCLUDED.status,
                                secret_revoked = EXCLUDED.secret_revoked,
                                occurrences_count = EXCLUDED.occurrences_count,
                                collected_at = NOW()
                        `, [
                            incident.id,
                            incident.date,
                            incident.detector.name,
                            incident.detector.display_name,
                            incident.secret_hash,
                            incident.gitguardian_url,
                            incident.regression,
                            incident.status,
                            incident.assignee_email || null,
                            incident.occurrences_count,
                            incident.secret_revoked,
                            incident.severity,
                            incident.validity,
                            incident.ignore_reason || null,
                            incident.triggered_at
                        ]);

                        totalCollected++;

                    } catch (err: any) {
                        console.error(`      ❌ Erro ao inserir incidente ${incident.id}:`, err.message);
                    }
                }

                page++;

                // Rate limiting
                await new Promise(resolve => setTimeout(resolve, 1000));

            } catch (err: any) {
                if (axios.isAxiosError(err)) {
                    console.error(`   ❌ Erro API página ${page}: ${err.response?.status} ${err.message}`);
                } else {
                    console.error(`   ❌ Erro página ${page}:`, err.message);
                }
                hasMore = false;
            }
        }

        // Estatísticas
        const stats = await client.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'TRIGGERED' THEN 1 END) as triggered,
                COUNT(CASE WHEN status = 'IGNORED' THEN 1 END) as ignored,
                COUNT(CASE WHEN status = 'RESOLVED' THEN 1 END) as resolved,
                COUNT(CASE WHEN secret_revoked = true THEN 1 END) as revoked,
                COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical,
                COUNT(CASE WHEN severity = 'high' THEN 1 END) as high,
                COUNT(DISTINCT detector_name) as detector_types
            FROM sofia.gitguardian_incidents
        `);

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Coletados: ${totalCollected} incidentes`);
        console.log('\n📊 Estatísticas GitGuardian:');
        console.log(`   Total de incidentes: ${stats.rows[0].total}`);
        console.log(`   🔴 Triggered: ${stats.rows[0].triggered}`);
        console.log(`   ⚠️  Ignored: ${stats.rows[0].ignored}`);
        console.log(`   ✅ Resolved: ${stats.rows[0].resolved}`);
        console.log(`   🔐 Secrets revogados: ${stats.rows[0].revoked}`);
        console.log(`\n   Severidade:`);
        console.log(`   🔴 Critical: ${stats.rows[0].critical}`);
        console.log(`   🟠 High: ${stats.rows[0].high}`);
        console.log(`\n   Tipos de detectores: ${stats.rows[0].detector_types}`);
        console.log('='.repeat(60));

    } catch (error: any) {
        console.error('❌ Erro fatal:', error.message);
    } finally {
        await client.end();
    }
}

if (require.main === module) {
    collectGitGuardianIncidents()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Erro fatal:', err);
            process.exit(1);
        });
}

export { collectGitGuardianIncidents };
