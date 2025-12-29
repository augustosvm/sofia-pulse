-- Migration 040: Add Verified Cities (Simplified)
-- Date: 2025-12-26
-- Purpose: Add ~150 VERIFIED world cities using KNOWN country_ids only
--
-- All cities are real and country_ids are verified to exist

BEGIN;

INSERT INTO sofia.cities (name, state_id, country_id) VALUES
  -- United States (1) - Top 35 cities
  ('New York', NULL, 1),
  ('Los Angeles', NULL, 1),
  ('San Francisco', NULL, 1),
  ('Chicago', NULL, 1),
  ('Seattle', NULL, 1),
  ('Boston', NULL, 1),
  ('Austin', NULL, 1),
  ('Denver', NULL, 1),
  ('Atlanta', NULL, 1),
  ('Miami', NULL, 1),
  ('Philadelphia', NULL, 1),
  ('Washington', NULL, 1),
  ('Dallas', NULL, 1),
  ('Houston', NULL, 1),
  ('San Diego', NULL, 1),
  ('Phoenix', NULL, 1),
  ('Portland', NULL, 1),
  ('Las Vegas', NULL, 1),
  ('Detroit', NULL, 1),
  ('Minneapolis', NULL, 1),
  ('Pittsburgh', NULL, 1),
  ('Baltimore', NULL, 1),
  ('Charlotte', NULL, 1),
  ('Nashville', NULL, 1),
  ('Salt Lake City', NULL, 1),
  ('Raleigh', NULL, 1),
  ('Tampa', NULL, 1),
  ('Orlando', NULL, 1),
  ('Cincinnati', NULL, 1),
  ('Cleveland', NULL, 1),
  ('San Jose', NULL, 1),
  ('Oakland', NULL, 1),
  ('Palo Alto', NULL, 1),
  ('Mountain View', NULL, 1),
  ('Sunnyvale', NULL, 1),

  -- Canada (4) - 10 cities
  ('Toronto', NULL, 4),
  ('Vancouver', NULL, 4),
  ('Montreal', NULL, 4),
  ('Calgary', NULL, 4),
  ('Edmonton', NULL, 4),
  ('Ottawa', NULL, 4),
  ('Winnipeg', NULL, 4),
  ('Quebec City', NULL, 4),
  ('Halifax', NULL, 4),
  ('Victoria', NULL, 4),

  -- Brazil (2) - 20 cities
  ('Rio de Janeiro', NULL, 2),
  ('São Paulo', NULL, 2),
  ('Brasília', NULL, 2),
  ('Salvador', NULL, 2),
  ('Fortaleza', NULL, 2),
  ('Belo Horizonte', NULL, 2),
  ('Manaus', NULL, 2),
  ('Curitiba', NULL, 2),
  ('Recife', NULL, 2),
  ('Porto Alegre', NULL, 2),
  ('Belém', NULL, 2),
  ('Goiânia', NULL, 2),
  ('Guarulhos', NULL, 2),
  ('Campinas', NULL, 2),
  ('Florianópolis', NULL, 2),
  ('Santos', NULL, 2),
  ('Natal', NULL, 2),
  ('João Pessoa', NULL, 2),
  ('Aracaju', NULL, 2),
  ('Maceió', NULL, 2),

  -- United Kingdom (3) - 15 cities
  ('London', NULL, 3),
  ('Manchester', NULL, 3),
  ('Birmingham', NULL, 3),
  ('Edinburgh', NULL, 3),
  ('Glasgow', NULL, 3),
  ('Liverpool', NULL, 3),
  ('Bristol', NULL, 3),
  ('Leeds', NULL, 3),
  ('Sheffield', NULL, 3),
  ('Cardiff', NULL, 3),
  ('Belfast', NULL, 3),
  ('Newcastle', NULL, 3),
  ('Nottingham', NULL, 3),
  ('Southampton', NULL, 3),
  ('Cambridge', NULL, 3),

  -- Germany (6) - 15 cities
  ('Berlin', NULL, 6),
  ('Munich', NULL, 6),
  ('Hamburg', NULL, 6),
  ('Frankfurt', NULL, 6),
  ('Cologne', NULL, 6),
  ('Stuttgart', NULL, 6),
  ('Düsseldorf', NULL, 6),
  ('Dortmund', NULL, 6),
  ('Essen', NULL, 6),
  ('Leipzig', NULL, 6),
  ('Bremen', NULL, 6),
  ('Dresden', NULL, 6),
  ('Hanover', NULL, 6),
  ('Nuremberg', NULL, 6),
  ('Bonn', NULL, 6),

  -- France (7) - 10 cities
  ('Paris', NULL, 7),
  ('Marseille', NULL, 7),
  ('Lyon', NULL, 7),
  ('Toulouse', NULL, 7),
  ('Nice', NULL, 7),
  ('Nantes', NULL, 7),
  ('Strasbourg', NULL, 7),
  ('Montpellier', NULL, 7),
  ('Bordeaux', NULL, 7),
  ('Lille', NULL, 7),

  -- India (8) - 15 cities
  ('Mumbai', NULL, 8),
  ('Delhi', NULL, 8),
  ('Bengaluru', NULL, 8),
  ('Hyderabad', NULL, 8),
  ('Chennai', NULL, 8),
  ('Kolkata', NULL, 8),
  ('Pune', NULL, 8),
  ('Ahmedabad', NULL, 8),
  ('Jaipur', NULL, 8),
  ('Surat', NULL, 8),
  ('Lucknow', NULL, 8),
  ('Kanpur', NULL, 8),
  ('Nagpur', NULL, 8),
  ('Indore', NULL, 8),
  ('Gurgaon', NULL, 8),

  -- China (9) - 10 cities
  ('Beijing', NULL, 9),
  ('Shanghai', NULL, 9),
  ('Guangzhou', NULL, 9),
  ('Shenzhen', NULL, 9),
  ('Chengdu', NULL, 9),
  ('Hangzhou', NULL, 9),
  ('Wuhan', NULL, 9),
  ('Xi''an', NULL, 9),
  ('Chongqing', NULL, 9),
  ('Tianjin', NULL, 9),

  -- Japan (10) - 8 cities
  ('Tokyo', NULL, 10),
  ('Osaka', NULL, 10),
  ('Yokohama', NULL, 10),
  ('Nagoya', NULL, 10),
  ('Sapporo', NULL, 10),
  ('Fukuoka', NULL, 10),
  ('Kobe', NULL, 10),
  ('Kyoto', NULL, 10),

  -- Italy (13) - 10 cities
  ('Rome', NULL, 13),
  ('Milan', NULL, 13),
  ('Naples', NULL, 13),
  ('Turin', NULL, 13),
  ('Palermo', NULL, 13),
  ('Genoa', NULL, 13),
  ('Bologna', NULL, 13),
  ('Florence', NULL, 13),
  ('Bari', NULL, 13),
  ('Venice', NULL, 13),

  -- Argentina (17) - 5 cities
  ('Buenos Aires', NULL, 17),
  ('Córdoba', NULL, 17),
  ('Rosario', NULL, 17),
  ('Mendoza', NULL, 17),
  ('La Plata', NULL, 17),

  -- Chile (18) - 3 cities
  ('Santiago', NULL, 18),
  ('Valparaíso', NULL, 18),
  ('Concepción', NULL, 18),

  -- Colombia (19) - 3 cities
  ('Bogotá', NULL, 19),
  ('Medellín', NULL, 19),
  ('Cali', NULL, 19),

  -- Australia (5) - 8 cities
  ('Sydney', NULL, 5),
  ('Melbourne', NULL, 5),
  ('Brisbane', NULL, 5),
  ('Perth', NULL, 5),
  ('Adelaide', NULL, 5),
  ('Gold Coast', NULL, 5),
  ('Newcastle', NULL, 5),
  ('Canberra', NULL, 5),

  -- New Zealand (31) - 4 cities
  ('Auckland', NULL, 31),
  ('Wellington', NULL, 31),
  ('Christchurch', NULL, 31),
  ('Hamilton', NULL, 31),

  -- Austria (28) - 3 cities
  ('Vienna', NULL, 28),
  ('Graz', NULL, 28),
  ('Salzburg', NULL, 28),

  -- Denmark (25) - 2 cities
  ('Copenhagen', NULL, 25),
  ('Aarhus', NULL, 25),

  -- Finland (26) - 2 cities
  ('Helsinki', NULL, 26),
  ('Tampere', NULL, 26),

  -- Belgium (29) - 3 cities
  ('Brussels', NULL, 29),
  ('Antwerp', NULL, 29),
  ('Ghent', NULL, 29),

  -- Ireland (30) - 2 cities
  ('Dublin', NULL, 30),
  ('Cork', NULL, 30),

  -- Israel (33) - 3 cities
  ('Tel Aviv', NULL, 33),
  ('Jerusalem', NULL, 33),
  ('Haifa', NULL, 33),

  -- Czech Republic (39) - 2 cities
  ('Prague', NULL, 39),
  ('Brno', NULL, 39),

  -- Greece (41) - 2 cities
  ('Athens', NULL, 41),
  ('Thessaloniki', NULL, 41),

  -- Indonesia (44) - 3 cities
  ('Jakarta', NULL, 44),
  ('Surabaya', NULL, 44),
  ('Bandung', NULL, 44),

  -- Bangladesh (48) - 2 cities
  ('Dhaka', NULL, 48),
  ('Chittagong', NULL, 48),

  -- Egypt (49) - 2 cities
  ('Cairo', NULL, 49),
  ('Alexandria', NULL, 49)

ON CONFLICT (name, state_id, country_id) DO NOTHING;

-- Update jobs with newly added cities
UPDATE sofia.jobs j
SET city_id = c.id
FROM sofia.cities c
WHERE j.city_id IS NULL
  AND j.city = c.name
  AND j.country_id = c.country_id
  AND (j.state_id = c.state_id OR (j.state_id IS NULL AND c.state_id IS NULL));

-- Statistics
DO $$
DECLARE
  city_count INTEGER;
  job_city_count INTEGER;
  job_city_pct NUMERIC;
BEGIN
  SELECT COUNT(*) INTO city_count FROM sofia.cities;
  SELECT COUNT(city_id), ROUND(100.0 * COUNT(city_id) / COUNT(*), 1)
  INTO job_city_count, job_city_pct
  FROM sofia.jobs;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'MIGRATION 040 - Add Verified Cities';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Total cities: %', city_count;
  RAISE NOTICE 'Jobs with city_id: % (%)', job_city_count, job_city_pct;
  RAISE NOTICE '========================================';
END $$;

COMMIT;
