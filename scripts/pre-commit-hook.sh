#!/usr/bin/env bash
# pre-commit-hook.sh - Git pre-commit hook for dataspine

set -e

echo "Running pre-commit checks..."

# Change to repository root
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Run smoketest
if [ -f "scripts/smoketest.sh" ]; then
    bash scripts/smoketest.sh || {
        echo ""
        echo "✗ Pre-commit checks failed!"
        echo "Please fix the issues above before committing."
        exit 1
    }
else
    echo "⚠ smoketest.sh not found, skipping checks"
fi

echo ""
echo "✓ Pre-commit checks passed"
exit 0
