#!/usr/bin/env bash
# Run bash unit tests with bashcov coverage
# Usage: ./scripts/run-bash-coverage.sh

set -euo pipefail

# Check if bashcov is installed
if ! command -v bashcov &> /dev/null; then
    echo "Error: bashcov is not installed"
    echo ""
    echo "Install with:  gem install bashcov simplecov-cobertura"
    exit 1
fi

echo "Running bash tests with bashcov coverage..."
mkdir -p coverage

# Run all bash tests with coverage
for test_file in tests/unit/bash/test-*.sh; do
    if [ ! -f "$test_file" ]; then
        continue
    fi

    test_name=$(basename "$test_file" .sh)
    echo "  → Running $test_name"

    bashcov --root . "$test_file" || {
        echo "    ✗ Test failed: $test_name"
        continue
    }

    echo "    ✓ Passed"
done

echo ""
if [ -f coverage/coverage.xml ]; then
    echo "✓ Bash coverage report generated: coverage/coverage.xml"
    ls -lh coverage/coverage.xml
else
    echo "⚠ No coverage report found"
