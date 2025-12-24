/**
 * Developer Tools Collector Configs
 *
 * Tracks developer tool adoption as a leading indicator for tech trends.
 *
 * Sources:
 * - VS Code Marketplace (extensions downloads, ratings)
 * - Chrome Web Store (dev tools extensions)
 * - npm Weekly Downloads (already covered in tech-trends-config)
 *
 * Why this matters:
 * - Tool adoption predicts framework/language trends
 * - Extension downloads = developer interest
 * - Can predict which tech stacks will boom
 */

import type { DeveloperToolCollectorConfig } from '../collectors/developer-tools-collector.js';

// ============================================================================
// VS CODE MARKETPLACE
// ============================================================================

export const vscodeMarketplace: DeveloperToolCollectorConfig = {
  name: 'vscode-marketplace',
  displayName: '🔌 VS Code Marketplace',
  url: 'https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json;api-version=7.1-preview.1',
  },
  requestBody: {
    filters: [{
      criteria: [
        { filterType: 8, value: 'Microsoft.VisualStudio.Code' },
        { filterType: 10, value: 'target:"Microsoft.VisualStudio.Code"' },
        { filterType: 12, value: '37888' } // 4096 (downloads) + 32768 (trending)
      ],
      pageNumber: 1,
      pageSize: 100,
      sortBy: 4, // Installs descending
      sortOrder: 2
    }],
    assetTypes: [],
    flags: 950
  },
  timeout: 30000,
  parseResponse: async (data) => {
    const extensions = data?.results?.[0]?.extensions || [];

    return extensions.map((ext: any) => {
      const stats = ext.statistics || [];
      const installs = stats.find((s: any) => s.statisticName === 'install')?.value || 0;
      const downloads = stats.find((s: any) => s.statisticName === 'updateCount')?.value || 0;
      const rating = stats.find((s: any) => s.statisticName === 'averagerating')?.value || 0;
      const ratingCount = stats.find((s: any) => s.statisticName === 'ratingcount')?.value || 0;

      const versions = ext.versions || [];
      const latestVersion = versions[0] || {};
      const properties = latestVersion.properties || [];

      const category = properties.find((p: any) => p.key === 'Microsoft.VisualStudio.Code.ExtensionCategory')?.value || 'Other';
      const tags = ext.tags || [];

      return {
        tool_name: ext.displayName || ext.extensionName,
        tool_id: ext.extensionId,
        platform: 'vscode',
        category,
        downloads: installs + downloads,
        rating,
        rating_count: ratingCount,
        version: latestVersion.version,
        publisher: ext.publisher?.displayName || ext.publisher?.publisherName,
        description: ext.shortDescription?.slice(0, 500),
        tags: tags.join(', ').slice(0, 255),
        homepage_url: `https://marketplace.visualstudio.com/items?itemName=${ext.publisher?.publisherName}.${ext.extensionName}`,
        source: 'vscode-marketplace',
      };
    });
  },
  schedule: '0 14 * * *', // Daily at 2pm UTC
  description: 'VS Code Marketplace trending extensions (leading indicator for tech stacks)',
  allowWithoutAuth: true,
};

// ============================================================================
// CHROME WEB STORE (Dev Tools)
// ============================================================================

export const chromeWebStore: DeveloperToolCollectorConfig = {
  name: 'chrome-webstore',
  displayName: '🌐 Chrome Web Store (Dev Tools)',
  url: 'https://chrome.google.com/webstore/ajax/item',
  timeout: 30000,
  parseResponse: async (data) => {
    // Chrome Web Store doesn't have a public API
    // We'll use the Chrome Web Store Discovery API (unofficial)
    // For now, return sample structure - can be implemented with scraping or unofficial API

    // Note: This would need proper implementation with either:
    // 1. Chrome Web Store Crawler API (if available)
    // 2. Scraping with Cheerio/Puppeteer
    // 3. Alternative data source

    console.warn('Chrome Web Store collector needs implementation - placeholder for now');
    return [];
  },
  schedule: null, // Disabled for now until proper API/scraping is implemented
  description: 'Chrome Web Store developer tools extensions (disabled - needs implementation)',
  allowWithoutAuth: true,
};

// ============================================================================
// JETBRAINS MARKETPLACE
// ============================================================================

export const jetbrainsMarketplace: DeveloperToolCollectorConfig = {
  name: 'jetbrains-marketplace',
  displayName: '🧰 JetBrains Marketplace',
  url: 'https://plugins.jetbrains.com/api/searchPlugins',
  params: {
    max: 100,
    orderBy: 'downloads',
    build: 'IU-233.11799.241', // Latest IntelliJ IDEA version
  },
  timeout: 30000,
  parseResponse: async (data) => {
    const plugins = Array.isArray(data) ? data : [];

    return plugins.map((plugin: any) => ({
      tool_name: plugin.name,
      tool_id: String(plugin.id),
      platform: 'jetbrains',
      category: plugin.category || 'Other',
      downloads: plugin.downloads || 0,
      rating: plugin.rating || 0,
      rating_count: plugin.votes || 0,
      version: plugin.version,
      publisher: plugin.vendor?.name || plugin.organization,
      description: plugin.description?.slice(0, 500),
      tags: plugin.tags?.join(', ').slice(0, 255) || '',
      homepage_url: `https://plugins.jetbrains.com/plugin/${plugin.id}`,
      source: 'jetbrains-marketplace',
    }));
  },
  schedule: '0 15 * * *', // Daily at 3pm UTC
  description: 'JetBrains Marketplace trending plugins (Java, Kotlin, Python IDE tools)',
  allowWithoutAuth: true,
};

// ============================================================================
// EXPORT ALL COLLECTORS
// ============================================================================

export const developerToolsCollectors = {
  'vscode-marketplace': vscodeMarketplace,
  'jetbrains-marketplace': jetbrainsMarketplace,
  // 'chrome-webstore': chromeWebStore, // Disabled until implementation
};
