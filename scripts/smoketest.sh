#!/usr/bin/env bash
# smoketest.sh - Quick validation of code quality and basic tests

set -e

echo "=== Running Dataspine Smoke Tests ==="

# Change to project root
cd "$(dirname "$0")/.."

# 1. Check Python syntax
echo "→ Checking Python syntax..."
python3 -m py_compile src/dataspine/__init__.py
python3 -m py_compile src/dataspine/config.py
python3 -m py_compile src/dataspine/logging_config.py
python3 -m py_compile scripts/run_pipeline.py
echo "✓ Python syntax valid"

# 2. Run ruff linter
echo "→ Running ruff linter..."
if command -v ruff &> /dev/null; then
    ruff check src/ scripts/ tests/ || {
        echo "✗ Linting failed"
        exit 1
    }
    echo "✓ Linting passed"
else
    echo "⚠ ruff not found, skipping lint check"
fi

# 3. Run fast tests (if any exist)
echo "→ Running tests..."
if command -v pytest &> /dev/null; then
    if [ -d "tests" ] && [ "$(find tests -name 'test_*.py' -o -name '*_test.py' | wc -l)" -gt 0 ]; then
        pytest tests/ -v -x --tb=short || {
            echo "✗ Tests failed"
            exit 1
        }
        echo "✓ Tests passed"
    else
        echo "⚠ No tests found, skipping"
    fi
else
    echo "⚠ pytest not found, skipping tests"
fi

# 4. Validate Docker Compose syntax
echo "→ Validating Docker Compose..."
if command -v docker-compose &> /dev/null; then
    docker-compose -f infra/docker-compose.yml config > /dev/null || {
        echo "✗ Docker Compose validation failed"
        exit 1
    }
    echo "✓ Docker Compose valid"
else
    echo "⚠ docker-compose not found, skipping validation"
fi

echo ""
echo "=== ✓ All smoke tests passed ==="
exit 0
