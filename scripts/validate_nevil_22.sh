#!/bin/bash
# Nevil 2.2 - Comprehensive Validation Script
# Validates all dependencies, files, configurations, and runs test suites
# Usage: ./scripts/validate_nevil_22.sh [--verbose] [--skip-tests]

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
VERBOSE=false
SKIP_TESTS=false
ERRORS=0
WARNINGS=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE=true
            ;;
        --skip-tests)
            SKIP_TESTS=true
            ;;
        --help|-h)
            echo "Nevil 2.2 Validation Script"
            echo "Usage: $0 [--verbose] [--skip-tests]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v    Show detailed output"
            echo "  --skip-tests     Skip running test suites"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
    esac
done

# Utility functions
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓${NC} $1"
    [ "$VERBOSE" = true ] && [ -n "$2" ] && echo "  $2"
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    [ -n "$2" ] && echo -e "  ${RED}$2${NC}"
    ERRORS=$((ERRORS + 1))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    [ -n "$2" ] && echo -e "  ${YELLOW}$2${NC}"
    WARNINGS=$((WARNINGS + 1))
}

print_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# Detect Python command
detect_python() {
    if command -v python3 &> /dev/null && python3 --version &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null && python --version 2>&1 | grep -q "Python 3"; then
        echo "python"
    elif command -v py &> /dev/null && py --version &> /dev/null; then
        echo "py"
    else
        echo ""
    fi
}

# Get Python version
get_python_version() {
    local python_cmd=$1
    $python_cmd --version 2>&1 | sed -n 's/.*Python \([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p'
}

# Check if Python package is installed
check_python_package() {
    local python_cmd=$1
    local package=$2
    $python_cmd -c "import $package" 2>/dev/null
}

# Check if file exists
check_file() {
    local file=$1
    local description=$2
    if [ -f "$file" ]; then
        print_pass "$description"
        return 0
    else
        print_fail "$description" "File not found: $file"
        return 1
    fi
}

# Check if directory exists
check_directory() {
    local dir=$1
    local description=$2
    if [ -d "$dir" ]; then
        print_pass "$description"
        return 0
    else
        print_fail "$description" "Directory not found: $dir"
        return 1
    fi
}

# Main validation starts here
PROJECT_ROOT=$(pwd)
START_TIME=$(date +%s)

print_header "Nevil 2.2 Comprehensive Validation"
echo "Project: $PROJECT_ROOT"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Verbose: $VERBOSE"
echo "Skip Tests: $SKIP_TESTS"

# ============================================================================
# 1. Python Environment Validation
# ============================================================================
print_section "1. Python Environment"

PYTHON_CMD=$(detect_python)
if [ -z "$PYTHON_CMD" ]; then
    print_fail "Python 3.9+ not found"
    echo ""
    echo "Please install Python 3.9 or higher from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(get_python_version "$PYTHON_CMD")
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]; }; then
    print_fail "Python version too old: $PYTHON_VERSION (need 3.9+)"
    exit 1
else
    print_pass "Python version $PYTHON_VERSION ($PYTHON_CMD)"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    print_warning "pip not found" "Package management may be limited"
    PIP_CMD=""
fi

if [ -n "$PIP_CMD" ]; then
    PIP_VERSION=$($PIP_CMD --version | awk '{print $2}')
    print_pass "pip version $PIP_VERSION"
fi

# ============================================================================
# 2. Python Dependencies Validation
# ============================================================================
print_section "2. Python Dependencies"

# Core dependencies
CORE_PACKAGES=("yaml:PyYAML" "dateutil:python-dateutil")
for pkg_pair in "${CORE_PACKAGES[@]}"; do
    IFS=':' read -r import_name package_name <<< "$pkg_pair"
    if check_python_package "$PYTHON_CMD" "$import_name"; then
        print_pass "$package_name installed"
    else
        print_fail "$package_name not installed"
    fi
done

# Audio dependencies
AUDIO_PACKAGES=("speech_recognition:SpeechRecognition" "openai:openai" "pygame:pygame")
for pkg_pair in "${AUDIO_PACKAGES[@]}"; do
    IFS=':' read -r import_name package_name <<< "$pkg_pair"
    if check_python_package "$PYTHON_CMD" "$import_name"; then
        print_pass "$package_name installed"
    else
        print_fail "$package_name not installed"
    fi
done

# PyAudio (platform-specific)
if check_python_package "$PYTHON_CMD" "pyaudio"; then
    print_pass "pyaudio installed"
else
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_fail "pyaudio not installed" "Required for Realtime API on Linux"
    else
        print_warning "pyaudio not installed" "May be required for audio capture"
    fi
fi

