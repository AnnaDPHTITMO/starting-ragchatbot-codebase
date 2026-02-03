#!/bin/bash

# Frontend Code Quality Check Script
# Run this script to check and fix code quality issues

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$FRONTEND_DIR"

echo "========================================"
echo "Frontend Code Quality Check"
echo "========================================"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

# Parse arguments
FIX_MODE=false
for arg in "$@"; do
    case $arg in
        --fix)
            FIX_MODE=true
            shift
            ;;
    esac
done

if [ "$FIX_MODE" = true ]; then
    echo "Running in FIX mode..."
    echo ""

    echo "1. Formatting code with Prettier..."
    npm run format
    echo ""

    echo "2. Fixing linting issues with ESLint..."
    npm run lint:fix
    echo ""

    echo "All fixes applied!"
else
    echo "Running in CHECK mode (use --fix to auto-fix issues)..."
    echo ""

    ERRORS=0

    echo "1. Checking code formatting with Prettier..."
    if npm run format:check; then
        echo "   Formatting check passed."
    else
        echo "   Formatting issues found. Run with --fix to auto-fix."
        ERRORS=$((ERRORS + 1))
    fi
    echo ""

    echo "2. Checking code quality with ESLint..."
    if npm run lint; then
        echo "   Linting check passed."
    else
        echo "   Linting issues found. Run with --fix to auto-fix."
        ERRORS=$((ERRORS + 1))
    fi
    echo ""

    if [ $ERRORS -gt 0 ]; then
        echo "========================================"
        echo "Quality check completed with $ERRORS issue(s)"
        echo "Run: ./scripts/quality-check.sh --fix"
        echo "========================================"
        exit 1
    else
        echo "========================================"
        echo "All quality checks passed!"
        echo "========================================"
    fi
fi
