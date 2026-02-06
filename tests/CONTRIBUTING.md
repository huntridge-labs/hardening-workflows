# Contributing to Tests

This guide helps you add or modify tests when contributing to hardening-workflows.

## Quick Start

**TL;DR**: Create a `test-*.sh` file in `.github/actions/YOUR_ACTION/tests/` and it will be automatically discovered. No configuration needed! 🎉

### Prerequisites

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r .devcontainer/requirements.txt

# Verify setup
npm test
```

## Test Structure

We use a **co-located test approach** with plain bash scripts for bash tests:
- **Unit tests** (<30s) for scripts and parsers - **co-located with actions**
  - **Bash tests**: Plain bash scripts with assert functions (63 tests across 5 files)
  - **JavaScript tests**: Using Node.js test framework (27+ tests)
  - **Python tests**: Using pytest (44 tests)
- **Schema validation** (174 tests) for composite actions - in `tests/unit/actions/`
- **Shared fixtures** - in `tests/fixtures/` reused across all tests
- **Integration tests** (16+ jobs in test-actions.yml) for end-to-end action validation
- **Total test coverage**: 300+ tests across all layers

```
.github/actions/
├── scanner-*/
│   ├── action.yml
│   ├── scripts/               # Parser & summary scripts
│   │   ├── parse-results.sh
│   │   └── generate-summary.sh
│   └── tests/                 # Co-located tests
│       ├── test-parse-results.sh        # Plain bash with assert functions
│       └── test-generate-summary.sh     # Plain bash with assert functions
├── parse-*/
│   ├── scripts/               # Config parsers
│   │   └── parse-config.js
│   └── tests/                 # Co-located tests
│       └── test-parse-config.test.js

tests/
├── fixtures/                  # Shared synthetic test data
│   ├── scanner-outputs/       # Mock scanner results
│   ├── test-apps/             # Minimal test applications
│   └── configs/               # Test configuration files
├── unit/actions/              # Action schema validation
└── CONTRIBUTING.md            # ← You are here
```

**Key Principles**:
- ✅ Tests live with the code they test (co-located in action directories)
- ✅ **Automatic discovery** - just add `test-*.sh` files, no config updates needed
- ✅ Shared fixtures - multiple actions reuse the same mock data from `tests/fixtures/`
- ✅ Plain bash scripts with colored output and assert functions

## Running Tests Locally

```bash
# All tests (recommended)
npm test

# Individual test suites
npm run test:bash      # Bash parser & summary tests
npm run test:js        # JavaScript config parsers
npm run test:python    # Python utilities
npm run test:actions   # Action schema validation

# Fast validation only (<1s)
npm run validate

