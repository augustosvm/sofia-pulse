#!/usr/bin/env tsx

import { Client } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

console.log('🔌 Testando conexão PostgreSQL...\n');

const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

console.log('📋 Config:');
console.log('  host:', dbConfig.host);
console.log('  port:', dbConfig.port);
console.log('  user:', dbConfig.user);
console.log('  password:', dbConfig.password === 'postgres' ? '❌ USANDO FALLBACK!' : '✅ from .env');
console.log('  database:', dbConfig.database);
console.log('');

async function testConnection() {
  const client = new Client(dbConfig);

  try {
    console.log('🔄 Conectando...');
    await client.connect();
    console.log('✅ CONECTADO COM SUCESSO!\n');

    const result = await client.query('SELECT current_user, current_database(), version()');
    console.log('📊 Informações do banco:');
    console.log('  current_user:', result.rows[0].current_user);
    console.log('  current_database:', result.rows[0].current_database);
    console.log('  version:', result.rows[0].version.split('\n')[0]);

    await client.end();
  } catch (error: any) {
    console.log('❌ ERRO NA CONEXÃO:');
    console.log('  Mensagem:', error.message);
    console.log('  Code:', error.code);
    console.log('  Detail:', error.detail);
    console.log('\n📋 Error completo:');
    console.log(error);
  }
}

testConnection();
