#!/usr/bin/env tsx

import * as dotenv from 'dotenv';
import * as path from 'path';
import * as fs from 'fs';

console.log('🔍 DEBUG - Verificando .env loading\n');

// Info sobre diretórios
console.log('📁 Diretórios:');
console.log('  __dirname:', __dirname);
console.log('  __filename:', __filename);
console.log('  process.cwd():', process.cwd());
console.log('');

// Verificar quais .env existem
console.log('📄 Arquivos .env encontrados:');
const rootEnv = path.join(process.cwd(), '.env');
const financeEnv = path.join(process.cwd(), 'finance', '.env');
const scriptDirEnv = path.join(__dirname, '..', '.env');

console.log(`  ${rootEnv}: ${fs.existsSync(rootEnv) ? '✅ EXISTS' : '❌ NOT FOUND'}`);
console.log(`  ${financeEnv}: ${fs.existsSync(financeEnv) ? '✅ EXISTS' : '❌ NOT FOUND'}`);
console.log(`  ${scriptDirEnv}: ${fs.existsSync(scriptDirEnv) ? '✅ EXISTS' : '❌ NOT FOUND'}`);
console.log('');

// Carregar .env
console.log('⚙️  Carregando .env com dotenv.config()...');
const result = dotenv.config();

if (result.error) {
  console.log('  ❌ ERRO:', result.error.message);
} else {
  console.log('  ✅ Loaded from:', result.parsed ? 'success' : 'no file found, using defaults');
}
console.log('');

// Mostrar variáveis POSTGRES_*
console.log('🔑 Variáveis POSTGRES_*:');
console.log('  POSTGRES_HOST:', process.env.POSTGRES_HOST || '❌ UNDEFINED');
console.log('  POSTGRES_PORT:', process.env.POSTGRES_PORT || '❌ UNDEFINED');
console.log('  POSTGRES_USER:', process.env.POSTGRES_USER || '❌ UNDEFINED');
console.log('  POSTGRES_PASSWORD:', process.env.POSTGRES_PASSWORD ? '***' : '❌ UNDEFINED');
console.log('  POSTGRES_DB:', process.env.POSTGRES_DB || '❌ UNDEFINED');
console.log('');

// Mostrar variáveis DB_*
console.log('🔑 Variáveis DB_*:');
console.log('  DB_HOST:', process.env.DB_HOST || '❌ UNDEFINED');
console.log('  DB_PORT:', process.env.DB_PORT || '❌ UNDEFINED');
console.log('  DB_USER:', process.env.DB_USER || '❌ UNDEFINED');
console.log('  DB_PASSWORD:', process.env.DB_PASSWORD ? '***' : '❌ UNDEFINED');
console.log('  DB_NAME:', process.env.DB_NAME || '❌ UNDEFINED');
console.log('');

// Testar conexão
console.log('🔌 Testando dbConfig:');
const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

console.log('  Config que será usado:');
console.log('    host:', dbConfig.host);
console.log('    port:', dbConfig.port);
console.log('    user:', dbConfig.user);
console.log('    password:', dbConfig.password === 'postgres' ? '❌ FALLBACK!' : '✅ from .env');
console.log('    database:', dbConfig.database);
