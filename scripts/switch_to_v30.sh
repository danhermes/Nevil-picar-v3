#!/bin/bash
# Switch Nevil from v2.2 (Realtime API) back to v3.0 (batch API)

set -e

echo "🔄 Switching Nevil back to v3.0 (Batch API)"
echo "════════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Check if backup exists
echo -e "${BLUE}>>> Step 1: Checking for v3.0 backup${NC}"
if [ -f .nodes.v3.0.backup ]; then
    echo -e "${GREEN}✓${NC} Found .nodes.v3.0.backup"
else
    echo -e "${YELLOW}⚠${NC}  No backup found, creating default v3.0 configuration"
    # Create default v3.0 configuration
    cat > .nodes.v3.0.backup << 'EOF'
# Nevil v3.0 Root Configuration
version: "3.0"
description: "Nevil v3.0 test system"

system:
  framework_version: "3.0.0"
  log_level: "INFO"
  health_check_interval: 5.0
  shutdown_timeout: 10.0
  startup_delay: 2.0

environment:
  NEVIL_VERSION: "3.0"
  LOG_LEVEL: "INFO"

launch:
  # Phase 1: Core conversation loop + navigation + visual + LED indicator
  startup_order: ["led_indicator", "speech_recognition", "speech_synthesis", "ai_cognition", "navigation", "visual"]
  parallel_launch: false
  wait_for_healthy: true
  ready_timeout: 30.0

# OpenAI API key will be loaded from system environment
EOF
fi

# Step 2: Backup current v2.2 configuration
echo -e "${BLUE}>>> Step 2: Backing up v2.2 configuration${NC}"
if [ -f .nodes ]; then
    cp .nodes .nodes.v2.2.backup
    echo -e "${GREEN}✓${NC} Backed up current .nodes to .nodes.v2.2.backup"
fi

# Step 3: Restore v3.0 configuration
echo -e "${BLUE}>>> Step 3: Restoring v3.0 configuration${NC}"
cp .nodes.v3.0.backup .nodes
echo -e "${GREEN}✓${NC} Restored .nodes from v3.0 backup"

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Nevil switched back to v3.0 (Batch API)${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 Configuration Summary:"
echo "   Current config: .nodes (v3.0)"
echo "   Backup config:  .nodes.v2.2.backup (v2.2)"
echo ""
echo "🚀 Next Steps:"
echo "   1. Verify: cat .nodes"
echo "   2. Start:  ./nevil"
echo ""
echo "🔄 To switch back to v2.2:"
echo "   ./scripts/switch_to_realtime.sh"
echo ""
