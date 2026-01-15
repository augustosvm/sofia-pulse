/**
 * Country Extractor - NLP-based country detection from text
 *
 * Extracts country information from funding news articles, product descriptions, etc.
 * Uses multiple strategies:
 * 1. Direct country mentions ("based in Germany", "French startup")
 * 2. City mentions ("San Francisco-based", "London startup")
 * 3. Company HQ patterns ("headquartered in Tokyo")
 * 4. Nationality adjectives ("Brazilian fintech", "Israeli company")
 */

// Country patterns: nationality adjective -> country name
const NATIONALITY_TO_COUNTRY: Record<string, string> = {
  // Americas
  'american': 'USA',
  'us': 'USA',
  'u.s.': 'USA',
  'united states': 'USA',
  'canadian': 'Canada',
  'mexican': 'Mexico',
  'brazilian': 'Brazil',
  'argentinian': 'Argentina',
  'argentine': 'Argentina',
  'chilean': 'Chile',
  'colombian': 'Colombia',
  'peruvian': 'Peru',

  // Europe
  'british': 'United Kingdom',
  'uk': 'United Kingdom',
  'english': 'United Kingdom',
  'scottish': 'United Kingdom',
  'french': 'France',
  'german': 'Germany',
  'spanish': 'Spain',
  'italian': 'Italy',
  'dutch': 'Netherlands',
  'belgian': 'Belgium',
  'swiss': 'Switzerland',
  'austrian': 'Austria',
  'swedish': 'Sweden',
  'norwegian': 'Norway',
  'danish': 'Denmark',
  'finnish': 'Finland',
  'polish': 'Poland',
  'portuguese': 'Portugal',
  'irish': 'Ireland',
  'greek': 'Greece',
  'czech': 'Czech Republic',
  'romanian': 'Romania',
  'hungarian': 'Hungary',
  'ukrainian': 'Ukraine',
  'estonian': 'Estonia',
  'latvian': 'Latvia',
  'lithuanian': 'Lithuania',

  // Asia
  'chinese': 'China',
  'japanese': 'Japan',
  'korean': 'South Korea',
  'south korean': 'South Korea',
  'indian': 'India',
  'singaporean': 'Singapore',
  'indonesian': 'Indonesia',
  'malaysian': 'Malaysia',
  'thai': 'Thailand',
  'vietnamese': 'Vietnam',
  'filipino': 'Philippines',
  'taiwanese': 'Taiwan',
  'hong kong': 'Hong Kong',

  // Middle East
  'israeli': 'Israel',
  'emirati': 'UAE',
  'uae': 'UAE',
  'dubai': 'UAE',
  'saudi': 'Saudi Arabia',
  'turkish': 'Turkey',
  'iranian': 'Iran',
  'egyptian': 'Egypt',

  // Oceania
  'australian': 'Australia',
  'new zealand': 'New Zealand',
  'kiwi': 'New Zealand',

  // Africa
  'south african': 'South Africa',
  'nigerian': 'Nigeria',
  'kenyan': 'Kenya',
  'egyptian': 'Egypt',
  'moroccan': 'Morocco',
};

