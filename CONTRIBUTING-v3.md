# Contributing to Security Hardening Workflows (v3.0)

Welcome! This guide covers how to contribute composite actions to the security scanning toolkit.

> **Note**: This project is transitioning from v2.x (reusable workflows) to v3.0 (composite actions). This guide reflects the new v3.0 architecture on the `feat/migrate-to-composite-actions` branch. For v2.x documentation, see `CONTRIBUTING.md`.

## Table of Contents

- [Getting Started](#getting-started)
- [Adding a New Scanner Action](#adding-a-new-scanner-action)
- [Testing Your Changes](#testing-your-changes)
- [Documentation Requirements](#documentation-requirements)
- [Pull Request Process](#pull-request-process)
- [Best Practices](#best-practices)

---

## Getting Started

### Prerequisites

- Git
- GitHub account
- Basic understanding of GitHub Actions
- Familiarity with bash scripting (for parser scripts)
- Knowledge of the scanner tool you're integrating

### Project Structure

```
.github/actions/
├── scanner-*/                    # Scanner composite actions
│   ├── action.yml               # Action definition
│   ├── README.md                # Action documentation
│   └── scripts/                 # Bundled scripts
│       ├── parse-results.sh     # Parse scanner output
│       └── generate-summary.sh  # Generate markdown summary
├── linter-*/                    # Linter composite actions
├── parse-container-config/      # Config parser actions
├── security-summary/            # Summary aggregators
└── README.md                    # Actions catalog

examples/
├── composite-actions-example.yml     # Complete security workflow
└── composite-linting-example.yml     # Complete linting workflow

.github/actions/*/tests/         # Co-located unit tests
tests/
├── fixtures/                    # Shared mock data and test apps
└── unit/actions/                # Action schema validation
```

### Key Concepts

**Composite Actions** vs **Reusable Workflows**:
- ✅ Self-contained with bundled scripts
- ✅ Works on GHES with github.com access
- ✅ Easier to compose and test
- ✅ No cross-repo workflow call overhead

---

## Adding a New Scanner Action

### Step 1: Create Action Structure

Create the directory structure for your scanner:

```bash
mkdir -p .github/actions/scanner-example/scripts
touch .github/actions/scanner-example/action.yml
touch .github/actions/scanner-example/README.md
touch .github/actions/scanner-example/scripts/parse-results.sh
touch .github/actions/scanner-example/scripts/generate-summary.sh
chmod +x .github/actions/scanner-example/scripts/*.sh
```

### Step 2: Define action.yml

See existing scanner actions for reference patterns (e.g., `scanner-bandit/action.yml`, `scanner-checkov/action.yml`).

**Standard structure**:
```yaml
name: 'Example Scanner'
description: |
  Run Example security scanner and generate reports.

inputs:
  scan_path:                  # What to scan
  fail_on_severity:          # Threshold (none/low/medium/high/critical)
  enable_code_security:      # Upload SARIF boolean
  post_pr_comment:          # Post PR comment boolean
  job_id:                   # For artifact naming

outputs:
  critical_count:           # Number of findings by severity
  high_count:
  medium_count:
  low_count:
  total_count:
  scan_status:             # passed/failed/skipped

runs:
  using: 'composite'
  steps:
    - name: Validate inputs
    - name: Run scanner
    - name: Parse results (using scripts/parse-results.sh)
    - name: Upload SARIF (if enabled)
    - name: Upload reports artifact
    - name: Generate summary (using scripts/generate-summary.sh)
    - name: Upload summary artifact
    - name: Comment PR (if enabled)
```

**Key patterns to follow**:
- Use `${{ github.action_path }}/scripts/` to reference bundled scripts
- Set `if: always()` on result processing steps
- Use `continue-on-error: true` for optional steps (SARIF, PR comments)
- Follow naming conventions for artifacts: `{scanner}-reports-{job_id}`

### Step 3: Create Parser Script

Create `scripts/parse-results.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Example Scanner Results Parser
# Usage: parse-results.sh counts <report_file>

COMMAND="${1:-}"
REPORT_FILE="${2:-}"

case "$COMMAND" in
  counts)
    # Parse scanner output and extract severity counts
    # TODO: Adjust parsing logic for your scanner's output format

    critical=$(jq -r '[.results[]? | select(.severity == "CRITICAL")] | length' "$REPORT_FILE" 2>/dev/null || echo "0")
    high=$(jq -r '[.results[]? | select(.severity == "HIGH")] | length' "$REPORT_FILE" 2>/dev/null || echo "0")
    medium=$(jq -r '[.results[]? | select(.severity == "MEDIUM")] | length' "$REPORT_FILE" 2>/dev/null || echo "0")
    low=$(jq -r '[.results[]? | select(.severity == "LOW")] | length' "$REPORT_FILE" 2>/dev/null || echo "0")

    # Output: critical high medium low (space-separated)
    echo "$critical $high $medium $low"
    ;;
  *)
    echo "Unknown command: $COMMAND"
    exit 1
    ;;
esac
```

**Parser requirements**:
- Must handle missing files gracefully (default to 0 counts)
- Must handle malformed data (use `|| echo "0"`)
- Must map scanner's severity levels to standard: CRITICAL, HIGH, MEDIUM, LOW
- Output format: space-separated counts for easy parsing

### Step 4: Create Summary Generator

Create `scripts/generate-summary.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Example Scanner Summary Generator
# Usage: generate-summary.sh <output_file> <is_pr_comment>

OUTPUT_FILE="${1:-scanner-summaries/example.md}"
IS_PR_COMMENT="${2:-false}"

# Get counts from environment
CRITICAL="${CRITICAL:-0}"
HIGH="${HIGH:-0}"
MEDIUM="${MEDIUM:-0}"
LOW="${LOW:-0}"
TOTAL="${TOTAL:-0}"

# Generate markdown summary
if [ "$IS_PR_COMMENT" = "true" ]; then
  echo "<details>" >> "$OUTPUT_FILE"
  echo "<summary>🔍 Example Scanner</summary>" >> "$OUTPUT_FILE"
else
  echo "## 🔍 Example Scanner Results" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | ❌ Total |" >> "$OUTPUT_FILE"
echo "|-------------|---------|-----------|--------|----------|" >> "$OUTPUT_FILE"
echo "| **$CRITICAL** | **$HIGH** | **$MEDIUM** | **$LOW** | **$TOTAL** |" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# TODO: Add detailed findings sections if needed

echo "**📁 Artifacts:** [View Reports](${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}#artifacts)" >> "$OUTPUT_FILE"

if [ "$IS_PR_COMMENT" = "true" ]; then
  echo "</details>" >> "$OUTPUT_FILE"
fi
```

**Summary requirements**:
- Use consistent emoji and formatting
- Support both PR comment and job summary modes
- Include artifacts link
- Keep it concise but informative

### Step 5: Create Documentation

Create `README.md` for your action:

```markdown
# Example Scanner Composite Action

Brief description of what this scanner detects.

## Usage

### Basic Example
\`\`\`yaml
- uses: huntridge-labs/hardening-workflows/.github/actions/scanner-example@v3
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    scan_path: 'src'
    fail_on_severity: 'high'
\`\`\`

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `scan_path` | Path to scan | No | `.` |
| `fail_on_severity` | Fail threshold | No | `none` |
| `enable_code_security` | Upload SARIF | No | `false` |
| `post_pr_comment` | Post PR comment | No | `true` |

## Outputs

| Output | Description |
|--------|-------------|
| `critical_count` | Critical findings |
| `high_count` | High findings |
| `total_count` | Total findings |
| `scan_status` | Status (passed/failed/skipped) |

## Requirements

- Scanner tool version requirements
- Supported file types
- Dependencies
```

### Step 6: Update Actions Catalog

Add to `.github/actions/README.md`:

```markdown
| [scanner-example](scanner-example/) | Example scanner description | Languages | [README](scanner-example/README.md) |
```

### Step 7: Add to Example Workflows

Add your scanner to `examples/composite-actions-example.yml`:

```yaml
  example-scanner:
    name: Example Scanner
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-example@feat/migrate-to-composite-actions
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          scan_path: 'src'
          post_pr_comment: false  # Let security-summary handle comments

  security-summary:
    needs:
      - example-scanner  # Add to needs array
      - bandit
      # ... other scanners
```

---

## Testing Your Changes

### Current Testing Approach

**Co-located tests** - tests live with the actions they validate:
```
.github/actions/scanner-myScanner/
├── action.yml
├── scripts/
│   ├── parse-results.sh
│   └── generate-summary.sh
└── tests/                      # ← Tests co-located here
    ├── test-parse-results.sh
    └── test-generate-summary.sh
```

**Shared fixtures** - mock data centralized for reuse:
```
tests/fixtures/
├── scanner-outputs/            # Mock scanner results
├── test-apps/                  # Minimal test apps
└── configs/                    # Test configurations
```

**Run tests**:
```bash
npm test                        # All 174+ tests
npm run test:bash               # Bash tests
npm run test:js                 # JavaScript tests
npm run test:python             # Python tests
```

**Key principles**:
1. Tests co-located with actions they test
2. Fixtures shared across actions (avoid duplication)
3. Use synthetic data, not real vulnerabilities
4. Measure coverage with Codecov

See `tests/TODO.md` and `tests/CONTRIBUTING.md` for detailed testing guide.

### Manual Testing

Create a test workflow:

```yaml
name: Test Example Scanner

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: ./.github/actions/scanner-example
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          scan_path: 'tests/fixtures/test-apps/example-app'
```

### Automated Testing ✅

Test infrastructure is complete:

- ✅ Unit tests for parser scripts (co-located in `.github/actions/*/tests/`)
- ✅ Unit tests for summary generators (co-located)
- ✅ Integration tests for full actions (`.github/workflows/test-actions*.yml`)
- ✅ Coverage reporting via Codecov
- ✅ 174+ tests running in CI/CD

### Validation Checklist

- [ ] Action runs without errors
- [ ] All outputs are set correctly
- [ ] Parser handles various input formats
- [ ] Summary markdown is valid
- [ ] Unit tests added in `.github/actions/*/tests/`
- [ ] Tests use shared fixtures from `tests/fixtures/`
- [ ] All tests pass: `npm test`
- [ ] SARIF upload works (if applicable)
- [ ] Artifacts upload with correct names
- [ ] PR comments work
- [ ] Severity thresholds fail appropriately

---

## Documentation Requirements

Every scanner action must include:

1. **Action README.md**
   - Purpose and capabilities
   - Usage examples
   - Complete inputs/outputs tables
   - Requirements

2. **Inline Documentation**
   - Comments in action.yml
   - Comments in scripts
   - Helpful error messages

3. **Catalog Entry**
   - Add to `.github/actions/README.md`

4. **Usage Example**
   - Add to `examples/composite-actions-example.yml`

5. **Changelog**
   - Update `CHANGELOG.md`

---

## Pull Request Process

### Before Submitting

- [ ] Manual testing complete
- [ ] Documentation complete
- [ ] Scripts are executable
- [ ] Follows existing patterns
- [ ] TODO: Automated tests pass (once available)

### PR Template

```markdown
## Add Example Scanner Composite Action

### Summary
Brief description of the scanner.

### Scanner Details
- **Tool**: Example Scanner v1.0
- **Languages**: Python, JavaScript
- **Output Formats**: SARIF, JSON

### Changes
- ✅ Created scanner-example action
- ✅ Added parser and summary scripts
- ✅ Updated actions catalog
- ✅ Added examples
- ✅ Documentation complete

### Testing
- [x] Tested manually
- [x] Verified outputs
- [x] Confirmed artifacts
- [ ] TODO: Unit tests
- [ ] TODO: Integration tests

### Usage
\`\`\`yaml
- uses: huntridge-labs/hardening-workflows/.github/actions/scanner-example@v3
\`\`\`
```

---

## Best Practices

### Naming Conventions

- **Actions**: `scanner-{tool}` or `linter-{tool}`
- **Scripts**: `parse-{tool}-results.sh`, `generate-{tool}-summary.sh`
- **Artifacts**: `{tool}-reports-{job_id}`, `scanner-summary-{tool}-{job_id}`

### Script Guidelines

1. Always use `set -euo pipefail`
2. Validate inputs before processing
3. Handle missing files gracefully
4. Provide default values
5. Use descriptive error messages

### Security

- Never hardcode secrets
- Validate all inputs
- Use `continue-on-error` for optional steps
- Pin action versions
- Minimize required permissions

### Performance

- Set reasonable timeouts
- Cache dependencies
- Minimize scan scope
- Generate only necessary formats

---

## TODO: Items Pending Migration Completion

Areas needing clarification:

- [ ] **Test Framework**: Exact unit/integration test process
- [ ] **CI Integration**: How tests run in PRs
- [ ] **Coverage Requirements**: Specific thresholds
- [ ] **Release Process**: How to version/release actions
- [ ] **Dependency Management**: Scanner tool updates
- [ ] **GHES Compatibility**: Testing procedures

See `tests/TODO.md` for testing roadmap details.

---

## Getting Help

- 📋 Check existing actions for patterns
- 📖 Review `CLAUDE.md` for architecture
- 📝 See `tests/TODO.md` for testing
- 💬 Open a [Discussion](https://github.com/huntridge-labs/hardening-workflows/discussions)
- 🐛 Report via [Issues](https://github.com/huntridge-labs/hardening-workflows/issues)

---

**Thank you for contributing! 🎉**
