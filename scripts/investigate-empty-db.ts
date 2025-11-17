#!/usr/bin/env tsx
/**
 * INVESTIGAÇÃO: Por que o banco está vazio?
 * Collectors rodaram no sábado mas nenhum dado foi salvo
 */

import { config } from 'dotenv';
import pg from 'pg';
import { execSync } from 'child_process';
import fs from 'fs';

config();

const { Pool } = pg;

async function investigate() {
  console.log('🔍 INVESTIGAÇÃO: Por que banco está vazio?\n');
  console.log('='.repeat(60));

  // 1. Verificar conexão com banco
  console.log('\n1. TESTANDO CONEXÃO COM BANCO');
  console.log('-'.repeat(60));

  const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'sofia_db',
    user: process.env.DB_USER || 'sofia',
    password: process.env.DB_PASSWORD,
  });

  try {
    const result = await pool.query('SELECT version()');
    console.log('✅ PostgreSQL conectado:', result.rows[0].version.substring(0, 50) + '...');
  } catch (error) {
    console.log('❌ ERRO ao conectar:', error.message);
    process.exit(1);
  }

  // 2. Verificar se há ALGUMA tabela
  console.log('\n2. VERIFICANDO TABELAS');
  console.log('-'.repeat(60));

  const tablesResult = await pool.query(`
    SELECT schemaname, tablename
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY tablename;
  `);

  if (tablesResult.rows.length === 0) {
    console.log('❌ ZERO tabelas encontradas!');
    console.log('   Isso significa: Collectors NUNCA criaram tabelas');
    console.log('   Causa provável: Rodaram com --dry-run OU erro de conexão');
  } else {
    console.log(`✅ ${tablesResult.rows.length} tabelas encontradas:`);
    tablesResult.rows.forEach(r => {
      console.log(`   - ${r.tablename}`);
    });
  }

  // 3. Verificar logs de execução
  console.log('\n3. VERIFICANDO LOGS DE EXECUÇÃO');
  console.log('-'.repeat(60));

  const logLocations = [
    '/var/log/sofia-daily.log',
    '/var/log/sofia-weekly.log',
    '/var/log/sofia-monthly.log',
    '~/sofia-pulse/collector.log',
    '~/sofia-pulse/npm-debug.log',
  ];

  let foundLogs = false;
  for (const logPath of logLocations) {
    try {
      const fullPath = logPath.replace('~', process.env.HOME || '/home/ubuntu');
      if (fs.existsSync(fullPath)) {
        foundLogs = true;
        console.log(`✅ Log encontrado: ${logPath}`);
        const lastLines = execSync(`tail -20 ${fullPath}`).toString();
        console.log('   Últimas 20 linhas:');
        console.log(lastLines.split('\n').map(l => '   ' + l).join('\n'));
      }
    } catch (e) {
      // Ignorar erros
    }
  }

  if (!foundLogs) {
    console.log('⚠️  Nenhum log encontrado nos locais padrão');
  }

  // 4. Verificar cron jobs
  console.log('\n4. VERIFICANDO CRON JOBS');
  console.log('-'.repeat(60));

  try {
    const crontab = execSync('crontab -l 2>&1').toString();
    if (crontab.includes('sofia-pulse') || crontab.includes('collect')) {
      console.log('✅ Cron jobs configurados:');
      console.log(crontab.split('\n').filter(l => l.includes('sofia')).map(l => '   ' + l).join('\n'));
    } else {
      console.log('⚠️  Nenhum cron job configurado para sofia-pulse');
      console.log('   Collectors precisam ser rodados manualmente');
    }
  } catch (e) {
    console.log('⚠️  Não foi possível verificar crontab:', e.message);
  }

  // 5. Verificar histórico de comandos npm
  console.log('\n5. VERIFICANDO HISTÓRICO NPM');
  console.log('-'.repeat(60));

  try {
    const npmLogs = execSync('ls -lt ~/.npm/_logs/ 2>&1 | head -10').toString();
    console.log('Últimos logs npm:');
    console.log(npmLogs);
  } catch (e) {
    console.log('⚠️  Não foi possível verificar logs npm');
  }

  // 6. Testar se collectors conseguem criar tabelas AGORA
  console.log('\n6. TESTANDO CRIAÇÃO DE TABELA (SIMULAÇÃO)');
  console.log('-'.repeat(60));

  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS test_table_investigation (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);
    console.log('✅ Conseguimos criar tabela de teste!');

    await pool.query(`INSERT INTO test_table_investigation DEFAULT VALUES`);
    console.log('✅ Conseguimos inserir dados!');

    const count = await pool.query('SELECT COUNT(*) FROM test_table_investigation');
    console.log(`✅ Tabela tem ${count.rows[0].count} registro(s)`);

    await pool.query('DROP TABLE test_table_investigation');
    console.log('✅ Tabela de teste removida');

    console.log('\n   CONCLUSÃO: Banco está FUNCIONANDO normalmente!');
    console.log('   Problema: Collectors NÃO foram executados corretamente');

  } catch (error) {
    console.log('❌ ERRO ao criar/inserir:', error.message);
    console.log('   CONCLUSÃO: Há problema de permissão ou conexão!');
  }

  // 7. Verificar variáveis de ambiente
  console.log('\n7. VERIFICANDO VARIÁVEIS DE AMBIENTE');
  console.log('-'.repeat(60));

  console.log('DB_HOST:', process.env.DB_HOST || 'localhost');
  console.log('DB_PORT:', process.env.DB_PORT || '5432');
  console.log('DB_NAME:', process.env.DB_NAME || 'sofia_db');
  console.log('DB_USER:', process.env.DB_USER || 'sofia');
  console.log('DB_PASSWORD:', process.env.DB_PASSWORD ? '***CONFIGURADA***' : '❌ NÃO CONFIGURADA');

  if (!process.env.DB_PASSWORD) {
    console.log('\n⚠️  AVISO: DB_PASSWORD não está configurada no .env!');
    console.log('   Collectors podem ter falhado por falta de senha');
  }

  await pool.end();

  // 8. DIAGNÓSTICO FINAL
  console.log('\n' + '='.repeat(60));
  console.log('📋 DIAGNÓSTICO FINAL');
  console.log('='.repeat(60));

  console.log('\nPOSSÍVEIS CAUSAS:');
  console.log('1. ❌ Collectors rodaram com --dry-run (não salvam no banco)');
  console.log('2. ❌ Erro de conexão durante execução (senha errada, etc)');
  console.log('3. ❌ Collectors foram interrompidos antes de criar tabelas');
  console.log('4. ❌ Banco foi limpo/resetado depois da execução');
  console.log('5. ❌ Variáveis de ambiente incorretas durante execução');

  console.log('\n💡 AÇÕES RECOMENDADAS:');
  console.log('1. Rodar collectors MANUALMENTE agora (sem --dry-run):');
  console.log('   npm run collect:cardboard');
  console.log('   npm run collect:arxiv-ai');
  console.log('   npm run collect:ai-companies');
  console.log('');
  console.log('2. Verificar output COMPLETO (erros?)');
  console.log('');
  console.log('3. Depois rodar: npm run audit');
  console.log('');
  console.log('4. Se funcionar: Configurar cron jobs para automação diária');

  console.log('\n' + '='.repeat(60));
}

investigate().catch(console.error);
