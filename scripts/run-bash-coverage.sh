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

# Find all bash test files in action directories
test_files=$(find .github/actions -path '*/tests/test-*.sh' -type f)

if [ -z "$test_files" ]; then
    echo "No bash test files found"
    exit 1
fi

# Count tests
test_count=$(echo "$test_files" | wc -l)
echo "Found $test_count bash test file(s)"
echo ""

# Run all bash tests with coverage
for test_file in $test_files; do
    test_name=$(basename "$test_file" .sh)
    echo "  → Running $test_name"

    bashcov --root . "$test_file" || {
        echo "    ✗ Test failed: $test_name"
        continue
    }

    echo "    ✓ Passed"
done

echo ""
if [ -f coverage/bash/cobertura.xml ]; then
    echo "✓ Bash coverage report generated: coverage/bash/cobertura.xml"
    ls -lh coverage/bash/cobertura.xml
else
    echo "⚠ No coverage report found"
    echo "Expected: coverage/bash/cobertura.xml"
fi
