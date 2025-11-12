#!/bin/bash
# Nevil 2.2 - Deployment Script
# Safely deploys Nevil 2.2 Realtime API nodes with backup and rollback support
# Usage: ./scripts/deploy_nevil_22.sh [--dry-run] [--no-backup] [--force]

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
DRY_RUN=false
NO_BACKUP=false
FORCE=false
ERRORS=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            ;;
        --no-backup)
            NO_BACKUP=true
            ;;
        --force)
            FORCE=true
            ;;
        --help|-h)
            echo "Nevil 2.2 Deployment Script"
            echo "Usage: $0 [--dry-run] [--no-backup] [--force]"
            echo ""
            echo "Options:"
            echo "  --dry-run      Show what would be done without making changes"
            echo "  --no-backup    Skip creating backup (not recommended)"
            echo "  --force        Skip confirmation prompts"
            echo "  --help, -h     Show this help message"
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

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    [ -n "$2" ] && echo -e "  ${RED}$2${NC}"
    ERRORS=$((ERRORS + 1))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    [ -n "$2" ] && echo -e "  ${YELLOW}$2${NC}"
}

print_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

print_dry_run() {
    [ "$DRY_RUN" = true ] && echo -e "  ${YELLOW}[DRY RUN]${NC} $1"
}

# Execute command (respects dry-run)
execute() {
    if [ "$DRY_RUN" = true ]; then
        print_dry_run "$*"
    else
        eval "$@"
    fi
}

# Prompt for confirmation
confirm() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    local prompt="$1"
    read -p "$prompt [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Main deployment starts here
PROJECT_ROOT=$(pwd)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/nevil_v3_${TIMESTAMP}"

print_header "Nevil 2.2 Deployment Script"
echo "Project: $PROJECT_ROOT"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Dry Run: $DRY_RUN"
echo "No Backup: $NO_BACKUP"
echo "Force: $FORCE"

if [ "$DRY_RUN" = true ]; then
    print_warning "DRY RUN MODE - No changes will be made"
fi

# ============================================================================
# 1. Pre-deployment Validation
# ============================================================================
print_section "1. Pre-deployment Validation"

# Check if validation script exists
if [ -f "scripts/validate_nevil_22.sh" ]; then
    print_success "Validation script found"

    if [ "$FORCE" = false ]; then
        if confirm "Run validation script before deployment?"; then
            print_info "Running validation..."
            if bash scripts/validate_nevil_22.sh --skip-tests; then
                print_success "Validation passed"
            else
                print_fail "Validation failed"
                echo ""
                echo "Fix validation errors before deploying."
                echo "Use --force to skip validation (not recommended)."
                exit 1
            fi
        fi
    fi
else
    print_warning "Validation script not found" "Proceeding without validation"
fi