# Single test file (bash format)
bash .github/actions/scanner-container/tests/test-parse-trivy-results.sh
```

**Current Status**: 300+ tests passing (63 bash tests + 27 JS tests + 44 Python tests + 174 schema validation + 16+ integration jobs)

## When to Add/Update Tests

### Scenario 1: Adding a New Scanner Action with Parser Script

**Files**:
- `.github/actions/scanner-myScanner/action.yml`
- `.github/actions/scanner-myScanner/scripts/parse-results.sh`
- `.github/actions/scanner-myScanner/scripts/generate-summary.sh`

**Add**: `.github/actions/scanner-myScanner/tests/test-parse-results.sh`

**✨ No configuration needed!** Tests are automatically discovered by:
- `npm run test:bash` - Finds all `test-*.sh` files in `.github/actions/*/tests/`
- `npm run test:coverage:bash` - Automatically includes them in coverage reports with bashcov

**Pattern** (plain bash format - copy from existing scanner action test):
```bash
#!/usr/bin/env bash
# Unit tests for parse-results.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="${SCRIPT_DIR}/../../../../tests/fixtures/scanner-outputs/myScanner"
PARSER_SCRIPT="${SCRIPT_DIR}/../scripts/parse-results.sh"

# Test helper functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✓${NC} PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} FAIL: $test_name"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Run tests
echo "Testing parse-results.sh"
echo "======================="

output=$("$PARSER_SCRIPT" counts "$FIXTURES_DIR/results-zero-findings.json")
assert_equals "0 0 0 0" "$output" "counts: zero findings"

output=$("$PARSER_SCRIPT" counts "$FIXTURES_DIR/results-with-findings.json")
assert_equals "1 2 3 4" "$output" "counts: with findings"

# Show summary
echo ""
echo "========================"
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed${NC}"
fi
echo "Total:  $TESTS_RUN"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo "========================"

# Exit with error if any tests failed
[ $TESTS_FAILED -eq 0 ] || exit 1
```

**Why Plain Bash?**
- Simple and straightforward - no additional framework needed
- Works with bashcov for code coverage
- Colored output for easy reading
- Full control over test execution
- **Automatic discovery** - no need to update package.json or test scripts!

**Shared Fixture**: Add to `tests/fixtures/scanner-outputs/myScanner/results-with-findings.json`

**Why shared?** Multiple tests may need the same mock data, so fixtures remain centralized in `tests/fixtures/`

**Test Discovery**:
Place your `test-*.sh` file anywhere in `.github/actions/*/tests/test-*.sh` and it will be automatically discovered:
```bash
# These all work automatically:
.github/actions/scanner-myScanner/tests/test-parse-results.sh
.github/actions/scanner-myScanner/tests/test-generate-summary.sh
.github/actions/scanner-foo/tests/test-parser.sh
```

### Scenario 2: Adding a New Composite Action

**File**: `.github/actions/scanner-myScanner/action.yml`

**Required**:
- All inputs must have `description`
- All outputs must have `description`
- Steps with `run:` must specify `shell: bash`

**Validation**: Automatically tested by `validate-action-schemas.py`

**Add integration test** (see Phase 3 in TODO.md):
- Add to `.github/workflows/test-actions-scanners.yml` matrix

### Scenario 3: Modifying an Existing Script

**Before committing**:
1. Run the relevant test: `bash .github/actions/scanner-X/tests/test-parse-results.sh`
2. If test fails, update test to match new behavior
3. If script output format changes, update shared fixtures in `tests/fixtures/`

### Scenario 4: Bug Fix in Script

**Steps**:
1. Add a test that reproduces the bug (should fail)
2. Fix the bug
3. Verify test passes
4. Commit both test and fix together

## Test Patterns & Examples

### Bash Test Template (Plain Bash)

**See existing tests for full examples:**
- [test-parse-trivy-results.sh](/.github/actions/scanner-container/tests/test-parse-trivy-results.sh)
- [test-generate-container-summary.sh](/.github/actions/scanner-container/tests/test-generate-container-summary.sh)

```bash
#!/usr/bin/env bash
# Unit tests for parse-results.sh

# Setup runs before each test
setup() {
  SCRIPT_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
  FIXTURES_DIR="${REPO_ROOT}/tests/fixtures/scanner-outputs/scanner-name"
  PARSER_SCRIPT="${SCRIPT_DIR}/../scripts/parse-results.sh"
}

# Colors for output
RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
TESTS_PASSED=0; TESTS_FAILED=0

# Helper functions
assert_equals() {
  local expected="$1" actual="$2" test_name="$3"
  if [[ "$expected" == "$actual" ]]; then
    echo -e "${GREEN}✓${NC} PASS: $test_name"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}✗${NC} FAIL: $test_name"
    echo "  Expected: $expected"
    echo "  Actual: $actual"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

print_summary() {
  echo "Tests passed: $TESTS_PASSED"
  echo "Tests failed: $TESTS_FAILED"
  [ "$TESTS_FAILED" -eq 0 ] && exit 0 || exit 1
}

# Your tests here
```

### JavaScript Test Template

```javascript
const fs = require('fs');
const path = require('path');

let passed = 0, failed = 0;

function assertEquals(expected, actual, testName) {
  if (expected === actual) {
    console.log(`✓ PASS: ${testName}`);
    passed++;
  } else {
    console.log(`✗ FAIL: ${testName}`);
    console.log(`  Expected: ${expected}`);
    console.log(`  Actual: ${actual}`);
    failed++;
  }
}

// Your tests here

console.log(`\nTests passed: ${passed}`);
console.log(`Tests failed: ${failed}`);
process.exit(failed === 0 ? 0 : 1);
```

### Python Test Template (pytest)

```python
import pytest
from pathlib import Path

# Fixtures are shared across all actions
FIXTURES = Path(__file__).parent.parent.parent.parent.parent / "tests" / "fixtures"

