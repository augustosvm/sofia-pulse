#!/usr/bin/env tsx
/**
 * Currency Exchange Rates Collector
 *
 * Fetches daily exchange rates for all major currencies and stores in sofia.currency_rates
 * Runs daily to maintain historical data for cross-currency analysis
 *
 * Sources:
 * - Primary: exchangerate-api.io (free tier: 1500 requests/month)
 * - Fallback: BACEN API for BRL rates
 *
 * Usage:
 *   npx tsx scripts/collect-currency-rates.ts
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

// ============================================================================
// CONFIGURATION
// ============================================================================

const dbConfig = {
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD,
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
};

// Currencies to track (can expand this list)
const CURRENCIES = [
  { code: 'USD', name: 'US Dollar' },
  { code: 'EUR', name: 'Euro' },
  { code: 'GBP', name: 'British Pound' },
  { code: 'BRL', name: 'Brazilian Real' },
  { code: 'CAD', name: 'Canadian Dollar' },
  { code: 'AUD', name: 'Australian Dollar' },
  { code: 'JPY', name: 'Japanese Yen' },
  { code: 'CNY', name: 'Chinese Yuan' },
  { code: 'INR', name: 'Indian Rupee' },
  { code: 'MXN', name: 'Mexican Peso' },
  { code: 'CHF', name: 'Swiss Franc' },
  { code: 'SGD', name: 'Singapore Dollar' },
  { code: 'HKD', name: 'Hong Kong Dollar' },
  { code: 'SEK', name: 'Swedish Krona' },
  { code: 'NOK', name: 'Norwegian Krone' },
  { code: 'DKK', name: 'Danish Krone' },
  { code: 'PLN', name: 'Polish Zloty' },
  { code: 'CZK', name: 'Czech Koruna' },
  { code: 'ARS', name: 'Argentine Peso' },
  { code: 'CLP', name: 'Chilean Peso' },
];

// ============================================================================
// TYPES
// ============================================================================

interface ExchangeRate {
  currency_code: string;
  currency_name: string;
  rate_to_usd: number;
  rate_from_usd: number;
  source: string;
}

// ============================================================================
// API CLIENTS
// ============================================================================

/**
 * Fetch rates from exchangerate-api.io (Free tier)
 */
async function fetchFromExchangeRateAPI(): Promise<Record<string, number>> {
  const apiKey = process.env.EXCHANGERATE_API_KEY;
  const url = apiKey
    ? `https://v6.exchangerate-api.com/v6/${apiKey}/latest/USD`
    : 'https://open.er-api.com/v6/latest/USD';  // Free endpoint (no key needed)

  console.log('   📡 Fetching from exchangerate-api.io...');

  const response = await axios.get(url, { timeout: 10000 });

  if (response.data.result !== 'success') {
    throw new Error(`API error: ${response.data['error-type']}`);
  }

  console.log(`   ✅ Fetched ${Object.keys(response.data.conversion_rates).length} rates`);

  return response.data.conversion_rates;
}

/**
 * Fetch rates from BACEN (Banco Central do Brasil)
 * Primary source for BRL and major currencies in Brazilian market
 */
