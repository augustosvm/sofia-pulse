-- Migration 042: Add US States with Codes
-- Adds the 50 US states + territories to sofia.states table
-- Note: Does NOT delete existing entries (they may be referenced by jobs)

-- Insert the 50 US states + major territories
-- Use ON CONFLICT to avoid duplicates if they already exist
INSERT INTO sofia.states (country_id, name, code) VALUES
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Alabama', 'AL'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Alaska', 'AK'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Arizona', 'AZ'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Arkansas', 'AR'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'California', 'CA'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Colorado', 'CO'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Connecticut', 'CT'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Delaware', 'DE'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Florida', 'FL'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Georgia', 'GA'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Hawaii', 'HI'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Idaho', 'ID'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Illinois', 'IL'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Indiana', 'IN'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Iowa', 'IA'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Kansas', 'KS'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Kentucky', 'KY'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Louisiana', 'LA'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Maine', 'ME'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Maryland', 'MD'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Massachusetts', 'MA'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Michigan', 'MI'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Minnesota', 'MN'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Mississippi', 'MS'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Missouri', 'MO'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Montana', 'MT'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Nebraska', 'NE'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Nevada', 'NV'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'New Hampshire', 'NH'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'New Jersey', 'NJ'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'New Mexico', 'NM'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'New York', 'NY'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'North Carolina', 'NC'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'North Dakota', 'ND'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Ohio', 'OH'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Oklahoma', 'OK'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Oregon', 'OR'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Pennsylvania', 'PA'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Rhode Island', 'RI'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'South Carolina', 'SC'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'South Dakota', 'SD'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Tennessee', 'TN'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Texas', 'TX'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Utah', 'UT'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Vermont', 'VT'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Virginia', 'VA'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Washington', 'WA'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'West Virginia', 'WV'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Wisconsin', 'WI'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Wyoming', 'WY'),
  -- Territories
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'District of Columbia', 'DC'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Puerto Rico', 'PR'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Guam', 'GU'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'U.S. Virgin Islands', 'VI'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'American Samoa', 'AS'),
  ((SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US'), 'Northern Mariana Islands', 'MP')
ON CONFLICT DO NOTHING;

-- Verify insertion
DO $$
DECLARE
  state_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO state_count
  FROM sofia.states
  WHERE country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US');

  RAISE NOTICE 'US States added: %', state_count;
END $$;
