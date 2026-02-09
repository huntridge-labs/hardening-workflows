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

## Pre-Migration State Inventory

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

- [x] **0.1** Create `requirements.txt` for action script dependencies
  - `pyyaml` — YAML parsing (replaces js-yaml)
  - `pytest`, `pytest-cov` — testing and coverage
  - No other runtime dependencies needed — `json`, `os`, `sys`, `argparse`, `pathlib` are stdlib
- [x] **0.4** Update `pytest.ini` to discover tests across all action directories
  - Coverage source: `.github/actions`
  - Omit: `*/tests/*`, `tests/*`
  - Added `--cov-fail-under=80`
  - Added markers: `unit`, `integration`, `slow`
- [x] **0.5** Validate Python scripts work in GitHub Actions runner environment

> **Note:** Phase 0 items 0.2 and 0.3 (shared `_shared/` module) were skipped — each script
> is self-contained following the scanner-clamav pattern. Shared utilities can be extracted
> as a future refactor if duplication becomes a maintenance issue.

### Phase 1: Migrate Scanner Parsers (Bash → Python)

#### Container Scanner (highest complexity — 4 duplicate scripts)

- [x] **1.1** Rewrite `scanner-container/scripts/parse-trivy-results.sh` → `parse_trivy_results.py`
- [x] **1.2** Port `scanner-container/tests/test-parse-trivy-results.sh` → `test_parse_trivy_results.py`
- [x] **1.3** Rewrite `scanner-container/scripts/parse-grype-results.sh` → `parse_grype_results.py`
- [x] **1.4** Port `scanner-container/tests/test-parse-grype-results.sh` → `test_parse_grype_results.py`
- [x] **1.5** Rewrite `scanner-container/scripts/generate-container-summary.sh` → `generate_container_summary.py`
- [x] **1.6** Port `scanner-container/tests/test-generate-container-summary.sh` → `test_generate_container_summary.py`
- [x] **1.7** Point `scanner-container-summary/` at shared Python scripts (eliminate duplicates)
- [x] **1.8** Update both `action.yml` files

#### ZAP Scanner (second highest complexity — 4 duplicate scripts)

- [x] **1.9** Rewrite `scanner-zap/scripts/parse-zap-results.sh` → `parse_zap_results.py`
- [x] **1.10** Port `scanner-zap/tests/test-parse-zap-results.sh` → `test_parse_zap_results.py`
- [x] **1.11** Rewrite `scanner-zap/scripts/generate-zap-summary.sh` → `generate_zap_summary.py`
- [x] **1.12** Port `scanner-zap/tests/test-generate-zap-summary.sh` → `test_generate_zap_summary.py`
- [x] **1.13** Point `scanner-zap-summary/` at shared Python scripts (eliminate duplicates)
- [x] **1.14** Update both `action.yml` files

#### Remaining Bash Scanners (no duplicates, simpler)

- [x] **1.15** Rewrite `scanner-checkov/scripts/generate-summary.sh` → `generate_summary.py`
- [x] **1.16** Update `scanner-checkov/action.yml`
- [x] **1.17** Rewrite `scanner-codeql/scripts/generate-summary.sh` → `generate_summary.py`
- [x] **1.18** Update `scanner-codeql/action.yml`
- [x] **1.19** Rewrite `scanner-opengrep/scripts/generate-summary.sh` → `generate_summary.py`
- [x] **1.20** Update `scanner-opengrep/action.yml`
- [x] **1.21** Rewrite `scanner-trivy-iac/scripts/generate-summary.sh` → `generate_summary.py`
- [x] **1.22** Update `scanner-trivy-iac/action.yml`

### Phase 2: Migrate Config Parsers (JavaScript → Python)

- [x] **2.1** Rewrite `parse-container-config/scripts/parse-container-config.js` → `parse_container_config.py`
- [x] **2.2** Port `parse-container-config/tests/test-parse-container-config.test.js` → `test_parse_container_config.py`
- [x] **2.3** Rewrite `parse-zap-config/scripts/parse-zap-config.js` → `parse_zap_config.py`
- [x] **2.4** Port `parse-zap-config/tests/test-parse-zap-config.test.js` → `test_parse_zap_config.py`
- [x] **2.5** Update both `action.yml` files
- [x] **2.6** Remove `ajv`, `ajv-formats`, `js-yaml` from `package.json` dependencies