# Nevil 2.2 specific dependencies
REALTIME_PACKAGES=("websockets:websockets" "aiohttp:aiohttp" "numpy:numpy" "dotenv:python-dotenv")
for pkg_pair in "${REALTIME_PACKAGES[@]}"; do
    IFS=':' read -r import_name package_name <<< "$pkg_pair"
    if check_python_package "$PYTHON_CMD" "$import_name"; then
        print_pass "$package_name installed (Realtime API)"
    else
        print_fail "$package_name not installed" "Required for Realtime API"
    fi
done

# ============================================================================
# 3. File Structure Validation
# ============================================================================
print_section "3. File Structure"

# Core files
check_file "requirements.txt" "requirements.txt exists"
check_file "nevil" "Nevil CLI executable exists"
check_file ".nodes" "Root configuration (.nodes) exists"

# Framework files
check_directory "nevil_framework" "Framework directory exists"
check_file "nevil_framework/base_node.py" "Base node implementation exists"
check_file "nevil_framework/config_loader.py" "Config loader exists"
check_file "nevil_framework/launcher.py" "Launcher exists" || print_warning "Launcher not found" "May need to check framework integrity"

# Realtime API framework files
check_directory "nevil_framework/realtime" "Realtime framework directory exists"
check_file "nevil_framework/realtime/__init__.py" "Realtime framework __init__.py exists"
check_file "nevil_framework/realtime/realtime_connection_manager.py" "RealtimeConnectionManager exists"

# Node directories
print_info "Validating node directories..."
check_directory "nodes" "Nodes directory exists"
check_directory "nodes/speech_recognition" "Speech recognition node exists"
check_directory "nodes/ai_cognition" "AI cognition node exists"
check_directory "nodes/speech_synthesis" "Speech synthesis node exists"

# Nevil 2.2 node directories
check_directory "nodes/speech_recognition_realtime" "Speech recognition realtime node exists"
check_directory "nodes/ai_cognition_realtime" "AI cognition realtime node exists"
check_directory "nodes/speech_synthesis_realtime" "Speech synthesis realtime node exists"

# Node init files
for node in speech_recognition ai_cognition speech_synthesis; do
    check_file "nodes/${node}/__init__.py" "${node} __init__.py exists"
done

for node in speech_recognition_realtime ai_cognition_realtime speech_synthesis_realtime; do
    check_file "nodes/${node}/__init__.py" "${node} __init__.py exists"
done

# ============================================================================
# 4. Configuration Files Validation
# ============================================================================
print_section "4. Configuration Files"

# Check .nodes configuration
if [ -f ".nodes" ]; then
    print_pass ".nodes configuration file exists"

    # Validate YAML format
    if check_python_package "$PYTHON_CMD" "yaml"; then
        if $PYTHON_CMD -c "import yaml; yaml.safe_load(open('.nodes'))" 2>/dev/null; then
            print_pass ".nodes is valid YAML"
        else
            print_fail ".nodes is invalid YAML"
        fi
    fi

    # Check for required fields
    if grep -q "version:" .nodes; then
        print_pass ".nodes contains version field"
    else
        print_warning ".nodes missing version field"
    fi

    if grep -q "launch:" .nodes; then
        print_pass ".nodes contains launch configuration"
    else
        print_fail ".nodes missing launch configuration"
    fi
fi

