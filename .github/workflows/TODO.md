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
| `scanner-bandit` | 289 lines | 323 lines | [x] | Good parity. Action has `python_version` input |
| `scanner-codeql` | 797 lines | 324 lines | [ ] | **Major gap** - see details below |
| `scanner-opengrep` | 260 lines | 215 lines | [~] | Action missing `post_pr_comment`, has extra `config`/`paths` |
| `scanner-gitleaks` | 187 lines | 195 lines | [x] | Good parity. Action does own checkout |
| `scanner-trivy-iac` | 255 lines | 328 lines | [x] | Action better - has GHES install logic |
| `scanner-checkov` | 265 lines | 291 lines | [x] | Good parity. Action has `api_key` input, uses external scripts |
| `scanner-clamav` | 283 lines | 334 lines | [x] | Action self-contained (inline Python), GHES-compatible |
| `scanner-zap` | ~300 lines | ~350 lines | [x] | Action has more inputs (build, registry auth) |
| `scanner-container` | 523 lines | 474 lines | [x] | Orchestrator action - handles Trivy/Grype/Syft, GHES-aware |
| `scanner-trivy-container` | thin | `scanner-container/` | [x] | Uses shared action with `scanners: trivy` |
| `scanner-grype` | thin | `scanner-container/` | [x] | Uses shared action with `scanners: grype` |
| `scanner-syft` | 145 lines | 220 lines | [x] | SBOM generation - **CREATED** |
| `container-scan` | orchestrator | N/A | N/A | Multi-job workflow: discover → build → scan → summary |
| `infrastructure-scan` | orchestrator | N/A | N/A | Calls trivy-iac + checkov |
| `linting` | orchestrator | `linter-*/` | [ ] | TODO: Audit linter actions |

#### CodeQL Gap Analysis (Critical)

**Workflow features NOT in action:**
- Multi-language matrix strategy (auto-generates jobs per language)
- Language auto-detection from codebase
- `codeql_languages` input (comma-separated)
- `query_suite`, `scan_paths`, `ignore_paths` inputs
- Auto-generated CodeQL config file
- BQRS extraction to JSON

**Action features:**
- Single `language` input (caller must do matrix)
- `setup_python_version`, `setup_node_version` inputs
- Relies on external script for summary

**Decision needed:** Should action support multi-language matrix, or should caller handle?

#### Gitleaks Note

Action does its own `actions/checkout` with `fetch-depth: 0`. This is unusual - most actions expect caller to checkout. Document clearly or change.

#### ClamAV Note

Action is self-contained with inline Python for report parsing. Uses `cvdupdate` for virus database updates which is more reliable than `freshclam` on CI runners. GHES-compatible using `github.server_url`.

#### Container Scanning Note

The `scanner-container/action.yml` is a comprehensive action that:
- Handles Trivy, Grype, and Syft via the `scanners` input
- Has GHES compatibility (installs Trivy directly on GHES, uses published action on github.com)
- Deduplicates CVEs across scanners for accurate counts
- Includes bundled scripts for summary generation

The `container-scan.yml` workflow is an orchestrator that:
- Discovers Dockerfiles in repo (discover mode)
- Or scans pre-existing remote images (remote mode)
- Calls `scanner-container` action for actual scanning

#### Syft/SBOM - RESOLVED

**Created:** `scanner-syft/action.yml` (220 lines)

Features:
- Supports both source code paths (`scan_path`) and container images (`scan_image`)
- Multiple output formats: cyclonedx-json, spdx-json, syft-json, table
- Registry authentication for private images
- GHES compatibility (installs Syft if not available)
- Generates human-readable table output alongside JSON
- GitHub Dependency Graph integration (optional)
- Outputs: `sbom_file`, `component_count`, `scan_target`

### 1.2 Identify Missing Actions

- [x] `scanner-syft/action.yml` - SBOM generation (**CREATED**)
- [ ] Verify `security-summary/action.yml` handles all scanner outputs
- [ ] Verify linter actions have parity with linting workflow

### 1.3 Document Input/Output Differences

| Scanner | Workflow-only Inputs | Action-only Inputs | Secret Handling |
|---------|---------------------|--------------------|-----------------|
| bandit | - | `python_version` | N/A |
| codeql | `codeql_languages`, `query_suite`, `scan_paths`, `ignore_paths` | `language`, `setup_*_version` | N/A |
| opengrep | `post_pr_comment` | `config`, `paths` | N/A |
| gitleaks | - | - | `GITLEAKS_LICENSE` via env var |
| trivy-iac | - | - | N/A |

**Secret handling pattern:** Actions use environment variables (`env.SECRET_NAME`) instead of `secrets` context. Callers must set `env:` block.

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

