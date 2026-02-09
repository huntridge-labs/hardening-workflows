# Test Alignment: Consolidate to Python

## Why

The project currently maintains **three languages** (Bash, JavaScript, Python) across action
scripts, tests, and coverage tooling — plus **Ruby** as a silent fourth dependency just to
measure Bash coverage via bashcov/SimpleCov.

This fragmentation directly undermines the project's core goal: a pipeline trusted enough to
auto-merge dependabot PRs and auto-release. Trust requires one clear coverage number, not
three stitched together from different tools with different reporting quirks. It also means
three test frameworks (two of which are hand-rolled), three sets of patterns for contributors
to learn, and three things that can break independently on dependency updates.

Python consolidation eliminates this:

- **One test framework** — pytest (fixtures, parametrize, markers, automatic discovery)
- **One coverage tool** — pytest-cov producing LCOV, Cobertura XML, and HTML in a single pass
- **One Codecov upload** — no stitching, one trustworthy number
- **One language for contributors** — lower barrier, consistent code review
- **Fewer CI dependencies** — drop Node.js (for tests/scripts), drop Ruby entirely
- **Better readability** — 200-line Bash jq pipelines become ~80 lines of Python
- **Pre-installed on runners** — Python ships on every GitHub Actions ubuntu-latest image

Node.js remains for release tooling (release-it, commitlint, husky) which is appropriate —
those are dev workflow tools, not pipeline logic.

---

## Current State Inventory

### Action Scripts (production code being tested)

| Language   | Files | LOC   | Location pattern                            |
|------------|-------|-------|---------------------------------------------|
| Bash       | 14    | 3,492 | `.github/actions/*/scripts/*.sh`            |
| JavaScript | 2     | 684   | `.github/actions/*/scripts/*.js`            |
| Python     | 2     | 358   | `.github/actions/*/scripts/*.py`            |
| **Total**  | **18**| **4,534** |                                         |

### Test Files

| Language   | Files | LOC   | Framework              | Coverage Tool              |
|------------|-------|-------|------------------------|----------------------------|
| Bash       | 5     | 2,128 | Custom assertions      | bashcov (Ruby/SimpleCov)   |
| JavaScript | 2     | 871   | Custom assertions      | c8 (Node/V8)              |
| Python     | 8     | 2,163 | pytest                 | pytest-cov                 |
| **Total**  | **15**| **5,162** |                    |                            |

### Config/Infra Files Affected

| File                        | Purpose                          | Post-migration action  |
|-----------------------------|----------------------------------|------------------------|
| `pytest.ini`                | pytest + coverage config         | Update paths/sources   |
| `.c8rc.json`                | JS coverage config               | Delete                 |
| `.simplecov`                | Bash coverage config (Ruby)      | Delete                 |
| `codecov.yml`               | Codecov thresholds               | Simplify (one flag)    |
| `package.json`              | npm test scripts                 | Remove test:bash/js/coverage:bash/js |
| `scripts/run-bash-coverage.sh` | Bash coverage runner          | Delete                 |
| `.github/workflows/test-unit.yml` | CI test workflow            | Simplify dramatically  |
| `.devcontainer/setup.sh`    | Dev environment setup            | Remove Ruby gems       |

### Duplicate Scripts (consolidation opportunity)

These pairs should become shared Python modules. Pairs marked **identical** have zero diff;
pairs marked **near-identical** have minor behavioral differences (e.g., scan type display
logic for combined vs. single-scan modes) that should be unified behind a flag or parameter.

- `scanner-container/scripts/parse-grype-results.sh` ↔ `scanner-container-summary/scripts/parse-grype-results.sh` — **identical**
- `scanner-container/scripts/parse-trivy-results.sh` ↔ `scanner-container-summary/scripts/parse-trivy-results.sh` — **identical**
- `scanner-container/scripts/generate-container-summary.sh` ↔ `scanner-container-summary/scripts/generate-combined-summary.sh` — **near-identical** (different filenames, combined variant has simplified scan type detection)
- `scanner-zap/scripts/parse-zap-results.sh` ↔ `scanner-zap-summary/scripts/parse-zap-results.sh` — **identical**
- `scanner-zap/scripts/generate-zap-summary.sh` ↔ `scanner-zap-summary/scripts/generate-zap-summary.sh` — **near-identical** (summary variant always clears `SCAN_TYPE_DISPLAY` for combined summaries)

### Already Python (no script migration needed)

