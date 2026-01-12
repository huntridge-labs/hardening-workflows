#!/usr/bin/env bash
#
# Example: Running hardening scans locally
#
# Prerequisites:
#   - Docker installed and running
#   - Dagger CLI installed: curl -fsSL https://dl.dagger.io/dagger/install.sh | sh
#
# No GitHub, GitLab, or any CI system required!

set -euo pipefail

# Configuration
HARDENING_IMAGE="${HARDENING_IMAGE:-ghcr.io/huntridge-labs/hardening:latest}"
SOURCE_DIR="${1:-.}"
OUTPUT_DIR="${2:-./hardening-reports}"
SCANNERS="${SCANNERS:-all}"

echo "=== Hardening Security Scan ==="
echo "Source: $SOURCE_DIR"
echo "Output: $OUTPUT_DIR"
echo "Scanners: $SCANNERS"
echo ""

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Run the scan
echo "Running security scan..."
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