async function fetchFromBACEN(): Promise<Record<string, number>> {
  try {
    console.log('   📡 Fetching from BACEN API...');

    const rates: Record<string, number> = {};

    // Format date for BACEN API (MMDDYYYY)
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const year = today.getFullYear();
    const dateStr = `${month}-${day}-${year}`;

    // Fetch USD/BRL (Cotação do Dólar)
    try {
      const usdUrl = `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='${dateStr}'&$format=json`;
      const usdResponse = await axios.get(usdUrl, { timeout: 10000 });

      if (usdResponse.data.value && usdResponse.data.value.length > 0) {
        rates['BRL'] = usdResponse.data.value[0].cotacaoCompra;  // BRL per USD
        console.log(`   ✅ BACEN USD/BRL: ${rates['BRL']}`);
      }
    } catch (error) {
      console.error('   ⚠️  BACEN USD failed');
    }

    // Fetch EUR/BRL (Cotação do Euro)
    try {
      const eurUrl = `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='EUR'&@dataCotacao='${dateStr}'&$format=json`;
      const eurResponse = await axios.get(eurUrl, { timeout: 10000 });

      if (eurResponse.data.value && eurResponse.data.value.length > 0) {
        const eurBrl = eurResponse.data.value[0].cotacaoCompra;  // BRL per EUR
        // Convert to EUR per USD: EUR/USD = (BRL/EUR) / (BRL/USD)
        if (rates['BRL']) {
          rates['EUR'] = eurBrl / rates['BRL'];
          console.log(`   ✅ BACEN EUR/BRL: ${eurBrl} (EUR/USD: ${rates['EUR'].toFixed(4)})`);
        }
      }
    } catch (error) {
      console.error('   ⚠️  BACEN EUR failed');
    }

    // Fetch other major currencies
    const bacenCurrencies = ['GBP', 'JPY', 'CHF', 'CAD', 'AUD'];

    for (const currency of bacenCurrencies) {
      try {
        const url = `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='${currency}'&@dataCotacao='${dateStr}'&$format=json`;
        const response = await axios.get(url, { timeout: 10000 });

        if (response.data.value && response.data.value.length > 0) {
          const currencyBrl = response.data.value[0].cotacaoCompra;
          if (rates['BRL']) {
            rates[currency] = currencyBrl / rates['BRL'];
            console.log(`   ✅ BACEN ${currency}: ${rates[currency].toFixed(4)} per USD`);
          }
        }
      } catch (error) {
        // Silently skip if currency not available
      }
    }

    console.log(`   ✅ BACEN: Fetched ${Object.keys(rates).length} rates`);

    return rates;
  } catch (error) {
    console.error('   ⚠️  BACEN fetch failed:', error);
    return {};
  }
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function saveExchangeRates(pool: Pool, rates: ExchangeRate[]): Promise<number> {
  let inserted = 0;

  for (const rate of rates) {
    try {
      await pool.query(`
        INSERT INTO sofia.currency_rates (
          currency_code,
          currency_name,
          rate_to_usd,
          rate_from_usd,
          source,
          valid_from
        )
        VALUES ($1, $2, $3, $4, $5, CURRENT_DATE)
        ON CONFLICT (currency_code, valid_from) DO UPDATE SET
          rate_to_usd = EXCLUDED.rate_to_usd,
          rate_from_usd = EXCLUDED.rate_from_usd,
          fetched_at = NOW()
      `, [
        rate.currency_code,
        rate.currency_name,
        rate.rate_to_usd,
        rate.rate_from_usd,
        rate.source
      ]);

      inserted++;
    } catch (error) {
      console.error(`   ⚠️  Error saving ${rate.currency_code}:`, error);
    }
  }

  return inserted;
}

// ============================================================================
// MAIN COLLECTOR
// ============================================================================

async function main() {
  console.log('='.repeat(70));
  console.log('💱 CURRENCY EXCHANGE RATES COLLECTOR');
  console.log('='.repeat(70));

  const pool = new Pool(dbConfig);
  const rates: ExchangeRate[] = [];

  try {
    // Fetch from BACEN first (primary source for BRL and major pairs)
    const bacenRates = await fetchFromBACEN();

    // Fetch from ExchangeRate API (comprehensive fallback)
    const exRates = await fetchFromExchangeRateAPI();

    // USD itself
    rates.push({
      currency_code: 'USD',
      currency_name: 'US Dollar',
      rate_to_usd: 1.0,
      rate_from_usd: 1.0,
      source: 'base_currency'
    });

    // Process all currencies - prefer BACEN for available currencies
    for (const currency of CURRENCIES) {
      if (currency.code === 'USD') continue;  // Already added

      let rateFromUSD: number | null = null;
      let source = 'exchangerate-api';

      // Prefer BACEN for BRL and currencies it provides
      if (bacenRates[currency.code]) {
        rateFromUSD = bacenRates[currency.code];
        source = 'bacen';
      } else if (exRates[currency.code]) {
        rateFromUSD = exRates[currency.code];
        source = 'exchangerate-api';
      }

      if (rateFromUSD) {
        rates.push({
          currency_code: currency.code,
          currency_name: currency.name,
          rate_to_usd: 1 / rateFromUSD,       // How much USD 1 unit equals
          rate_from_usd: rateFromUSD,         // How much of currency 1 USD equals
          source: source
        });
      }
    }

    console.log(`\n📊 Total rates collected: ${rates.length}`);

    // Save to database
    console.log('\n💾 Saving to database...');
    const inserted = await saveExchangeRates(pool, rates);

    console.log(`\n✅ Saved ${inserted} exchange rates`);
    console.log('='.repeat(70));

    // Show sample rates
    console.log('\n📈 Sample Rates (to USD):');
    rates.slice(0, 10).forEach(r => {
      console.log(`   ${r.currency_code}: ${r.rate_to_usd.toFixed(6)} (1 ${r.currency_code} = ${r.rate_to_usd.toFixed(4)} USD)`);
    });

  } catch (error) {
    console.error('\n❌ Error:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

export { main as collectCurrencyRates };
