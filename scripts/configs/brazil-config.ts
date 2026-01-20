/**
 * Brazil Data Collectors Configs
 *
 * Configs for MDIC and FIESP data:
 * - MDIC ComexStat (Regionalized Import/Export)
 * - FIESP Sensor & INA (Industrial Indicators)
 *
 * Each config specifies:
 * - Command to execute (Python script)
 * - Schedule (cron)
 * - Description
 */

export interface BrazilCollectorConfig {
    name: string;
    displayName: string;
    scriptPath: string; // Path relative to project root
    schedule?: string;
    description?: string;
}

export const mdicRegional: BrazilCollectorConfig = {
    name: 'mdic-regional',
    displayName: '🇧🇷 MDIC ComexStat (Regional)',
    scriptPath: 'scripts/collect-mdic-comexstat.py',
    schedule: '0 9 * * *', // Daily at 06:00 BRT (09:00 UTC)
    description: 'Regionalized trade data (State/City) for tech products',
};

export const fiespData: BrazilCollectorConfig = {
    name: 'fiesp-data',
    displayName: '🏭 FIESP Industrial Indicators',
    scriptPath: 'scripts/collect-fiesp-data.py',
    schedule: '0 9 1 * *', // Monthly on the 1st day at 06:00 BRT (09:00 UTC)
    description: 'Industrial Sentiment (Sensor) and Activity (INA) indexes',
};

export const cniIndicators: BrazilCollectorConfig = {
    name: 'cni-indicators',
    displayName: '🏭 CNI Industrial Indicators',
    scriptPath: 'scripts/collect-cni-indicators.py',
    schedule: '0 9 5 * *', // Monthly on the 5th day at 06:00 BRT (09:00 UTC)
    description: 'CNI industrial indicators (production, sales, market sentiment)',
};

export const collectors = {
    'mdic-regional': mdicRegional,
    'fiesp-data': fiespData,
    'cni-indicators': cniIndicators,
};
