-- Migration 044: Add Major European Cities
-- Adds top cities from UK, Germany, France, Spain, Netherlands, and other European countries

-- United Kingdom Cities
INSERT INTO sofia.cities (country_id, name) VALUES
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'London'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Manchester'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Birmingham'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Leeds'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Glasgow'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Liverpool'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Newcastle'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Sheffield'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Bristol'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Edinburgh'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Cardiff'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Belfast'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Leicester'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Nottingham'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Southampton'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Reading'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Brighton'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Aberdeen'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Cambridge'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB'), 'Oxford'),

  -- Germany Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Berlin'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Munich'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Hamburg'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Frankfurt'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Cologne'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Stuttgart'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Düsseldorf'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Dortmund'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Essen'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Leipzig'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Bremen'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Dresden'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Hannover'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Nuremberg'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Duisburg'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Bochum'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Wuppertal'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Bielefeld'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Bonn'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE'), 'Mannheim'),

  -- France Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Paris'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Marseille'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Lyon'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Toulouse'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Nice'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Nantes'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Strasbourg'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Montpellier'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Bordeaux'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Lille'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Rennes'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Reims'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Le Havre'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Saint-Étienne'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Toulon'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR'), 'Grenoble'),

  -- Spain Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Madrid'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Barcelona'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Valencia'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Seville'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Zaragoza'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Málaga'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Murcia'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Palma'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Bilbao'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ES'), 'Alicante'),

  -- Netherlands Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Amsterdam'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Rotterdam'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'The Hague'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Utrecht'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Eindhoven'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Groningen'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Tilburg'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Almere'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Breda'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL'), 'Nijmegen'),

  -- Italy Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Rome'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Milan'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Naples'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Turin'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Palermo'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Genoa'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Bologna'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Florence'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IT'), 'Venice'),

  -- Switzerland Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CH'), 'Zurich'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CH'), 'Geneva'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CH'), 'Basel'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CH'), 'Bern'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CH'), 'Lausanne'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CH'), 'Lucerne'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CH'), 'Zug'),

  -- Austria Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AT'), 'Vienna'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AT'), 'Graz'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AT'), 'Linz'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AT'), 'Salzburg'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AT'), 'Innsbruck'),

  -- Belgium Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BE'), 'Brussels'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BE'), 'Antwerp'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BE'), 'Ghent'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BE'), 'Bruges'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BE'), 'Leuven'),

  -- Portugal Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PT'), 'Lisbon'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PT'), 'Porto'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PT'), 'Braga'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PT'), 'Coimbra'),

  -- Ireland Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IE'), 'Dublin'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IE'), 'Cork'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IE'), 'Galway'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IE'), 'Limerick'),

  -- Poland Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PL'), 'Warsaw'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PL'), 'Kraków'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PL'), 'Wrocław'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PL'), 'Poznań'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'PL'), 'Gdańsk'),

  -- Sweden Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'SE'), 'Stockholm'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'SE'), 'Gothenburg'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'SE'), 'Malmö'),

  -- Denmark Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DK'), 'Copenhagen'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DK'), 'Aarhus'),

  -- Norway Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NO'), 'Oslo'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NO'), 'Bergen'),

  -- Finland Cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FI'), 'Helsinki'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FI'), 'Espoo'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FI'), 'Tampere')

ON CONFLICT DO NOTHING;

-- Verify insertion
DO $$
DECLARE
  uk_count INTEGER;
  de_count INTEGER;
  fr_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO uk_count FROM sofia.cities WHERE country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB');
  SELECT COUNT(*) INTO de_count FROM sofia.cities WHERE country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE');
  SELECT COUNT(*) INTO fr_count FROM sofia.cities WHERE country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR');

  RAISE NOTICE 'UK cities: %', uk_count;
  RAISE NOTICE 'Germany cities: %', de_count;
  RAISE NOTICE 'France cities: %', fr_count;
END $$;
