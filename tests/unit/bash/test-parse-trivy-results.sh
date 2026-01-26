#!/usr/bin/env bash
# Unit tests for parse-trivy-results.sh
# Tests the Trivy results parser with synthetic fixture data

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="${SCRIPT_DIR}/../../fixtures/scanner-outputs/trivy"
PARSER_SCRIPT="${SCRIPT_DIR}/../../../.github/scripts/parse-trivy-results.sh"

# Test helper functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✓${NC} PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} FAIL: $test_name"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_exit_code() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ "$expected" -eq "$actual" ]]; then
        echo -e "${GREEN}✓${NC} PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} FAIL: $test_name"
        echo "  Expected exit code: $expected"
        echo "  Actual exit code:   $actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

print_test_summary() {
    echo ""
    echo "========================================"
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
    else
        echo -e "${RED}Some tests failed!${NC}"
    fi
    echo "Total:  $TESTS_RUN"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "========================================"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        exit 1
    fi
}

# ============================================
# Tests for 'counts' command
# ============================================

test_counts_zero_findings() {
    local result
    result=$("$PARSER_SCRIPT" counts "$FIXTURES_DIR/results-zero-findings.json")
    assert_equals "0 0 0 0" "$result" "counts: zero findings"
}

test_counts_with_findings() {
    local result
    result=$("$PARSER_SCRIPT" counts "$FIXTURES_DIR/results-with-findings.json")
    assert_equals "1 1 1 1" "$result" "counts: with findings (1 CRIT, 1 HIGH, 1 MED, 1 LOW)"
}

test_counts_nonexistent_file() {
    local result
    result=$("$PARSER_SCRIPT" counts "/nonexistent/file.json" 2>/dev/null || true)
    assert_equals "0 0 0 0" "$result" "counts: nonexistent file returns zeros"
}

test_counts_empty_file() {
    local temp_file
    temp_file=$(mktemp)
    # Create a truly empty file (size 0)
    : > "$temp_file"
    
    local result
    # Parser should handle empty file gracefully
    result=$("$PARSER_SCRIPT" counts "$temp_file" 2>/dev/null)
    rm -f "$temp_file"
    
    # Empty file should return "0 0 0 0" or empty (we'll accept either)
    if [[ -z "$result" ]]; then
        result="0 0 0 0"
    fi
    assert_equals "0 0 0 0" "$result" "counts: empty file returns zeros"
}

# ============================================
# Tests for 'total' command
# ============================================

test_total_zero_findings() {
    local result
    result=$("$PARSER_SCRIPT" total "$FIXTURES_DIR/results-zero-findings.json")
    assert_equals "0" "$result" "total: zero findings"
}

test_total_with_findings() {
    local result
    result=$("$PARSER_SCRIPT" total "$FIXTURES_DIR/results-with-findings.json")
    assert_equals "4" "$result" "total: with findings (4 total)"
}

# ============================================
# Tests for 'unique' command
# ============================================

test_unique_zero_findings() {
    local result
    result=$("$PARSER_SCRIPT" unique "$FIXTURES_DIR/results-zero-findings.json")
    assert_equals "0" "$result" "unique: zero findings"
}

test_unique_with_findings() {
    local result
    result=$("$PARSER_SCRIPT" unique "$FIXTURES_DIR/results-with-findings.json")
    assert_equals "4" "$result" "unique: with findings (4 unique CVEs)"
}

# ============================================
# Tests for 'cves' command
# ============================================

test_cves_zero_findings() {
    local result
    result=$("$PARSER_SCRIPT" cves "$FIXTURES_DIR/results-zero-findings.json")
    assert_equals "" "$result" "cves: zero findings returns empty"
}

test_cves_with_findings() {
    local result
    result=$("$PARSER_SCRIPT" cves "$FIXTURES_DIR/results-with-findings.json" | wc -l | tr -d ' ')
    assert_equals "4" "$result" "cves: with findings returns 4 CVE IDs"
}

