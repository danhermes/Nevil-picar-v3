#!/bin/bash
#
# Test Runner for Nevil 2.2 Realtime API Integration Tests
# Runs all integration tests with various reporting options
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test directory
TEST_DIR="tests/realtime"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Nevil 2.2 Realtime API Integration Tests${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Function to print section headers
section() {
    echo
    echo -e "${YELLOW}>>> $1${NC}"
    echo
}

# Function to run tests with a label
run_test() {
    local label=$1
    local cmd=$2

    echo -e "${GREEN}Running: ${label}${NC}"
    if eval "$cmd"; then
        echo -e "${GREEN}✓ Passed${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Parse command line arguments
VERBOSE=""
COVERAGE=""
SPECIFIC_TEST=""
COLLECT_ONLY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v -s"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=nevil_framework.realtime --cov-report=term --cov-report=html"
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --collect)
            COLLECT_ONLY="--collect-only"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  -v, --verbose     Run tests with verbose output"
            echo "  -c, --coverage    Run tests with coverage report"
            echo "  -t, --test FILE   Run specific test file"
            echo "  --collect         Just collect tests, don't run"
            echo "  -h, --help        Show this help message"
            echo
            echo "Examples:"
            echo "  $0                                    # Run all tests"
            echo "  $0 -v                                 # Run with verbose output"
            echo "  $0 -c                                 # Run with coverage"
            echo "  $0 -t test_integration_realtime_pipeline.py  # Run specific file"
            echo "  $0 --collect                          # Just list tests"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check if we're in the correct directory
if [ ! -d "$TEST_DIR" ]; then
    echo -e "${RED}Error: Must be run from project root directory${NC}"
    echo -e "${YELLOW}Current directory: $(pwd)${NC}"
    echo -e "${YELLOW}Expected to find: $TEST_DIR${NC}"
    exit 1
fi

# If just collecting, do that and exit
if [ -n "$COLLECT_ONLY" ]; then
    section "Collecting Tests"
    pytest $TEST_DIR --collect-only
    exit 0
fi

# If specific test requested, run only that
if [ -n "$SPECIFIC_TEST" ]; then
    section "Running Specific Test: $SPECIFIC_TEST"
    pytest "$TEST_DIR/$SPECIFIC_TEST" $VERBOSE $COVERAGE
    exit $?
fi

# Run all test suites
section "1. Pipeline Integration Tests (test_integration_realtime_pipeline.py)"
run_test "Full Voice Pipeline Tests" \
    "pytest $TEST_DIR/test_integration_realtime_pipeline.py $VERBOSE $COVERAGE"
PIPELINE_RESULT=$?

section "2. Audio Playback Validation Tests (test_audio_playback_validation.py)"
run_test "Hardware Playback Validation" \
    "pytest $TEST_DIR/test_audio_playback_validation.py $VERBOSE $COVERAGE"
PLAYBACK_RESULT=$?

section "3. Node Integration Tests (test_node_integration.py)"
run_test "Message Bus & Inter-Node Communication" \
    "pytest $TEST_DIR/test_node_integration.py $VERBOSE $COVERAGE"
NODE_RESULT=$?

# Summary
echo
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Test Results Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo

if [ $PIPELINE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Pipeline Integration Tests: PASSED"
else
    echo -e "${RED}✗${NC} Pipeline Integration Tests: FAILED"
fi

if [ $PLAYBACK_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Audio Playback Validation: PASSED"
else
    echo -e "${RED}✗${NC} Audio Playback Validation: FAILED"
fi

if [ $NODE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Node Integration Tests: PASSED"
else
    echo -e "${RED}✗${NC} Node Integration Tests: FAILED"
fi

echo

# Overall result
if [ $PIPELINE_RESULT -eq 0 ] && [ $PLAYBACK_RESULT -eq 0 ] && [ $NODE_RESULT -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  ALL TESTS PASSED ✓${NC}"
    echo -e "${GREEN}================================================${NC}"
    exit 0
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}  SOME TESTS FAILED ✗${NC}"
    echo -e "${RED}================================================${NC}"
    exit 1
fi