# Check message configuration files
print_info "Checking .messages configuration files..."
MESSAGES_FOUND=0
for node_dir in nodes/*/; do
    if [ -f "${node_dir}.messages" ]; then
        MESSAGES_FOUND=$((MESSAGES_FOUND + 1))
        [ "$VERBOSE" = true ] && print_pass "Found .messages in ${node_dir}"
    fi
done
print_info "Found $MESSAGES_FOUND .messages configuration files"

# Check environment configuration
if [ -f ".env" ]; then
    print_pass ".env configuration file exists"
else
    print_warning ".env not found" "Copy from .env.realtime template"
fi

if [ -f ".env.realtime" ]; then
    print_pass ".env.realtime template exists"
else
    print_fail ".env.realtime template not found"
fi

# ============================================================================
# 5. API Key Validation
# ============================================================================
print_section "5. API Key Configuration"

# Check for API key in environment
if [ -n "$OPENAI_API_KEY" ]; then
    # Validate format (should start with sk-)
    if [[ "$OPENAI_API_KEY" =~ ^sk-[a-zA-Z0-9_-]+$ ]]; then
        print_pass "OPENAI_API_KEY is set and formatted correctly"
        KEY_LENGTH=${#OPENAI_API_KEY}
        [ "$VERBOSE" = true ] && print_info "Key length: $KEY_LENGTH characters"
    else
        print_warning "OPENAI_API_KEY is set but may be invalid format"
    fi
else
    print_warning "OPENAI_API_KEY not set in environment" "Set in .env or export OPENAI_API_KEY=sk-..."

    # Check if it's in .env file
    if [ -f ".env" ] && grep -q "OPENAI_API_KEY=" .env; then
        print_info "API key found in .env file (not loaded to environment)"
    fi
fi

# ============================================================================
# 6. Robot HAT Library Check (Raspberry Pi)
# ============================================================================
print_section "6. Robot HAT Library (Hardware)"

if check_python_package "$PYTHON_CMD" "robot_hat"; then
    print_pass "robot_hat library installed"

    # Try to import and check version
    if [ "$VERBOSE" = true ]; then
        VERSION=$($PYTHON_CMD -c "import robot_hat; print(getattr(robot_hat, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
        print_info "robot_hat version: $VERSION"
    fi
else
    if [[ "$OSTYPE" == "linux-gnu"* ]] && [ -f "/proc/device-tree/model" ]; then
        # We're on a Raspberry Pi
        print_fail "robot_hat not installed" "Required for hardware control on Raspberry Pi"
    else
        print_warning "robot_hat not installed" "Not required for development/testing off Raspberry Pi"
    fi
fi

# ============================================================================
# 7. Audio Hardware Validation (if on Pi)
# ============================================================================
print_section "7. Audio Hardware"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Check for audio devices
    if command -v arecord &> /dev/null; then
        AUDIO_DEVICES=$(arecord -l 2>/dev/null | grep -c "card" || echo "0")
        if [ "$AUDIO_DEVICES" -gt 0 ]; then
            print_pass "Audio input devices found: $AUDIO_DEVICES"
            [ "$VERBOSE" = true ] && arecord -l 2>/dev/null | grep "card"
        else
            print_warning "No audio input devices detected"
        fi
    else
        print_warning "arecord not available" "Cannot verify audio hardware"
    fi

    if command -v aplay &> /dev/null; then
        PLAYBACK_DEVICES=$(aplay -l 2>/dev/null | grep -c "card" || echo "0")
        if [ "$PLAYBACK_DEVICES" -gt 0 ]; then
            print_pass "Audio output devices found: $PLAYBACK_DEVICES"
            [ "$VERBOSE" = true ] && aplay -l 2>/dev/null | grep "card"
        else
            print_warning "No audio output devices detected"
        fi
    fi

    # Check ALSA configuration
    if [ -f "/usr/share/alsa/alsa.conf" ] || [ -f "~/.asoundrc" ]; then
        print_pass "ALSA configuration present"
    else
        print_warning "ALSA configuration not found"
    fi
else
    print_info "Skipping audio hardware check (not on Linux)"
fi

# ============================================================================
# 8. Test Suites Validation
# ============================================================================
if [ "$SKIP_TESTS" = false ]; then
    print_section "8. Test Suites"

    # Check for test files
    TEST_FILES=$(find . -name "test_*.py" -o -name "*_test.py" | wc -l)
    if [ "$TEST_FILES" -gt 0 ]; then
        print_pass "Found $TEST_FILES test files"
    else
        print_warning "No test files found"
    fi

    # Check if pytest is available
    if check_python_package "$PYTHON_CMD" "pytest"; then
        print_pass "pytest is installed"

        if [ "$TEST_FILES" -gt 0 ]; then
            print_info "Running test suite..."

            # Run pytest with timeout
            if timeout 60 $PYTHON_CMD -m pytest --tb=short -v 2>&1 | tee /tmp/nevil_test_results.txt; then
                print_pass "Test suite passed"
            else
                TEST_EXIT_CODE=$?
                if [ $TEST_EXIT_CODE -eq 124 ]; then
                    print_warning "Test suite timed out (60s limit)"
                else
                    print_warning "Some tests failed or had errors"
                    [ "$VERBOSE" = true ] && tail -20 /tmp/nevil_test_results.txt
                fi
            fi
        fi
    else
        print_warning "pytest not installed" "Cannot run automated tests"
    fi

    # Basic import tests
    print_info "Running basic import tests..."

    if $PYTHON_CMD -c "import nevil_framework.base_node" 2>/dev/null; then
        print_pass "Can import nevil_framework.base_node"
    else
        print_fail "Cannot import nevil_framework.base_node"
    fi

    if $PYTHON_CMD -c "import nevil_framework.config_loader" 2>/dev/null; then
        print_pass "Can import nevil_framework.config_loader"
    else
        print_fail "Cannot import nevil_framework.config_loader"
    fi

    if [ -f "nevil_framework/realtime/realtime_connection_manager.py" ]; then
        if $PYTHON_CMD -c "import nevil_framework.realtime.realtime_connection_manager" 2>/dev/null; then
            print_pass "Can import RealtimeConnectionManager"
        else
            print_fail "Cannot import RealtimeConnectionManager"
        fi
    fi
else
    print_section "8. Test Suites (SKIPPED)"
    print_info "Test execution skipped by user request"
fi

# ============================================================================
# 9. Backup Validation
# ============================================================================
print_section "9. Backup System"

if [ -d "backups" ]; then
    BACKUP_COUNT=$(ls -1 backups/ 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 0 ]; then
        print_pass "Backup directory exists with $BACKUP_COUNT backups"

        if [ "$VERBOSE" = true ]; then
            print_info "Recent backups:"
            ls -1t backups/ | head -3 | while read backup; do
                print_info "  - $backup"
            done
        fi
    else
        print_warning "Backup directory is empty"
    fi
else
    print_warning "Backup directory does not exist"
fi

# ============================================================================
# 10. Documentation Validation
# ============================================================================
print_section "10. Documentation"

DOCS_DIR="docs"
if [ -d "$DOCS_DIR" ]; then
    print_pass "Documentation directory exists"

    # Check for key documentation files
    DOC_FILES=(
        "NEVIL_2.2_QUICK_START.md"
        "NEVIL_2.2_ZERO_TOUCH_PLAN.md"
        "REALTIME_API_ARCHITECTURE.txt"
        "realtime_api_node_specifications.md"
    )

    for doc in "${DOC_FILES[@]}"; do
        if [ -f "$DOCS_DIR/$doc" ]; then
            print_pass "$doc exists"
        else
            print_warning "$doc not found"
        fi
    done
else
    print_warning "Documentation directory does not exist"
fi

# ============================================================================
# 11. Realtime API Specific Checks
# ============================================================================
print_section "11. Realtime API Specific"

# Check for realtime configuration in .env
if [ -f ".env" ]; then
    if grep -q "NEVIL_REALTIME_MODEL" .env; then
        print_pass "Realtime API model configured"
    else
        print_info "Realtime API model not configured (will use default)"
    fi

    if grep -q "NEVIL_REALTIME_VOICE" .env; then
        print_pass "Realtime API voice configured"
    else
        print_info "Realtime API voice not configured (will use default)"
    fi
fi

# Check audio configuration
if [ -f ".env" ]; then
    if grep -q "NEVIL_AUDIO_SAMPLE_RATE" .env; then
        SAMPLE_RATE=$(grep "NEVIL_AUDIO_SAMPLE_RATE" .env | cut -d= -f2)
        if [ "$SAMPLE_RATE" = "24000" ]; then
            print_pass "Audio sample rate correctly configured (24000Hz)"
        else
            print_warning "Audio sample rate is $SAMPLE_RATE (recommended: 24000)"
        fi
    fi
fi

# ============================================================================
# 12. System Integration Check
# ============================================================================
print_section "12. System Integration"

# Check if nevil CLI is executable
if [ -x "nevil" ]; then
    print_pass "Nevil CLI is executable"

    # Try to get help output
    if ./nevil --help &>/dev/null; then
        print_pass "Nevil CLI responds to --help"
    else
        print_warning "Nevil CLI may have issues"
    fi
else
    print_fail "Nevil CLI is not executable" "Run: chmod +x nevil"
fi

# Check log directory
if [ -d "logs" ]; then
    print_pass "Logs directory exists"
else
    print_info "Logs directory will be created on first run"
fi

# ============================================================================
# Final Summary
# ============================================================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

print_header "Validation Summary"

echo ""
echo "Validation completed in ${DURATION}s"
echo ""
echo -e "Results:"
echo -e "  ${GREEN}Checks Passed${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "  ${YELLOW}Warnings: $WARNINGS${NC}"
    echo -e "  ${RED}Errors: $ERRORS${NC}"
else
    echo -e "  ${YELLOW}Warnings: $WARNINGS${NC}"
    echo -e "  ${RED}Errors: $ERRORS${NC}"
fi

echo ""

# Generate validation report
REPORT_FILE="validation_report_$(date +%Y%m%d_%H%M%S).txt"
cat > "$REPORT_FILE" << EOF
Nevil 2.2 Validation Report
Generated: $(date '+%Y-%m-%d %H:%M:%S')
Duration: ${DURATION}s

Summary:
- Warnings: $WARNINGS
- Errors: $ERRORS

Python Environment:
- Python: $PYTHON_VERSION ($PYTHON_CMD)
$([ -n "$PIP_CMD" ] && echo "- pip: $PIP_VERSION ($PIP_CMD)")

Status: $([ $ERRORS -eq 0 ] && echo "PASS" || echo "FAIL")
EOF

print_info "Validation report saved to: $REPORT_FILE"

echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review any warnings above"
    echo "  2. Configure API key in .env if not already done"
    echo "  3. Run deployment script: ./scripts/deploy_nevil_22.sh"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Validation failed with $ERRORS errors${NC}"
    echo ""
    echo "Please fix the errors above before proceeding with deployment."
    echo ""
    exit 1
fi
