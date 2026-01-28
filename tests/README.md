# Tests

Comprehensive testing suite for hardening-workflows composite actions and supporting scripts.

## Overview

This testing infrastructure validates all components of the hardening-workflows project:

- **281+ tests** across multiple languages (Bash, JavaScript, Python)
- **Zero vulnerable code** - all tests use synthetic fixtures
- **Automated CI/CD** - tests run on every PR
- **Fast feedback** - unit tests complete in <30 seconds

## Test Structure

```
tests/
├── fixtures/              # Synthetic test data (no real vulnerabilities)
│   ├── scanner-outputs/   # Mock scanner results (Bandit, Trivy, ZAP, etc.)
│   ├── test-apps/         # Minimal test applications
│   └── configs/           # Test configuration files
├── unit/                  # Unit tests for scripts and parsers
│   ├── bash/              # Bash script tests (73 tests)
│   ├── javascript/        # JS config parser tests (60 tests)
│   ├── python/            # Python utility tests (44 tests)
│   └── actions/           # Action schema validation (174 tests)
├── CONTRIBUTING.md        # Detailed testing guide
└── TODO.md                # Testing roadmap and status
```

## Quick Start

```bash
# Install dependencies
npm install
pip install -r requirements-dev.txt

# Run all tests
npm test

# Run specific test suites
npm run test:bash      # Bash parser & summary tests
npm run test:js        # JavaScript config parsers
npm run test:python    # Python utilities
npm run test:actions   # Action schema validation

# Fast validation only (<1s)
npm run validate
```

## Test Coverage

| Category | Tests | Purpose |
|----------|-------|---------|
| **Unit Tests** | 177 | Parser scripts, summary generators, config parsers |
| **Schema Validation** | 174 | Composite action metadata validation |
| **Integration Tests** | 16+ jobs | End-to-end action testing in workflows |
| **Total** | **281+** | Complete validation of all components |

## CI/CD Integration

Tests run automatically via GitHub Actions:

- **`test-unit.yml`** - Runs on all PRs (unit tests + coverage)
- **`test-actions.yml`** - Runs on action changes (integration tests)
- **Path-based triggers** - Only affected components tested
- **Non-blocking** - Tests provide feedback but don't block PRs

## Adding Tests

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidance on:

- When to add unit vs integration tests
- Test patterns and templates
- Updating fixtures
- Common pitfalls

## Key Design Principles

1. **No Real Vulnerabilities** - All tests use synthetic fixtures from `fixtures/scanner-outputs/`
2. **Fast Feedback** - Unit tests run in seconds, integration tests in minutes
3. **Clear Failures** - Descriptive test names and error messages
4. **Easy Contribution** - Templates and examples for new tests

## More Information

- **Fixtures**: See [fixtures/README.md](fixtures/README.md) for test data structure
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guide
- **Status**: See [TODO.md](TODO.md) for implementation roadmap

---

**Current Status**: All 5 phases complete! 🎉 Zero vulnerable code, comprehensive CI/CD integration, 281+ tests validating every change.
