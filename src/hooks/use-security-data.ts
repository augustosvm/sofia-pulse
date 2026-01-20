// hooks/use-security-data.ts
'use client';

import { useState, useEffect, useCallback } from 'react';

// Types for Security API
export interface SecurityCountry {
  country_code: string;
  country_name: string;
  acute_risk: number;
  structural_risk: number;
  total_risk: number;
  risk_level: string;
  coverage_score_global: number;
  sources_used: string[];
  last_update: string | null;
  warning: string | null;
  breakdown: {
    total_incidents: number;
    fatalities: number;
    indicators_count: number;
  };
}

export interface SecurityCountriesResponse {
  countries: SecurityCountry[];
  metadata: {
    total_countries: number;
    avg_coverage: number;
  };
}

// Base URL for Security API - use env var or relative path
const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // Check for env var first
    const envBase = process.env.NEXT_PUBLIC_SECURITY_API_BASE;
    if (envBase) return envBase;
    // Default to relative path (assumes same origin or proxy configured)
    return '';
  }
  return '';
};

export function useSecurityCountries() {
  const [data, setData] = useState<SecurityCountriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/security/countries`);

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
      }

      const json: SecurityCountriesResponse = await response.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
      console.error('Error fetching security countries:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Create a Map keyed by ISO2 country code for quick lookups
  const countriesMap = new Map<string, SecurityCountry>();
  if (data?.countries) {
    for (const country of data.countries) {
      countriesMap.set(country.country_code, country);
    }
  }

  return {
    data,
    countriesMap,
    loading,
    error,
    refetch: fetchData,
  };
}

// Hook for security map points (ACLED data)
export interface SecurityPoint {
  latitude: number;
  longitude: number;
  source: string;
  severity_norm: number;
  country_code: string;
  country_name: string;
  event_count: number;
  fatalities: number;
  coverage_score: number;
  coverage_scope: string;
  event_date: string | null;
  admin1: string;
  city: string;
  warning: string | null;
}

export interface SecurityMapResponse {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: {
      type: 'Point';
      coordinates: [number, number];
    };
    properties: SecurityPoint;
  }>;
  metadata: {
    total_points: number;
    sources_used: string[];
    zoom_level: number | null;
    limit_applied: number;
  };
}

export function useSecurityMap(options?: {
  zoom?: number;
  country?: string;
  bbox?: string;
  sources?: string;
}) {
  const [data, setData] = useState<SecurityMapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const baseUrl = getApiBaseUrl();
      const params = new URLSearchParams();

      if (options?.zoom !== undefined) params.set('zoom', String(options.zoom));
      if (options?.country) params.set('country', options.country);
      if (options?.bbox) params.set('bbox', options.bbox);
      if (options?.sources) params.set('sources', options.sources);

      const url = `${baseUrl}/api/security/map${params.toString() ? '?' + params.toString() : ''}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
      }

      const json: SecurityMapResponse = await response.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
      console.error('Error fetching security map:', err);
    } finally {
      setLoading(false);
    }
  }, [options?.zoom, options?.country, options?.bbox, options?.sources]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}
