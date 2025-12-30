/**
 * Economic Data Collectors Configuration
 *
 * Collectors for economic indicators, currency rates, and financial data
 * that can be used across multiple analyses (jobs, funding, trade, etc.)
 */

export interface EconomicCollectorConfig {
  name: string;
  description: string;
  scriptPath: string;
  schedule: string;  // Cron format
  category: 'currency' | 'indicators' | 'trade';
}

export const collectors: Record<string, EconomicCollectorConfig> = {
  'currency-rates': {
    name: 'currency-rates',
    description: 'Daily exchange rates for global currency normalization',
    scriptPath: 'scripts/collect-currency-rates.ts',
    schedule: '0 1 * * *',  // Daily at 1am (after midnight data refresh)
    category: 'currency'
  },
};

export default collectors;
