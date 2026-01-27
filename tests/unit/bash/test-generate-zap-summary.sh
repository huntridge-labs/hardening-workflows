#!/usr/bin/env bash
# Unit tests for generate-zap-summary.sh
# Tests markdown generation for ZAP DAST scan results

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
GENERATOR_SCRIPT="$REPO_ROOT/.github/scripts/generate-zap-summary.sh"
ZAP_PARSER="$REPO_ROOT/.github/scripts/parse-zap-results.sh"

# Verify scripts exist
if [ ! -f "$GENERATOR_SCRIPT" ]; then
  echo -e "${RED}✗ Generator script not found: $GENERATOR_SCRIPT${NC}"
  exit 1
fi
if [ ! -f "$ZAP_PARSER" ]; then
  echo -e "${RED}✗ ZAP parser not found: $ZAP_PARSER${NC}"
  exit 1
fi

echo "Testing generate-zap-summary.sh"
echo "==============================="

# Setup test workspace
setup_test() {
  TEST_WORKSPACE="$(mktemp -d)"
  cd "$TEST_WORKSPACE"
  mkdir -p scanner-summaries
  mkdir -p zap-downloads
}

# Cleanup test workspace
cleanup_test() {
  cd "$REPO_ROOT"
  [ -n "${TEST_WORKSPACE:-}" ] && rm -rf "$TEST_WORKSPACE"
}

# Test: No scan results
test_no_scan_results() {
  local test_name="generate_zap_summary_no_results"
  setup_test

  export ZAP_PARSER

  # Run generator
  if "$GENERATOR_SCRIPT" 2>&1 | grep -q "No ZAP scan results found"; then
    if [ -f "scanner-summaries/zap.md" ]; then
      if grep -q "Status.*Skipped" "scanner-summaries/zap.md"; then
        assert_pass "$test_name"
      else
        assert_fail "$test_name" "Output missing 'Skipped' status"
      fi
    else
      assert_fail "$test_name" "Output file not created"
    fi
  else
    assert_fail "$test_name" "Expected 'No ZAP scan results found' message"
  fi

  cleanup_test
}

# Test: Single scan with baseline type
test_single_baseline_scan() {
  local test_name="generate_zap_summary_single_baseline"
  setup_test

  # Copy baseline scan results
  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER
  export ZAP_SCAN_TYPE="baseline"

  # Run generator
  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for key elements
    if echo "$output" | grep -q "ZAP (DAST)" && \
       echo "$output" | grep -q "Baseline" && \
       echo "$output" | grep -q "Completed"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Missing expected content in summary"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  unset ZAP_SCAN_TYPE
  cleanup_test
}

