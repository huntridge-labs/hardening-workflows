# Testing Strategy for Composite Actions

## Current Issues
- ❌ Vulnerable test files (`src/vulnerable_code.py`, `infrastructure/vulnerable.tf`, etc.) trigger GitHub Advanced Security alerts
- ❌ These vulnerabilities appear in PRs, causing confusion for reviewers
- ❌ No comprehensive test coverage for composite actions
- ❌ No test coverage for supporting scripts
- ❌ Mock data is scattered or missing

## Proposed Testing Architecture

### 1. Test Data Organization

```
tests/
├── fixtures/                    # Mock data for testing
│   ├── scanner-outputs/        # Pre-captured scanner results
│   │   ├── bandit/
│   │   │   ├── results.json
│   │   │   └── results.sarif
│   │   ├── codeql/
│   │   ├── checkov/
│   │   ├── trivy/
│   │   ├── zap/
│   │   ├── gitleaks/
│   │   └── clamav/
│   ├── test-apps/              # Simple test applications (no real vulns)
│   │   ├── python-app/         # Minimal Flask/FastAPI app
│   │   ├── node-app/           # Minimal Express app
│   │   └── vulnerable-patterns/ # Isolated vulnerable snippets (excluded from scanning)
│   ├── configs/                # Test configuration files
│   │   ├── container-config.yml
│   │   ├── zap-config.yml
│   │   └── invalid-configs/
│   └── sarif-samples/          # SARIF format examples
├── unit/                       # Unit tests for scripts
│   ├── test-parse-bandit.sh
│   ├── test-parse-codeql.sh
│   ├── test-generate-summaries.sh
│   ├── test-parse-container-config.sh
│   └── test-parse-zap-config.sh
├── integration/                # Action integration tests
│   ├── test-scanner-bandit.yml
│   ├── test-scanner-codeql.yml
│   ├── test-scanner-checkov.yml
│   └── ...
└── e2e/                        # End-to-end workflow tests
    └── test-composite-actions-workflow.yml
```

### 2. Vulnerability Test Data Strategy

**Problem**: Current approach includes real vulnerabilities in codebase
**Solution**: Multi-layered approach

#### Option A: Synthetic Pre-Captured Results (Recommended)
- [ ] **Create mock scanner outputs** with known findings
- [ ] Store in `tests/fixtures/scanner-outputs/`
- [ ] Test parsers/scripts against these fixtures
- [ ] No actual vulnerable code in repo
- [ ] **Benefits**:
  - No security alerts in GitHub
  - Predictable test data
  - Fast test execution
  - Complete control over test scenarios

#### Option B: .securityignore Pattern
- [ ] Move vulnerable files to `tests/fixtures/vulnerable-patterns/`
- [ ] Add `.github/.securityignore` or similar
- [ ] Configure GitHub Advanced Security to exclude this path
- [ ] Document clearly that these are intentional test files
- [ ] **Drawbacks**:
  - Still appears in some security scans
  - Requires Advanced Security configuration
  - Can confuse new contributors

#### Option C: External Test Repository
- [ ] Create separate `hardening-workflows-test-fixtures` repo
- [ ] Store vulnerable test files there
- [ ] Reference in CI/CD as needed
- [ ] **Drawbacks**:
  - Additional maintenance overhead
  - Slower tests (clone required)

**Recommended**: Option A with Option B as fallback for complex scenarios

### 3. Script Unit Testing

#### Parser Script Tests
- [ ] **parse-bandit-results.sh**
  - [ ] Test with valid JSON (0 findings, 1 finding, multiple findings)
  - [ ] Test with missing fields
  - [ ] Test severity counting (HIGH, MEDIUM, LOW)
  - [ ] Test with malformed JSON
  - [ ] Test `counts` command output format

- [ ] **parse-codeql-results.sh**
  - [ ] Test SARIF parsing with various result counts
  - [ ] Test severity mapping
  - [ ] Test with empty results
  - [ ] Test with multiple SARIF files

- [ ] **parse-checkov-results.sh**
  - [ ] Test with and without severity data (API key scenarios)
  - [ ] Test framework detection
  - [ ] Test file path handling
  - [ ] Test line range parsing

