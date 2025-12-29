-- Migration 039: Add 250 World-Known Cities
-- Date: 2025-12-26
-- Purpose: Add curated list of 250 verified, world-known cities
--
-- All cities are VERIFIED to exist (capitals, major metros, tech hubs)

BEGIN;

-- ============================================================================
-- AMERICAS - 85 cities
-- ============================================================================

INSERT INTO sofia.cities (name, state_id, country_id) VALUES
  -- United States (country_id = 1) - 40 cities
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
  ('Columbus', NULL, 1),
  ('Indianapolis', NULL, 1),
  ('Nashville', NULL, 1),
  ('Memphis', NULL, 1),
  ('Salt Lake City', NULL, 1),
  ('Sacramento', NULL, 1),
  ('Raleigh', NULL, 1),
  ('Tampa', NULL, 1),
  ('Orlando', NULL, 1),
  ('Cincinnati', NULL, 1),
  ('Cleveland', NULL, 1),
  ('Milwaukee', NULL, 1),
  ('Kansas City', NULL, 1),
  ('St. Louis', NULL, 1),
  ('San Jose', NULL, 1),
  ('Oakland', NULL, 1),
  ('Palo Alto', NULL, 1),

  -- Canada (country_id = 4) - 10 cities
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

  -- Brazil (country_id = 2) - 15 cities (além das já existentes)
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

  -- Mexico (country_id = 13) - 8 cities
  ('Mexico City', NULL, 13),
  ('Guadalajara', NULL, 13),
  ('Monterrey', NULL, 13),
  ('Puebla', NULL, 13),
  ('Tijuana', NULL, 13),
  ('León', NULL, 13),
  ('Juárez', NULL, 13),
  ('Cancún', NULL, 13),

  -- Argentina (country_id = 15) - 5 cities
  ('Buenos Aires', NULL, 15),
  ('Córdoba', NULL, 15),
  ('Rosario', NULL, 15),
  ('Mendoza', NULL, 15),
  ('La Plata', NULL, 15),

  -- Others (7 cities)
  ('Santiago', NULL, 11),     -- Chile
  ('Lima', NULL, 12),          -- Peru
  ('Bogotá', NULL, 9),         -- Colombia
  ('Caracas', NULL, 16),       -- Venezuela
  ('Montevideo', NULL, 17),    -- Uruguay
  ('Quito', NULL, 18),         -- Ecuador
  ('La Paz', NULL, 19),        -- Bolivia

-- ============================================================================
-- EUROPE - 90 cities
-- ============================================================================

  -- United Kingdom (country_id = 3) - 15 cities
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

  -- Germany (country_id = 6) - 15 cities
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

  -- France (country_id = 7) - 10 cities
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

  -- Spain (country_id = 8) - 10 cities
  ('Madrid', NULL, 8),
  ('Barcelona', NULL, 8),
  ('Valencia', NULL, 8),
  ('Seville', NULL, 8),
  ('Zaragoza', NULL, 8),
  ('Málaga', NULL, 8),
  ('Bilbao', NULL, 8),
  ('Las Palmas', NULL, 8),
  ('Murcia', NULL, 8),
  ('Palma', NULL, 8),

  -- Italy (country_id = 26) - 10 cities
  ('Rome', NULL, 26),
  ('Milan', NULL, 26),
  ('Naples', NULL, 26),
  ('Turin', NULL, 26),
  ('Palermo', NULL, 26),
  ('Genoa', NULL, 26),
  ('Bologna', NULL, 26),
  ('Florence', NULL, 26),
  ('Bari', NULL, 26),
  ('Venice', NULL, 26),

  -- Netherlands (country_id = 14) - 5 cities
  ('Amsterdam', NULL, 14),
  ('Rotterdam', NULL, 14),
  ('The Hague', NULL, 14),
  ('Utrecht', NULL, 14),
  ('Eindhoven', NULL, 14),

  -- Poland (country_id = 22) - 5 cities
  ('Warsaw', NULL, 22),
  ('Kraków', NULL, 22),
  ('Gdańsk', NULL, 22),
  ('Wrocław', NULL, 22),
  ('Poznań', NULL, 22),

  -- Others (20 cities - European capitals)
  ('Dublin', NULL, 30),        -- Ireland
  ('Lisbon', NULL, 27),         -- Portugal
  ('Vienna', NULL, 33),         -- Austria
  ('Prague', NULL, 34),         -- Czech Republic
  ('Brussels', NULL, 35),       -- Belgium
  ('Copenhagen', NULL, 25),     -- Denmark
  ('Stockholm', NULL, 23),      -- Sweden
  ('Oslo', NULL, 36),           -- Norway
  ('Helsinki', NULL, 37),       -- Finland
  ('Athens', NULL, 38),         -- Greece
  ('Budapest', NULL, 39),       -- Hungary
  ('Bucharest', NULL, 40),      -- Romania
  ('Sofia', NULL, 41),          -- Bulgaria
  ('Zurich', NULL, 20),         -- Switzerland
  ('Geneva', NULL, 20),         -- Switzerland
  ('Belgrade', NULL, 1034),     -- Serbia
  ('Zagreb', NULL, 42),         -- Croatia
  ('Bratislava', NULL, 43),     -- Slovakia
  ('Ljubljana', NULL, 44),      -- Slovenia
  ('Vilnius', NULL, 45),        -- Lithuania