scanner-clamav already has Python scripts (`extract-archives.py`, `parse-clamav-report.py`)
and full pytest coverage (`test_extract_archives.py`, `test_parse_clamav_report.py`). No
migration work required — these serve as the reference pattern for newly ported scripts.

---

## Migration Plan

### Phase 0: Foundation

Set up the Python project structure and shared utilities before touching any scanners.

- [ ] **0.1** Create `requirements.txt` (or `pyproject.toml`) for action script dependencies
  - `pyyaml` — YAML parsing (replaces js-yaml)
  - `jsonschema` — JSON schema validation (replaces ajv)
  - `pytest`, `pytest-cov` — testing and coverage
  - No other runtime dependencies needed — `json`, `os`, `sys`, `argparse`, `pathlib` are stdlib
- [ ] **0.2** Create shared Python utility module at `.github/actions/_shared/`
  - `sarif.py` — SARIF file reading, severity counting, finding extraction
  - `summary.py` — Markdown summary generation (tables, severity badges, collapsible sections)
  - `github_output.py` — Write to `$GITHUB_OUTPUT` and `$GITHUB_STEP_SUMMARY`
  - `severity.py` — Severity level constants, comparison, threshold checking
- [ ] **0.3** Write pytest tests for the shared utilities (target: 100% coverage on shared code)
- [ ] **0.4** Update `pytest.ini` to discover tests across all action directories
  - Ensure `pythonpath` includes `.github/actions/_shared`
  - Coverage source: `.github/actions`
  - Omit: `*/tests/*`, `tests/*`
- [ ] **0.5** Validate shared utilities work in GitHub Actions runner environment
  - Python 3.11+ is pre-installed on ubuntu-latest
  - Confirm `json`, `pathlib`, `subprocess` behave as expected in composite action steps

### Phase 1: Migrate Scanner Parsers (Bash → Python)

Each item: rewrite the Bash script, port the corresponding Bash tests to pytest, verify
output parity against existing test fixtures. Migrate one scanner at a time, each as its
own PR with passing CI.

#### Container Scanner (highest complexity — 4 duplicate scripts)

- [ ] **1.1** Rewrite `scanner-container/scripts/parse-trivy-results.sh` → `parse_trivy_results.py`
  - Parse Trivy JSON output, extract CVE counts by severity, output JSON summary
  - Use shared `sarif.py` and `severity.py` utilities
- [ ] **1.2** Port `scanner-container/tests/test-parse-trivy-results.sh` → `test_parse_trivy_results.py`
  - Convert custom bash assertions to pytest parametrized tests
  - Reuse existing fixture files in `tests/fixtures/scanner-outputs/trivy/`
- [ ] **1.3** Rewrite `scanner-container/scripts/parse-grype-results.sh` → `parse_grype_results.py`
- [ ] **1.4** Port `scanner-container/tests/test-parse-grype-results.sh` → `test_parse_grype_results.py`
- [ ] **1.5** Rewrite `scanner-container/scripts/generate-container-summary.sh` → `generate_container_summary.py`
  - Use shared `summary.py` for markdown generation
- [ ] **1.6** Port `scanner-container/tests/test-generate-container-summary.sh` → `test_generate_container_summary.py`
- [ ] **1.7** Point `scanner-container-summary/` at shared Python scripts (eliminate duplicates)
  - Identical parsers: shared imports from `scanner-container/scripts/`
  - Near-identical summary generators: unify into one `generate_container_summary.py` with
    a `--combined` flag to handle the scan type display difference
  - Update `scanner-container-summary/action.yml` to call Python instead of Bash
- [ ] **1.8** Update both `action.yml` files: `run: bash scripts/*.sh` → `run: python scripts/*.py`

#### ZAP Scanner (second highest complexity — 4 duplicate scripts)

- [ ] **1.9** Rewrite `scanner-zap/scripts/parse-zap-results.sh` → `parse_zap_results.py`
- [ ] **1.10** Port `scanner-zap/tests/test-parse-zap-results.sh` → `test_parse_zap_results.py`
- [ ] **1.11** Rewrite `scanner-zap/scripts/generate-zap-summary.sh` → `generate_zap_summary.py`
- [ ] **1.12** Port `scanner-zap/tests/test-generate-zap-summary.sh` → `test_generate_zap_summary.py`
- [ ] **1.13** Point `scanner-zap-summary/` at shared Python scripts (eliminate duplicates)
  - Identical parser: shared import from `scanner-zap/scripts/`
  - Near-identical summary generator: unify into one `generate_zap_summary.py` with
    a `--combined` flag to handle the scan type display difference
