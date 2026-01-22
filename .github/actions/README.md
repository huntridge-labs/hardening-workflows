# Hardening Workflows - Composite Actions

This directory contains reusable composite actions for security scanning. Each action is self-contained and can be used independently in your workflows.

## Available Actions

### Code Security Scanners

| Action | Description | Language/Type | Documentation |
|--------|-------------|---------------|---------------|
| [scanner-bandit](scanner-bandit/) | Python security scanner (SAST) | Python | [README](scanner-bandit/README.md) |
| [scanner-codeql](scanner-codeql/) | GitHub CodeQL SAST scanner | Multi-language | [action.yml](scanner-codeql/action.yml) |

### Secrets Detection

| Action | Description | Language/Type | Documentation |
|--------|-------------|---------------|---------------|
| [scanner-gitleaks](scanner-gitleaks/) | Git secrets scanner | All languages | [README](scanner-gitleaks/README.md) |

### Infrastructure Security

| Action | Description | Language/Type | Documentation |
|--------|-------------|---------------|---------------|
| [scanner-trivy-iac](scanner-trivy-iac/) | Infrastructure-as-code scanner | Terraform, K8s, etc. | [README](scanner-trivy-iac/README.md) |

### Container Security

| Action | Description | Language/Type | Documentation |
|--------|-------------|---------------|---------------|
| [scanner-container](scanner-container/) | Multi-scanner container security | Container images | [README](scanner-container/README.md) |
| [scanner-container-summary](scanner-container-summary/) | Aggregate parallel container scan results | Container images | [README](scanner-container-summary/README.md) |

### Web Application Security

| Action | Description | Language/Type | Documentation |
|--------|-------------|---------------|---------------|
| [scanner-zap](scanner-zap/) | OWASP ZAP DAST scanner | Web applications | [README](scanner-zap/README.md) |

### Malware Detection

| Action | Description | Language/Type | Documentation |
|--------|-------------|---------------|---------------|
| [scanner-clamav](scanner-clamav/) | ClamAV malware scanner | All files | [README](scanner-clamav/README.md) |

### Code Quality & Linting

| Action | Description | Language/Type | Documentation |
|--------|-------------|---------------|---------------|
| [linter-yaml](linter-yaml/) | YAML syntax and style validation | YAML | [action.yml](linter-yaml/action.yml) |
| [linter-json](linter-json/) | JSON syntax validation | JSON | [action.yml](linter-json/action.yml) |
| [linter-python](linter-python/) | Python code quality (flake8 + bandit) | Python | [action.yml](linter-python/action.yml) |
| [linter-javascript](linter-javascript/) | JavaScript syntax and quality (JSHint) | JavaScript | [action.yml](linter-javascript/action.yml) |
| [linter-dockerfile](linter-dockerfile/) | Dockerfile best practices (Hadolint) | Dockerfile | [action.yml](linter-dockerfile/action.yml) |
| [linter-terraform](linter-terraform/) | Terraform formatting and validation | Terraform | [action.yml](linter-terraform/action.yml) |
| [linting-summary](linting-summary/) | Aggregate linter results into report | All | [action.yml](linting-summary/action.yml) |

### Utility Actions

| Action | Description | Documentation |
|--------|-------------|---------------|
| [parse-container-config](parse-container-config/) | Parse container scan configuration | [action.yml](parse-container-config/action.yml) |
| [get-job-id](get-job-id/) | Retrieve GitHub Actions job ID | [action.yml](get-job-id/action.yml) |

## Quick Start

### 1. Choose Your Approach

**Option A: Individual Scanners** (Most Flexible)
```yaml
- uses: actions/checkout@v6
- uses: huntridge-labs/hardening-workflows/.github/actions/scanner-bandit@main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Option B: Complete Security Example** (Recommended)
See [examples/composite-actions-example.yml](../../examples/composite-actions-example.yml) for a full security workflow.

**Option C: Complete Linting Example**
See [examples/composite-linting-example.yml](../../examples/composite-linting-example.yml) for a full linting workflow.

### 2. Common Usage Pattern

All scanner actions follow a similar pattern:

```yaml
steps:
  # 1. Checkout your code
  - name: Checkout repository
    uses: actions/checkout@v6

  # 2. Run the scanner
  - name: Run Security Scanner
    uses: huntridge-labs/hardening-workflows/.github/actions/scanner-{name}@main
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    with:
      fail_on_severity: 'high'
      enable_code_security: true
      post_pr_comment: true
