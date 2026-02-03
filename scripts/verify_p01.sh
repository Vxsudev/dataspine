#!/usr/bin/env bash
# verify_p01.sh - Verify Phase 01 project structure and setup

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Dataspine Phase 01 Verification ==="
echo ""

# Change to project root
cd "$(dirname "$0")/.."

ERRORS=0
WARNINGS=0

check_file() {
    local file=$1
    local desc=$2
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc: $file"
    else
        echo -e "${RED}✗${NC} $desc: $file (MISSING)"
        ((ERRORS++))
    fi
}

check_dir() {
    local dir=$1
    local desc=$2
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $desc: $dir"
    else
        echo -e "${RED}✗${NC} $desc: $dir (MISSING)"
        ((ERRORS++))
    fi
}

check_python_syntax() {
    local file=$1
    local desc=$2
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $desc syntax valid: $file"
        else
            echo -e "${RED}✗${NC} $desc syntax invalid: $file"
            ((ERRORS++))
        fi
    fi
}

check_content() {
    local file=$1
    local pattern=$2
    local desc=$3
    if [ -f "$file" ]; then
        if grep -q "$pattern" "$file"; then
            echo -e "${GREEN}✓${NC} $desc found in $file"
        else
            echo -e "${YELLOW}⚠${NC} $desc not found in $file"
            ((WARNINGS++))
        fi
    fi
}

echo "--- Directory Structure ---"
check_dir "src/dataspine" "Core package"
check_dir "src/dataspine/schemas" "Schemas module"
check_dir "src/dataspine/adapters" "Adapters module"
check_dir "src/dataspine/normalization" "Normalization module"
check_dir "src/dataspine/validation" "Validation module"
check_dir "src/dataspine/scheduling" "Scheduling module"
check_dir "src/dataspine/detection" "Detection module"
check_dir "src/dataspine/reconciliation" "Reconciliation module"
check_dir "src/dataspine/audit" "Audit module"
check_dir "scripts" "Scripts directory"
check_dir "tests" "Tests directory"
check_dir "tests/fixtures" "Test fixtures"
check_dir "infra" "Infrastructure"
check_dir "config" "Configuration"
check_dir ".github/workflows" "CI workflows"

echo ""
echo "--- Core Files ---"
check_file "src/dataspine/__init__.py" "Package init"
check_file "src/dataspine/config.py" "Configuration module"
check_file "src/dataspine/logging_config.py" "Logging configuration"
check_file "scripts/run_pipeline.py" "Pipeline runner"
check_file "requirements.txt" "Python dependencies"
check_file "pyproject.toml" "Project configuration"
check_file "Makefile" "Build targets"
check_file ".gitignore" "Git ignore rules"
check_file "README.md" "Documentation"

echo ""
echo "--- Schema Files ---"
check_file "src/dataspine/schemas/__init__.py" "Schemas init"
check_file "src/dataspine/schemas/market_data.py" "Market data schema"
check_file "src/dataspine/schemas/trade_data.py" "Trade data schema"

echo ""
echo "--- Adapter Files ---"
check_file "src/dataspine/adapters/__init__.py" "Adapters init"
check_file "src/dataspine/adapters/base.py" "Base adapter"

echo ""
echo "--- Infrastructure Files ---"
check_file "infra/Dockerfile" "Dockerfile"
check_file "infra/docker-compose.yml" "Docker Compose"
check_file "config/.env.example" "Environment template"

echo ""
echo "--- CI/CD Files ---"
check_file ".github/workflows/ci.yml" "GitHub CI workflow"

echo ""
echo "--- Automation Scripts ---"
check_file "scripts/smoketest.sh" "Smoke test script"
check_file "scripts/pre-commit-hook.sh" "Pre-commit hook"
check_file "scripts/setup-hooks.sh" "Hook setup script"

echo ""
echo "--- Python Syntax Validation ---"
check_python_syntax "src/dataspine/__init__.py" "Package init"
check_python_syntax "src/dataspine/config.py" "Config module"
check_python_syntax "src/dataspine/logging_config.py" "Logging module"
check_python_syntax "scripts/run_pipeline.py" "Pipeline runner"

echo ""
echo "--- Content Validation ---"
check_content "src/dataspine/__init__.py" "__version__" "Version export"
check_content "src/dataspine/config.py" "load_config" "Config loader function"
check_content "src/dataspine/logging_config.py" "setup_logging" "Logging setup function"
check_content "scripts/run_pipeline.py" "argparse" "CLI argument parser"
check_content "requirements.txt" "fastapi" "FastAPI dependency"
check_content "requirements.txt" "psycopg2-binary" "PostgreSQL driver"
check_content "requirements.txt" "pytest" "Testing framework"
check_content "infra/docker-compose.yml" "dataspine" "Network definition"
check_content "infra/docker-compose.yml" "postgres" "Database service"

echo ""
echo "--- Git Repository ---"
if [ -d ".git" ]; then
    echo -e "${GREEN}✓${NC} Git repository initialized"
    if [ -f ".git/hooks/pre-commit" ]; then
        echo -e "${GREEN}✓${NC} Pre-commit hook installed"
    else
        echo -e "${YELLOW}⚠${NC} Pre-commit hook not installed (run: bash scripts/setup-hooks.sh)"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗${NC} Git repository not initialized (run: git init)"
    ((ERRORS++))
fi

echo ""
echo "--- Functional Tests ---"

# Test run_pipeline.py
echo -n "Testing pipeline script... "
if PYTHONPATH=src python3 scripts/run_pipeline.py --mode live --dry-run > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    ((ERRORS++))
fi

# Test config loading (should fail without .env)
echo -n "Testing config validation... "
if PYTHONPATH=src python3 -c "from dataspine.config import load_config; load_config()" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} (config loaded without .env - unexpected)"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓${NC} (correctly fails without .env)"
fi

# Test logging setup
echo -n "Testing logging setup... "
if PYTHONPATH=src python3 -c "from dataspine.logging_config import setup_logging; setup_logging('INFO')" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    ((ERRORS++))
fi

echo ""
echo "==================================="
echo "Verification Complete"
echo "==================================="
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 01 setup verified successfully!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ Please review warnings above${NC}"
    fi
    exit 0
else
    echo -e "${RED}✗ Phase 01 setup incomplete - please fix errors above${NC}"
    exit 1
fi
