# Workflow Migration Plan: Reusable Workflows → Actions

## Overview

Migrate from reusable workflows to action-first architecture while maintaining backwards compatibility for existing github.com users.

### Goals

1. **Actions as primary building blocks** - All scanner logic lives in composite actions
2. **Reusable workflows as thin wrappers** - Maintain backwards compatibility for github.com users
3. **Example workflows for GHES** - Provide templates showing direct action usage for GitHub Enterprise Server

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Consumer Workflows                          │
├─────────────────────────────────────────────────────────────────┤
│  github.com Users          │  GHES Users                        │
│  ─────────────────         │  ─────────────────                 │
│  Reusable Workflows        │  Copy example workflows            │
│  (workflow_call)           │  (direct action usage)             │
│           │                │           │                        │
│           ▼                │           ▼                        │
│  ┌─────────────────────────┴───────────────────────────────┐   │
│  │              Composite Actions (source of truth)         │   │
│  │  scanner-bandit/  scanner-codeql/  scanner-gitleaks/    │   │
│  │  scanner-trivy-iac/  scanner-checkov/  scanner-zap/     │   │
│  │  scanner-container/  linter-*/  *-summary/              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Audit & Gap Analysis

### 1.1 Compare Workflow vs Action Feature Parity

For each scanner, document differences between reusable workflow and action:

| Scanner | Workflow | Action | Parity | Notes |
|---------|----------|--------|--------|-------|
| `scanner-bandit` | `scanner-bandit.yml` | `scanner-bandit/action.yml` | [ ] | |
| `scanner-codeql` | `scanner-codeql.yml` | `scanner-codeql/action.yml` | [ ] | |
| `scanner-opengrep` | `scanner-opengrep.yml` | `scanner-opengrep/action.yml` | [ ] | |
| `scanner-gitleaks` | `scanner-gitleaks.yml` | `scanner-gitleaks/action.yml` | [ ] | |
| `scanner-trivy-iac` | `scanner-trivy-iac.yml` | `scanner-trivy-iac/action.yml` | [ ] | |
| `scanner-checkov` | `scanner-checkov.yml` | `scanner-checkov/action.yml` | [ ] | |
| `scanner-clamav` | `scanner-clamav.yml` | `scanner-clamav/action.yml` | [ ] | |
| `scanner-zap` | `scanner-zap.yml` | `scanner-zap/action.yml` | [ ] | |
| `scanner-container` | `container-scan.yml` | `scanner-container/action.yml` | [ ] | |
| `scanner-trivy-container` | `scanner-trivy-container.yml` | `scanner-container/action.yml` | [ ] | Uses shared action |
| `scanner-grype` | `scanner-grype.yml` | `scanner-container/action.yml` | [ ] | Uses shared action |
| `scanner-syft` | `scanner-syft.yml` | (needs action) | [ ] | SBOM generation |
| `infrastructure-scan` | `infrastructure-scan.yml` | (orchestrator) | [ ] | Coordinates trivy-iac + checkov |
| `linting` | `linting.yml` | `linter-*/action.yml` | [ ] | Multiple linter actions |

### 1.2 Identify Missing Actions

- [ ] `scanner-syft/action.yml` - SBOM generation
- [ ] `infrastructure-scanner/action.yml` - Unified IaC action (or keep separate)
- [ ] Review if `security-summary/action.yml` handles all scanner outputs

### 1.3 Document Input/Output Differences