def test_parser_with_findings():
    """Test parser with sample findings"""
    result = parse_results(FIXTURES / "scanner-outputs/myScanner/results.json")
    assert result['critical'] == 1
    assert result['high'] == 2
```

**Note**: Fixtures are in repo root at `tests/fixtures/`, so tests in `.github/actions/*/tests/` navigate up to reach them.

## Updating Fixtures

### Adding a New Fixture File

1. **Create synthetic data** (not real vulnerabilities!)
2. Place in `tests/fixtures/scanner-outputs/{scanner-name}/`
3. Use consistent naming:
   - `results-with-findings.json` (has vulnerabilities)
   - `results-zero-findings.json` (clean scan)
   - `results-baseline-scan.json` (specific scan type)

### Regenerating Fixtures

```bash
# DO NOT include real vulnerabilities
# Use redacted/synthetic data only

# Example: Creating a Trivy fixture
trivy image --format json alpine:3.18 > results.json
# Manually edit to remove/redact sensitive info
# Keep structure but use safe CVE examples
```

## Common Pitfalls

❌ **Don't**: Use real vulnerabilities in fixtures
✅ **Do**: Use synthetic/redacted data

❌ **Don't**: Skip tests when modifying scripts
✅ **Do**: Run tests before committing

❌ **Don't**: Hard-code absolute paths
✅ **Do**: Use relative paths from REPO_ROOT

❌ **Don't**: Commit broken tests
✅ **Do**: Fix or skip (with TODO) failing tests

## CI/CD Integration

Tests run automatically on:
- Every push to any branch
- Every pull request

### Test Workflows Overview

| Workflow | Triggers On | Tests |
|----------|-------------|-------|
| `test-unit.yml` | Any PR / push to main | Unit tests (bash/JS/Python), coverage |
| `test-actions.yml` | Changes to `.github/actions/**` | Integration tests for all composite actions (16+ jobs) |

### Understanding Integration Test Results

When a PR changes composite actions, `test-actions.yml` runs:

```
┌─────────────────────────────────────────────────────────┐
│ Composite Actions Test Summary                          │
├──────────────────────────┬──────────────────────────────┤
│ Category                 │ Status                       │
├──────────────────────────┼──────────────────────────────┤
│ SAST Scanners            │ ✅ success                   │
│ CodeQL                   │ ✅ success                   │
│ Secrets Detection        │ ✅ success                   │
│ Infrastructure (IaC)     │ ✅ success                   │
│ Container Scanners       │ ✅ success                   │
│ ZAP DAST                 │ ✅ success                   │
│ Linters                  │ ✅ success                   │
│ ClamAV Malware           │ ✅ success                   │
│ Config Parsers           │ ✅ success                   │
│ Security Summary         │ ✅ success                   │
└──────────────────────────┴──────────────────────────────┘
```

**To debug a failure:**
1. Click the failed job name (e.g., "IaC / checkov")
2. Expand step logs to see the actual error
3. Most failures are input mismatches or missing dependencies

### Adding Your Action to Integration Tests

If you create a new action, add it to the appropriate matrix in `.github/workflows/test-actions.yml`:

```yaml
# Example: Adding scanner-newscan to SAST tests
strategy:
  matrix:
    scanner:
      - bandit
      - opengrep
      - newscan          # ← Add here
    include:
      - scanner: newscan
        fixture: tests/fixtures/test-apps/python-app
        action_path: .github/actions/scanner-newscan
```

**Pre-commit hooks** run:
- Whitespace cleanup
- YAML/JSON validation
- Secret scanning

**GitHub Actions workflow**: `.github/workflows/test-unit.yml`

## Getting Help

- **See existing tests**: Best examples are in `tests/unit/bash/test-parse-*.sh`
- **Phase 2 complete docs**: `tests/PHASE2-COMPLETE.md`
- **Testing strategy**: `tests/TODO.md`

---

## Quick Reference

| Task | Command |
|------|---------|
| Run all tests | `npm test` |
| Run bash tests | `npm run test:bash` |
| Run JS tests | `npm run test:js` |
| Run Python tests | `npm run test:python` |
| Validate actions | `npm run validate` |
| Run single test | `./tests/unit/bash/test-parse-trivy-results.sh` |

**Test fast, test often, ship with confidence!** 🚀
