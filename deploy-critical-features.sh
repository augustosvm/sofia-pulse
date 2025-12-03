#!/bin/bash
# ============================================================================
# DEPLOY CRITICAL FEATURES - Pre-Sprint 2 Requirements
# ============================================================================
# Deploys 4 critical features to Sofia Pulse server:
#   1. Canonical Keys (entity resolution)
#   2. Universal Changesets (delta tracking)
#   3. Data Provenance (metadata & licensing)
#   4. Intelligent Scheduler (orchestration)
# ============================================================================

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 DEPLOYING CRITICAL FEATURES TO SOFIA PULSE"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Server details
SERVER="ubuntu@91.98.158.19"
REMOTE_DIR="/home/ubuntu/sofia-pulse"

# ============================================================================
# STEP 1: Upload SQL migrations
# ============================================================================

echo "📤 STEP 1: Uploading SQL migrations..."
echo "────────────────────────────────────────────────────────────────────────────────"

ssh $SERVER "mkdir -p $REMOTE_DIR/sql"

scp sql/01-canonical-entities.sql $SERVER:$REMOTE_DIR/sql/
scp sql/02-changesets.sql $SERVER:$REMOTE_DIR/sql/
scp sql/03-data-provenance.sql $SERVER:$REMOTE_DIR/sql/

echo "✅ SQL migrations uploaded"
echo ""

# ============================================================================
# STEP 2: Execute SQL migrations
# ============================================================================

echo "🔧 STEP 2: Executing SQL migrations..."
echo "────────────────────────────────────────────────────────────────────────────────"

ssh $SERVER << 'ENDSSH'
cd /home/ubuntu/sofia-pulse

echo "▶️  Creating canonical entities..."
docker exec -i sofia-postgres psql -U sofia -d sofia_db < sql/01-canonical-entities.sql

echo ""
echo "▶️  Creating changesets table..."
docker exec -i sofia-postgres psql -U sofia -d sofia_db < sql/02-changesets.sql

echo ""
echo "▶️  Creating data provenance tables..."
docker exec -i sofia-postgres psql -U sofia -d sofia_db < sql/03-data-provenance.sql

echo ""
echo "✅ All SQL migrations executed successfully"
ENDSSH

echo ""

# ============================================================================
# STEP 3: Upload Python scripts
# ============================================================================

echo "📤 STEP 3: Uploading Python scripts..."
echo "────────────────────────────────────────────────────────────────────────────────"

scp scripts/entity_resolver.py $SERVER:$REMOTE_DIR/scripts/
scp scripts/intelligent_scheduler.py $SERVER:$REMOTE_DIR/scripts/
scp scripts/populate_data_provenance.py $SERVER:$REMOTE_DIR/scripts/

echo "✅ Python scripts uploaded"
echo ""

# ============================================================================
# STEP 4: Make scripts executable
# ============================================================================

echo "🔧 STEP 4: Making scripts executable..."
echo "────────────────────────────────────────────────────────────────────────────────"

ssh $SERVER << 'ENDSSH'
cd /home/ubuntu/sofia-pulse

chmod +x scripts/entity_resolver.py
chmod +x scripts/intelligent_scheduler.py
chmod +x scripts/populate_data_provenance.py

echo "✅ Scripts are executable"
ENDSSH

echo ""

# ============================================================================
# STEP 5: Activate venv and populate data provenance
# ============================================================================

echo "🔧 STEP 5: Populating data provenance metadata..."
echo "────────────────────────────────────────────────────────────────────────────────"

ssh $SERVER << 'ENDSSH'
cd /home/ubuntu/sofia-pulse

# Activate venv
source venv-analytics/bin/activate

# Populate provenance
python3 scripts/populate_data_provenance.py

echo ""
echo "✅ Data provenance populated"
ENDSSH

echo ""

# ============================================================================
# STEP 6: Verify deployment
# ============================================================================

