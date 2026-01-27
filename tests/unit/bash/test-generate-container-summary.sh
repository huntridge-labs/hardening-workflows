#!/usr/bin/env bash
# Unit tests for generate-container-summary.sh
# Tests markdown generation for container scan results

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FIXTURES_DIR="$REPO_ROOT/tests/fixtures"

# Test helper functions
assert_pass() {
  local test_name="$1"
  echo -e "${GREEN}✓${NC} PASS: $test_name"
  TESTS_PASSED=$((TESTS_PASSED + 1))
}

assert_fail() {
  local test_name="$1"
  local reason="${2:-Unknown failure}"
  echo -e "${RED}✗${NC} FAIL: $test_name"
  echo "  Reason: $reason"
  TESTS_FAILED=$((TESTS_FAILED + 1))
}

print_summary() {
  echo ""
  echo "======================================"
  echo "Tests passed: $TESTS_PASSED"
  echo "Tests failed: $TESTS_FAILED"
  echo "======================================"
  if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
  else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
  fi
}

# Script under test
GENERATOR_SCRIPT="$REPO_ROOT/.github/scripts/generate-container-summary.sh"
TRIVY_PARSER="$REPO_ROOT/.github/scripts/parse-trivy-results.sh"
GRYPE_PARSER="$REPO_ROOT/.github/scripts/parse-grype-results.sh"

# Verify scripts exist
if [ ! -f "$GENERATOR_SCRIPT" ]; then
  echo -e "${RED}✗ Generator script not found: $GENERATOR_SCRIPT${NC}"
  exit 1
fi
if [ ! -f "$TRIVY_PARSER" ]; then
  echo -e "${RED}✗ Trivy parser not found: $TRIVY_PARSER${NC}"
  exit 1
fi
if [ ! -f "$GRYPE_PARSER" ]; then
  echo -e "${RED}✗ Grype parser not found: $GRYPE_PARSER${NC}"
  exit 1
fi

echo "Testing generate-container-summary.sh"
echo "======================================"

# Setup test workspace
setup_test() {
  TEST_WORKSPACE="$(mktemp -d)"
  cd "$TEST_WORKSPACE"
  mkdir -p scanner-summaries
}

# Cleanup test workspace
cleanup_test() {
  cd "$REPO_ROOT"
  [ -n "${TEST_WORKSPACE:-}" ] && rm -rf "$TEST_WORKSPACE"
}

# Test: No scan results
test_no_scan_results() {
  local test_name="generate_container_summary_no_results"
  setup_test

  export TRIVY_PARSER GRYPE_PARSER

  # Run generator
  if "$GENERATOR_SCRIPT" 2>&1 | grep -q "No container scan results found"; then
    if [ -f "scanner-summaries/container.md" ]; then
      if grep -q "Status.*Skipped" "scanner-summaries/container.md"; then
        assert_pass "$test_name"
      else
        assert_fail "$test_name" "Output missing 'Skipped' status"
      fi
    else
      assert_fail "$test_name" "Output file not created"
    fi
  else
    assert_fail "$test_name" "Expected 'No container scan results found' message"
  fi

  cleanup_test
}

