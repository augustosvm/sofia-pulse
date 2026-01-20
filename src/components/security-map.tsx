// components/security-map.tsx
'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useSecurityCountries, SecurityCountry } from '@/hooks/use-security-data';

// MapLibre types - we'll use dynamic import to avoid SSR issues
type MapLibreMap = any;
type MapLibreGl = any;

// Layer modes
type LayerMode = 'acled' | 'hybrid' | 'structural' | 'local';

// Risk color palette (5-step from green to red)
const RISK_COLORS = {
  0: '#22c55e',   // Low risk - green
  25: '#84cc16',  // Moderate - lime
  50: '#eab308',  // Elevated - yellow
  75: '#f97316',  // High - orange
  100: '#ef4444', // Critical - red
};

// Tooltip state
interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  country: SecurityCountry | null;
  iso2: string;
}

export function SecurityMap() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [activeLayer, setActiveLayer] = useState<LayerMode>('hybrid');
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    country: null,
    iso2: '',
  });
  const [mapLibreGl, setMapLibreGl] = useState<MapLibreGl | null>(null);

  // Fetch security countries data
  const { countriesMap, loading, error, data } = useSecurityCountries();

  // Dynamic import of maplibre-gl (avoid SSR issues)
  useEffect(() => {
    // Import CSS
    import('maplibre-gl/dist/maplibre-gl.css');
    // Import module
    import('maplibre-gl').then((module) => {
      setMapLibreGl(module.default);
    }).catch((err) => {
      console.error('Failed to load maplibre-gl:', err);
    });
  }, []);

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || !mapLibreGl || mapRef.current) return;

    const map = new mapLibreGl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: { 'background-color': '#0f172a' }, // slate-900
          },
        ],
      },
      center: [0, 20],
      zoom: 1.5,
      minZoom: 1,
      maxZoom: 12,
    });

    mapRef.current = map;

    map.on('load', () => {
      // Add countries GeoJSON source
      map.addSource('countries', {
        type: 'geojson',
        data: '/data/countries-110m.geojson',
        promoteId: 'ISO_A2', // Use ISO_A2 as feature id if 'id' not present
      });

      // Add countries fill layer (choropleth)
      map.addLayer({
        id: 'countries-fill',
        type: 'fill',
        source: 'countries',
        paint: {
          // Color based on feature-state risk value
          'fill-color': [
            'case',
            ['==', ['feature-state', 'risk_value'], null],
            '#374151', // gray-700 for no data
            [
              'interpolate',
              ['linear'],
              ['feature-state', 'risk_value'],
              0, RISK_COLORS[0],
              25, RISK_COLORS[25],
              50, RISK_COLORS[50],
              75, RISK_COLORS[75],
              100, RISK_COLORS[100],
            ],
          ],
          // Opacity based on coverage
          'fill-opacity': [
            'case',
            ['==', ['feature-state', 'coverage'], null],
            0.1, // No data
            ['>=', ['feature-state', 'coverage'], 75],
            0.85,
            ['>=', ['feature-state', 'coverage'], 50],
            0.65,
            ['>=', ['feature-state', 'coverage'], 30],
            0.45,
            0.25, // Low coverage
          ],
        },
      });

      // Add countries outline layer
      map.addLayer({
        id: 'countries-outline',
        type: 'line',
        source: 'countries',
        paint: {
          'line-color': '#64748b', // slate-500
          'line-width': 0.5,
          'line-opacity': 0.6,
        },
      });

      setMapLoaded(true);
      console.log('[SecurityMap] Map loaded, countries source added');
    });

    // Cleanup
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [mapLibreGl]);

  // Apply feature-state when data and map are ready
  useEffect(() => {
    if (!mapLoaded || !mapRef.current || !countriesMap.size) return;

    const map = mapRef.current;

    // Wait for source to be loaded
    const applyFeatureStates = () => {
      const source = map.getSource('countries');
      if (!source) {
        console.warn('[SecurityMap] Countries source not found');
        return;
      }

      let assignedCount = 0;

      // Apply feature-state for each country
      countriesMap.forEach((country, iso2) => {
        try {
          // Determine which risk value to use based on active layer
          const riskValue = activeLayer === 'structural'
            ? country.structural_risk
            : country.total_risk; // hybrid uses total_risk

          map.setFeatureState(
            { source: 'countries', id: iso2 },
            {
              risk_total: country.total_risk,
              risk_structural: country.structural_risk,
              risk_acute: country.acute_risk,
              risk_value: riskValue,
              coverage: country.coverage_score_global,
              warning: country.warning ? 1 : 0,
              name: country.country_name,
            }
          );
          assignedCount++;
        } catch (err) {
          // Feature might not exist in GeoJSON
        }
      });

      console.log(`[SecurityMap] Feature-state assigned to ${assignedCount} countries`);
    };

    // Check if source is loaded
    if (map.isSourceLoaded('countries')) {
      applyFeatureStates();
    } else {
      map.once('sourcedata', (e: any) => {
        if (e.sourceId === 'countries' && e.isSourceLoaded) {
          applyFeatureStates();
        }
      });
    }
  }, [mapLoaded, countriesMap, activeLayer]);

  // Update fill-color expression when layer mode changes
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;

    const map = mapRef.current;

    // Update the risk_value in feature-state based on active layer
    countriesMap.forEach((country, iso2) => {
      try {
        const riskValue = activeLayer === 'structural'
          ? country.structural_risk
          : country.total_risk;

        map.setFeatureState(
          { source: 'countries', id: iso2 },
          { risk_value: riskValue }
        );
      } catch (err) {
        // Feature might not exist
      }
    });

    // Show/hide choropleth layers
    const showChoropleth = activeLayer === 'hybrid' || activeLayer === 'structural';
    map.setLayoutProperty('countries-fill', 'visibility', showChoropleth ? 'visible' : 'none');
    map.setLayoutProperty('countries-outline', 'visibility', showChoropleth ? 'visible' : 'none');

  }, [activeLayer, mapLoaded, countriesMap]);

  // Tooltip on hover
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;

    const map = mapRef.current;

    const handleMouseMove = (e: any) => {
      if (!e.features || e.features.length === 0) {
        setTooltip((prev) => ({ ...prev, visible: false }));
        map.getCanvas().style.cursor = '';
        return;
      }

      const feature = e.features[0];
      const iso2 = feature.id || feature.properties?.ISO_A2;

      if (!iso2 || iso2 === '-99') {
        setTooltip((prev) => ({ ...prev, visible: false }));
        return;
      }

      // Get feature state
      const state = map.getFeatureState({ source: 'countries', id: iso2 });
      const country = countriesMap.get(iso2);

      map.getCanvas().style.cursor = 'pointer';

      setTooltip({
        visible: true,
        x: e.originalEvent.clientX,
        y: e.originalEvent.clientY,
        country: country || null,
        iso2,
      });
    };

    const handleMouseLeave = () => {
      setTooltip((prev) => ({ ...prev, visible: false }));
      map.getCanvas().style.cursor = '';
    };

    map.on('mousemove', 'countries-fill', handleMouseMove);
    map.on('mouseleave', 'countries-fill', handleMouseLeave);

    return () => {
      map.off('mousemove', 'countries-fill', handleMouseMove);
      map.off('mouseleave', 'countries-fill', handleMouseLeave);
    };
  }, [mapLoaded, countriesMap]);

  // Layer toggle buttons
  const toggleButtons: { mode: LayerMode; label: string; icon: string }[] = [
    { mode: 'acled', label: 'ACLED Points', icon: 'O' },
    { mode: 'hybrid', label: 'Hybrid Risk', icon: 'H' },
    { mode: 'structural', label: 'Structural Risk', icon: 'S' },
    { mode: 'local', label: 'Local (BR)', icon: 'BR' },
  ];

  // Risk level to color
  const getRiskColor = (risk: number) => {
    if (risk >= 75) return 'text-red-400';
    if (risk >= 50) return 'text-orange-400';
    if (risk >= 25) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <div className="mb-6">
      <h2 className="text-lg font-semibold text-slate-300 mb-3 flex items-center gap-2">
        <span className="text-base">Security Map</span>
        {loading && <span className="text-xs text-slate-500">(Loading...)</span>}
        {error && <span className="text-xs text-red-400">(Error loading data)</span>}
      </h2>

      <div className="relative rounded-lg overflow-hidden border border-slate-700/50">
        {/* Toggle Controls */}
        <div className="absolute top-3 left-3 z-10 flex gap-2">
          {toggleButtons.map((btn) => (
            <button
              key={btn.mode}
              onClick={() => setActiveLayer(btn.mode)}
              className={`
                px-3 py-1.5 rounded-md text-xs font-medium
                transition-all duration-200
                ${activeLayer === btn.mode
                  ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/20'
                  : 'bg-slate-800/80 text-slate-400 hover:bg-slate-700/80 hover:text-slate-300'
                }
              `}
              title={btn.label}
            >
              {btn.label}
            </button>
          ))}
        </div>

        {/* Legend */}
        <div className="absolute bottom-3 left-3 z-10 bg-slate-900/90 rounded-lg p-2 border border-slate-700/50">
          <div className="text-xs text-slate-400 mb-1">Risk Level</div>
          <div className="flex gap-1">
            {Object.entries(RISK_COLORS).map(([value, color]) => (
              <div key={value} className="flex flex-col items-center">
                <div
                  className="w-6 h-3 rounded-sm"
                  style={{ backgroundColor: color }}
                />
                <span className="text-[10px] text-slate-500">{value}</span>
              </div>
            ))}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">
            Opacity = Coverage Score
          </div>
        </div>

        {/* Metadata */}
        {data?.metadata && (
          <div className="absolute bottom-3 right-3 z-10 bg-slate-900/90 rounded-lg p-2 border border-slate-700/50">
            <div className="text-[10px] text-slate-500">
              {data.metadata.total_countries} countries
            </div>
            <div className="text-[10px] text-slate-500">
              Avg coverage: {data.metadata.avg_coverage}%
            </div>
          </div>
        )}

        {/* Map Container */}
        <div
          ref={mapContainerRef}
          className="w-full h-[400px] bg-slate-900"
        />

        {/* Tooltip */}
        {tooltip.visible && tooltip.country && (
          <div
            className="fixed z-50 pointer-events-none"
            style={{
              left: tooltip.x + 10,
              top: tooltip.y + 10,
            }}
          >
            <div className="bg-slate-900/95 rounded-lg p-3 border border-slate-600 shadow-xl max-w-xs">
              <div className="font-semibold text-white mb-2">
                {tooltip.country.country_name}
                <span className="text-slate-500 text-xs ml-2">
                  ({tooltip.iso2})
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-400">Total Risk:</span>
                  <span className={`ml-1 font-medium ${getRiskColor(tooltip.country.total_risk)}`}>
                    {tooltip.country.total_risk.toFixed(1)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Acute:</span>
                  <span className={`ml-1 font-medium ${getRiskColor(tooltip.country.acute_risk)}`}>
                    {tooltip.country.acute_risk.toFixed(1)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Structural:</span>
                  <span className={`ml-1 font-medium ${getRiskColor(tooltip.country.structural_risk)}`}>
                    {tooltip.country.structural_risk.toFixed(1)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Coverage:</span>
                  <span className={`ml-1 font-medium ${
                    tooltip.country.coverage_score_global >= 50 ? 'text-green-400' : 'text-yellow-400'
                  }`}>
                    {tooltip.country.coverage_score_global.toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="text-[10px] text-slate-500 mt-2">
                Level: <span className="text-slate-300">{tooltip.country.risk_level}</span>
              </div>

              {tooltip.country.coverage_score_global < 50 && (
                <div className="mt-2 text-[10px] text-yellow-400 bg-yellow-400/10 rounded px-2 py-1">
                  Baixa cobertura - risco pode estar subestimado
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tooltip for countries without data */}
        {tooltip.visible && !tooltip.country && tooltip.iso2 && (
          <div
            className="fixed z-50 pointer-events-none"
            style={{
              left: tooltip.x + 10,
              top: tooltip.y + 10,
            }}
          >
            <div className="bg-slate-900/95 rounded-lg p-3 border border-slate-600 shadow-xl">
              <div className="font-semibold text-slate-400">
                {tooltip.iso2}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                No security data available
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Mode info */}
      <div className="mt-2 text-xs text-slate-500">
        {activeLayer === 'hybrid' && 'Hybrid Risk = ACLED conflicts + GDELT events + World Bank structural indicators'}
        {activeLayer === 'structural' && 'Structural Risk = World Bank indicators (governance, poverty, stability)'}
        {activeLayer === 'acled' && 'ACLED Points = Individual conflict events (requires API)'}
        {activeLayer === 'local' && 'Local (BR) = Brazil-specific security data (zoom >= 8)'}
      </div>
    </div>
  );
}
