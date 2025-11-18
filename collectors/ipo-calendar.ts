/**
 * Sofia Pulse - IPO Calendar Collector
 *
 * Coleta IPOs pendentes de:
 * - NASDAQ IPO Calendar
 * - B3 IPO Calendar
 * - EDGAR Filings (S-1 forms)
 *
 * Tabela: sofia.ipo_calendar
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import { db } from '../db';

interface IPO {
  company: string;
  ticker?: string;
  exchange: string; // 'NASDAQ' | 'B3' | 'NYSE'
  expectedDate?: Date;
  priceRange?: string;
  sharesOffered?: number;
  marketCap?: number;
  sector?: string;
  country: string;
  underwriters?: string[];
  description?: string;
  status: 'Expected' | 'Filed' | 'Priced' | 'Trading';
  filingDate?: Date;
  source: string;
}

/**
 * Coleta IPOs do NASDAQ Calendar
 */
async function collectNasdaqIPOs(): Promise<IPO[]> {
  console.log('📊 Coletando IPOs do NASDAQ...');

  try {
    // NASDAQ IPO Calendar endpoint
    const url = 'https://www.nasdaq.com/market-activity/ipos';

    const response = await axios.get(url, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
    });

    const $ = cheerio.load(response.data);
    const ipos: IPO[] = [];

    // Parse table (estrutura pode variar)
    $('table tr').each((_, row) => {
      const cells = $(row).find('td');
      if (cells.length >= 4) {
        const company = $(cells[0]).text().trim();
        const ticker = $(cells[1]).text().trim();
        const priceRange = $(cells[2]).text().trim();
        const dateStr = $(cells[3]).text().trim();

        if (company && ticker) {
          ipos.push({
            company,
            ticker,
            exchange: 'NASDAQ',
            expectedDate: new Date(dateStr),
            priceRange,
            country: 'USA',
            status: 'Expected',
            source: 'nasdaq.com',
          });
        }
      }
    });

    console.log(`   ✅ ${ipos.length} IPOs encontrados no NASDAQ`);
    return ipos;
  } catch (error) {
    console.error('   ❌ Erro ao coletar NASDAQ IPOs:', error);
    return [];
  }
}

/**
 * Coleta IPOs do B3 Calendar
 */
async function collectB3IPOs(): Promise<IPO[]> {
  console.log('📊 Coletando IPOs da B3...');

  try {
    // B3 IPO Calendar
    const url = 'https://www.b3.com.br/pt_br/produtos-e-servicos/renda-variavel/ofertas-publicas/ofertas-em-andamento/';

    const response = await axios.get(url, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
    });

    const $ = cheerio.load(response.data);
    const ipos: IPO[] = [];

    // Parse ofertas em andamento
    $('.offering-card').each((_, card) => {
      const company = $(card).find('.company-name').text().trim();
      const ticker = $(card).find('.ticker').text().trim();
      const sector = $(card).find('.sector').text().trim();
      const dateStr = $(card).find('.date').text().trim();

      if (company) {
        ipos.push({
          company,
          ticker: ticker || undefined,
          exchange: 'B3',
          expectedDate: dateStr ? new Date(dateStr) : undefined,
          sector,
          country: 'Brasil',
          status: 'Expected',
          source: 'b3.com.br',
        });
      }
    });

    console.log(`   ✅ ${ipos.length} IPOs encontrados na B3`);
    return ipos;
  } catch (error) {
    console.error('   ❌ Erro ao coletar B3 IPOs:', error);
    return [];
  }
}

/**
 * Coleta S-1 Filings do EDGAR (SEC)
 */
async function collectSECFilings(): Promise<IPO[]> {
  console.log('📊 Coletando S-1 Filings (SEC/EDGAR)...');

  try {
    // SEC EDGAR API
    const url = 'https://www.sec.gov/cgi-bin/browse-edgar';

    const params = {
      action: 'getcompany',
      type: 'S-1',
      dateb: new Date().toISOString().split('T')[0],
      owner: 'exclude',
      count: 100,
      output: 'atom',
    };

    const response = await axios.get(url, {
      params,
      headers: {
        'User-Agent': 'Sofia Pulse contact@sofiapulse.com',
      },
    });

    const $ = cheerio.load(response.data, { xmlMode: true });
    const ipos: IPO[] = [];

    $('entry').each((_, entry) => {
      const company = $(entry).find('title').text().trim();
      const filingDate = $(entry).find('updated').text().trim();

      if (company) {
        ipos.push({
          company,
          exchange: 'NASDAQ', // A maioria
          country: 'USA',
          status: 'Filed',
          filingDate: new Date(filingDate),
          source: 'sec.gov/edgar',
        });
      }
    });

    console.log(`   ✅ ${ipos.length} S-1 Filings encontrados`);
    return ipos;
  } catch (error) {
    console.error('   ❌ Erro ao coletar SEC filings:', error);
    return [];
  }
}

/**
 * Salva IPOs no banco de dados
 */
async function saveIPOs(ipos: IPO[]) {
  console.log(`\n💾 Salvando ${ipos.length} IPOs no banco...`);

  for (const ipo of ipos) {
    try {
      await db.execute(
        `
        INSERT INTO sofia.ipo_calendar (
          company, ticker, exchange, expected_date, price_range,
          shares_offered, market_cap, sector, country,
          underwriters, description, status, filing_date, source
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        ON CONFLICT (company, exchange, expected_date)
        DO UPDATE SET
          ticker = EXCLUDED.ticker,
          price_range = EXCLUDED.price_range,
          status = EXCLUDED.status,
          updated_at = NOW()
      `,
        [
          ipo.company,
          ipo.ticker,
          ipo.exchange,
          ipo.expectedDate,
          ipo.priceRange,
          ipo.sharesOffered,
          ipo.marketCap,
          ipo.sector,
          ipo.country,
          ipo.underwriters,
          ipo.description,
          ipo.status,
          ipo.filingDate,
          ipo.source,
        ]
      );
    } catch (error) {
      console.error(`   ❌ Erro ao salvar ${ipo.company}:`, error);
    }
  }

  console.log('   ✅ IPOs salvos!');
}

/**
 * Função principal
 */
export async function collectIPOCalendar() {
  console.log('🔔 Sofia Pulse - IPO Calendar Collector');
  console.log('=' .repeat(60));

  const allIPOs: IPO[] = [];

  // Coletar de todas as fontes
  const nasdaqIPOs = await collectNasdaqIPOs();
  const b3IPOs = await collectB3IPOs();
  const secFilings = await collectSECFilings();

  allIPOs.push(...nasdaqIPOs, ...b3IPOs, ...secFilings);

  // Salvar no banco
  await saveIPOs(allIPOs);

  console.log('\n' + '='.repeat(60));
  console.log(`✅ Total: ${allIPOs.length} IPOs coletados`);
  console.log('=' .repeat(60));

  return allIPOs;
}

// Run if called directly
if (require.main === module) {
  collectIPOCalendar()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error('❌ Erro fatal:', error);
      process.exit(1);
    });
}