- [ ] **1.14** Update both `action.yml` files

#### Remaining Bash Scanners (no duplicates, simpler)

- [ ] **1.15** Rewrite `scanner-checkov/scripts/generate-summary.sh` → `generate_summary.py`
  - Existing Python test (`test_checkov_generate_summary.py`) stays — update imports only
- [ ] **1.16** Update `scanner-checkov/action.yml`
- [ ] **1.17** Rewrite `scanner-codeql/scripts/generate-summary.sh` → `generate_summary.py`
  - Existing Python test (`test_codeql_generate_summary.py`) stays — update imports only
- [ ] **1.18** Update `scanner-codeql/action.yml`
- [ ] **1.19** Rewrite `scanner-opengrep/scripts/generate-summary.sh` → `generate_summary.py`
  - Existing Python test (`test_opengrep_generate_summary.py`) stays — update imports only
- [ ] **1.20** Update `scanner-opengrep/action.yml`
- [ ] **1.21** Rewrite `scanner-trivy-iac/scripts/generate-summary.sh` → `generate_summary.py`
  - Existing Python test (`test_trivy_iac_generate_summary.py`) stays — update imports only
- [ ] **1.22** Update `scanner-trivy-iac/action.yml`

### Phase 2: Migrate Config Parsers (JavaScript → Python)

- [ ] **2.1** Rewrite `parse-container-config/scripts/parse-container-config.js` → `parse_container_config.py`
  - Replace `ajv` with `jsonschema` for schema validation
  - Replace `js-yaml` with `pyyaml` for YAML loading
  - Maintain identical JSON output format for GitHub Actions matrix
- [ ] **2.2** Port `parse-container-config/tests/test-parse-container-config.test.js` → `test_parse_container_config.py`
  - 429 LOC of JS tests → pytest parametrized tests
  - Reuse fixture configs in `tests/fixtures/configs/`
- [ ] **2.3** Rewrite `parse-zap-config/scripts/parse-zap-config.js` → `parse_zap_config.py`
  - Support grouped and flat config styles
  - Maintain matrix output format
- [ ] **2.4** Port `parse-zap-config/tests/test-parse-zap-config.test.js` → `test_parse_zap_config.py`
  - 442 LOC of JS tests → pytest parametrized tests
- [ ] **2.5** Update both `action.yml` files: `run: node scripts/*.js` → `run: python scripts/*.py`
- [ ] **2.6** Remove `ajv`, `ajv-formats`, `js-yaml` from `package.json` dependencies
  - These were only needed for the config parsers
  - Verify no other scripts depend on them

### Phase 3: Clean Up Infrastructure

- [ ] **3.1** Delete old Bash/JS scripts and tests (after confirming Python replacements pass)
  - Remove all `.sh` files from `.github/actions/*/scripts/`
  - Remove all `.js` files from `.github/actions/*/scripts/`
  - Remove all `.sh` files from `.github/actions/*/tests/`
  - Remove all `.test.js` files from `.github/actions/*/tests/`
- [ ] **3.2** Delete Bash/JS coverage infrastructure
  - Delete `.c8rc.json`
  - Delete `.simplecov`
  - Delete `scripts/run-bash-coverage.sh`
- [ ] **3.3** Update `package.json`
  - Remove `test:bash`, `test:js`, `test:coverage:bash`, `test:coverage:js` scripts
  - Simplify `test` script to: `pytest --no-cov -q`
  - Simplify `test:coverage` to: `pytest`
  - Remove `c8` from devDependencies
  - Remove `ajv`, `ajv-formats`, `js-yaml` from dependencies (if not done in 2.6)
- [ ] **3.4** Update `pytest.ini`
  - Confirm `testpaths` discovers all new test files
  - Confirm `--cov` source covers all Python scripts
  - Add `--cov-fail-under=80` to enforce minimum coverage
- [ ] **3.5** Simplify `codecov.yml`
  - Remove multi-flag complexity (was: bash, js, python flags)
  - Single unified coverage upload
- [ ] **3.6** Simplify `.github/workflows/test-unit.yml`
  - Remove: `actions/setup-node` (for tests — keep if needed for release-it)
  - Remove: Ruby installation (`apt-get install ruby-full`, `gem install bashcov`)
  - Remove: `npm ci` (for tests — keep if needed for release-it)
  - Remove: separate JS/Bash coverage steps
  - Simplify to: setup-python → pip install → pytest → upload coverage
