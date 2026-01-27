# Contributing to Tests

This guide helps you add or modify tests when contributing to hardening-workflows.

## Setup

### Prerequisites

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements-dev.txt

# Verify setup
npm test
```

## Test Structure

We use a **pragmatic hybrid approach**:
- **Fast unit tests** (177 tests, <30s) for scripts and parsers
- **Schema validation** (174 tests) for composite actions
- **Integration tests** (workflows) for end-to-end action validation

```
tests/
├── fixtures/                    # Synthetic test data (no real vulns!)
│   ├── scanner-outputs/        # Mock scanner results
│   ├── test-apps/              # Minimal test applications
│   └── configs/                # Test configuration files
├── unit/
│   ├── bash/                   # Parser & summary generator tests
│   ├── javascript/             # Config parser tests
│   ├── python/                 # Python utility tests
│   └── actions/                # Action schema validation
└── CONTRIBUTING.md             # ← You are here
```

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

# Single test file
./tests/unit/bash/test-parse-trivy-results.sh
```

**Current Status**: 351+ tests passing (177 unit + 174 schema)

## When to Add/Update Tests

### Scenario 1: Adding a New Parser Script

**File**: `.github/scripts/parse-myScanner-results.sh`

**Add**: `tests/unit/bash/test-parse-myScanner-results.sh`

**Pattern** (copy from existing parser test):
```bash
#!/usr/bin/env bash
set -euo pipefail

# ... test helpers ...

# Test: counts command
test_counts() {
  result=$("$PARSER" counts "$FIXTURE_FILE")
  read crit high med low <<< "$result"

  assert_equals "1" "$crit" "Critical count"
  assert_equals "2" "$high" "High count"
}

# Run all tests
test_counts
# ... more tests ...
print_summary
```

**Fixture**: Add to `tests/fixtures/scanner-outputs/myScanner/results-with-findings.json`

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
1. Run the relevant test: `./tests/unit/bash/test-parse-X-results.sh`
2. If test fails, update test to match new behavior
3. If script output format changes, update fixtures

### Scenario 4: Bug Fix in Script

**Steps**:
1. Add a test that reproduces the bug (should fail)
2. Fix the bug
3. Verify test passes
4. Commit both test and fix together

## Test Patterns & Examples

### Bash Test Template

```bash
#!/usr/bin/env bash
set -euo pipefail

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

FIXTURES = Path(__file__).parent.parent.parent / "fixtures"

def test_parser_with_findings():
    """Test parser with sample findings"""
    result = parse_results(FIXTURES / "scanner-outputs/myScanner/results.json")
    assert result['critical'] == 1
    assert result['high'] == 2
```

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