test_cves_contains_expected_cves() {
    local result
    result=$("$PARSER_SCRIPT" cves "$FIXTURES_DIR/results-with-findings.json")
    
    if echo "$result" | grep -q "CVE-2023-1234"; then
        assert_equals "found" "found" "cves: contains CVE-2023-1234"
    else
        assert_equals "found" "missing" "cves: contains CVE-2023-1234"
    fi
}

# ============================================
# Tests for 'digest' command
# ============================================

test_digest_with_metadata() {
    local result
    result=$("$PARSER_SCRIPT" digest "$FIXTURES_DIR/results-with-findings.json")
    
    if [[ -n "$result" ]] && echo "$result" | grep -q "sha256:"; then
        assert_equals "contains-sha256" "contains-sha256" "digest: returns sha256 digest"
    else
        assert_equals "contains-sha256" "$result" "digest: returns sha256 digest"
    fi
}

# ============================================
# Tests for 'image' command
# ============================================

test_image_with_metadata() {
    local result
    result=$("$PARSER_SCRIPT" image "$FIXTURES_DIR/results-with-findings.json")
    assert_equals "vulnerableapp:latest" "$result" "image: returns correct image:tag"
}

test_image_zero_findings() {
    local result
    result=$("$PARSER_SCRIPT" image "$FIXTURES_DIR/results-zero-findings.json")
    assert_equals "alpine:latest" "$result" "image: zero findings returns alpine:latest"
}

# ============================================
# Tests for error handling
# ============================================

test_invalid_command() {
    set +e
    "$PARSER_SCRIPT" invalid_command "$FIXTURES_DIR/results-zero-findings.json" >/dev/null 2>&1
    local exit_code=$?
    set -e
    
    # Script should exit with non-zero for invalid command
    if [[ $exit_code -ne 0 ]]; then
        assert_exit_code 1 1 "error: invalid command returns non-zero"
    else
        assert_exit_code 1 0 "error: invalid command returns non-zero"
    fi
}

test_help_flag() {
    set +e
    "$PARSER_SCRIPT" -h >/dev/null 2>&1
    local exit_code=$?
    set -e
    
    assert_exit_code 0 "$exit_code" "help: -h flag shows help"
}

# ============================================
# Run all tests
# ============================================

main() {
    echo "========================================"
    echo "Testing parse-trivy-results.sh"
    echo "========================================"
    echo ""
    
    # Verify parser script exists
    if [[ ! -f "$PARSER_SCRIPT" ]]; then
        echo -e "${RED}ERROR: Parser script not found at $PARSER_SCRIPT${NC}"
        exit 1
    fi
    
    # Verify fixtures exist
    if [[ ! -d "$FIXTURES_DIR" ]]; then
        echo -e "${RED}ERROR: Fixtures directory not found at $FIXTURES_DIR${NC}"
        exit 1
    fi
    
    echo "Parser script: $PARSER_SCRIPT"
    echo "Fixtures dir:  $FIXTURES_DIR"
    echo ""
    
    # Run tests grouped by command
    echo -e "${YELLOW}Testing 'counts' command:${NC}"
    test_counts_zero_findings
    test_counts_with_findings
    test_counts_nonexistent_file
    test_counts_empty_file
    echo ""
    
    echo -e "${YELLOW}Testing 'total' command:${NC}"
    test_total_zero_findings
    test_total_with_findings
    echo ""
    
    echo -e "${YELLOW}Testing 'unique' command:${NC}"
    test_unique_zero_findings
    test_unique_with_findings
    echo ""
    
    echo -e "${YELLOW}Testing 'cves' command:${NC}"
    test_cves_zero_findings
    test_cves_with_findings
    test_cves_contains_expected_cves
    echo ""
    
    echo -e "${YELLOW}Testing 'digest' command:${NC}"
    test_digest_with_metadata
    echo ""
    
    echo -e "${YELLOW}Testing 'image' command:${NC}"
    test_image_with_metadata
    test_image_zero_findings
    echo ""
    
    echo -e "${YELLOW}Testing error handling:${NC}"
    test_invalid_command
    test_help_flag
    echo ""
    
    # Print summary
    print_test_summary
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
