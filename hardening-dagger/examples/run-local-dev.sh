#!/usr/bin/env bash
#
# Local Development: Test the hardening module from source
#
# Use this script when developing/testing the Dagger module locally.
# It runs the module directly from your local source code.
#
# Prerequisites:
#   - Docker installed and running
#   - Dagger CLI installed: brew install dagger/tap/dagger
#   - Run from the hardening-dagger directory (or set MODULE_PATH)
#
# Usage:
#   ./examples/run-local-dev.sh [source_dir] [output_dir]
#   ./examples/run-local-dev.sh ../my-project ./reports
#
# Environment variables:
#   MODULE_PATH  - Path to the Dagger module (default: current directory)
#   SCANNERS     - Comma-separated scanners or groups (default: sast)
#

set -euo pipefail

# Configuration
MODULE_PATH="${MODULE_PATH:-.}"
SOURCE_DIR="${1:-.}"
OUTPUT_DIR="${2:-./hardening-reports}"
SCANNERS="${SCANNERS:-sast}"

echo "=== Hardening Security Scan (Local Development) ==="
echo "Module: $MODULE_PATH"
echo "Source: $SOURCE_DIR"
echo "Output: $OUTPUT_DIR"
echo "Scanners: $SCANNERS"
echo ""

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Run the scan using the local module
echo "Running security scan from local module..."
dagger call -m "$MODULE_PATH" \
  scan \
  --source "$SOURCE_DIR" \
  --scanners "$SCANNERS" \
  --output-format all \
  export --path "$OUTPUT_DIR"

echo ""
echo "=== Scan Complete ==="
echo ""

# Display summary
if [ -f "$OUTPUT_DIR/hardening-report.md" ]; then
  echo "Report generated at: $OUTPUT_DIR/hardening-report.md"

  # Show quick summary (first 30 lines)
  echo ""
  echo "--- Quick Summary ---"
  head -30 "$OUTPUT_DIR/hardening-report.md"
  echo "..."
  echo ""
fi

# Check threshold
if [ -f "$OUTPUT_DIR/THRESHOLD_EXCEEDED" ]; then
  echo "WARNING: Severity threshold exceeded!"
  cat "$OUTPUT_DIR/THRESHOLD_EXCEEDED"
  exit 1
fi

echo "All checks passed!"
echo ""
echo "Full reports available in: $OUTPUT_DIR"
echo "  - hardening-report.md   (human readable)"
echo "  - hardening-report.json (machine readable)"
echo "  - hardening-report.sarif (for code scanning tools)"