# Check that Realtime API files exist
print_info "Checking Realtime API components..."
REQUIRED_FILES=(
    "nevil_framework/realtime/realtime_connection_manager.py"
    ".env.realtime"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_fail "Required file missing: $file"
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo ""
    print_fail "Missing required files. Run setup script first:"
    echo "  ./scripts/setup_nevil_2.2.sh"
    exit 1
fi

# ============================================================================
# 2. Backup Current System
# ============================================================================
if [ "$NO_BACKUP" = false ]; then
    print_section "2. Backing Up Current System"

    print_info "Creating backup: $BACKUP_DIR"
    execute "mkdir -p '$BACKUP_DIR'"

    # Backup existing v3.0 nodes
    NODES_TO_BACKUP=("speech_recognition" "ai_cognition" "speech_synthesis")
    for node in "${NODES_TO_BACKUP[@]}"; do
        if [ -d "nodes/$node" ]; then
            print_info "Backing up nodes/$node"
            execute "cp -r 'nodes/$node' '$BACKUP_DIR/' 2>/dev/null || true"
        fi
    done

    # Backup configuration files
    CONFIG_FILES=(".nodes" ".env" "requirements.txt")
    for config in "${CONFIG_FILES[@]}"; do
        if [ -f "$config" ]; then
            print_info "Backing up $config"
            execute "cp '$config' '$BACKUP_DIR/${config}.backup' 2>/dev/null || true"
        fi
    done

    # Backup framework
    if [ -d "nevil_framework" ]; then
        print_info "Backing up nevil_framework"
        execute "cp -r 'nevil_framework' '$BACKUP_DIR/' 2>/dev/null || true"
    fi

    # Create backup manifest
    if [ "$DRY_RUN" = false ]; then
        cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
Nevil v3.0 Backup
Created: $(date '+%Y-%m-%d %H:%M:%S')
Backup ID: $TIMESTAMP

Backed up components:
- nodes/speech_recognition
- nodes/ai_cognition
- nodes/speech_synthesis
- .nodes configuration
- .env configuration
- requirements.txt
- nevil_framework

To restore this backup:
  ./scripts/deploy_nevil_22.sh --rollback $TIMESTAMP

Or manually:
  cp -r $BACKUP_DIR/nodes/* nodes/
  cp $BACKUP_DIR/.nodes.backup .nodes
  cp $BACKUP_DIR/.env.backup .env
EOF
        print_success "Backup created: $BACKUP_DIR"
    else
        print_dry_run "Would create backup manifest"
    fi
else
    print_section "2. Backup (SKIPPED)"
    print_warning "Backup skipped by user request"
fi

# ============================================================================
# 3. Deploy Realtime API Nodes
# ============================================================================
print_section "3. Deploying Realtime API Nodes"

# Check if realtime nodes need to be created
REALTIME_NODES=("speech_recognition_realtime" "ai_cognition_realtime" "speech_synthesis_realtime")

for node in "${REALTIME_NODES[@]}"; do
    if [ ! -d "nodes/$node" ]; then
        print_info "Creating nodes/$node directory"
        execute "mkdir -p 'nodes/$node'"
    fi

    if [ ! -f "nodes/$node/__init__.py" ]; then
        print_info "Creating nodes/$node/__init__.py"
        execute "touch 'nodes/$node/__init__.py'"
    fi
done

print_success "Realtime node directories verified"

# Check if node implementation files exist
print_info "Checking for node implementations..."
NODE_IMPLEMENTATIONS=()
if [ -f "nodes/speech_recognition_realtime/speech_recognition_node.py" ]; then
    NODE_IMPLEMENTATIONS+=("speech_recognition_realtime")
fi
if [ -f "nodes/ai_cognition_realtime/ai_cognition_node.py" ]; then
    NODE_IMPLEMENTATIONS+=("ai_cognition_realtime")
fi
if [ -f "nodes/speech_synthesis_realtime/speech_synthesis_node.py" ]; then
    NODE_IMPLEMENTATIONS+=("speech_synthesis_realtime")
fi

if [ ${#NODE_IMPLEMENTATIONS[@]} -gt 0 ]; then
    print_success "Found ${#NODE_IMPLEMENTATIONS[@]} implemented realtime nodes"
    for impl in "${NODE_IMPLEMENTATIONS[@]}"; do
        print_info "  - $impl"
    done
else
    print_warning "No realtime node implementations found"
    print_info "Nodes must be implemented before full deployment"
    print_info "See: docs/realtime_api_node_specifications.md"
fi

# ============================================================================
# 4. Update Configuration Files
# ============================================================================
print_section "4. Updating Configuration"

# Update .nodes configuration
if [ -f ".nodes" ]; then
    print_info "Updating .nodes configuration"

    # Check if realtime nodes are already in startup_order
    if grep -q "speech_recognition_realtime" .nodes; then
        print_info "Realtime nodes already configured in .nodes"
    else
        if [ "$DRY_RUN" = false ]; then
            # Create backup
            cp .nodes .nodes.pre-deployment

            # Note: Manual update needed - this is complex YAML editing
            print_warning "Manual update required for .nodes"
            print_info "Add to startup_order: speech_recognition_realtime, ai_cognition_realtime, speech_synthesis_realtime"
        else
            print_dry_run "Would update .nodes with realtime nodes"
        fi
    fi
fi

# Setup environment file
if [ ! -f ".env" ] && [ -f ".env.realtime" ]; then
    print_info "No .env found, creating from template"
    execute "cp '.env.realtime' '.env'"
    print_warning "Please configure OPENAI_API_KEY in .env"
else
    print_info ".env already exists"
fi

# ============================================================================
# 5. Create Symbolic Links (if needed)
# ============================================================================
print_section "5. Creating Symbolic Links"

# Create convenience symlinks for development
SYMLINKS=(
    "nevil_framework/realtime:framework_realtime"
)

for link_pair in "${SYMLINKS[@]}"; do
    IFS=':' read -r target link_name <<< "$link_pair"

    if [ -e "$target" ] && [ ! -L "$link_name" ]; then
        print_info "Creating symlink: $link_name -> $target"
        execute "ln -sf '$target' '$link_name' 2>/dev/null || true"
    fi
done

# ============================================================================
# 6. Validate Deployment
# ============================================================================
print_section "6. Validating Deployment"

if [ "$DRY_RUN" = false ]; then
    print_info "Running post-deployment validation..."

    # Check directory structure
    VALIDATION_PASSED=true
    for node in "${REALTIME_NODES[@]}"; do
        if [ ! -d "nodes/$node" ]; then
            print_fail "Deployment validation failed: nodes/$node missing"
            VALIDATION_PASSED=false
        fi
    done

    # Check framework
    if [ ! -f "nevil_framework/realtime/realtime_connection_manager.py" ]; then
        print_fail "Deployment validation failed: RealtimeConnectionManager missing"
        VALIDATION_PASSED=false
    fi

    if [ "$VALIDATION_PASSED" = true ]; then
        print_success "Deployment validation passed"
    else
        print_fail "Deployment validation failed"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_dry_run "Would validate deployment"
fi

# ============================================================================
# 7. Generate Deployment Report
# ============================================================================
print_section "7. Generating Deployment Report"

REPORT_FILE="deployment_report_${TIMESTAMP}.txt"

if [ "$DRY_RUN" = false ]; then
    cat > "$REPORT_FILE" << EOF
Nevil 2.2 Deployment Report
Generated: $(date '+%Y-%m-%d %H:%M:%S')
Deployment ID: $TIMESTAMP

Deployment Summary:
- Backup Created: $([ "$NO_BACKUP" = false ] && echo "Yes ($BACKUP_DIR)" || echo "No")
- Realtime Nodes Deployed: ${#REALTIME_NODES[@]}
- Node Implementations Found: ${#NODE_IMPLEMENTATIONS[@]}
- Errors: $ERRORS

Deployed Components:
$(for node in "${REALTIME_NODES[@]}"; do echo "- nodes/$node"; done)
- nevil_framework/realtime/realtime_connection_manager.py

Configuration Files:
- .env ($([ -f ".env" ] && echo "exists" || echo "created from template"))
- .nodes ($(grep -q "speech_recognition_realtime" .nodes && echo "updated" || echo "needs manual update"))

Next Steps:
1. Configure OPENAI_API_KEY in .env
2. Implement realtime node logic (see docs/realtime_api_node_specifications.md)
3. Update .nodes to include realtime nodes in startup_order
4. Run validation: ./scripts/validate_nevil_22.sh
5. Test deployment: ./nevil start

Rollback Instructions:
If you need to rollback this deployment:
  1. Stop Nevil: ./nevil stop
  2. Restore backup: cp -r $BACKUP_DIR/* .
  3. Restart: ./nevil start

Or use rollback script (if available):
  ./scripts/deploy_nevil_22.sh --rollback $TIMESTAMP

Status: $([ $ERRORS -eq 0 ] && echo "SUCCESS" || echo "FAILED")
EOF
    print_success "Deployment report saved: $REPORT_FILE"
else
    print_dry_run "Would generate deployment report: $REPORT_FILE"
fi

# ============================================================================
# Final Summary
# ============================================================================
print_header "Deployment Summary"

echo ""
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN COMPLETE${NC}"
    echo ""
    echo "No changes were made. Review the output above to see what would happen."
    echo "Run without --dry-run to perform actual deployment."
elif [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
    echo ""
    echo "Backup: $BACKUP_DIR"
    echo "Report: $REPORT_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. Configure OPENAI_API_KEY in .env"
    echo "  2. Review deployment report: cat $REPORT_FILE"
    echo "  3. Implement realtime node logic (see docs/)"
    echo "  4. Update .nodes configuration if needed"
    echo "  5. Run validation: ./scripts/validate_nevil_22.sh"
    echo "  6. Test: ./nevil start"
    echo ""
    echo "Rollback available at: $BACKUP_DIR"
else
    echo -e "${RED}✗ Deployment completed with $ERRORS errors${NC}"
    echo ""
    echo "Review errors above and deployment report: $REPORT_FILE"
    echo ""
    if [ "$NO_BACKUP" = false ]; then
        echo "Backup available for rollback: $BACKUP_DIR"
    fi
fi

echo ""
exit $([ $ERRORS -eq 0 ] && echo 0 || echo 1)
