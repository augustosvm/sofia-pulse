-- Migration: Unify Brazil Data Collectors (Compliance & Lineage)
-- Purpose: Add 'source' column to tracking origin in unified architecture
-- Affects: comexstat_trade, fiesp_sensor, fiesp_ina

-- 1. MDIC ComexStat
ALTER TABLE sofia.comexstat_trade
ADD COLUMN IF NOT EXISTS source VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_comexstat_trade_source ON sofia.comexstat_trade(source);

COMMENT ON COLUMN sofia.comexstat_trade.source IS 'Data source (e.g., mdic-comexstat) for compliance tracking';

-- 2. FIESP Sensor
ALTER TABLE sofia.fiesp_sensor
ADD COLUMN IF NOT EXISTS source VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_fiesp_sensor_source ON sofia.fiesp_sensor(source);

COMMENT ON COLUMN sofia.fiesp_sensor.source IS 'Data source (e.g., fiesp-sensor) for compliance tracking';

-- 3. FIESP INA
ALTER TABLE sofia.fiesp_ina
ADD COLUMN IF NOT EXISTS source VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_fiesp_ina_source ON sofia.fiesp_ina(source);

COMMENT ON COLUMN sofia.fiesp_ina.source IS 'Data source (e.g., fiesp-ina) for compliance tracking';
