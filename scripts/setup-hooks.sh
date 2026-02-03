#!/usr/bin/env bash
# setup-hooks.sh - Install Git hooks for dataspine

set -e

echo "=== Installing Git Hooks ==="

# Change to repository root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "✗ Not a git repository. Please run 'git init' first."
    exit 1
}

cd "$REPO_ROOT"

# Create hooks directory if it doesn't exist
HOOKS_DIR=".git/hooks"
mkdir -p "$HOOKS_DIR"

# Install pre-commit hook
echo "→ Installing pre-commit hook..."
cp scripts/pre-commit-hook.sh "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"
echo "✓ Pre-commit hook installed at $HOOKS_DIR/pre-commit"

# Make smoketest executable
if [ -f "scripts/smoketest.sh" ]; then
    chmod +x scripts/smoketest.sh
    echo "✓ Made smoketest.sh executable"
fi

echo ""
echo "=== ✓ Git hooks installed successfully ==="
echo ""
echo "The pre-commit hook will run automatically before each commit."
echo "To bypass the hook (not recommended), use: git commit --no-verify"
exit 0