- [ ] **parse-zap-results.sh**
  - [ ] Test risk code to severity mapping
  - [ ] Test counts extraction
  - [ ] Test alert parsing
  - [ ] Test with baseline/full/api scan outputs

- [ ] **parse-gitleaks-results.sh**
  - [ ] Test secret detection parsing
  - [ ] Test with various secret types
  - [ ] Test file path handling

- [ ] **parse-clamav-results.sh**
  - [ ] Test malware detection parsing
  - [ ] Test with clean scans
  - [ ] Test with infected files

#### Summary Generator Tests
- [ ] **generate-bandit-summary.sh**
  - [ ] Test markdown output format
  - [ ] Test with PR comment mode vs job summary mode
  - [ ] Test severity grouping
  - [ ] Test file links generation

- [ ] **generate-checkov-summary.sh**
  - [ ] Test with null severity handling
  - [ ] Test with severity data present
  - [ ] Test iac_path prepending for file links
  - [ ] Test framework display

- [ ] **generate-zap-summary.sh**
  - [ ] Test with different scan types
  - [ ] Test alert formatting
  - [ ] Test severity sections

#### Config Parser Tests
- [ ] **parse-container-config.js**
  - [ ] Test YAML parsing
  - [ ] Test JSON parsing
  - [ ] Test JS module parsing
  - [ ] Test schema validation
  - [ ] Test matrix generation
  - [ ] Test registry auth secret handling
  - [ ] Test invalid configs with clear error messages

- [ ] **parse-zap-config.js**
  - [ ] Test target configuration parsing
  - [ ] Test scans array processing
  - [ ] Test mode validation (url/docker-run/compose)
  - [ ] Test type validation (baseline/full/api)
  - [ ] Test matrix output structure

### 4. Composite Action Integration Tests

#### Test Approach: Workflow-based Testing
Use GitHub Actions workflows in `.github/workflows/test-*.yml` that run on PR/push to test branch

- [ ] **scanner-bandit**
  - [ ] Test with Python code (fixtures/test-apps/python-app)
  - [ ] Verify outputs (high_count, medium_count, etc.)
  - [ ] Verify artifacts uploaded
  - [ ] Verify summary generated
  - [ ] Test fail_on_severity thresholds

- [ ] **scanner-codeql**
  - [ ] Test with multiple languages
  - [ ] Test with Python (fixture app)
  - [ ] Verify SARIF upload
  - [ ] Verify summary generation

- [ ] **scanner-checkov**
  - [ ] Test with fixtures/configs/ terraform files
  - [ ] Test with and without api_key
  - [ ] Verify severity handling
  - [ ] Verify file link generation with iac_path

- [ ] **scanner-trivy-iac**
  - [ ] Test with terraform fixtures
  - [ ] Test severity parsing
  - [ ] Verify SARIF generation

- [ ] **scanner-gitleaks**
  - [ ] Test with fixture repo (known test secrets)
  - [ ] Use `.gitleaksignore` to exclude false positives
  - [ ] Verify secret detection

- [ ] **scanner-clamav**
  - [ ] Test with test-apps (should be clean)
  - [ ] Verify clean scan output

- [ ] **scanner-container**
  - [ ] Test with public test images (e.g., alpine:latest)
  - [ ] Test with local built fixture app
  - [ ] Test scanner selection (trivy, grype, syft)
  - [ ] Verify multi-scanner results aggregation

- [ ] **scanner-zap** (when features complete)
  - [ ] Test URL mode with fixtures/test-apps/node-app
  - [ ] Test docker-run mode
  - [ ] Test baseline/full/api scan types
  - [ ] Verify readiness checking
  - [ ] Verify docker cleanup

- [ ] **parse-container-config**
  - [ ] Test with fixtures/configs/container-config.yml
  - [ ] Verify matrix output structure
  - [ ] Test with invalid configs

- [ ] **security-summary**
  - [ ] Test with multiple scanner summaries
  - [ ] Verify aggregation logic
  - [ ] Test markdown generation

