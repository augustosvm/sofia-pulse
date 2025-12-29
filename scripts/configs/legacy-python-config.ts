
/**
 * Legacy Python Collectors Configuration
 * 
 * Maps legacy Python scripts to the Unified Architecture.
 * Bridges via: python-bridge-collector.ts
 */

export interface PythonCollectorConfig {
    name: string;
    description: string;
    script: string;
    schedule: string; // Cron suggestion
    category: 'economic' | 'social' | 'health' | 'security' | 'tech' | 'other';
}

export const collectors: Record<string, PythonCollectorConfig> = {
    // --- CONFLICT & SECURITY ---
    'acled-conflicts': { name: 'acled-conflicts', description: 'ACLED Conflict Data', script: 'scripts/collect-acled-conflicts.py', schedule: '0 2 * * *', category: 'security' },
    'brazil-security': { name: 'brazil-security', description: 'Brazil Security Data', script: 'scripts/collect-brazil-security.py', schedule: '0 3 * * *', category: 'security' },
    'world-security': { name: 'world-security', description: 'Global Security Index', script: 'scripts/collect-world-security.py', schedule: '0 3 * * *', category: 'security' },
    'geopolitical-impacts': { name: 'geopolitical-impacts', description: 'Geopolitical Impact Analysis', script: 'scripts/collect-geopolitical-impacts.py', schedule: '0 4 * * *', category: 'security' },

    // --- ECONOMIC ---
    'bacen-sgs': { name: 'bacen-sgs', description: 'BACEN Time Series', script: 'scripts/collect-bacen-sgs.py', schedule: '0 5 * * *', category: 'economic' },
    'central-banks-women': { name: 'central-banks-women', description: 'Women in Central Banks', script: 'scripts/collect-central-banks-women.py', schedule: '0 0 1 * *', category: 'economic' },
    'commodity-prices': { name: 'commodity-prices', description: 'Global Commodity Prices', script: 'scripts/collect-commodity-prices.py', schedule: '0 6 * * *', category: 'economic' },
    'cni-indicators': { name: 'cni-indicators', description: 'CNI Industry Indicators', script: 'scripts/collect-cni-indicators.py', schedule: '0 0 5 * *', category: 'economic' },
    'electricity-consumption': { name: 'electricity-consumption', description: 'Global Electricity Consumption', script: 'scripts/collect-electricity-consumption.py', schedule: '0 0 4 * *', category: 'economic' },
    'energy-global': { name: 'energy-global', description: 'Global Energy Stats', script: 'scripts/collect-energy-global.py', schedule: '0 0 4 * *', category: 'economic' },
    'fao-agriculture': { name: 'fao-agriculture', description: 'FAO Agriculture Data', script: 'scripts/collect-fao-agriculture.py', schedule: '0 0 3 * *', category: 'economic' },
    'fiesp-data': { name: 'fiesp-data', description: 'FIESP Industry Indicators (Sensor + INA)', script: 'scripts/collect-fiesp-data.py', schedule: '0 9 * * *', category: 'economic' },
    'ibge-api': { name: 'ibge-api', description: 'IBGE Brazil Statistics', script: 'scripts/collect-ibge-api.py', schedule: '0 5 * * *', category: 'economic' },
    'ipea-api': { name: 'ipea-api', description: 'IPEA Economic Data', script: 'scripts/collect-ipea-api.py', schedule: '0 0 5 * *', category: 'economic' },
    'mdic-comexstat': { name: 'mdic-comexstat', description: 'MDIC ComexStat Trade', script: 'scripts/collect-mdic-comexstat.py', schedule: '0 9 * * *', category: 'economic' },
    'port-traffic': { name: 'port-traffic', description: 'Global Port Traffic', script: 'scripts/collect-port-traffic.py', schedule: '0 0 2 * *', category: 'economic' },
    'semiconductor-sales': { name: 'semiconductor-sales', description: 'Semiconductor Sales', script: 'scripts/collect-semiconductor-sales.py', schedule: '0 0 1 * *', category: 'economic' },
    'socioeconomic-indicators': { name: 'socioeconomic-indicators', description: 'General Socioeconomic Indicators', script: 'scripts/collect-socioeconomic-indicators.py', schedule: '0 0 1 * *', category: 'economic' },
    'wto-trade': { name: 'wto-trade', description: 'WTO Trade Data', script: 'scripts/collect-wto-trade.py', schedule: '0 0 1 * *', category: 'economic' },

    // --- SOCIAL & HEALTH ---
    'drugs-data': { name: 'drugs-data', description: 'UNODC Drugs Data', script: 'scripts/collect-drugs-data.py', schedule: '0 0 1 1 *', category: 'health' },
    'who-health': { name: 'who-health', description: 'WHO Global Health', script: 'scripts/collect-who-health.py', schedule: '0 0 1 * *', category: 'health' },
    'religion-data': { name: 'religion-data', description: 'Global Religion Stats', script: 'scripts/collect-religion-data.py', schedule: '0 0 1 1 *', category: 'social' },
    'unicef': { name: 'unicef', description: 'UNICEF Child Data', script: 'scripts/collect-unicef.py', schedule: '0 0 1 * *', category: 'social' },
    'un-sdg': { name: 'un-sdg', description: 'UN SDG Goals', script: 'scripts/collect-un-sdg.py', schedule: '0 0 1 * *', category: 'social' },
    'world-ngos': { name: 'world-ngos', description: 'World NGOs Directory', script: 'scripts/collect-world-ngos.py', schedule: '0 0 1 1 *', category: 'social' },

    // --- WOMEN & GENDER ---
    'women-brazil': { name: 'women-brazil', description: 'Women in Brazil Stats', script: 'scripts/collect-women-brazil.py', schedule: '0 0 1 * *', category: 'social' },
    'women-eurostat': { name: 'women-eurostat', description: 'Women in EU (Eurostat)', script: 'scripts/collect-women-eurostat.py', schedule: '0 0 1 * *', category: 'social' },
    'women-fred': { name: 'women-fred', description: 'Women Labor Data (FRED)', script: 'scripts/collect-women-fred.py', schedule: '0 0 1 * *', category: 'social' },
    'women-ilostat': { name: 'women-ilostat', description: 'Women Labor (ILO)', script: 'scripts/collect-women-ilostat.py', schedule: '0 0 1 * *', category: 'social' },
    'women-world-bank': { name: 'women-world-bank', description: 'Women Global Data (WB)', script: 'scripts/collect-women-world-bank.py', schedule: '0 0 1 * *', category: 'social' },
    'world-bank-gender': { name: 'world-bank-gender', description: 'WB Gender Portal', script: 'scripts/collect-world-bank-gender.py', schedule: '0 0 1 * *', category: 'social' },

    // --- SPORTS ---
    'sports-federations': { name: 'sports-federations', description: 'Intl Sports Federations', script: 'scripts/collect-sports-federations.py', schedule: '0 0 1 * *', category: 'social' },
    'sports-regional': { name: 'sports-regional', description: 'Regional Sports Participation', script: 'scripts/collect-sports-regional.py', schedule: '0 0 1 * *', category: 'social' },
    'world-sports': { name: 'world-sports', description: 'World Sports Participation', script: 'scripts/collect-world-sports.py', schedule: '0 0 1 * *', category: 'social' },

    // --- JOBS & TECH (Legacy) ---
    'careerjet-api': { name: 'careerjet-api', description: 'Careerjet Jobs', script: 'scripts/collect-careerjet-api.py', schedule: '0 10 * * *', category: 'economic' },
    'freejobs-api': { name: 'freejobs-api', description: 'Free Jobs API', script: 'scripts/collect-freejobs-api.py', schedule: '0 10 * * *', category: 'economic' },
    'infojobs-brasil': { name: 'infojobs-brasil', description: 'InfoJobs Brasil Web Scraper', script: 'scripts/collect-infojobs-web-scraper.py', schedule: '0 */6 * * *', category: 'economic' },
    'rapidapi-activejobs': { name: 'rapidapi-activejobs', description: 'ActiveJobs API', script: 'scripts/collect-rapidapi-activejobs.py', schedule: '0 10 * * *', category: 'economic' },
    'rapidapi-linkedin': { name: 'rapidapi-linkedin', description: 'LinkedIn Jobs API', script: 'scripts/collect-rapidapi-linkedin.py', schedule: '0 10 * * *', category: 'economic' },
    'serpapi-googlejobs': { name: 'serpapi-googlejobs', description: 'Google Jobs Search', script: 'scripts/collect-serpapi-googlejobs.py', schedule: '0 10 * * *', category: 'economic' },
    'theirstack-api': { name: 'theirstack-api', description: 'Theirstack Tech Jobs', script: 'scripts/collect-theirstack-api.py', schedule: '0 10 * * *', category: 'economic' },

    // --- OTHER ---
    'hdx-humanitarian': { name: 'hdx-humanitarian', description: 'HDX Humanitarian Data', script: 'scripts/collect-hdx-humanitarian.py', schedule: '0 0 1 * *', category: 'social' },
    'cepal-latam': { name: 'cepal-latam', description: 'CEPAL Latin America', script: 'scripts/collect-cepal-latam.py', schedule: '0 0 1 * *', category: 'economic' },
    'brazil-ministries': { name: 'brazil-ministries', description: 'Brazil Ministries Data', script: 'scripts/collect-brazil-ministries.py', schedule: '0 0 1 * *', category: 'other' },
    'world-tourism': { name: 'world-tourism', description: 'World Tourism Stats', script: 'scripts/collect-world-tourism.py', schedule: '0 0 1 * *', category: 'economic' },

    // --- FUNDING & STARTUPS ---
    'sec-edgar-funding': { name: 'sec-edgar-funding', description: 'SEC Edgar Funding Data', script: 'scripts/collect-sec-edgar-funding.py', schedule: '0 0 2 * *', category: 'economic' },
    'yc-companies': { name: 'yc-companies', description: 'Y Combinator Companies', script: 'scripts/collect-yc-companies.py', schedule: '0 0 1 * *', category: 'economic' },
};
