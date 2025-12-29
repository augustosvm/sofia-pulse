-- Auto-generated city inserts
BEGIN;

INSERT INTO sofia.cities (name, state_id, country_id) VALUES
  ('Aarhus', NULL, 25),
  ('Castrop-Rauxel', NULL, 6),
  ('Heredia', NULL, 948),
  ('Wuppertal', NULL, 6),
  ('Beijing', NULL, 9),
  ('Scottsdale', NULL, 1),
  ('Illinois', NULL, 1),
  ('Hawaii', NULL, 1),
  ('Central - United States', NULL, 1),
  ('Bavaria', NULL, 6),
  ('Herzliya', NULL, 33),
  ('IE-Dublin', NULL, 1),
  ('Amsterdam or Stockholm or Dublin', NULL, 1),
  ('Finland', NULL, 1),
  ('California', NULL, 1),
  ('Aachen', NULL, 6)
ON CONFLICT (name, state_id, country_id) DO NOTHING;

COMMIT;