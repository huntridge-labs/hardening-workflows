#!/bin/bash
set -e

echo "📋 Testing workflow synchronization validation..."
echo ""

# Extract core structure (remove comments, normalize paths and tags)
normalize_workflow() {
  local file="$1"

  # First pass: remove checkout-related lines specific to production workflow and conditional logic
  local temp=$(grep -v "^#" "$file" | \
    grep -v 'repository: huntridge-labs/hardening-workflows' | \
    grep -v -E 'ref: [^[:space:]]+' | \
    grep -v 'path: .hardening-workflows' | \
    grep -v 'sparse-checkout:' | \
    grep -v '.github/actions/get-job-id/action.yml' | \
    grep -v "Skip this checkout if we're already in the hardening-workflows repo" | \
    grep -v "if: github.repository != 'huntridge-labs/hardening-workflows'" | \
    grep -v "if: github.repository == 'huntridge-labs/hardening-workflows'")

  # Second pass: normalize remaining content and remove duplicates
  echo "$temp" | \
    grep -v "^name:" | \
    sed -E 's/@[^[:space:]]+//g' | \
    sed 's|huntridge-labs/hardening-workflows/.github/workflows/||g' | \
    sed 's|\./.github/workflows/||g' | \
    sed 's/name: Reusable Security Hardening Pipeline/name: Security Hardening Pipeline/g' | \
    sed 's/name: PR Testing - Reusable Security Hardening Pipeline/name: Security Hardening Pipeline/g' | \
    sed 's/name: Checkout hardening-workflows for actions/name: Checkout/g' | \
    sed 's/name: Checkout repository/name: Checkout/g' | \
    sed 's/name: Get job ID (external)/name: Get job ID/g' | \
    sed 's/name: Get job ID (local)/name: Get job ID/g' | \
    sed 's|./.hardening-workflows/.github/actions/|./.github/actions/|g' | \
    sed 's/id: job_id_ext/id: job_id/g' | \
    sed 's/id: job_id_local/id: job_id/g' | \
    grep -v 'name: Set job ID output' | \
    grep -v 'steps.job_id_local.outputs.job-id' | \
    grep -v 'steps.job_id_ext.outputs.job-id' | \
    grep -v 'echo "job-id=' | \
    grep -v '^\s*run: |' | \
    grep -v '^\s*if \[' | \
    grep -v '^\s*else' | \
    grep -v '^\s*fi' | \
    awk '!/^[[:space:]]*with:[[:space:]]*$/' | \
    grep -v '^[[:space:]]*$' | \
    awk '!seen[$0]++'  # Remove duplicate lines while preserving order
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