// Major cities -> country mapping
const CITY_TO_COUNTRY: Record<string, string> = {
  // USA
  'san francisco': 'USA',
  'sf': 'USA',
  'silicon valley': 'USA',
  'new york': 'USA',
  'nyc': 'USA',
  'manhattan': 'USA',
  'brooklyn': 'USA',
  'los angeles': 'USA',
  'la': 'USA',
  'seattle': 'USA',
  'boston': 'USA',
  'austin': 'USA',
  'denver': 'USA',
  'chicago': 'USA',
  'miami': 'USA',
  'atlanta': 'USA',
  'washington dc': 'USA',
  'palo alto': 'USA',
  'mountain view': 'USA',
  'menlo park': 'USA',
  'cupertino': 'USA',
  'san jose': 'USA',
  'santa clara': 'USA',
  'redwood city': 'USA',
  'sunnyvale': 'USA',

  // UK
  'london': 'United Kingdom',
  'manchester': 'United Kingdom',
  'edinburgh': 'United Kingdom',
  'cambridge': 'United Kingdom',
  'oxford': 'United Kingdom',
  'bristol': 'United Kingdom',

  // Europe
  'paris': 'France',
  'berlin': 'Germany',
  'munich': 'Germany',
  'frankfurt': 'Germany',
  'amsterdam': 'Netherlands',
  'stockholm': 'Sweden',
  'copenhagen': 'Denmark',
  'oslo': 'Norway',
  'helsinki': 'Finland',
  'zurich': 'Switzerland',
  'geneva': 'Switzerland',
  'dublin': 'Ireland',
  'barcelona': 'Spain',
  'madrid': 'Spain',
  'milan': 'Italy',
  'rome': 'Italy',
  'lisbon': 'Portugal',
  'vienna': 'Austria',
  'warsaw': 'Poland',
  'prague': 'Czech Republic',
  'brussels': 'Belgium',
  'tallinn': 'Estonia',

  // Asia
  'tokyo': 'Japan',
  'osaka': 'Japan',
  'beijing': 'China',
  'shanghai': 'China',
  'shenzhen': 'China',
  'hangzhou': 'China',
  'hong kong': 'Hong Kong',
  'singapore': 'Singapore',
  'seoul': 'South Korea',
  'bangalore': 'India',
  'bengaluru': 'India',
  'mumbai': 'India',
  'delhi': 'India',
  'hyderabad': 'India',
  'tel aviv': 'Israel',
  'jerusalem': 'Israel',
  'dubai': 'UAE',
  'abu dhabi': 'UAE',
  'taipei': 'Taiwan',
  'jakarta': 'Indonesia',
  'kuala lumpur': 'Malaysia',
  'bangkok': 'Thailand',
  'ho chi minh': 'Vietnam',
  'hanoi': 'Vietnam',

  // Oceania
  'sydney': 'Australia',
  'melbourne': 'Australia',
  'auckland': 'New Zealand',

  // Latin America
  'sao paulo': 'Brazil',
  'são paulo': 'Brazil',
  'rio de janeiro': 'Brazil',
  'rio': 'Brazil',
  'mexico city': 'Mexico',
  'buenos aires': 'Argentina',
  'bogota': 'Colombia',
  'santiago': 'Chile',
  'lima': 'Peru',

  // Africa
  'johannesburg': 'South Africa',
  'cape town': 'South Africa',
  'lagos': 'Nigeria',
  'nairobi': 'Kenya',
  'cairo': 'Egypt',
};

// Direct country name mentions
const COUNTRY_NAMES: string[] = [
  'USA', 'United States', 'America',
  'Canada', 'Mexico', 'Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru',
  'United Kingdom', 'UK', 'Britain', 'England',
  'France', 'Germany', 'Spain', 'Italy', 'Netherlands', 'Belgium',
  'Switzerland', 'Austria', 'Sweden', 'Norway', 'Denmark', 'Finland',
  'Poland', 'Portugal', 'Ireland', 'Greece', 'Czech Republic',
  'Romania', 'Hungary', 'Ukraine', 'Estonia', 'Latvia', 'Lithuania',
  'China', 'Japan', 'South Korea', 'Korea', 'India', 'Singapore',
  'Indonesia', 'Malaysia', 'Thailand', 'Vietnam', 'Philippines', 'Taiwan',
  'Hong Kong', 'Israel', 'UAE', 'Saudi Arabia', 'Turkey', 'Egypt',
  'Australia', 'New Zealand',
  'South Africa', 'Nigeria', 'Kenya', 'Morocco',
];

// Normalize country names
const COUNTRY_NORMALIZE: Record<string, string> = {
  'united states': 'USA',
  'america': 'USA',
  'uk': 'United Kingdom',
  'britain': 'United Kingdom',
  'england': 'United Kingdom',
  'korea': 'South Korea',
};

/**
 * Extract country from text using NLP patterns
 *
 * @param text - Text to analyze (title, description, etc.)
 * @returns Country name or null if not detected
 */
