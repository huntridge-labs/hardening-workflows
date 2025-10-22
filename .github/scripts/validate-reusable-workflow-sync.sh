#!/bin/bash
set -e

echo "📋 Testing workflow synchronization validation..."
echo ""

# Extract core structure (remove comments, normalize paths and tags)
normalize_workflow() {
  local file="$1"
  grep -v "^#" "$file" | \
  grep -v "^name:" | \
  sed -E 's/@[^[:space:]]+//g' | \
  sed 's|huntridge-labs/hardening-workflows/.github/workflows/||g' | \
  sed 's|\./.github/workflows/||g' | \
  sed 's/name: Reusable Security Hardening Pipeline/name: Security Hardening Pipeline/g' | \
  sed 's/name: PR Testing - Reusable Security Hardening Pipeline/name: Security Hardening Pipeline/g' | \
  grep -v '^[[:space:]]*$'  # Remove blank lines
}

PROD_NORMALIZED=$(normalize_workflow .github/workflows/reusable-security-hardening.yml)
PR_NORMALIZED=$(normalize_workflow .github/workflows/pr-reusable-security-hardening.yml)

if diff <(echo "$PROD_NORMALIZED") <(echo "$PR_NORMALIZED") > /dev/null 2>&1; then
  echo "✅ Workflows are in sync (structurally identical)"
  exit 0
else
  echo "❌ Workflows have structural differences:"
  echo ""
  diff <(echo "$PROD_NORMALIZED") <(echo "$PR_NORMALIZED") | head -50
  echo ""
  echo "❌ Validation failed - workflows are out of sync"
  exit 1
fi