- [x] **Basic GHES Example** - All scanners using actions directly (`all-scanners.yml`)
- [x] **SAST-Only GHES** - CodeQL, Bandit, OpenGrep, Gitleaks (`sast-only.yml`)
- [x] **Container Scanning GHES** - Trivy + Grype + SBOM (`container-scanning.yml`)
- [x] **IaC Scanning GHES** - Trivy IaC + Checkov (`infrastructure-scanning.yml`)
- [x] **DAST Scanning GHES** - ZAP with various modes (`dast-scanning.yml`)
- [x] **Combined Summary** - Documented in README.md

### 3.3 GHES Example Template Pattern

**Primary Pattern: Direct Action Reference**

For GHES instances that can reach github.com or have the repo mirrored internally:

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

jobs:
  sast-scanning:
    name: SAST Scanners
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Use full path with ref for each action
      - name: Run Bandit
        uses: huntridge-labs/hardening-workflows/.github/actions/scanner-bandit@v2.12.0
        with:
          fail_on_severity: 'high'

      - name: Run OpenGrep
        uses: huntridge-labs/hardening-workflows/.github/actions/scanner-opengrep@v2.12.0
        with:
          fail_on_severity: 'high'

      - name: Run Gitleaks
        uses: huntridge-labs/hardening-workflows/.github/actions/scanner-gitleaks@v2.12.0
        with:
          fail_on_severity: 'high'

  container-scanning:
    name: Container Scanners
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy Container
        uses: huntridge-labs/hardening-workflows/.github/actions/scanner-container@v2.12.0
        with:
          image_ref: 'myorg/myapp:latest'
          scanner: 'trivy'
          fail_on_severity: 'high'

  infrastructure-scanning:
    name: Infrastructure Scanners
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy IaC
        uses: huntridge-labs/hardening-workflows/.github/actions/scanner-trivy-iac@v2.12.0
        with:
          iac_path: 'terraform/'
          fail_on_severity: 'high'

      - name: Run Checkov
        uses: huntridge-labs/hardening-workflows/.github/actions/scanner-checkov@v2.12.0
        with:
          iac_path: 'terraform/'
          fail_on_severity: 'high'
```

**Alternative Pattern: Air-Gapped / Mirrored Repo**

For GHES instances without github.com access, mirror the repo internally and reference your GHES instance:

```yaml
jobs:
  sast-scanning:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Reference from internal GHES mirror
      - name: Run Bandit
        uses: my-ghes-org/hardening-workflows/.github/actions/scanner-bandit@v2.12.0
        with:
          fail_on_severity: 'high'
```

---

## Phase 4: Migrate Reusable Workflows

### 4.1 Workflow Deprecation Strategy

1. **Add deprecation notices** - Workflow annotations/comments
2. **Document migration path** - Clear upgrade guide
3. **Maintain backwards compatibility** - Existing callers continue working
4. **Sunset timeline** - Announce removal date (e.g., next major version)

### 4.2 Thin Wrapper Pattern

Convert workflows to thin wrappers that call actions directly:

```yaml
# scanner-bandit.yml (thin wrapper - ~60 lines)

name: Bandit Python Security Scanner

on:
  workflow_dispatch:
  workflow_call:
    inputs:
      post_pr_comment:
        type: boolean
        default: true
      enable_code_security:
        type: boolean
        default: false
      fail_on_severity:
        type: string
        default: 'none'
      python_version:
        type: string
        default: '3.12'

permissions:
  contents: read
  security-events: write
  actions: read
  pull-requests: write

jobs:
  bandit-analysis:
    name: Bandit Python Security
    runs-on: ubuntu-latest
    timeout-minutes: 15
    continue-on-error: true

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Run Bandit Scanner
        uses: huntridge-labs/hardening-workflows/.github/actions/scanner-bandit@v2.12.0
        with:
          post_pr_comment: ${{ inputs.post_pr_comment }}
          enable_code_security: ${{ inputs.enable_code_security }}
          fail_on_severity: ${{ inputs.fail_on_severity }}
          python_version: ${{ inputs.python_version }}