### Phase 3: Clean Up Infrastructure

- [x] **3.1** Delete old Bash/JS scripts and tests
- [x] **3.2** Delete Bash/JS coverage infrastructure (`.c8rc.json`, `.simplecov`, `scripts/run-bash-coverage.sh`)
- [x] **3.3** Update `package.json` — simplified test scripts, removed `c8` and JS deps
- [x] **3.4** Update `pytest.ini` — discovers all tests, `--cov-fail-under=80` enforced
- [x] **3.5** Simplify `codecov.yml` — single unified coverage upload
- [x] **3.6** Simplify `.github/workflows/test-unit.yml` — Python 3.13 only, no Ruby/Node for tests
- [x] **3.7** Simplify `.devcontainer/setup.sh` — removed Ruby gems, simplified to pip + npm
- [x] **3.8** Confirm `validate-action-schemas.py` is sole validator
- [x] **3.9** Audit `package.json` dependencies — only release/commit tooling remains

### Phase 4: Harden Testing for Pipeline Trust

- [x] **4.1** Enforce `--cov-fail-under=80` in CI (pytest.ini)
- [x] **4.2** Add edge case tests across all scanners (116 new tests)
  - Empty scan results, malformed JSON, missing fields, null values
  - Unicode/CJK characters, very long strings, duplicate findings
  - Nonexistent files, empty arrays, unknown severity levels
- [x] **4.3** Add integration tests that validate `action.yml` step outputs (33 tests)
  - Mock `$GITHUB_OUTPUT` and `$GITHUB_STEP_SUMMARY` as temp files
  - Verify each action writes expected output variables
- [x] **4.4** Add pytest markers for test categorization (`unit`, `integration`, `slow`)
- [x] **4.5** Add CI step: `pytest --dead-fixtures` to catch unused test fixtures
- [x] **4.6** Ensure Codecov PR comments block merge if coverage drops below threshold
  - `fail_ci_if_error: true` in Codecov action
- [x] **4.7** Add dependabot configuration for Python dependencies
  - `.github/dependabot.yml` — pip, npm, github-actions ecosystems
  - `dependabot-auto-merge.yml` — auto-squash-merge patch/minor when CI passes

### Phase 5: Documentation Updates

- [x] **5.1** Update `.ai/architecture.yaml` — reflect Python-only scripts/tests
- [x] **5.2** Update `.ai/decisions.yaml` — add ADR for Python consolidation (supersedes ADR-003)
- [x] **5.3** Update `.ai/workflows.yaml` — simplify test/coverage commands
- [x] **5.4** Update `.ai/errors.yaml` — remove Bash/JS error patterns, add Python ones
- [x] **5.5** Update `AGENTS.md` and `CLAUDE.md` — reflect new test/script conventions
- [x] **5.6** Update `CONTRIBUTING.md` — new contributor setup (no Ruby, simplified)
- [x] **5.7** Update `tests/CONTRIBUTING.md` — pytest conventions, how to add tests

---

## Final Results

| Metric                | Before          | After           |
|-----------------------|-----------------|-----------------|
| Languages (scripts)   | Bash, JS, Python | Python only    |
| Languages (tests)     | Bash, JS, Python | Python only    |
| Coverage tools        | bashcov + c8 + pytest-cov | pytest-cov only |
| Runtime deps for tests| Ruby, Node 22, Python 3.11 | Python 3.13 only |
| Total tests           | ~175            | 491             |
| Code coverage         | ~60% (stitched) | 93.31% (unified) |
| Coverage enforced     | No              | Yes (80% min, CI fails) |
| Codecov merge gate    | No              | Yes (`fail_ci_if_error: true`) |
| Dependabot auto-merge | No              | Yes (patch/minor when CI green) |

---

## Migration Rules (retained for reference)

1. **No new dependencies without justification.** `json`, `os`, `sys`, `pathlib`, `argparse`,
   `re` are stdlib. Only `pyyaml` should be added.
2. **80% coverage minimum.** No PR merges if coverage drops below threshold.
3. **Update `.ai/` files in the same PR** as the code change they describe.
4. **scanner-clamav is the reference pattern** for Python action scripts + tests.