For each scanner, ensure action exposes same inputs as workflow:
- [ ] All workflow inputs available as action inputs
- [ ] All workflow outputs available as action outputs
- [ ] Secret handling documented (actions can't receive secrets directly)

---

## Phase 2: Action Enhancement

### 2.1 Standardize Action Interface

All scanner actions should follow this pattern:

```yaml
inputs:
  # Common inputs (all scanners)
  post_pr_comment:
    description: 'Post results as PR comment'
    default: 'true'
  enable_code_security:
    description: 'Upload SARIF to GitHub Security tab'
    default: 'false'
  fail_on_severity:
    description: 'Fail on severity threshold (none, low, medium, high, critical)'
    default: 'none'

  # Scanner-specific inputs
  # ...

outputs:
  # Common outputs
  issue_count:
    description: 'Total issues found'
  high_count:
    description: 'High severity issues'
  medium_count:
    description: 'Medium severity issues'
  low_count:
    description: 'Low severity issues'
  sarif_file:
    description: 'Path to SARIF report'

  # Scanner-specific outputs
  # ...
```

### 2.2 Action Checklist

For each action, verify:

- [ ] **Checkout not assumed** - Action documents that caller must checkout
- [ ] **Outputs exposed** - All relevant data available as outputs
- [ ] **SARIF upload optional** - Controlled by `enable_code_security`
- [ ] **Summary generation** - Creates both job summary and PR comment artifact
- [ ] **Severity threshold** - Respects `fail_on_severity` input
- [ ] **GHES compatible** - Uses `github.server_url` not hardcoded `github.com`

### 2.3 Actions to Update

- [ ] `scanner-bandit/action.yml` - Verify all inputs match workflow
- [ ] `scanner-codeql/action.yml` - Complex, verify language detection
- [ ] `scanner-opengrep/action.yml` - Verify rule sets
- [ ] `scanner-gitleaks/action.yml` - License handling for orgs
- [ ] `scanner-trivy-iac/action.yml` - IaC path handling
- [ ] `scanner-checkov/action.yml` - Framework detection
- [ ] `scanner-clamav/action.yml` - Scan path handling
- [ ] `scanner-zap/action.yml` - Complex scan modes
- [ ] `scanner-container/action.yml` - Registry auth handling

---

## Phase 3: Create Example Workflows

### 3.1 Directory Structure

```
examples/
├── README.md                           # Overview and index
├── github-enterprise/
│   ├── README.md                       # GHES-specific guidance
│   ├── all-scanners.yml               # Complete example
│   ├── sast-only.yml                  # SAST scanners
│   ├── container-scanning.yml         # Container scanning
│   ├── infrastructure-scanning.yml    # IaC scanning
│   └── dast-scanning.yml              # ZAP DAST
├── github-com/
│   ├── README.md                       # Reusable workflow examples
│   └── (link to main docs)
└── advanced/
    ├── custom-scanner-selection.yml   # Pick specific scanners
    ├── matrix-container-scan.yml      # Multi-container matrix
    ├── monorepo-scanning.yml          # Monorepo patterns
    └── scheduled-scanning.yml         # Cron-based scanning
```

### 3.2 Example Templates to Create

- [ ] **Basic GHES Example** - All scanners using actions directly
- [ ] **SAST-Only GHES** - CodeQL, Bandit, OpenGrep, Gitleaks
- [ ] **Container Scanning GHES** - Trivy + Grype + SBOM
- [ ] **IaC Scanning GHES** - Trivy IaC + Checkov
- [ ] **DAST Scanning GHES** - ZAP with various modes
- [ ] **Combined Summary** - How to aggregate results from multiple actions

### 3.3 GHES Example Template Pattern

```yaml
# examples/github-enterprise/all-scanners.yml
name: Security Scanning (GHES Compatible)

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write
  pull-requests: write

env:
  # Pin to a release tag - update as needed
  HARDENING_WORKFLOWS_REF: 'v2.12.0'

jobs:
  checkout-actions:
    name: Checkout Hardening Workflows
    runs-on: ubuntu-latest
    steps:
      - name: Checkout hardening-workflows
        uses: actions/checkout@v4
        with:
          repository: huntridge-labs/hardening-workflows
          ref: ${{ env.HARDENING_WORKFLOWS_REF }}
          path: .hardening-workflows
          # For GHES: use a PAT or GitHub App token
          # token: ${{ secrets.HARDENING_WORKFLOWS_TOKEN }}

      - name: Upload actions
        uses: actions/upload-artifact@v4
        with:
          name: hardening-actions
          path: .hardening-workflows/.github/actions/
          retention-days: 1

  sast-scanning:
    name: SAST Scanners
    needs: checkout-actions
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Download actions
        uses: actions/download-artifact@v4
        with:
          name: hardening-actions
          path: .actions/

      - name: Run Bandit
        uses: ./.actions/scanner-bandit
        with:
          fail_on_severity: 'high'

      - name: Run OpenGrep
        uses: ./.actions/scanner-opengrep
        with:
          fail_on_severity: 'high'

      - name: Run Gitleaks
        uses: ./.actions/scanner-gitleaks
        with:
          fail_on_severity: 'high'

  # ... more jobs for other scanner categories
```

---

## Phase 4: Migrate Reusable Workflows

### 4.1 Workflow Deprecation Strategy

1. **Add deprecation notices** - Workflow annotations/comments
2. **Document migration path** - Clear upgrade guide
3. **Maintain backwards compatibility** - Existing callers continue working
4. **Sunset timeline** - Announce removal date (e.g., next major version)

### 4.2 Thin Wrapper Pattern

Convert workflows to thin wrappers that call actions:

```yaml
# Before: scanner-bandit.yml (contains all logic)
# After: scanner-bandit.yml (thin wrapper)

name: Bandit Python Security Scanner

on:
  workflow_call:
    inputs:
      post_pr_comment:
        type: boolean
        default: true
      # ... other inputs
    secrets:
      HARDENING_WORKFLOWS_CHECKOUT_TOKEN:
        required: false

jobs:
  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Bandit Scanner
        uses: huntridge-labs/hardening-workflows/.github/actions/scanner-bandit@v2
        with:
          post_pr_comment: ${{ inputs.post_pr_comment }}
          enable_code_security: ${{ inputs.enable_code_security }}
          fail_on_severity: ${{ inputs.fail_on_severity }}
```

### 4.3 Workflows to Convert

- [ ] `scanner-bandit.yml` → thin wrapper
- [ ] `scanner-codeql.yml` → thin wrapper
- [ ] `scanner-opengrep.yml` → thin wrapper
- [ ] `scanner-gitleaks.yml` → thin wrapper
- [ ] `scanner-trivy-iac.yml` → thin wrapper
- [ ] `scanner-checkov.yml` → thin wrapper
- [ ] `scanner-clamav.yml` → thin wrapper
- [ ] `scanner-zap.yml` → thin wrapper
- [ ] `scanner-trivy-container.yml` → thin wrapper
- [ ] `scanner-grype.yml` → thin wrapper
- [ ] `scanner-syft.yml` → thin wrapper
- [ ] `linting.yml` → thin wrapper (calls multiple linter actions)
- [ ] `infrastructure-scan.yml` → thin wrapper
- [ ] `container-scan.yml` → thin wrapper

### 4.4 Orchestrator Workflow

Update `reusable-security-hardening.yml` to:
- [ ] Use action outputs for coordination
- [ ] Simplify job dependencies
- [ ] Maintain identical interface for consumers

---

## Phase 5: Documentation

### 5.1 Update Main README

- [ ] Document dual usage patterns (github.com vs GHES)
- [ ] Add "Which approach should I use?" decision tree
- [ ] Link to examples directory

### 5.2 Create Migration Guide

```markdown
# docs/migration/workflows-to-actions.md

## Why Actions?

- GHES compatibility
- More flexibility
- Easier testing
- Can be composed differently

## Migration Steps

1. Identify current workflow usage
2. Choose appropriate example template
3. Copy and customize
4. Test in non-production branch
5. Update production workflows
```

### 5.3 Update Scanner Reference

- [ ] Document both workflow and action usage for each scanner
- [ ] Add GHES-specific notes

---

## Phase 6: Testing

### 6.1 Test Matrix

| Test Type | github.com | GHES Simulation | Notes |
|-----------|------------|-----------------|-------|
| Reusable workflows | ✓ | N/A | Existing tests |
| Direct action usage | ✓ | ✓ | New tests needed |
| Example workflows | ✓ | ✓ | E2E validation |
| Backwards compatibility | ✓ | N/A | Ensure no breaking changes |

### 6.2 New Tests to Add

- [ ] Action unit tests (all inputs/outputs)
- [ ] Example workflow integration tests
- [ ] GHES compatibility tests (mock `github.server_url`)
- [ ] Backwards compatibility tests for workflows

---

## Phase 7: Release Plan

### 7.1 Version Strategy

- **v2.x** - Maintain current interface, add deprecation warnings
- **v3.0** - Actions-first, workflows are thin wrappers
- **v4.0** - (Future) Remove deprecated workflow-specific code

### 7.2 Release Checklist

- [ ] All actions have feature parity with workflows
- [ ] Examples tested and documented
- [ ] Migration guide complete
- [ ] Deprecation notices added
- [ ] Changelog updated
- [ ] README updated

---

## Open Questions

1. **Artifact sharing for GHES**: Best pattern for sharing actions across jobs?
   - Upload/download artifact (current proposal)
   - Git submodule
   - Copy action files into consumer repo

2. **Secret handling**: Actions can't receive secrets directly. Best pattern?
   - Pass as environment variables from caller
   - Use GitHub App tokens
   - Document clearly

3. **Coordinator workflow**: Should `reusable-security-hardening.yml` become:
   - A thin wrapper that calls individual workflows?
   - A single job that calls actions sequentially?
   - A matrix that parallelizes action calls?

4. **Version pinning**: How to handle version pinning for GHES examples?
   - Hardcoded in examples (update manually)
   - Input variable with default
   - Document recommended approach

---

## Timeline

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Audit & Gap Analysis | [ ] Not Started |
| 2 | Action Enhancement | [ ] Not Started |
| 3 | Create Example Workflows | [ ] Not Started |
| 4 | Migrate Reusable Workflows | [ ] Not Started |
| 5 | Documentation | [ ] Not Started |
| 6 | Testing | [ ] Not Started |
| 7 | Release | [ ] Not Started |

---

## References

- [GitHub Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [GitHub Composite Actions](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action)
- [GHES Actions Sync](https://docs.github.com/en/enterprise-server/admin/github-actions/managing-access-to-actions-from-githubcom)
