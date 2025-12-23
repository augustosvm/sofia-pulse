import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import { OrganizationsInserter } from './shared/organizations-inserter.js';

dotenv.config();

const pool = new Pool({
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
});

async function main() {
    const inserter = new OrganizationsInserter(pool);

    console.log('🇧🇷 Registering Brazil Organizations...');

    // 1. MDIC - Ministério do Desenvolvimento
    await inserter.insertOrganization({
        org_id: 'mdic-gov-br',
        name: 'Ministério do Desenvolvimento, Indústria, Comércio e Serviços (MDIC)',
        type: 'government_agency',
        source: 'manual-registration',
        country: 'Brazil',
        country_code: 'BR',
        location: 'Brasília, DF',
        website: 'https://www.gov.br/mdic',
        description: 'Órgão do governo federal responsável pela política de desenvolvimento, indústria, comércio e serviços.',
        tags: ['Government', 'Trade', 'Economy', 'Brazil', 'ComexStat'],
        metadata: {
            acronym: 'MDIC',
            jurisdiction: 'Federal',
            data_portal: 'ComexStat'
        }
    });
    console.log('✅ MDIC registered.');

    // 2. FIESP - Federação das Indústrias do Estado de São Paulo
    await inserter.insertOrganization({
        org_id: 'fiesp-org-br',
        name: 'Federação das Indústrias do Estado de São Paulo (FIESP)',
        type: 'ngo', // Technically an Industry Association, fitting NGO or Corporation
        source: 'manual-registration',
        country: 'Brazil',
        country_code: 'BR',
        location: 'São Paulo, SP',
        website: 'https://www.fiesp.com.br',
        description: 'Entidade de representação da indústria do estado de São Paulo.',
        tags: ['Industry', 'Economy', 'Brazil', 'Manufacturing'],
        metadata: {
            acronym: 'FIESP',
            jurisdiction: 'State (São Paulo)',
            data_portal: 'Sensor/INA'
        }
    });
    console.log('✅ FIESP registered.');

    await pool.end();
}

main().catch(console.error);
