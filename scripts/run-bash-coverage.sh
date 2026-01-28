#!/usr/bin/env bash
# Run bash unit tests with kcov coverage
# Usage: ./scripts/run-bash-coverage.sh

set -euo pipefail

# Check if kcov is installed
if ! command -v kcov &> /dev/null; then
    echo "Error: kcov is not installed"
    echo ""
    echo "Install on macOS:   brew install kcov"
    echo "Install on Ubuntu:  sudo apt-get install kcov"
    exit 1
fi

# Create coverage directory
COVERAGE_DIR="coverage/bash"
mkdir -p "$COVERAGE_DIR"

# Run each bash test with coverage
echo "Running bash tests with kcov coverage..."
for test_file in tests/unit/bash/test-*.sh; do
    if [ ! -f "$test_file" ]; then
        continue
    fi

    test_name=$(basename "$test_file" .sh)
    echo "  → Running $test_name"

    # Run test with kcov
    kcov --exclude-pattern=/usr/share,/usr/lib,/opt \
         "$COVERAGE_DIR/$test_name" \
         "$test_file" || {
        echo "    ✗ Test failed: $test_name"
        continue
    }

    echo "    ✓ Coverage report: $COVERAGE_DIR/$test_name/index.html"
done

echo ""
echo "✓ Bash coverage reports generated in $COVERAGE_DIR/"
echo "  View reports: open $COVERAGE_DIR/test-*/index.html"
echo ""

# Show coverage summary if available
if [ -f "$COVERAGE_DIR"/test-parse-grype-results/index.json ]; then
    echo "Example coverage data available in JSON format"
fi