```

**Key simplifications:**
- No `HRL_REF` env variable
- No checkout of hardening-workflows repo
- No local vs external conditional steps
- Direct action reference with version tag
- GitHub automatically fetches the action

### 4.3 Workflows to Convert

- [x] `scanner-bandit.yml` → thin wrapper
- [x] `scanner-codeql.yml` → thin wrapper (retains matrix generation for multi-language)
- [x] `scanner-opengrep.yml` → thin wrapper
- [x] `scanner-gitleaks.yml` → thin wrapper
- [x] `scanner-trivy-iac.yml` → thin wrapper
- [x] `scanner-checkov.yml` → thin wrapper
- [x] `scanner-clamav.yml` → thin wrapper
- [x] `scanner-zap.yml` → thin wrapper
- [x] `scanner-trivy-container.yml` → thin wrapper
- [x] `scanner-grype.yml` → thin wrapper
- [x] `scanner-syft.yml` → thin wrapper
- [x] `linting.yml` → thin wrapper (calls multiple linter actions)
- [x] `infrastructure-scan.yml` → thin wrapper
- [x] `container-scan.yml` → thin wrapper (retains discovery/build orchestration)

**Simplification achieved:** Removed HRL_REF, checkout complexity, and local vs external conditional steps. All scanner workflows now use direct action references (e.g., `huntridge-labs/hardening-workflows/.github/actions/scanner-bandit@ref`).

### 4.4 Orchestrator Workflow

Update `reusable-security-hardening.yml` to:
- [x] Use action outputs for coordination (scan-coordinator already handles this)
- [x] Simplify job dependencies (removed HRL_REF and checkout complexity)
- [x] Maintain identical interface for consumers (inputs unchanged, CodeQL query_suite/scan_paths/ignore_paths inputs now no-ops)

**Note:** CodeQL inputs `query_suite`, `scan_paths`, and `ignore_paths` are accepted for backwards compatibility but are no longer passed to the thin wrapper. Use `config_file` to specify a custom CodeQL configuration instead.

---

## Phase 5: Documentation

### 5.1 Update Main README

- [x] Document dual usage patterns (github.com vs GHES)
- [x] Add architecture overview section
- [x] Link to examples directory

### 5.2 Update docs/scanners.md

- [x] Add architecture overview at top
- [x] Document thin wrapper pattern

### 5.3 Create Migration Guide

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

### 7.2 Release-it Configuration

The `.release-it.json` must be updated to maintain version refs across all files.

**Current coverage (via `@j-ulrich/release-it-regex-bumper`):**
- `HRL_REF` env variable in workflows
- `hardening-workflows/.github/workflows/*.yml@X.X.X` refs
- `hardening-workflows/.github/actions/*@X.X.X` refs in `.github/actions/**`
- Schema `$id` URLs

**New patterns to add:**

```json
{
  "files": [
    "examples/github-enterprise/**/*.yml",
    "examples/github-enterprise/**/*.yaml"
  ],
  "search": {
    "pattern": "(huntridge-labs/hardening-workflows/.github/actions/[^@]+)@[^\\s]+",
    "flags": "g"
  },
  "replace": "${1}@{{version}}"
}
```

```json
{
  "files": [
    ".github/workflows/scanner-*.yml",
    ".github/workflows/linting.yml",
    ".github/workflows/infrastructure-scan.yml",
    ".github/workflows/container-scan.yml"
  ],
  "search": {
    "pattern": "(huntridge-labs/hardening-workflows/.github/actions/[^@]+)@[^\\s]+",
    "flags": "g"
  },
  "replace": "${1}@{{version}}"
}
```

**Checklist:**
- [x] Add GHES example workflow patterns to release-it config
- [x] Add thin wrapper workflow patterns to release-it config
- [x] Add docs/migration guide patterns if action refs are used (no action refs in docs currently)
- [ ] Test release-it dry-run to verify all refs are updated
- [ ] Verify no refs are missed with: `grep -r "@v[0-9]" --include="*.yml" --include="*.md"`

### 7.3 Release Checklist

- [x] All actions have feature parity with workflows
- [x] Examples tested and documented
- [ ] Migration guide complete
- [ ] Deprecation notices added
- [ ] Changelog updated
- [x] README updated
- [x] **Release-it config updated for new file patterns**
- [ ] **Dry-run release to verify version refs**

### 7.4 Current Status

Thin wrapper workflows currently use feature branch ref (`@refactor/depricate-reusable-workflows`) for testing. On release, release-it will update these to the release version tag.

---

## Open Questions

1. ~~**Artifact sharing for GHES**: Best pattern for sharing actions across jobs?~~ **RESOLVED**
   - GHES can pull actions directly from github.com public repos
   - No mirroring or local copies needed

2. **Secret handling**: Actions can't receive secrets directly. Best pattern?
   - Pass as environment variables from caller (**current approach**)
   - Document clearly in examples

3. **Coordinator workflow**: Should `reusable-security-hardening.yml` become:
   - A thin wrapper that calls individual workflows?
   - A single job that calls actions sequentially?
   - A matrix that parallelizes action calls?

4. ~~**Version pinning**: How to handle version pinning for GHES examples?~~ **RESOLVED**
   - Hardcoded in examples with pinned versions (e.g., `@v2.12.0`)
   - release-it regex-bumper will update on release

---

## Timeline

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Audit & Gap Analysis | [x] Complete - All scanners audited, syft action created |
| 2 | Action Enhancement | [~] Partial - Most actions already have good parity |
| 3 | Create Example Workflows | [x] Complete - GHES examples created in `examples/github-enterprise/` |
| 4 | Migrate Reusable Workflows | [x] Complete - All scanner + orchestrator workflows converted to thin wrappers |
| 5 | Documentation | [x] Complete - README.md and docs/scanners.md updated |
| 6 | Testing | [~] In Progress - Testing via feature branch |
| 7 | Release | [ ] Pending - Action refs use feature branch, release-it will update |

---

## References

- [GitHub Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [GitHub Composite Actions](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action)
- [GHES Actions Sync](https://docs.github.com/en/enterprise-server/admin/github-actions/managing-access-to-actions-from-githubcom)
