#!/usr/bin/env bash
#
# Run Released Container: Use the published hardening module
#
# Use this script to run the hardening pipeline using a published container image.
# This is for end-users who want to scan their code without cloning the module source.
#
# Prerequisites:
#   - Docker installed and running
#   - Dagger CLI installed: brew install dagger/tap/dagger
#
# Usage:
#   ./run-release.sh [source_dir] [output_dir]
#   ./run-release.sh /path/to/my-project ./reports
#
# Environment variables:
#   HARDENING_IMAGE - Container image to use (default: ghcr.io/huntridge-labs/hardening:latest)
#   SCANNERS        - Comma-separated scanners or groups (default: all)
#

set -euo pipefail

# Configuration
HARDENING_IMAGE="${HARDENING_IMAGE:-ghcr.io/huntridge-labs/hardening:latest}"
SOURCE_DIR="${1:-.}"
OUTPUT_DIR="${2:-./hardening-reports}"
SCANNERS="${SCANNERS:-all}"

echo "=== Hardening Security Scan (Released Container) ==="
echo "Image: $HARDENING_IMAGE"
echo "Source: $SOURCE_DIR"
echo "Output: $OUTPUT_DIR"
echo "Scanners: $SCANNERS"
echo ""

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Run the scan using the published container
echo "Running security scan from released container..."
dagger call -m "$HARDENING_IMAGE" \
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
