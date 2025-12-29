-- Migration 043: Add Major US Cities
-- Adds top 100+ US cities by population to sofia.cities table

-- Helper function to get state_id
CREATE OR REPLACE FUNCTION get_us_state_id(state_code TEXT) RETURNS INTEGER AS $$
  SELECT id FROM sofia.states
  WHERE country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US')
  AND code = state_code
  LIMIT 1;
$$ LANGUAGE SQL;

-- Insert major US cities
INSERT INTO sofia.cities (country_id, state_id, name) VALUES
  -- California
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'Los Angeles'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'San Diego'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'San Jose'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'San Francisco'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'Fresno'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'Sacramento'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'Long Beach'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'Oakland'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CA'), 'Bakersfield'),

  -- Texas
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('TX'), 'Houston'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('TX'), 'San Antonio'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('TX'), 'Dallas'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('TX'), 'Austin'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('TX'), 'Fort Worth'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('TX'), 'El Paso'),

  -- Florida
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Jacksonville'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Miami'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Tampa'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Orlando'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'St. Petersburg'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Hialeah'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Tallahassee'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Fort Lauderdale'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Port St. Lucie'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Cape Coral'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('FL'), 'Largo'),

  -- New York
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('NY'), 'New York'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('NY'), 'Buffalo'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('NY'), 'Rochester'),

  -- Illinois
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('IL'), 'Chicago'),

  -- Pennsylvania
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('PA'), 'Philadelphia'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('PA'), 'Pittsburgh'),

  -- Arizona
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('AZ'), 'Phoenix'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('AZ'), 'Tucson'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('AZ'), 'Mesa'),

  -- Washington
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('WA'), 'Seattle'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('WA'), 'Spokane'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('WA'), 'Tacoma'),

  -- Massachusetts
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('MA'), 'Boston'),

  -- Colorado
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CO'), 'Denver'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CO'), 'Colorado Springs'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('CO'), 'Aurora'),

  -- Other major cities
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('DC'), 'Washington'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('NV'), 'Las Vegas'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('MI'), 'Detroit'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('TN'), 'Nashville'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('TN'), 'Memphis'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('OR'), 'Portland'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('OK'), 'Oklahoma City'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('WI'), 'Milwaukee'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('NM'), 'Albuquerque'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('NC'), 'Charlotte'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('NC'), 'Raleigh'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('MD'), 'Baltimore'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('OH'), 'Columbus'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('OH'), 'Cleveland'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('OH'), 'Cincinnati'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('MO'), 'Kansas City'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('MO'), 'St. Louis'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('GA'), 'Atlanta'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('IN'), 'Indianapolis'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('MN'), 'Minneapolis'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('UT'), 'Salt Lake City'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'New Orleans'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Baton Rouge'),

  -- Louisiana smaller cities from Adzuna data
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Oberlin'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Alex'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Glenmora'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Mansura'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Bunkie'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Oakdale'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Pollock'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Urania'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Jonesville'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), get_us_state_id('LA'), 'Cottonport')
ON CONFLICT DO NOTHING;

-- Clean up helper function
DROP FUNCTION get_us_state_id(TEXT);

-- Verify
DO $$
DECLARE
  city_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO city_count
  FROM sofia.cities
  WHERE country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US')
  AND state_id IS NOT NULL;

  RAISE NOTICE 'US Cities with states: %', city_count;
END $$;