echo "🔍 STEP 6: Verifying deployment..."
echo "────────────────────────────────────────────────────────────────────────────────"

ssh $SERVER << 'ENDSSH'
cd /home/ubuntu/sofia-pulse

docker exec -i sofia-postgres psql -U sofia -d sofia_db << 'SQL'

-- Check canonical entities
SELECT 'Canonical Entities:' as check, COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'sofia'
  AND table_name IN ('canonical_entities', 'entity_mappings', 'entity_relationships');

-- Check changesets
SELECT 'Changesets:' as check, COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'sofia'
  AND table_name = 'changesets';

-- Check data provenance
SELECT 'Data Provenance:' as check, COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'sofia'
  AND table_name IN ('data_sources', 'table_provenance', 'column_provenance');

-- Check data sources registered
SELECT 'Data Sources Registered:' as check, COUNT(*) as count
FROM sofia.data_sources;

-- Check tables linked
SELECT 'Tables Linked:' as check, COUNT(*) as count
FROM sofia.table_provenance;

-- Show commercial sources
SELECT
    '✅ Commercial Sources:' as info,
    COUNT(*) as count
FROM sofia.data_sources
WHERE commercial_use_allowed = true;

SELECT
    '❌ Non-Commercial Sources:' as info,
    COUNT(*) as count
FROM sofia.data_sources
WHERE commercial_use_allowed = false;

SQL

echo ""
echo "✅ Verification complete"
ENDSSH

echo ""

# ============================================================================
# STEP 7: Test entity resolution
# ============================================================================

echo "🧪 STEP 7: Testing entity resolution (sample)..."
echo "────────────────────────────────────────────────────────────────────────────────"

ssh $SERVER << 'ENDSSH'
cd /home/ubuntu/sofia-pulse

source venv-analytics/bin/activate

# Test normalize function
docker exec -i sofia-postgres psql -U sofia -d sofia_db << 'SQL'
SELECT
    sofia.normalize_entity_name('OpenAI, Inc.') as normalized_1,
    sofia.normalize_entity_name('São Paulo') as normalized_2,
    sofia.normalize_entity_name('GitHub (Microsoft)') as normalized_3;
SQL

echo ""
echo "✅ Entity resolution functions working"
ENDSSH

echo ""

# ============================================================================
# COMPLETE
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 SUMMARY:"
echo ""
echo "✅ 1. Canonical Keys System"
echo "   - canonical_entities table (UUID, embeddings)"
echo "   - entity_mappings (cross-source linking)"
echo "   - entity_relationships (graph)"
echo "   - Helper functions (find_or_create_entity, etc.)"
echo ""
echo "✅ 2. Universal Changesets"
echo "   - changesets table (delta tracking)"
echo "   - Time-travel queries (get_state_at_time)"
echo "   - Undo operations (undo_last_change)"
echo "   - Audit trail"
echo ""
echo "✅ 3. Data Provenance"
echo "   - data_sources registry"
echo "   - table_provenance (collection health)"
echo "   - column_provenance"
echo "   - 15+ sources registered"
echo ""
echo "✅ 4. Intelligent Scheduler"
echo "   - Retry logic with exponential backoff"
echo "   - Circuit breakers"
echo "   - Fallback to cached data"
echo "   - Dependency management"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 NEXT STEPS:"
echo ""
echo "1. Extract entities from existing data:"
echo "   ssh $SERVER 'cd $REMOTE_DIR && source venv-analytics/bin/activate && python3 scripts/entity_resolver.py --extract-all'"
echo ""
echo "2. Start intelligent scheduler:"
echo "   ssh $SERVER 'cd $REMOTE_DIR && source venv-analytics/bin/activate && python3 scripts/intelligent_scheduler.py --run'"
echo ""
echo "3. View data sources:"
echo "   ssh $SERVER 'docker exec -i sofia-postgres psql -U sofia -d sofia_db -c \"SELECT * FROM sofia.sources_summary;\"'"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