# Test: Single container with Trivy results
test_single_container_trivy() {
  local test_name="generate_container_summary_single_trivy"
  setup_test

  # Create artifact structure
  mkdir -p "container-scan-results-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"

  export TRIVY_PARSER GRYPE_PARSER

  # Run generator
  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check for key elements
    if echo "$output" | grep -q "Container Security" && \
       echo "$output" | grep -q "Completed" && \
       echo "$output" | grep -q "alpine"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Missing expected content in summary"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Single container with both Trivy and Grype
test_single_container_both_scanners() {
  local test_name="generate_container_summary_both_scanners"
  setup_test

  # Create artifact structure with both scanners
  mkdir -p "container-scan-results-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"
  cp "$FIXTURES_DIR/scanner-outputs/grype/results-with-findings.json" \
     "container-scan-results-alpine/grype-alpine-results.json"

  export TRIVY_PARSER GRYPE_PARSER

  # Run generator
  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check for both scanner sections
    if echo "$output" | grep -q "Trivy Scanner" && \
       echo "$output" | grep -q "Grype Scanner" && \
       echo "$output" | grep -q "Combined (Deduplicated)"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Missing scanner sections"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Multiple containers
test_multiple_containers() {
  local test_name="generate_container_summary_multiple"
  setup_test

  # Create artifact structure for multiple containers
  mkdir -p "container-scan-results-alpine"
  mkdir -p "container-scan-results-nginx"

  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-nginx/trivy-nginx-results.json"

  export TRIVY_PARSER GRYPE_PARSER

  # Run generator
  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check for container breakdown section (only appears with multiple containers)
    if echo "$output" | grep -q "Container Breakdown" && \
       echo "$output" | grep -q "alpine" && \
       echo "$output" | grep -q "nginx" && \
       echo "$output" | grep -q "Scanned.*2 containers"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Missing multi-container elements"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Summary table format
test_summary_table_format() {
  local test_name="generate_container_summary_table_format"
  setup_test

  mkdir -p "container-scan-results-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"

  export TRIVY_PARSER GRYPE_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check for markdown table structure
    if echo "$output" | grep -q "| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low |" && \
       echo "$output" | grep -q "|--------" && \
       echo "$output" | grep -q "Combined Findings Summary"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Table format incorrect"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Clean scan (no vulnerabilities)
test_clean_scan() {
  local test_name="generate_container_summary_clean"
  setup_test

  mkdir -p "container-scan-results-clean"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-zero-findings.json" \
     "container-scan-results-clean/trivy-clean-results.json"

  export TRIVY_PARSER GRYPE_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check for zero counts
    if echo "$output" | grep -q "| \*\*0\*\* | \*\*0\*\* | \*\*0\*\* | \*\*0\*\* | \*\*0\*\* |" && \
       echo "$output" | grep -q "✅"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Clean scan not properly represented"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Collapsible details sections
test_collapsible_sections() {
  local test_name="generate_container_summary_collapsible"
  setup_test

  mkdir -p "container-scan-results-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"

  export TRIVY_PARSER GRYPE_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check for collapsible HTML tags
    if echo "$output" | grep -q "<details>" && \
       echo "$output" | grep -q "</details>" && \
       echo "$output" | grep -q "<summary>"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Missing collapsible sections"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Container with build failure
test_build_failure() {
  local test_name="generate_container_summary_build_failure"
  setup_test

  # Create directory but no results files (simulates build failure)
  mkdir -p "container-scan-results-failed"

  export TRIVY_PARSER GRYPE_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check for failure indicators
    if echo "$output" | grep -q "Build Failures: 1" || \
       echo "$output" | grep -q "❌.*failed"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Build failure not indicated"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: GitHub step summary output
test_github_step_summary() {
  local test_name="generate_container_summary_step_summary"
  setup_test

  mkdir -p "container-scan-results-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"

  # Create temp file for step summary
  export GITHUB_STEP_SUMMARY="$(mktemp)"
  export TRIVY_PARSER GRYPE_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "$GITHUB_STEP_SUMMARY" ]; then
    local output
    output=$(cat "$GITHUB_STEP_SUMMARY")

    # Step summary should have heading and summary table
    if echo "$output" | grep -q "## 🐳 Container Security Scan Summary" && \
       echo "$output" | grep -q "Combined Findings Summary"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Step summary format incorrect"
    fi
  else
    assert_fail "$test_name" "Step summary file not created"
  fi

  rm -f "$GITHUB_STEP_SUMMARY"
  cleanup_test
}

# Test: Deduplication of CVEs
test_cve_deduplication() {
  local test_name="generate_container_summary_deduplication"
  setup_test

  # Use both scanners which may report same CVEs
  mkdir -p "container-scan-results-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"
  cp "$FIXTURES_DIR/scanner-outputs/grype/results-with-findings.json" \
     "container-scan-results-alpine/grype-alpine-results.json"

  export TRIVY_PARSER GRYPE_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check that "Unique" count is mentioned (indicates deduplication occurred)
    if echo "$output" | grep -q "Unique" && \
       echo "$output" | grep -q "Combined (Deduplicated)"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Deduplication not evident in output"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Artifact links with GitHub env vars
test_artifact_links() {
  local test_name="generate_container_summary_artifact_links"
  setup_test

  mkdir -p "container-scan-results-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"

  export TRIVY_PARSER GRYPE_PARSER
  export GITHUB_REPOSITORY="huntridge-labs/hardening-workflows"
  export GITHUB_RUN_ID="12345"

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Check for artifact link
    if echo "$output" | grep -q "https://github.com/huntridge-labs/hardening-workflows/actions/runs/12345"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Artifact link not present"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  unset GITHUB_REPOSITORY GITHUB_RUN_ID
  cleanup_test
}

# Test: SBOM containers are skipped
test_sbom_skip() {
  local test_name="generate_container_summary_skip_sbom"
  setup_test

  # Create SBOM container (should be skipped)
  mkdir -p "container-scan-results-sbom-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-sbom-alpine/trivy-sbom-alpine-results.json"

  # Create regular container
  mkdir -p "container-scan-results-alpine"
  cp "$FIXTURES_DIR/scanner-outputs/trivy/results-with-findings.json" \
     "container-scan-results-alpine/trivy-alpine-results.json"

  export TRIVY_PARSER GRYPE_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/container.md" ]; then
    local output
    output=$(cat "scanner-summaries/container.md")

    # Should show only 1 scanned container (SBOM skipped)
    if echo "$output" | grep -q "Scanned.*1" && \
       ! echo "$output" | grep -q "sbom-alpine"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "SBOM container not properly skipped"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Required environment variables
test_required_env_vars() {
  local test_name="generate_container_summary_required_env"
  setup_test

  # Unset required vars
  unset TRIVY_PARSER GRYPE_PARSER

  # Should fail with error about missing env vars (allow non-zero exit)
  if "$GENERATOR_SCRIPT" 2>&1 | grep -q "must be set" || \
     ("$GENERATOR_SCRIPT" 2>&1 || true) | grep -q "must be set"; then
    assert_pass "$test_name"
  else
    assert_fail "$test_name" "Missing required env var check failed"
  fi

  cleanup_test
}

# Run all tests
test_no_scan_results
test_single_container_trivy
test_single_container_both_scanners
test_multiple_containers
test_summary_table_format
test_clean_scan
test_collapsible_sections
test_build_failure
test_github_step_summary
test_cve_deduplication
test_artifact_links
test_sbom_skip
test_required_env_vars

# Print summary
print_summary