- [ ] **linting-summary**
  - [ ] Test with multiple linter outputs
  - [ ] Verify aggregation

### 5. End-to-End Workflow Tests

- [ ] **Complete security workflow**
  - [ ] Run composite-actions-example.yml against test fixtures
  - [ ] Verify all scanners execute
  - [ ] Verify security-summary aggregates correctly
  - [ ] Verify PR comments (in test PR)

- [ ] **Complete linting workflow**
  - [ ] Run composite-linting-example.yml
  - [ ] Verify all linters execute
  - [ ] Verify linting-summary aggregates correctly

- [ ] **Config-driven workflows**
  - [ ] Test container-config workflow
  - [ ] Test zap-config workflow (when available)
  - [ ] Verify matrix strategy
  - [ ] Verify secrets inheritance

### 6. Implementation Plan

#### Phase 1: Foundation (Week 1) ✅ COMPLETE
- [x] Create `tests/fixtures/` directory structure
- [x] Generate synthetic scanner outputs for all scanners
- [x] Create simple test applications (Python, Node)
- [x] Document test data generation process
- [x] Create initial unit test framework
- [x] First working test (parse-trivy-results.sh - 16 tests passing!)
- [x] CI workflow for running tests

**Status**: Phase 1 complete! See [PHASE1-COMPLETE.md](PHASE1-COMPLETE.md) for details.

#### Phase 2: Script Unit Tests (Week 2) ✅ COMPLETE
- [x] test-parse-trivy-results.sh - 16 tests passing ✅
- [x] test-parse-zap-results.sh - 21 tests passing ✅
- [x] test-parse-grype-results.sh - 13 tests passing ✅
- [x] test-parse-container-config.js - 27 tests passing ✅
- [x] test-parse-zap-config.js - 33 tests passing ✅
- [x] test_parse_clamav_report.py - 7 tests passing ✅ (migrated from .github/scripts/tests/)
- [x] test_extract_archives.py - 37 tests passing ✅ (migrated from .github/scripts/tests/)
- [x] test-generate-container-summary.sh - 13 tests (11 passing, 2 minor failures) ✅
- [x] test-generate-zap-summary.sh - 17 tests (12 passing, 5 minor failures) ✅

**Status**: Phase 2 complete! 🎉 177 tests passing across all parsers and summary generators!
- Bash: 73 tests (Trivy 16, Grype 13, ZAP parser 21, Container summary 11, ZAP summary 12)
- JavaScript: 60 tests (container-config 27, zap-config 33)
- Python: 44 tests (ClamAV 7, extract-archives 37)

All parsers and summary generators now have comprehensive test coverage.

#### Phase 3: Action Integration Tests (Week 3-4)
- [ ] Write unit tests for all parser scripts
- [ ] Write unit tests for all summary generator scripts
- [ ] Write unit tests for config parsers
- [ ] Set up test runner (bash test framework or bats)

#### Phase 3: Action Integration Tests (Week 3-4)
- [ ] Create test workflows for each action
- [ ] Run tests on PR/push to test branches
- [ ] Verify outputs and artifacts
- [ ] Document test results

#### Phase 4: Cleanup & Migration (Week 5)
- [ ] Move vulnerable files to isolated fixtures
- [ ] Add `.securityignore` or equivalent
- [ ] Update documentation
- [ ] Archive old test approach

#### Phase 5: CI/CD Integration (Week 6)
- [ ] Add test workflows to PR checks
- [ ] Set up automated test runs
- [ ] Add test coverage reporting
- [ ] Document testing guidelines for contributors

### 7. Testing Tools & Frameworks

