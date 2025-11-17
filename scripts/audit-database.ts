#!/usr/bin/env tsx
/**
 * AUDIT DATABASE
 * ==============
 * Verifica TUDO que foi coletado no banco de dados:
 * - Quais tabelas existem
 * - Quantos registros em cada
 * - Data mais antiga e mais recente
 * - Status de coleta (vazio, dados antigos, dados recentes)
 */

import { config } from 'dotenv';
import pg from 'pg';

config();

const { Pool } = pg;

interface TableStats {
  table_name: string;
  row_count: number;
  oldest_date: string | null;
  newest_date: string | null;
  date_column: string | null;
  status: string;
}

async function auditDatabase() {
  const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'sofia_db',
    user: process.env.DB_USER || 'sofia',
    password: process.env.DB_PASSWORD,
  });

  try {
    console.log('🔍 SOFIA PULSE - DATABASE AUDIT');
    console.log('================================\n');

    // 1. Listar todas as tabelas (TODOS os schemas, não apenas 'public')
    const tablesResult = await pool.query(`
      SELECT table_schema, table_name
      FROM information_schema.tables
      WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_type = 'BASE TABLE'
      ORDER BY table_schema, table_name;
    `);

    const tables = tablesResult.rows.map(r => ({ schema: r.table_schema, name: r.table_name }));
    console.log(`📊 Encontradas ${tables.length} tabelas no banco\n`);

    const stats: TableStats[] = [];

    // 2. Para cada tabela, pegar estatísticas
    for (const table of tables) {
      const schemaName = table.schema;
      const tableName = table.name;
      const fullTableName = `${schemaName}.${tableName}`;

      console.log(`\n📋 Analisando: ${fullTableName}`);
      console.log('─'.repeat(60));

      // Contar registros
      const countResult = await pool.query(`SELECT COUNT(*) as count FROM "${schemaName}"."${tableName}"`);
      const rowCount = parseInt(countResult.rows[0].count);

      console.log(`   Registros: ${rowCount.toLocaleString()}`);

      if (rowCount === 0) {
        stats.push({
          table_name: fullTableName,
          row_count: 0,
          oldest_date: null,
          newest_date: null,
          date_column: null,
          status: '❌ VAZIO - Nenhum dado coletado',
        });
        console.log(`   Status: ❌ VAZIO`);
        continue;
      }

      // Descobrir coluna de data
      const dateColumns = ['collected_at', 'created_at', 'updated_at', 'published_date',
                          'publication_date', 'month', 'quarter', 'date', 'fiscal_year'];

      let dateColumn: string | null = null;
      for (const col of dateColumns) {
        const colCheck = await pool.query(`
          SELECT column_name
          FROM information_schema.columns
          WHERE table_schema = $1 AND table_name = $2 AND column_name = $3
        `, [schemaName, tableName, col]);

        if (colCheck.rows.length > 0) {
          dateColumn = col;
          break;
        }
      }

      if (!dateColumn) {
        stats.push({
          table_name: fullTableName,
          row_count: rowCount,
          oldest_date: null,
          newest_date: null,
          date_column: null,
          status: '⚠️  TEM DADOS mas sem coluna de data',
        });
        console.log(`   Status: ⚠️  TEM DADOS mas sem coluna de data para análise temporal`);
        continue;
      }

      // Pegar datas mais antiga e mais recente
      const dateQuery = `
        SELECT
          MIN("${dateColumn}") as oldest,
          MAX("${dateColumn}") as newest
        FROM "${schemaName}"."${tableName}"
        WHERE "${dateColumn}" IS NOT NULL
      `;
      const dateResult = await pool.query(dateQuery);

      const oldestDate = dateResult.rows[0]?.oldest;
      const newestDate = dateResult.rows[0]?.newest;

      console.log(`   Coluna de data: ${dateColumn}`);
      console.log(`   Período: ${oldestDate || 'N/A'} → ${newestDate || 'N/A'}`);

      // Calcular status
      let status = '';
      if (newestDate) {
        const now = new Date();
        const newest = new Date(newestDate);
        const daysDiff = Math.floor((now.getTime() - newest.getTime()) / (1000 * 60 * 60 * 24));

        if (daysDiff === 0) {
          status = '✅ HOJE - Dados coletados hoje!';
        } else if (daysDiff === 1) {
          status = '🟡 ONTEM - Dados de ontem (precisa atualizar)';
        } else if (daysDiff <= 7) {
          status = `🟠 ${daysDiff} DIAS ATRÁS - Dados desatualizados`;
        } else if (daysDiff <= 30) {
          status = `🔴 ${daysDiff} DIAS ATRÁS - Muito desatualizado!`;
        } else {
          status = `⚫ ${daysDiff} DIAS ATRÁS - CRÍTICO: Não está sendo coletado!`;
        }
      } else {
        status = '⚠️  Dados sem timestamp válido';
      }

      stats.push({
        table_name: fullTableName,
        row_count: rowCount,
        oldest_date: oldestDate,
        newest_date: newestDate,
        date_column: dateColumn,
        status: status,
      });

      console.log(`   ${status}`);

      // Mostrar amostra de dados (primeira linha)
      const sampleResult = await pool.query(`SELECT * FROM "${schemaName}"."${tableName}" LIMIT 1`);
      if (sampleResult.rows.length > 0) {
        const columns = Object.keys(sampleResult.rows[0]);
        console.log(`   Colunas: ${columns.slice(0, 5).join(', ')}${columns.length > 5 ? ', ...' : ''}`);
      }
    }

    // 3. Resumo final
    console.log('\n\n' + '='.repeat(80));
    console.log('📊 RESUMO GERAL');
    console.log('='.repeat(80));

    const totalTables = stats.length;
    const emptyTables = stats.filter(s => s.row_count === 0).length;
    const tablesWithData = stats.filter(s => s.row_count > 0).length;
    const totalRows = stats.reduce((sum, s) => sum + s.row_count, 0);

    console.log(`\n✅ Tabelas com dados: ${tablesWithData}/${totalTables}`);
    console.log(`❌ Tabelas vazias: ${emptyTables}/${totalTables}`);
    console.log(`📈 Total de registros: ${totalRows.toLocaleString()}\n`);

    console.log('📋 Detalhamento por tabela:');
    console.log('─'.repeat(100));
    console.log(
      'Tabela'.padEnd(40) +
      'Registros'.padEnd(15) +
      'Última coleta'.padEnd(20) +
      'Status'.padEnd(25)
    );
    console.log('─'.repeat(100));

    for (const stat of stats.sort((a, b) => b.row_count - a.row_count)) {
      const tableName = stat.table_name.padEnd(40);
      const count = stat.row_count.toLocaleString().padEnd(15);
      const date = (stat.newest_date ? new Date(stat.newest_date).toISOString().split('T')[0] : 'N/A').padEnd(20);
      const status = stat.status;

      console.log(`${tableName}${count}${date}${status}`);
    }

    console.log('─'.repeat(100));

    // 4. Recomendações
    console.log('\n\n💡 RECOMENDAÇÕES:');
    console.log('─'.repeat(80));

    const emptyTablesList = stats.filter(s => s.row_count === 0);
    if (emptyTablesList.length > 0) {
      console.log('\n❌ Tabelas vazias (collectors nunca rodaram):');
      emptyTablesList.forEach(s => {
        console.log(`   - ${s.table_name}`);
        // Sugerir comando
        const collectorName = s.table_name
          .replace(/_/g, '-')
          .replace(/s$/, ''); // remover 's' do plural
        console.log(`     → Rodar: npm run collect:${collectorName}`);
      });
    }

    const outdatedTables = stats.filter(s =>
      s.row_count > 0 &&
      s.newest_date &&
      (new Date().getTime() - new Date(s.newest_date).getTime()) > 24 * 60 * 60 * 1000
    );

    if (outdatedTables.length > 0) {
      console.log('\n🟠 Tabelas com dados desatualizados (>24h):');
      outdatedTables.forEach(s => {
        const daysSince = Math.floor(
          (new Date().getTime() - new Date(s.newest_date!).getTime()) / (1000 * 60 * 60 * 24)
        );
        console.log(`   - ${s.table_name} (${daysSince} dias atrás)`);
      });
      console.log('\n   💡 Considerar configurar cron jobs para atualização automática');
      console.log('      Ver: DEPLOY.md (seção Cron Jobs)');
    }

    const healthyTables = stats.filter(s =>
      s.row_count > 0 &&
      s.newest_date &&
      (new Date().getTime() - new Date(s.newest_date).getTime()) <= 24 * 60 * 60 * 1000
    );

    if (healthyTables.length > 0) {
      console.log('\n✅ Tabelas atualizadas (últimas 24h):');
      healthyTables.forEach(s => {
        console.log(`   - ${s.table_name} (${s.row_count.toLocaleString()} registros)`);
      });
    }

    console.log('\n' + '='.repeat(80));
    console.log('✅ Auditoria concluída!');
    console.log('='.repeat(80) + '\n');

  } catch (error) {
    console.error('❌ Erro ao auditar banco:', error);
    throw error;
  } finally {
    await pool.end();
  }
}

// Executar
auditDatabase().catch(console.error);
