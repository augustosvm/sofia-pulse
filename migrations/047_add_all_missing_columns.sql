-- Add organization_id and country_id to all remaining tables

-- ORGANIZATIONS
ALTER TABLE sofia.market_data_brazil ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);
ALTER TABLE sofia.global_universities_progress ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);
ALTER TABLE sofia.world_ngos ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);
ALTER TABLE sofia.hdx_humanitarian_data ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);
ALTER TABLE sofia.hkex_ipos ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);
ALTER TABLE sofia.market_data_nasdaq ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);
ALTER TABLE sofia.startups ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);
ALTER TABLE sofia.nih_grants ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);

CREATE INDEX IF NOT EXISTS idx_market_data_brazil_org ON sofia.market_data_brazil(organization_id);
CREATE INDEX IF NOT EXISTS idx_global_universities_org ON sofia.global_universities_progress(organization_id);
CREATE INDEX IF NOT EXISTS idx_world_ngos_org ON sofia.world_ngos(organization_id);
CREATE INDEX IF NOT EXISTS idx_hdx_humanitarian_org ON sofia.hdx_humanitarian_data(organization_id);
CREATE INDEX IF NOT EXISTS idx_hkex_ipos_org ON sofia.hkex_ipos(organization_id);
CREATE INDEX IF NOT EXISTS idx_market_data_nasdaq_org ON sofia.market_data_nasdaq(organization_id);
CREATE INDEX IF NOT EXISTS idx_startups_org ON sofia.startups(organization_id);
CREATE INDEX IF NOT EXISTS idx_nih_grants_org ON sofia.nih_grants(organization_id);

-- GEOGRAPHIC
ALTER TABLE sofia.authors ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.gdelt_events ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.cardboard_production ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.publications ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.electricity_consumption ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.energy_global ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.gender_names ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.startups ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.global_universities_progress ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);
ALTER TABLE sofia.world_ngos ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);

CREATE INDEX IF NOT EXISTS idx_authors_country ON sofia.authors(country_id);
CREATE INDEX IF NOT EXISTS idx_gdelt_country ON sofia.gdelt_events(country_id);
CREATE INDEX IF NOT EXISTS idx_cardboard_country ON sofia.cardboard_production(country_id);
CREATE INDEX IF NOT EXISTS idx_publications_country ON sofia.publications(country_id);
CREATE INDEX IF NOT EXISTS idx_electricity_country ON sofia.electricity_consumption(country_id);
CREATE INDEX IF NOT EXISTS idx_energy_country ON sofia.energy_global(country_id);
CREATE INDEX IF NOT EXISTS idx_gender_names_country ON sofia.gender_names(country_id);

DO $$ BEGIN RAISE NOTICE '✅ Columns and indexes created'; END $$;