```

## Common Inputs

Most actions support these inputs:

| Input | Description | Default |
|-------|-------------|---------|
| `post_pr_comment` | Post results as PR comment | `true` |
| `enable_code_security` | Upload SARIF to GitHub Security tab | `false` |
| `fail_on_severity` | Fail on severity threshold | `none` |

Scanner-specific inputs are documented in each action's README.

## Common Outputs

Most actions provide:
- Severity counts (critical, high, medium, low)
- Total finding count
- Scanner-specific metadata

## Requirements

All actions require:
1. **Repository checkout** before use
2. **GITHUB_TOKEN** environment variable (automatically available)
3. Appropriate **permissions** in workflow (see examples)

## Examples

### Scan Python Code

```yaml
- uses: actions/checkout@v6
- uses: huntridge-labs/hardening-workflows/.github/actions/scanner-bandit@main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    fail_on_severity: 'high'
```

### Scan for Secrets

```yaml
- uses: actions/checkout@v6
  with:
    fetch-depth: 0  # Full history for comprehensive scan
- uses: huntridge-labs/hardening-workflows/.github/actions/scanner-gitleaks@main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Scan Infrastructure

```yaml
- uses: actions/checkout@v6
- uses: huntridge-labs/hardening-workflows/.github/actions/scanner-trivy-iac@main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    iac_path: 'terraform'
```

### Scan Container

```yaml
- uses: actions/checkout@v6
- run: docker build -t myapp:test .
- uses: huntridge-labs/hardening-workflows/.github/actions/scanner-container@main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    image_ref: 'myapp:test'
```

### Lint YAML Files

```yaml
- uses: actions/checkout@v6
- uses: huntridge-labs/hardening-workflows/.github/actions/linter-yaml@main
  with:
    fail_on_issues: false
```

### Lint Python Code

```yaml
- uses: actions/checkout@v6
- uses: huntridge-labs/hardening-workflows/.github/actions/linter-python@main
  with:
    fail_on_issues: false
    max_line_length: '120'
```

### Lint Dockerfiles

```yaml
- uses: actions/checkout@v6
- uses: huntridge-labs/hardening-workflows/.github/actions/linter-dockerfile@main
  with:
    fail_on_issues: false
```

## Matrix Scanning

Scan multiple targets efficiently:

```yaml
jobs:
  security-scan:
    strategy:
      matrix:
        scanner: [bandit, gitleaks, trivy-iac]
    steps:
      - uses: actions/checkout@v6
      - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-${{ matrix.scanner }}@main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Best Practices

1. **Enable Code Security**: Set `enable_code_security: true` to populate the Security tab
2. **Use PR Comments**: Keep `post_pr_comment: true` for developer feedback
3. **Set Thresholds**: Use `fail_on_severity` to enforce standards
4. **Run on Schedule**: Add scheduled runs for continuous monitoring
5. **Review Results**: Don't ignore findings - review and address them

## Permissions

Workflows using these actions need:

```yaml
permissions:
  contents: read          # Read repository
  security-events: write  # Upload SARIF
  actions: read          # Read workflow info
  pull-requests: write   # Post PR comments
```

## Migrating from Reusable Workflows

If you're currently using reusable workflows, composite actions offer:
- ✅ More flexibility and control
- ✅ Easier customization
- ✅ Better debugging visibility
- ✅ Simpler matrix strategies

See [examples/README.md](../../examples/README.md) for migration guidance.

## Documentation

- **Action READMEs**: Detailed docs in each action directory
- **Examples**: [examples/](../../examples/) directory
- **Main Docs**: [docs/](../../docs/) directory
- **Changelog**: [CHANGELOG.md](../../CHANGELOG.md)

## Coming Soon

The following scanners are being migrated to composite actions:

- ✅ **scanner-codeql** - GitHub's code analysis (completed)
- ⏳ **scanner-opengrep** - Pattern-based security
- ⏳ **scanner-checkov** - Multi-framework IaC
- ⏳ **scanner-trivy-container** - Container scanning

## Support

- [Report Issues](https://github.com/huntridge-labs/hardening-workflows/issues)
- [Contributing Guide](../../CONTRIBUTING.md)
- [Discussions](https://github.com/huntridge-labs/hardening-workflows/discussions)

---

_Last Updated: January 2026_