# Test: Multiple scans with different types
test_multiple_scan_types() {
  local test_name="generate_zap_summary_multiple_types"
  setup_test

  # Create multiple artifact directories
  mkdir -p "zap-downloads/zap-reports-a1b2c3d4-baseline-e5f6a7"
  mkdir -p "zap-downloads/zap-reports-b2c3d4e5-full-f6a7b8"

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/zap-reports-a1b2c3d4-baseline-e5f6a7/report_json.json"
  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/zap-reports-b2c3d4e5-full-f6a7b8/report_json.json"

  export ZAP_PARSER

  # Run generator
  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for scan breakdown section (appears with multiple scans)
    if echo "$output" | grep -q "Scan Breakdown" && \
       echo "$output" | grep -q "baseline" && \
       echo "$output" | grep -q "full" && \
       echo "$output" | grep -q "Scanned.*2"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Missing multi-scan elements"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Summary table format
test_summary_table_format() {
  local test_name="generate_zap_summary_table_format"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for markdown table structure
    if echo "$output" | grep -q "| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low |" && \
       echo "$output" | grep -q "|--------" && \
       echo "$output" | grep -q "Overall Findings Summary"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Table format incorrect"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Clean scan (no findings)
test_clean_scan() {
  local test_name="generate_zap_summary_clean"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-zero-findings.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for zero counts and success emoji
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

# Test: API scan type
test_api_scan_type() {
  local test_name="generate_zap_summary_api_scan"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER
  export ZAP_SCAN_TYPE="api"

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for API scan type in output
    if echo "$output" | grep -q "API Scan"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "API scan type not shown"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  unset ZAP_SCAN_TYPE
  cleanup_test
}

# Test: Full scan type
test_full_scan_type() {
  local test_name="generate_zap_summary_full_scan"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER
  export ZAP_SCAN_TYPE="full"

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for full scan type in output
    if echo "$output" | grep -q "Full Scan"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Full scan type not shown"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  unset ZAP_SCAN_TYPE
  cleanup_test
}

# Test: Collapsible details sections
test_collapsible_sections() {
  local test_name="generate_zap_summary_collapsible"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

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

# Test: Severity sections (Critical, High, Medium, Low)
test_severity_sections() {
  local test_name="generate_zap_summary_severity_sections"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for severity section summaries
    if echo "$output" | grep -q "Severity" && \
       echo "$output" | grep -q "findings"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Missing severity sections"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: GitHub step summary output
test_github_step_summary() {
  local test_name="generate_zap_summary_step_summary"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  # Create temp file for step summary
  export GITHUB_STEP_SUMMARY="$(mktemp)"
  export ZAP_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "$GITHUB_STEP_SUMMARY" ]; then
    local output
    output=$(cat "$GITHUB_STEP_SUMMARY")

    # Step summary should have heading and summary table
    if echo "$output" | grep -q "## 🕷️ ZAP DAST Summary" && \
       echo "$output" | grep -q "Overall Findings"; then
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

# Test: Target display in summary
test_target_display() {
  local test_name="generate_zap_summary_target_display"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for target URL/info
    if echo "$output" | grep -q "Target:"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Target not displayed"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Artifact links with GitHub env vars
test_artifact_links() {
  local test_name="generate_zap_summary_artifact_links"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER
  export GITHUB_REPOSITORY="huntridge-labs/hardening-workflows"
  export GITHUB_RUN_ID="54321"

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for artifact link
    if echo "$output" | grep -q "https://github.com/huntridge-labs/hardening-workflows/actions/runs/54321"; then
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

# Test: Required environment variables
test_required_env_vars() {
  local test_name="generate_zap_summary_required_env"
  setup_test

  # Save original value
  local original_parser="$ZAP_PARSER"

  # Unset required vars
  unset ZAP_PARSER

  # Should fail with error about missing env var (allow non-zero exit)
  if ("$GENERATOR_SCRIPT" 2>&1 || true) | grep -q "must be set"; then
    assert_pass "$test_name"
  else
    assert_fail "$test_name" "Missing required env var check failed"
  fi

  # Restore original value
  export ZAP_PARSER="$original_parser"

  cleanup_test
}

# Test: Scan mode display (docker-run, compose, url)
test_scan_mode_display() {
  local test_name="generate_zap_summary_scan_mode"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER
  export ZAP_SCAN_TYPE="baseline"
  export ZAP_SCAN_MODE="docker-run"

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check for scan mode in output
    if echo "$output" | grep -q "docker-run"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Scan mode not displayed"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  unset ZAP_SCAN_TYPE ZAP_SCAN_MODE
  cleanup_test
}

# Test: Unique alert count
test_unique_alert_count() {
  local test_name="generate_zap_summary_unique_count"
  setup_test

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Check that unique count is displayed
    if echo "$output" | grep -q "unique"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Unique count not displayed"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Test: Single artifact path handling
test_single_artifact_path() {
  local test_name="generate_zap_summary_single_artifact"
  setup_test

  # Place report directly in zap-downloads (single artifact case)
  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/report_json.json"

  export ZAP_PARSER
  export ZAP_SCAN_TYPE="baseline"

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Should successfully process single artifact
    if echo "$output" | grep -q "Completed"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Single artifact not processed correctly"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  unset ZAP_SCAN_TYPE
  cleanup_test
}

# Test: Multiple artifact path handling
test_multiple_artifact_paths() {
  local test_name="generate_zap_summary_multiple_artifacts"
  setup_test

  # Create multiple artifact subdirectories
  mkdir -p "zap-downloads/zap-reports-12345678-baseline-abc123"
  mkdir -p "zap-downloads/zap-reports-87654321-api-def456"

  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/zap-reports-12345678-baseline-abc123/report_json.json"
  cp "$FIXTURES_DIR/scanner-outputs/zap/results-baseline-scan.json" \
     "zap-downloads/zap-reports-87654321-api-def456/report_json.json"

  export ZAP_PARSER

  "$GENERATOR_SCRIPT" > /dev/null 2>&1

  if [ -f "scanner-summaries/zap.md" ]; then
    local output
    output=$(cat "scanner-summaries/zap.md")

    # Should show 2 scans
    if echo "$output" | grep -q "Scanned.*2"; then
      assert_pass "$test_name"
    else
      assert_fail "$test_name" "Multiple artifacts not processed correctly"
    fi
  else
    assert_fail "$test_name" "Output file not created"
  fi

  cleanup_test
}

# Run all tests
test_no_scan_results
test_single_baseline_scan
test_multiple_scan_types
test_summary_table_format
test_clean_scan
test_api_scan_type
test_full_scan_type
test_collapsible_sections
test_severity_sections
test_github_step_summary
test_target_display
test_artifact_links
test_required_env_vars
test_scan_mode_display
test_unique_alert_count
test_single_artifact_path
test_multiple_artifact_paths

# Print summary
print_summary