export function extractCountryFromText(text: string): string | null {
  if (!text) return null;

  const textLower = text.toLowerCase();

  // Strategy 1: Look for "based in [City/Country]" patterns
  const basedInPatterns = [
    /(?:based|headquartered|hq)\s+in\s+([a-z\s]+?)(?:\.|,|$|\s+(?:and|has|is|with|that|which|to|for))/gi,
    /([a-z\s]+?)-based\s+(?:startup|company|firm|fintech|healthtech|edtech|saas)/gi,
    /(?:startup|company|firm)\s+(?:based|from|in)\s+([a-z\s]+?)(?:\.|,|$)/gi,
  ];

  for (const pattern of basedInPatterns) {
    const matches = Array.from(text.matchAll(pattern));
    for (const match of matches) {
      const location = match[1]?.toLowerCase().trim();
      if (!location) continue;

      // Check if it's a city
      if (CITY_TO_COUNTRY[location]) {
        return CITY_TO_COUNTRY[location];
      }

      // Check if it's a country name
      for (const country of COUNTRY_NAMES) {
        if (location.includes(country.toLowerCase())) {
          return COUNTRY_NORMALIZE[country.toLowerCase()] || country;
        }
      }
    }
  }

  // Strategy 2: Look for nationality adjectives
  for (const [nationality, country] of Object.entries(NATIONALITY_TO_COUNTRY)) {
    // Look for patterns like "French startup", "Brazilian fintech"
    const nationalityPattern = new RegExp(
      `\\b${nationality}\\s+(?:startup|company|firm|fintech|healthtech|edtech|saas|unicorn|tech)`,
      'i'
    );
    if (nationalityPattern.test(textLower)) {
      return country;
    }
  }

  // Strategy 3: Look for city mentions with context
  for (const [city, country] of Object.entries(CITY_TO_COUNTRY)) {
    // Patterns like "San Francisco startup" or "from London"
    const cityPatterns = [
      new RegExp(`\\b${city}\\s+(?:startup|company|firm|based)`, 'i'),
      new RegExp(`(?:from|in|of)\\s+${city}\\b`, 'i'),
    ];

    for (const pattern of cityPatterns) {
      if (pattern.test(textLower)) {
        return country;
      }
    }
  }

  // Strategy 4: Direct country mentions with context
  for (const country of COUNTRY_NAMES) {
    const countryLower = country.toLowerCase();
    const countryPatterns = [
      new RegExp(`\\b${countryLower}\\s+(?:startup|company|firm)`, 'i'),
      new RegExp(`(?:from|in|of)\\s+${countryLower}\\b`, 'i'),
    ];

    for (const pattern of countryPatterns) {
      if (pattern.test(textLower)) {
        return COUNTRY_NORMALIZE[countryLower] || country;
      }
    }
  }

  return null;
}

/**
 * Extract country from website TLD
 *
 * @param website - Website URL
 * @returns Country name or null
 */
export function extractCountryFromWebsite(website: string | null | undefined): string | null {
  if (!website) return null;

  try {
    const url = new URL(website.startsWith('http') ? website : `https://${website}`);
    const domain = url.hostname.toLowerCase();

    // Extract TLD
    const parts = domain.split('.');
    const tld = parts[parts.length - 1];

    // Country code TLDs
    const TLD_TO_COUNTRY: Record<string, string> = {
      'us': 'USA',
      'uk': 'United Kingdom',
      'co.uk': 'United Kingdom',
      'de': 'Germany',
      'fr': 'France',
      'es': 'Spain',
      'it': 'Italy',
      'nl': 'Netherlands',
      'be': 'Belgium',
      'ch': 'Switzerland',
      'at': 'Austria',
      'se': 'Sweden',
      'no': 'Norway',
      'dk': 'Denmark',
      'fi': 'Finland',
      'pl': 'Poland',
      'pt': 'Portugal',
      'ie': 'Ireland',
      'br': 'Brazil',
      'mx': 'Mexico',
      'ar': 'Argentina',
      'cl': 'Chile',
      'co': 'Colombia',
      'cn': 'China',
      'jp': 'Japan',
      'kr': 'South Korea',
      'in': 'India',
      'sg': 'Singapore',
      'au': 'Australia',
      'nz': 'New Zealand',
      'il': 'Israel',
      'ae': 'UAE',
      'za': 'South Africa',
      'ng': 'Nigeria',
      'ke': 'Kenya',
    };

    // Check compound TLDs first (e.g., co.uk)
    if (parts.length >= 3) {
      const compoundTld = `${parts[parts.length - 2]}.${tld}`;
      if (TLD_TO_COUNTRY[compoundTld]) {
        return TLD_TO_COUNTRY[compoundTld];
      }
    }

    // Check simple TLD
    if (TLD_TO_COUNTRY[tld]) {
      return TLD_TO_COUNTRY[tld];
    }

    // .com, .io, .ai, etc. are often US companies but not always
    // Return null for generic TLDs - let text analysis decide
    return null;
  } catch {
    return null;
  }
}

/**
 * Combined country extraction using all strategies
 *
 * @param params - Object with text and optional website
 * @returns Country name or 'USA' as default (most TechCrunch coverage is US)
 */
export function extractCountry(params: {
  title?: string | null;
  description?: string | null;
  website?: string | null;
  defaultCountry?: string;
}): string {
  const { title, description, website, defaultCountry = 'USA' } = params;

  // Try text extraction first (most reliable)
  const textContent = [title, description].filter(Boolean).join(' ');
  const textCountry = extractCountryFromText(textContent);
  if (textCountry) {
    return textCountry;
  }

  // Try website TLD
  const websiteCountry = extractCountryFromWebsite(website);
  if (websiteCountry) {
    return websiteCountry;
  }

  // Default (TechCrunch primarily covers US companies)
  return defaultCountry;
}

export default extractCountry;