- [ ] **3.7** Simplify `.devcontainer/setup.sh`
  - Remove Ruby gem installation
  - Remove `chmod +x` on `.sh` scripts (no longer needed)
  - Keep Node.js setup for release-it/commitlint/husky
- [ ] **3.8** Update `tests/unit/actions/validate-action-schemas.sh` → confirm Python version
      (`validate-action-schemas.py`) is the sole validator, delete `.sh` wrapper
- [ ] **3.9** Clean up `package.json` dependencies — audit what remains and confirm each
      is still needed post-migration

### Phase 4: Harden Testing for Pipeline Trust

With a unified Python test suite, raise the bar so the pipeline verdict is trustworthy
enough for auto-merge.

- [ ] **4.1** Enforce `--cov-fail-under=80` in CI (pytest.ini or workflow)
- [ ] **4.2** Add edge case tests across all scanners
  - Empty scan results (zero findings)
  - Malformed/truncated scanner output
  - Missing expected fields in JSON/SARIF
  - Extremely large result sets (performance)
  - Unicode and special characters in file paths and findings
- [ ] **4.3** Add integration tests that validate `action.yml` step outputs
  - Mock `$GITHUB_OUTPUT` and `$GITHUB_STEP_SUMMARY` as temp files
  - Verify each action writes expected output variables
  - Verify each action produces valid SARIF
- [ ] **4.4** Add pytest markers for test categorization
  - `@pytest.mark.unit` — fast, isolated tests
  - `@pytest.mark.integration` — tests that exercise full script entry points
  - `@pytest.mark.slow` — large fixture tests
- [ ] **4.5** Add CI step: `pytest --dead-fixtures` to catch unused test fixtures
- [ ] **4.6** Ensure Codecov PR comments block merge if coverage drops below threshold
  - Configure `codecov.yml` `status.patch.default.target: 80%` (already set)
  - Set `fail_ci_if_error: true` in Codecov action (currently `false`)
- [ ] **4.7** Add dependabot configuration for Python dependencies
  - `.github/dependabot.yml` entry for pip ecosystem
  - Target: `requirements.txt` (or `pyproject.toml`)
  - Auto-merge rules for patch/minor updates when CI passes

### Phase 5: Documentation Updates

- [ ] **5.1** Update `.ai/architecture.yaml` — reflect Python-only scripts/tests
- [ ] **5.2** Update `.ai/decisions.yaml` — add ADR for Python consolidation (supersedes ADR-003)
- [ ] **5.3** Update `.ai/workflows.yaml` — simplify test/coverage commands
- [ ] **5.4** Update `.ai/errors.yaml` — remove Bash/JS error patterns, add Python ones
- [ ] **5.5** Update `AGENTS.md` and `CLAUDE.md` — reflect new test/script conventions
- [ ] **5.6** Update `CONTRIBUTING.md` — new contributor setup (no Ruby, simplified)
- [ ] **5.7** Update `tests/CONTRIBUTING.md` — pytest conventions, how to add tests

---

## Migration Rules

1. **One scanner per PR.** Each migration is isolated, reviewable, and independently revertable.
2. **Output parity first.** New Python scripts must produce byte-identical output to the
   Bash/JS originals for the same input fixtures. Diff the outputs in CI.
3. **Tests before scripts.** Port or write the pytest tests first against the existing
   Bash/JS scripts (using subprocess calls), then swap the implementation to Python.
   This catches regressions immediately.
4. **No new dependencies without justification.** `json`, `os`, `sys`, `pathlib`, `argparse`,
   `re` are stdlib. Only `pyyaml` and `jsonschema` should be added.
5. **Shared code lives in `_shared/`.** Do not duplicate parsing logic across scanners.
6. **80% coverage minimum.** No PR merges if coverage drops below threshold.
7. **Update `.ai/` files in the same PR** as the code change they describe.

---

## Estimated Scope

| Phase | PRs | Estimated LOC (new Python) | LOC Deleted |
|-------|-----|---------------------------|-------------|
| 0 — Foundation        | 1   | ~400     | 0           |
| 1 — Bash → Python     | 4-6 | ~2,000   | ~5,620      |
| 2 — JS → Python       | 1-2 | ~600     | ~1,555      |
| 3 — Cleanup           | 1   | 0        | ~300        |
| 4 — Harden            | 1-2 | ~500     | 0           |
| 5 — Docs              | 1   | ~200     | ~200        |
| **Total**             | **9-13** | **~3,700** | **~7,675** |

Net result: fewer total lines, one language, one test framework, one coverage tool,
one trustworthy pipeline verdict.