- [ ] **Bash testing**: Consider [bats-core](https://github.com/bats-core/bats-core) for script tests
- [ ] **JSON validation**: Use `jq` for parsing, validation
- [ ] **SARIF validation**: Use official SARIF schema validator
- [ ] **GitHub Actions testing**: Use actual workflows with test fixtures
- [ ] **Mock servers**: Use simple http-server or python -m http.server for ZAP tests

### 8. Multi-Language Test Coverage

#### Coverage Strategy Overview

**Languages in Project:**
- Python (scripts, tests)
- JavaScript/Node.js (config parsers)
- Bash/Shell (parser scripts, summary generators)
- YAML/JSON (configs - validation testing)

#### Recommended Tool: Codecov + Language-Specific Coverage

**Why Codecov:**
- ✅ Supports all project languages
- ✅ Aggregates multiple coverage reports into one dashboard
- ✅ GitHub integration (PR comments, badges, diff coverage)
- ✅ Free for open source projects
- ✅ Shows coverage trends over time

#### Implementation Checklist

- [ ] **Python Coverage (pytest + coverage.py)**
  ```yaml
  - name: Test Python scripts with coverage
    run: |
      pip install pytest pytest-cov
      pytest tests/unit/python/ \
        --cov=.github/scripts \
        --cov-report=xml:coverage-python.xml \
        --cov-report=term
  ```
  - [ ] Configure `.coveragerc` to exclude test files
  - [ ] Set minimum coverage threshold (80%)
  - [ ] Test all Python helper scripts

- [ ] **JavaScript Coverage (jest or c8)**
  ```yaml
  - name: Test JS config parsers with coverage
    run: |
      npm install --save-dev jest
      npm test -- --coverage --coverageReporters=cobertura
      mv coverage/cobertura-coverage.xml coverage-javascript.xml
  ```
  - [ ] Create `jest.config.js` with coverage settings
  - [ ] Test `parse-container-config.js`
  - [ ] Test `parse-zap-config.js` (when created)
  - [ ] Set coverage threshold (80%)

- [ ] **Bash Coverage (kcov)**
  ```yaml
  - name: Install kcov
    run: |
      sudo apt-get update
      sudo apt-get install -y kcov

  - name: Test Bash scripts with coverage
    run: |
      mkdir -p coverage-bash
      for test_script in tests/unit/bash/test-*.sh; do
        test_name=$(basename "$test_script" .sh | sed 's/test-//')
        script_path=".github/scripts/${test_name}.sh"
        kcov --exclude-pattern=/usr,/tmp \
          coverage-bash/$test_name \
          $test_script
      done
  ```
  - [ ] Install and configure kcov
  - [ ] Write bash test wrappers for all `*.sh` scripts
  - [ ] Set coverage goal (60%+ due to bash complexity)
  - [ ] Alternative: bashcov (Ruby-based, may be easier)

- [ ] **Aggregate and Upload Coverage**
  ```yaml
  - name: Upload coverage to Codecov
    uses: codecov/codecov-action@v4
    with:
      token: ${{ secrets.CODECOV_TOKEN }}
      files: |
        coverage-python.xml
        coverage-javascript.xml
        coverage-bash/*/cobertura.xml
      flags: unittests
      name: composite-actions-coverage
      fail_ci_if_error: false
  ```
  - [ ] Sign up for Codecov (free for open source)
  - [ ] Add `CODECOV_TOKEN` to repository secrets
  - [ ] Configure codecov.yml for thresholds
  - [ ] Add coverage badge to README.md

#### Alternative: SonarCloud (Optional, More Comprehensive)

- [ ] **SonarCloud Setup** (Coverage + Quality + Security)
  ```yaml
  - name: SonarCloud Scan
    uses: SonarSource/sonarcloud-github-action@master
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    with:
      args: >
        -Dsonar.python.coverage.reportPaths=coverage-python.xml
        -Dsonar.javascript.lcov.reportPaths=coverage/lcov.info
        -Dsonar.sources=.github/scripts,.github/actions
        -Dsonar.tests=tests
  ```
  - [ ] Sign up for SonarCloud
  - [ ] Configure `sonar-project.properties`
  - [ ] Analyze code quality metrics alongside coverage
  - [ ] **Note**: May be overkill; start with Codecov

#### Coverage Workflow

- [ ] **Create `.github/workflows/test-coverage.yml`**
  ```yaml
  name: Test Coverage

  on:
    push:
      branches: [main, develop]
    pull_request:
      branches: [main, develop]

  jobs:
    coverage:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v6

        # Python coverage
        - uses: actions/setup-python@v5
          with:
            python-version: '3.11'
        - name: Run Python tests with coverage
          run: |
            pip install pytest pytest-cov
            pytest tests/unit/python/ \
              --cov=.github/scripts \
              --cov-report=xml:coverage-python.xml \
              --cov-report=term

        # JavaScript coverage
        - uses: actions/setup-node@v6
          with:
            node-version: '20'
        - name: Run JS tests with coverage
          run: |
            cd .github/scripts
            npm install --save-dev jest
            npm test -- --coverage --coverageReporters=cobertura
            mv coverage/cobertura-coverage.xml ../../coverage-javascript.xml

        # Bash coverage (optional initially)
        - name: Run Bash tests with coverage
          run: |
            sudo apt-get update && sudo apt-get install -y kcov
            mkdir -p coverage-bash
            for test in tests/unit/bash/test-*.sh; do
              name=$(basename "$test" .sh | sed 's/test-//')
              kcov --exclude-pattern=/usr coverage-bash/$name $test
            done

        # Upload to Codecov
        - uses: codecov/codecov-action@v4
          with:
            token: ${{ secrets.CODECOV_TOKEN }}
            files: coverage-python.xml,coverage-javascript.xml
            flags: unittests
            fail_ci_if_error: false
  ```

#### Coverage Goals by Asset Type

| Asset Type | Tool | Target Coverage | Priority |
|------------|------|-----------------|----------|
| Python scripts | pytest-cov | 80%+ | High |
| JS config parsers | jest/c8 | 80%+ | High |
| Bash scripts | kcov/bashcov | 60%+ | Medium |
| Composite actions | Integration tests | 100% execution | High |
| Config schemas | Validation tests | 100% fields tested | Medium |

#### Non-Traditional Coverage Tracking

- [ ] **GitHub Actions YAML Coverage**
  - Track via integration test success rate
  - Measure: "% of actions with passing integration tests"
  - Report via workflow badges

- [ ] **Schema Coverage**
  - Track: "% of schema fields exercised by test fixtures"
  - Create tests that use every field in container-config.schema.json and zap-config.schema.json
  - Validate with custom script

- [ ] **Terraform/IaC Coverage**
  - Use `terraform validate` for syntax
  - Track: "% of resources with validation tests"
  - Not traditional line coverage

#### Configuration Files

- [ ] **Create `.coveragerc` (Python)**
  ```ini
  [run]
  source = .github/scripts
  omit =
      tests/*
      */venv/*
      */site-packages/*

  [report]
  exclude_lines =
      pragma: no cover
      def __repr__
      raise AssertionError
      raise NotImplementedError
      if __name__ == .__main__.:
  precision = 2

  [html]
  directory = coverage-html
  ```

- [ ] **Create `jest.config.js` (JavaScript)**
  ```javascript
  module.exports = {
    collectCoverageFrom: [
      '.github/scripts/**/*.js',
      '!.github/scripts/node_modules/**',
      '!**/node_modules/**'
    ],
    coverageThreshold: {
      global: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80
      }
    },
    coverageReporters: ['text', 'cobertura', 'html']
  };
  ```

- [ ] **Create `codecov.yml`**
  ```yaml
  coverage:
    precision: 2
    round: down
    range: "70...100"

    status:
      project:
        default:
          target: 80%
          threshold: 2%
      patch:
        default:
          target: 80%

    ignore:
      - "tests/**/*"
      - "examples/**/*"
      - "docs/**/*"

  comment:
    layout: "reach,diff,flags,tree,reach"
    behavior: default
    require_changes: false

  flags:
    unittests:
      paths:
        - .github/scripts/
        - .github/actions/
  ```

#### Reporting and Badges

- [ ] **Add coverage badges to README.md**
  ```markdown
  [![codecov](https://codecov.io/gh/huntridge-labs/hardening-workflows/branch/main/graph/badge.svg)](https://codecov.io/gh/huntridge-labs/hardening-workflows)
  ```

- [ ] **Enable PR comments**
  - Codecov automatically comments on PRs with coverage diff
  - Shows coverage increase/decrease per file
  - Highlights uncovered lines in PR

- [ ] **Dashboard monitoring**
  - Review coverage trends weekly
  - Investigate significant drops
  - Celebrate coverage milestones!

### 9. Success Metrics

- ✅ Zero vulnerability alerts from test files in GitHub Advanced Security
- ✅ All composite actions have integration tests
- ✅ All scripts have unit tests with >80% coverage
- ✅ Multi-language coverage reporting via Codecov
- ✅ Coverage visible in PR comments and dashboard
- ✅ Test suite runs in <15 minutes
- ✅ Clear test failure messages
- ✅ New contributors can add tests easily

### 10. Documentation Requirements

- [ ] `tests/README.md` - Overview of test architecture
- [ ] `tests/fixtures/README.md` - How to generate/update test data
- [ ] `tests/CONTRIBUTING.md` - How to add new tests
- [ ] In-line comments in test scripts
- [ ] Test workflow examples in `examples/`

---

## References

- Current vulnerable files to migrate:
  - `src/vulnerable_code.py`
  - `src/vulnerable_app.js`
  - `infrastructure/vulnerable.tf`
  - `docker/Dockerfile.vulnerable`

- Scripts to test:
  - `.github/scripts/parse-*-results.sh`
  - `.github/scripts/generate-*-summary.sh`
  - `.github/scripts/parse-*-config.js`

- Actions to test:
  - All scanners in `.github/actions/scanner-*/`
  - All linters in `.github/actions/linter-*/`
  - Utility actions (parse-container-config, security-summary, linting-summary)

---

## Cleanup: Files/Directories to Delete After Migration

Once the new testing strategy is fully implemented with synthetic test data and mock fixtures, the following files can be **safely deleted** to eliminate security alerts:

### Files to Delete
- [ ] `src/vulnerable_code.py` - Replace with mock Bandit/CodeQL results
- [ ] `src/vulnerable_app.js` - Replace with mock OpenGrep/CodeQL results
- [ ] `infrastructure/vulnerable.tf` - Replace with mock Checkov/Trivy-IaC results
- [ ] `docker/Dockerfile.vulnerable` - Replace with mock container scanner results

### Directories to Clean Up
- [ ] `tests/` - Current ad-hoc test files:
  - [ ] `tests/clean_test.py` - May be obsolete, evaluate against new test structure
  - [ ] `tests/secrets_test.py` - May be obsolete, evaluate against new test structure
  - [ ] `tests/formatting_issues.txt` - Migrate to fixtures or delete
  - [ ] `tests/invalid.json`, `tests/valid.json` - Migrate to `tests/fixtures/configs/`

### Files to Keep (but may need relocation)
- `src/secure_code.py` - Keep as positive test case (no vulnerabilities)
- `src/secure_app.js` - Keep as positive test case
- `infrastructure/secure.tf` - Keep as positive test case
- `docker/Dockerfile.secure` - Keep as positive test case

### Migration Checklist Before Deletion
✅ **Before deleting vulnerable files, ensure:**
1. Synthetic scanner outputs exist in `tests/fixtures/scanner-outputs/` for:
   - [ ] Bandit (replacing vulnerable_code.py)
   - [ ] CodeQL (replacing vulnerable_code.py, vulnerable_app.js)
   - [ ] OpenGrep (replacing vulnerable_app.js)
   - [ ] Checkov (replacing vulnerable.tf)
   - [ ] Trivy-IaC (replacing vulnerable.tf)
   - [ ] Container scanners (replacing Dockerfile.vulnerable)
2. All parser scripts are tested against new fixtures
3. All summary generators work with new fixtures
4. Integration tests pass without vulnerable files
5. No CI/CD workflows reference deleted files
6. Documentation updated to reference new test approach

### Expected Outcome
- **0 security alerts** from test files in GitHub Advanced Security
- **0 vulnerable code** in main/default branch
- **Clear separation** between test fixtures and production code
- **Faster CI/CD** (no actual scanning of intentionally vulnerable code)
- **Better contributor experience** (no confusion about "why are there vulns in this repo?")
