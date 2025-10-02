# Quick Start

## Templates

### Fast CodeQL Scan (Development)
```yaml
name: Dev Security
on: [push]
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
    with:
      scan_type: 'codeql-only'
    permissions:
      contents: read
      security-events: write
```

### Full Scan (Pre-merge)
```yaml
name: PR Security
on: [pull_request]
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
    with:
      scan_type: 'full'
      post_pr_comment: true
    permissions:
      contents: read
      security-events: write
      pull-requests: write
      checks: write
```

### Custom Mix
```yaml
name: Custom Security
on: [push]
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
    with:
      enable_codeql: true
      enable_gitleaks: true
      enable_bandit: false
      enable_semgrep: false
    permissions:
      contents: read
      security-events: write
```

### Python Project
```yaml
name: Python Security
on: [push, pull_request]
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
    with:
      codeql_languages: 'python'
      enable_codeql: true
      enable_bandit: true
    permissions:
      contents: read
      security-events: write
```

## Scanner Reference

| Scanner | Finds | Speed |
|---------|-------|-------|
| CodeQL | SQL injection, XSS, vulnerabilities | Medium |
| Semgrep | Security patterns | Fast |
| Bandit | Python security issues | Very Fast |
| Gitleaks | Hardcoded secrets | Fast |

## When to Use

- **Development**: `scan_type: 'codeql-only'` (fast feedback)
- **Pre-merge**: `scan_type: 'full'` (comprehensive)
- **Custom needs**: Use `enable_*` flags

## More Info

- [Full Docs](docs/granular-scanner-control.md)
- [Examples](examples/granular-scanner-usage.yml)
- [Architecture](docs/architecture.md)