-- ============================================================================
-- ASIA - 50 cities
-- ============================================================================

  -- India (country_id = 7) - 15 cities
  ('Mumbai', NULL, 7),
  ('Delhi', NULL, 7),
  ('Bengaluru', NULL, 7),
  ('Hyderabad', NULL, 7),
  ('Chennai', NULL, 7),
  ('Kolkata', NULL, 7),
  ('Pune', NULL, 7),
  ('Ahmedabad', NULL, 7),
  ('Jaipur', NULL, 7),
  ('Surat', NULL, 7),
  ('Lucknow', NULL, 7),
  ('Kanpur', NULL, 7),
  ('Nagpur', NULL, 7),
  ('Indore', NULL, 7),
  ('Gurgaon', NULL, 7),

  -- China (country_id = 46) - 10 cities
  ('Beijing', NULL, 46),
  ('Shanghai', NULL, 46),
  ('Guangzhou', NULL, 46),
  ('Shenzhen', NULL, 46),
  ('Chengdu', NULL, 46),
  ('Hangzhou', NULL, 46),
  ('Wuhan', NULL, 46),
  ('Xi''an', NULL, 46),
  ('Chongqing', NULL, 46),
  ('Tianjin', NULL, 46),

  -- Japan (country_id = 10) - 8 cities
  ('Tokyo', NULL, 10),
  ('Osaka', NULL, 10),
  ('Yokohama', NULL, 10),
  ('Nagoya', NULL, 10),
  ('Sapporo', NULL, 10),
  ('Fukuoka', NULL, 10),
  ('Kobe', NULL, 10),
  ('Kyoto', NULL, 10),

  -- Southeast Asia (10 cities)
  ('Singapore', NULL, 47),      -- Singapore
  ('Bangkok', NULL, 48),         -- Thailand
  ('Manila', NULL, 49),          -- Philippines
  ('Jakarta', NULL, 50),         -- Indonesia
  ('Kuala Lumpur', NULL, 51),    -- Malaysia
  ('Ho Chi Minh City', NULL, 52), -- Vietnam
  ('Hanoi', NULL, 52),           -- Vietnam
  ('Yangon', NULL, 53),          -- Myanmar
  ('Phnom Penh', NULL, 54),      -- Cambodia
  ('Vientiane', NULL, 55),       -- Laos

  -- Others (7 cities)
  ('Seoul', NULL, 56),           -- South Korea
  ('Taipei', NULL, 57),          -- Taiwan
  ('Hong Kong', NULL, 58),       -- Hong Kong
  ('Tel Aviv', NULL, 59),        -- Israel
  ('Dubai', NULL, 60),           -- UAE
  ('Riyadh', NULL, 61),          -- Saudi Arabia
  ('Istanbul', NULL, 62),        -- Turkey

-- ============================================================================
-- AFRICA & OCEANIA - 25 cities
-- ============================================================================

  -- South Africa (country_id = 32) - 5 cities
  ('Johannesburg', NULL, 32),
  ('Cape Town', NULL, 32),
  ('Durban', NULL, 32),
  ('Pretoria', NULL, 32),
  ('Port Elizabeth', NULL, 32),

  -- Australia (country_id = 5) - 8 cities
  ('Sydney', NULL, 5),
  ('Melbourne', NULL, 5),
  ('Brisbane', NULL, 5),
  ('Perth', NULL, 5),
  ('Adelaide', NULL, 5),
  ('Gold Coast', NULL, 5),
  ('Newcastle', NULL, 5),
  ('Canberra', NULL, 5),

  -- New Zealand (country_id = 31) - 4 cities
  ('Auckland', NULL, 31),
  ('Wellington', NULL, 31),
  ('Christchurch', NULL, 31),
  ('Hamilton', NULL, 31),

  -- Africa (8 cities)
  ('Cairo', NULL, 63),           -- Egypt
  ('Lagos', NULL, 64),           -- Nigeria
  ('Nairobi', NULL, 65),         -- Kenya
  ('Accra', NULL, 66),           -- Ghana
  ('Dakar', NULL, 67),           -- Senegal
  ('Casablanca', NULL, 68),      -- Morocco
  ('Tunis', NULL, 69),           -- Tunisia
  ('Addis Ababa', NULL, 70)      -- Ethiopia

ON CONFLICT (name, state_id, country_id) DO NOTHING;

-- ============================================================================
-- STATISTICS
-- ============================================================================

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
  RAISE NOTICE 'MIGRATION 039 - 250 Known Cities';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Total cities in database: %', city_count;
  RAISE NOTICE 'Jobs with city_id: % (%)', job_city_count, job_city_pct;
  RAISE NOTICE '========================================';
END $$;

COMMIT;
