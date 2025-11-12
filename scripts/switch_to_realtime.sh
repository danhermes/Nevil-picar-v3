#!/bin/bash
# Switch Nevil from v3.0 (batch API) to v2.2 (Realtime API)

set -e

echo "🔄 Switching Nevil to Realtime API (v2.2)"
echo "════════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT=$(pwd)

# Step 1: Backup current configuration
echo -e "${BLUE}>>> Step 1: Backing up v3.0 configuration${NC}"
if [ -f .nodes ]; then
    cp .nodes .nodes.v3.0.backup
    echo -e "${GREEN}✓${NC} Backed up .nodes to .nodes.v3.0.backup"
else
    echo -e "${YELLOW}⚠${NC}  No .nodes file found"
fi

# Step 2: Copy realtime nodes to proper locations
echo -e "${BLUE}>>> Step 2: Setting up Realtime API nodes${NC}"

# Copy speech_recognition_node22.py to nodes directory
if [ -f nevil_framework/realtime/speech_recognition_node22.py ]; then
    cp nevil_framework/realtime/speech_recognition_node22.py nodes/speech_recognition_realtime/
    echo -e "${GREEN}✓${NC} Copied speech_recognition_node22.py"
fi

# Copy ai_node22.py to nodes directory
if [ -f nevil_framework/realtime/ai_node22.py ]; then
    cp nevil_framework/realtime/ai_node22.py nodes/ai_cognition_realtime/
    echo -e "${GREEN}✓${NC} Copied ai_node22.py"
fi

# Copy speech_synthesis_node22.py to nodes directory
if [ -f nevil_framework/realtime/speech_synthesis_node22.py ]; then
    cp nevil_framework/realtime/speech_synthesis_node22.py nodes/speech_synthesis_realtime/
    echo -e "${GREEN}✓${NC} Copied speech_synthesis_node22.py"
fi

# Copy .messages files
if [ -f nevil_framework/realtime/.messages ]; then
    cp nevil_framework/realtime/.messages nodes/speech_recognition_realtime/
    echo -e "${GREEN}✓${NC} Copied speech_recognition .messages config"
fi

if [ -f nevil_framework/realtime/ai_node22.messages ]; then
    cp nevil_framework/realtime/ai_node22.messages nodes/ai_cognition_realtime/.messages
    echo -e "${GREEN}✓${NC} Copied ai_cognition .messages config"
fi

# speech_synthesis already has .messages in nodes/speech_synthesis_realtime/

# Step 3: Create v2.2 configuration
echo -e "${BLUE}>>> Step 3: Creating v2.2 configuration${NC}"

cat > .nodes.v2.2 << 'EOF'
# Nevil v2.2 Root Configuration
# OpenAI Realtime API Integration
version: "2.2"
description: "Nevil v2.2 with OpenAI Realtime API (streaming STT/TTS)"

system:
  framework_version: "2.2.0"
  log_level: "INFO"
  health_check_interval: 5.0
  shutdown_timeout: 10.0
  startup_delay: 2.0

environment:
  NEVIL_VERSION: "2.2"
  LOG_LEVEL: "INFO"
  NEVIL_REALTIME_ENABLED: "true"

launch:
  # Phase 1: Realtime API nodes (streaming) + navigation + visual + LED indicator
  startup_order: ["led_indicator", "speech_recognition_realtime", "speech_synthesis_realtime", "ai_cognition_realtime", "navigation", "visual"]
  parallel_launch: false
  wait_for_healthy: true
  ready_timeout: 30.0

# OpenAI API key will be loaded from system environment
# Realtime API WebSocket connection managed by RealtimeConnectionManager
EOF

echo -e "${GREEN}✓${NC} Created .nodes.v2.2 configuration"

# Step 4: Create node entry point files
echo -e "${BLUE}>>> Step 4: Creating node entry points${NC}"

# speech_recognition_realtime/__init__.py
cat > nodes/speech_recognition_realtime/__init__.py << 'EOF'
"""Speech Recognition Node (Realtime API v2.2)"""
from .speech_recognition_node22 import SpeechRecognitionNode22

# Export the node class (launcher expects this)
SpeechRecognitionNode = SpeechRecognitionNode22
EOF
echo -e "${GREEN}✓${NC} Created speech_recognition_realtime/__init__.py"

# ai_cognition_realtime/__init__.py
cat > nodes/ai_cognition_realtime/__init__.py << 'EOF'
"""AI Cognition Node (Realtime API v2.2)"""
from .ai_node22 import AINode22

# Export the node class (launcher expects this)
AINode = AINode22
EOF
echo -e "${GREEN}✓${NC} Created ai_cognition_realtime/__init__.py"

# speech_synthesis_realtime/__init__.py
cat > nodes/speech_synthesis_realtime/__init__.py << 'EOF'
"""Speech Synthesis Node (Realtime API v2.2)"""
from .speech_synthesis_node22 import SpeechSynthesisNode22

# Export the node class (launcher expects this)
SpeechSynthesisNode = SpeechSynthesisNode22
EOF
echo -e "${GREEN}✓${NC} Created speech_synthesis_realtime/__init__.py"

# Step 5: Switch to v2.2 configuration
echo -e "${BLUE}>>> Step 5: Activating v2.2 configuration${NC}"
cp .nodes.v2.2 .nodes
echo -e "${GREEN}✓${NC} Activated .nodes.v2.2 (current .nodes)"

# Step 6: Verify OPENAI_API_KEY
echo -e "${BLUE}>>> Step 6: Verifying environment${NC}"
if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo -e "${GREEN}✓${NC} OPENAI_API_KEY configured in .env"
else
    echo -e "${YELLOW}⚠${NC}  OPENAI_API_KEY not found in .env"
    echo -e "${YELLOW}   Please add: OPENAI_API_KEY=sk-your-key-here${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Nevil switched to Realtime API (v2.2)${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 Configuration Summary:"
echo "   Current config: .nodes (v2.2)"
echo "   Backup config:  .nodes.v3.0.backup (v3.0)"
echo ""
echo "🚀 Next Steps:"
echo "   1. Verify: cat .nodes"
echo "   2. Start:  ./nevil"
echo "   3. Test:   Say 'Hello Nevil'"
echo ""
echo "🔄 To switch back to v3.0:"
echo "   ./scripts/switch_to_v30.sh"
echo ""
echo "📈 Expected Performance:"
echo "   v3.0: 5-8 seconds latency"
echo "   v2.2: 1.5-2.1 seconds latency"
echo "   Improvement: 75-80% reduction"
echo ""
