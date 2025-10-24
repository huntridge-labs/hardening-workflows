# Contributing to Security Hardening Workflows

Thank you for your interest in contributing! This guide will help you add new security scanners to the hardening pipeline.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Adding a New Scanner](#adding-a-new-scanner)
- [Step-by-Step Guide](#step-by-step-guide)
- [Scanner Workflow Template](#scanner-workflow-template)
- [Testing Your Scanner](#testing-your-scanner)
- [Documentation Requirements](#documentation-requirements)
- [Best Practices](#best-practices)

---

## Architecture Overview

The security hardening pipeline uses a modular architecture:

```
.github/workflows/
├── reusable-security-hardening.yml   # Main orchestration workflow
├── scanner-{name}.yml                # Individual scanner workflows
├── container-scan.yml                # Container security scanning
├── infrastructure.yml                # Infrastructure as Code scanning
└── linting.yml                       # Code quality & linting

Key Components:
1. Scan Coordinator - Resolves scanner selection logic
2. Individual Scanner Workflows - Standalone, reusable scanners
3. Report Generator - Consolidates all scanner outputs
4. PR Comment Generator - Creates unified security report
```

**Scanner Flow:**
1. User specifies scanners via `scanners` input (e.g., `codeql,bandit,container`)
2. Scan coordinator resolves which scanners to run
3. Each enabled scanner runs as a separate job
4. Scanners generate standardized summary artifacts
5. Report generator consolidates all summaries
6. PR comment is posted with collapsible sections per scanner

---

## Adding a New Scanner

### Prerequisites

Before adding a new scanner, ensure:
- [ ] The scanner is open-source or freely available in GitHub Actions
- [ ] It can generate machine-readable output (JSON, SARIF, XML, etc.)
- [ ] It provides severity/priority levels for findings
- [ ] It's actively maintained and widely used

### Files to Update

When adding a new scanner named `example`, you'll need to update:

1. **Create scanner workflow**: `.github/workflows/scanner-example.yml`
2. **Update BOTH workflow files**:
   - `.github/workflows/reusable-security-hardening.yml` (production version)
   - `.github/workflows/pr-reusable-security-hardening.yml` (PR testing version)
3. **Update documentation**: `README.md`, `QUICK-START.md`
4. **Add examples**: `examples/scanner-list-examples.yml`

> **Important:** We maintain two versions of the reusable workflow:
> - **`reusable-security-hardening.yml`** uses pinned tags for external consumers (e.g., `@2.4.0`)
> - **`pr-reusable-security-hardening.yml`** uses relative paths for PR testing
>
> Both workflows must be kept in sync. See [PR Workflow Sync docs](docs/pr-workflow-sync.md) for details.

---

## Step-by-Step Guide

### Step 1: Create the Scanner Workflow

Create a new file: `.github/workflows/scanner-{name}.yml`

**Required structure:**

```yaml
name: [Scanner Name] Security Scanner

on:
  workflow_dispatch:
  workflow_call:
    inputs:
      post_pr_comment:
        description: 'Whether to post PR comments'
        required: false
        type: boolean
        default: true
      enable_code_security:
        description: 'Whether GitHub Code Security is enabled for this repository'
        required: false
        type: boolean
        default: false
      # Add scanner-specific inputs here

permissions:
  contents: read
  security-events: write
  actions: read
  pull-requests: write

env:
  # Define environment variables

jobs:
  scanner-analysis:
    name: [Scanner Name] Analysis
    runs-on: ubuntu-latest
    timeout-minutes: 15
    continue-on-error: true

    steps:
    # 1. Checkout code
    - name: Checkout repository
      uses: actions/checkout@v5

    # 2. Setup environment (if needed)
    - name: Set up Python/Node/etc
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    # 3. Install scanner
    - name: Install [Scanner Name]
      run: |
        # Installation commands

    # 4. Run scanner with multiple output formats
    - name: Run [Scanner Name] Scan
      run: |
        echo "🔍 Running [Scanner Name] security analysis..."
        mkdir -p scanner-reports

        # Generate SARIF (for GitHub Security tab)
        scanner-command -f sarif -o scanner-reports/report.sarif || true

        # Generate JSON (for parsing)
        scanner-command -f json -o scanner-reports/report.json || true

        # Generate text (for humans)
        scanner-command -f txt -o scanner-reports/report.txt || true
      continue-on-error: true

    # 5. Upload artifacts
    - name: Upload [Scanner Name] artifacts
      uses: actions/upload-artifact@v4
      with:
        name: scanner-name-reports
        path: scanner-reports/
        retention-days: 30
      if: always()

    # 6. Upload SARIF to GitHub Security (optional)
    - name: Upload [Scanner Name] SARIF
      uses: github/codeql-action/upload-sarif@v4
      with:
        sarif_file: scanner-reports/report.sarif
      if: inputs.enable_code_security == true && always() && github.actor != 'nektos/act' && hashFiles('scanner-reports/report.sarif') != ''
      continue-on-error: true

    # 7. Generate standardized summary section
    - name: Generate [Scanner Name] summary section
      if: always()
      run: |
        mkdir -p scanner-summaries

        echo "<details>" > scanner-summaries/scanner-name.md
        echo "<summary>🔍 [Scanner Name]</summary>" >> scanner-summaries/scanner-name.md
        echo "" >> scanner-summaries/scanner-name.md

        if [ -d "scanner-reports" ] && [ "$(ls -A scanner-reports)" ]; then
          echo "**Status:** ✅ Completed" >> scanner-summaries/scanner-name.md
          echo "" >> scanner-summaries/scanner-name.md

          # Parse results and count issues
          ISSUE_COUNT=0
          CRITICAL_COUNT=0
          HIGH_COUNT=0
          MEDIUM_COUNT=0
          LOW_COUNT=0

          # Parse JSON report (adjust based on your scanner's output format)
          if [ -f "scanner-reports/report.json" ] && command -v jq >/dev/null 2>&1; then
            # Example parsing - adjust to your scanner's JSON structure
            ISSUE_COUNT=$(jq -r '.results | length' scanner-reports/report.json 2>/dev/null || echo "0")
            CRITICAL_COUNT=$(jq -r '.results[] | select(.severity == "CRITICAL") | .id' scanner-reports/report.json 2>/dev/null | wc -l | tr -d ' ')
            HIGH_COUNT=$(jq -r '.results[] | select(.severity == "HIGH") | .id' scanner-reports/report.json 2>/dev/null | wc -l | tr -d ' ')
            MEDIUM_COUNT=$(jq -r '.results[] | select(.severity == "MEDIUM") | .id' scanner-reports/report.json 2>/dev/null | wc -l | tr -d ' ')
            LOW_COUNT=$(jq -r '.results[] | select(.severity == "LOW") | .id' scanner-reports/report.json 2>/dev/null | wc -l | tr -d ' ')
          fi

          echo "**Issues Found:** $ISSUE_COUNT" >> scanner-summaries/scanner-name.md
          echo "" >> scanner-summaries/scanner-name.md

          if [ $ISSUE_COUNT -gt 0 ]; then
            echo "| Severity | Count |" >> scanner-summaries/scanner-name.md
            echo "|----------|-------|" >> scanner-summaries/scanner-name.md
            [ $CRITICAL_COUNT -gt 0 ] && echo "| 🔴 Critical | $CRITICAL_COUNT |" >> scanner-summaries/scanner-name.md
            [ $HIGH_COUNT -gt 0 ] && echo "| 🟠 High | $HIGH_COUNT |" >> scanner-summaries/scanner-name.md
            [ $MEDIUM_COUNT -gt 0 ] && echo "| 🟡 Medium | $MEDIUM_COUNT |" >> scanner-summaries/scanner-name.md
            [ $LOW_COUNT -gt 0 ] && echo "| 🟢 Low | $LOW_COUNT |" >> scanner-summaries/scanner-name.md
            echo "" >> scanner-summaries/scanner-name.md
          fi

          echo "**📁 Artifacts:** [[Scanner Name] Reports](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}#artifacts)" >> scanner-summaries/scanner-name.md
        else
          echo "**Status:** ⏭️ Skipped" >> scanner-summaries/scanner-name.md
        fi

        echo "" >> scanner-summaries/scanner-name.md
        echo "</details>" >> scanner-summaries/scanner-name.md
        echo "" >> scanner-summaries/scanner-name.md
      continue-on-error: true

    # 8. Upload summary artifact
    - name: Upload [Scanner Name] summary section
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: scanner-summary-scanner-name
        path: scanner-summaries/scanner-name.md
        retention-days: 7
      continue-on-error: true
```

### Step 2: Update Both Reusable Workflows

Edit **BOTH** workflow files:
- `.github/workflows/reusable-security-hardening.yml`
- `.github/workflows/pr-reusable-security-hardening.yml`

The changes below apply to both files. The only difference is the scanner job path:
- Production uses: `huntridge-labs/hardening-workflows/.github/workflows/scanner-example.yml@2.4.0`
- PR testing uses: `./.github/workflows/scanner-example.yml`

#### 2.1 Add to Scanner Resolution Logic

Find the `scan-coordinator` job and add your scanner:

```yaml
jobs:
  scan-coordinator:
    name: Scan Coordinator
    runs-on: ubuntu-latest
    outputs:
      # Add your scanner's output
      run_example: ${{ steps.resolve.outputs.run_example }}
      # ... existing outputs

    steps:
    - name: Resolve scanner selection
      id: resolve
      run: |
        # Add to RUN associative array
        declare -A RUN=(
          [codeql]=false
          [opengrep]=false
          [bandit]=false
          [gitleaks]=false
          [container]=false
          [infrastructure]=false
          [lint]=false
          [example]=false  # <-- Add your scanner here
        )

        # Add to DEFAULT_SCANNERS if it should run by default
        DEFAULT_SCANNERS=(codeql opengrep bandit gitleaks container infrastructure example)

        # Add token handling in apply_token function
        apply_token() {
          local token="$1"
          case "$token" in
            # ... existing cases
            example|example-scanner)  # Add aliases if needed
              add_scanner example
              ;;
            # ... other cases
          esac
        }

        # At the end, add output for your scanner
        echo "run_example=${RUN[example]}" >> $GITHUB_OUTPUT
```

#### 2.2 Add Scanner Job

Add your scanner job after the scan-coordinator.

**In `reusable-security-hardening.yml` (production):**
```yaml
  example-scanner:
    name: Example Scanner
    needs: scan-coordinator
    if: needs.scan-coordinator.outputs.run_example == 'true'
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-example.yml@2.4.0
    with:
      post_pr_comment: ${{ inputs.post_pr_comment }}
      enable_code_security: ${{ inputs.enable_code_security }}
      # Pass any scanner-specific inputs
    permissions:
      contents: read
      security-events: write
      actions: read
      pull-requests: write
```

**In `pr-reusable-security-hardening.yml` (PR testing):**
```yaml
  example-scanner:
    name: Example Scanner
    needs: scan-coordinator
    if: needs.scan-coordinator.outputs.run_example == 'true'
    uses: ./.github/workflows/scanner-example.yml
    with:
      post_pr_comment: ${{ inputs.post_pr_comment }}
      enable_code_security: ${{ inputs.enable_code_security }}
      # Pass any scanner-specific inputs
    permissions:
      contents: read
      security-events: write
      actions: read
      pull-requests: write
```

#### 2.3 Update Report Generator

Find the `generate-security-report` job and add your scanner to the needs:

```yaml
  generate-security-report:
    name: Generate Security Report
    runs-on: ubuntu-latest
    needs:
      - scan-coordinator
      - codeql-scanner
      - opengrep-scanner
      - bandit-scanner
      - gitleaks-scanner
      - container-scanner
      - infrastructure-scanner
      - example-scanner  # <-- Add here
    if: always()
```

In the report generation step, download your scanner's artifacts:

```yaml
    - name: Download Example artifacts
      if: needs.scan-coordinator.outputs.run_example == 'true'
      uses: actions/download-artifact@v5
      with:
        pattern: example-*
      continue-on-error: true

    - name: Download all scanner summaries
      uses: actions/download-artifact@v5
      with:
        pattern: scanner-summary-*
        merge-multiple: true
      continue-on-error: true
```

#### 2.4 Add Scanner to Summary Loop

**CRITICAL:** Add your scanner to the summary aggregation loop, otherwise it won't appear in PR comments!

Find the "Combine scanner summaries" step and add your scanner to the list:

```bash
# Combine all scanner summaries in a specific order
for scanner in codeql opengrep bandit gitleaks example container infrastructure sbom trivy-iac checkov trivy-container grype; do
  if [ -f "${scanner}.md" ]; then
    echo "✅ Adding ${scanner} summary..."
    cat "${scanner}.md" >> security-hardening-report.md
  else
    echo "⏭️  No ${scanner}.md summary found"
  fi
done
```

> **Note:** Add your scanner in a logical position in the list. Group similar scanners together (e.g., SAST scanners, container scanners, etc.).

### Step 3: Sync and Validate Workflows

After making changes to both workflow files, validate they're in sync:

```bash
./.github/scripts/validate-reusable-workflow-sync.sh
```

This script ensures that `reusable-security-hardening.yml` and `pr-reusable-security-hardening.yml` are structurally identical (ignoring path differences).

### Step 4: Update Documentation

#### 4.1 Update README.md

Add your scanner to the available scanners list:

```markdown
**Available scanners:**
- **SAST:** `codeql`, `opengrep`, `bandit`, `gitleaks`
- **Container:** `container`, `trivy-container`, `grype`
- **Infrastructure:** `infrastructure`, `trivy-iac`, `checkov`
- **Linting:** `lint`
- **New:** `example`
```

Add a usage example:

```markdown
**Example Security Focus:**
```yaml
with:
  scanners: codeql,example,gitleaks
```

#### 4.2 Update QUICK-START.md

Add quick-start examples:

```yaml
## Example Scanner Only

```yaml
name: security-example
on: [push]

jobs:
  scan:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.5.0
    with:
      scanners: example
```

#### 4.3 Create Examples

Add to `examples/scanner-list-examples.yml`:

```yaml
  example-focus:
    name: Example Scanner Focus
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.5.0
    with:
      scanners: 'example'
      post_pr_comment: true
```

### Step 4: Add Input Validation (Optional)

If your scanner requires specific inputs, add validation to the scan-coordinator:

```yaml
    - name: Validate example scanner inputs
      if: steps.resolve.outputs.run_example == 'true'
      run: |
        if [ -z "${{ inputs.example_config }}" ]; then
          echo "::warning::Example scanner requires example_config input"
        fi
```

---

## Scanner Workflow Template

Use this minimal template as a starting point:

```yaml
name: Example Security Scanner

on:
  workflow_dispatch:
  workflow_call:
    inputs:
      post_pr_comment:
        required: false
        type: boolean
        default: true
      enable_code_security:
        required: false
        type: boolean
        default: false

permissions:
  contents: read
  security-events: write
  actions: read
  pull-requests: write

jobs:
  example-analysis:
    name: Example Analysis
    runs-on: ubuntu-latest
    timeout-minutes: 15
    continue-on-error: true

    steps:
    - uses: actions/checkout@v5

    - name: Run Example Scanner
      run: |
        mkdir -p scanner-reports
        echo "🔍 Running example scanner..."
        # Run your scanner here

    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: example-reports
        path: scanner-reports/
        retention-days: 30
      if: always()

    - name: Generate summary
      if: always()
      run: |
        mkdir -p scanner-summaries
        cat > scanner-summaries/example.md << 'EOF'
        <details>
        <summary>🔍 Example Scanner</summary>

        **Status:** ✅ Completed
        **Issues Found:** 0

        **📁 Artifacts:** [Reports](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}#artifacts)

        </details>
        EOF

    - name: Upload summary
      uses: actions/upload-artifact@v4
      with:
        name: scanner-summary-example
        path: scanner-summaries/example.md
        retention-days: 7
      if: always()
```

---

## Testing Your Scanner

### Local Testing with act

Test your scanner locally before pushing:

```bash
# Install act (if not already)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test your scanner workflow
act workflow_dispatch -W .github/workflows/scanner-example.yml

# Test the full pipeline with your scanner
act push -W .github/workflows/reusable-security-hardening.yml -s scanners='example'
```

### Create Test Workflow

Create `.github/workflows/test-example-scanner.yml`:

```yaml
name: Test Example Scanner

on:
  workflow_dispatch:

jobs:
  test-scanner:
    uses: ./.github/workflows/scanner-example.yml
    with:
      post_pr_comment: false
      enable_code_security: false
    permissions:
      contents: read
      security-events: write
      actions: read
      pull-requests: write
```

### Integration Testing

Test with the full pipeline:

```yaml
name: Test Full Pipeline with Example

on:
  workflow_dispatch:

jobs:
  test-integration:
    uses: ./.github/workflows/reusable-security-hardening.yml
    with:
      scanners: example
      post_pr_comment: false
```

### Validation Checklist

- [ ] Scanner runs successfully in isolation
- [ ] Scanner generates all expected artifacts
- [ ] Summary section formats correctly
- [ ] Scanner integrates with **both** reusable workflows
- [ ] Scanner added to summary aggregation loop in both workflows
- [ ] Workflow sync validation passes (`./.github/scripts/validate-reusable-workflow-sync.sh`)
- [ ] Report generator includes scanner output
- [ ] No breaking changes to existing scanners
- [ ] Documentation is complete and accurate

---

## Documentation Requirements

Every new scanner must include:

### 1. Inline Documentation

Add comments explaining:
- What the scanner does
- Input requirements
- Output formats
- Severity level mappings

### 2. README Entry

Add a section describing:
- Scanner purpose
- Supported languages/technologies
- Configuration options
- Known limitations

### 3. Example Usage

Provide at least 3 examples:
- Standalone scanner usage
- Combined with other scanners
- Production-ready configuration

### 4. Changelog Entry

Update `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- New Example Scanner for detecting X vulnerabilities
- Support for Y file formats in Example Scanner
```

---

## Best Practices

### Scanner Naming

- Use descriptive, lowercase names: `trivy`, `snyk`, `sonarqube`
- Use hyphens for multi-word names: `secret-scanner`, `license-checker`
- Avoid version numbers: `scanner-v2` ❌, `scanner` ✅

### Error Handling

Always use `continue-on-error: true` for:
- Scanner execution steps (scanners may find issues)
- Artifact uploads (GitHub may have issues)
- SARIF uploads (may not be available)

Never use `continue-on-error: true` for:
- Checkout steps
- Setup steps (Python, Node, etc.)

### Performance

- Set reasonable `timeout-minutes` (10-15 minutes typical)
- Use caching for dependencies when possible
- Generate only necessary output formats

### Security

- Never hardcode credentials or tokens
- Use `secrets` for sensitive inputs
- Validate user inputs
- Use pinned action versions: `actions/checkout@v5` not `@main`

### Artifacts

- Set appropriate `retention-days` (7 for summaries, 30 for reports)
- Use descriptive artifact names: `example-scanner-reports`
- Include multiple formats (SARIF, JSON, text) when possible

### Summary Format

Follow the standard format:

```markdown
<details>
<summary>🔍 Scanner Name</summary>

**Status:** ✅ Completed | ⏭️ Skipped | ❌ Failed

**Issues Found:** N

| Severity | Count |
|----------|-------|
| 🔴 Critical | N |
| 🟠 High | N |
| 🟡 Medium | N |
| 🟢 Low | N |
| 🔵 Info | N |

**📁 Artifacts:** [Scanner Reports](link)

</details>
```

### Output Parsing

When parsing scanner output:

1. **Prefer JSON over text parsing**
   ```bash
   jq -r '.results[] | .severity' report.json
   ```

2. **Handle missing files gracefully**
   ```bash
   if [ -f "report.json" ]; then
     # parse
   else
     echo "Report not found"
   fi
   ```

3. **Provide default values**
   ```bash
   COUNT=$(jq -r '.count' report.json 2>/dev/null || echo "0")
   ```

4. **Map severity levels consistently**
   - CRITICAL/FATAL → 🔴 Critical
   - HIGH → 🟠 High
   - MEDIUM/MODERATE → 🟡 Medium
   - LOW → 🟢 Low
   - INFO/NOTE → 🔵 Info

---

## Common Issues and Solutions

### Issue: Scanner not appearing in output

**Solution:** Check that:
1. Scanner is added to `DEFAULT_SCANNERS` array
2. Output variable is set: `echo "run_example=${RUN[example]}" >> $GITHUB_OUTPUT`
3. Job needs include your scanner

### Issue: Summary not showing in PR comment

**Solution:** Verify:
1. Summary artifact is uploaded with pattern `scanner-summary-*`
2. Artifact name matches the pattern: `scanner-summary-example`
3. Report generator job includes your scanner in `needs`
4. **Scanner is added to the summary aggregation loop** in both workflow files
5. Both workflows are in sync (run validation script)

### Issue: SARIF upload fails

**Solution:**
1. Ensure SARIF file is valid JSON
2. Check `enable_code_security` is true
3. Verify file exists: `hashFiles('report.sarif') != ''`
4. Use `continue-on-error: true` (SARIF upload is optional)

### Issue: Scanner takes too long

**Solution:**
1. Increase `timeout-minutes`
2. Add caching for dependencies
3. Limit scan scope with configuration
4. Consider parallel execution for large repos

---

## Getting Help

- 📋 Check existing scanner implementations for reference
- 💬 Open a [Discussion](https://github.com/huntridge-labs/hardening-workflows/discussions)
- 🐛 Report bugs via [Issues](https://github.com/huntridge-labs/hardening-workflows/issues)
- 📧 Contact maintainers for major changes

---

## Pull Request Checklist

Before submitting your PR:

- [ ] Scanner workflow created and tested
- [ ] **Both** reusable workflows updated with scanner integration
- [ ] Scanner added to summary aggregation loop in both workflows
- [ ] Workflow sync validation passes
- [ ] Documentation added/updated
- [ ] Examples provided
- [ ] Tests passing
- [ ] No breaking changes to existing scanners
- [ ] PR description explains the scanner's purpose
- [ ] Changelog updated

---

## Example PR Description Template

```markdown
## Add [Scanner Name] Security Scanner

### Summary
This PR adds [Scanner Name] to detect [type of vulnerabilities] in [languages/technologies].

### Scanner Details
- **Tool**: [Scanner Name] v[version]
- **Language**: [Supported languages]
- **Output Formats**: SARIF, JSON, Text
- **Severity Levels**: Critical, High, Medium, Low

### Changes
- ✅ Created `scanner-example.yml` workflow
- ✅ Integrated with `reusable-security-hardening.yml`
- ✅ Added documentation and examples
- ✅ Tested with sample projects

### Usage
```yaml
with:
  scanners: example
```

### Testing
- [x] Tested standalone scanner workflow
- [x] Tested integration with full pipeline
- [x] Verified summary generation
- [x] Confirmed PR comment includes scanner output

### Screenshots
[Include screenshot of PR comment with scanner section]
```

---

**Thank you for contributing to making security scanning more accessible! 🎉**
