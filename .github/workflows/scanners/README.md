# Security Scanners

This directory contains modular security scanner workflows that can be called independently or as part of the comprehensive security hardening pipeline.

## Directory Structure

```
scanners/
├── container-scan.yml     # Container image security scanning
├── infrastructure.yml     # Infrastructure-as-code security scanning
├── sast.yml              # Coordinating workflow for all SAST scanners
├── sast/                 # Static Application Security Testing scanners
│   ├── codeql.yml        # GitHub CodeQL scanner for multi-language code analysis
│   ├── semgrep.yml       # Semgrep/OpenGrep for pattern-based security scanning
│   └── bandit.yml        # Bandit for Python-specific security analysis
└── secrets/              # Secret detection scanners
    └── gitleaks.yml      # Gitleaks for detecting hardcoded secrets
```

## Scanner Categories

### Container Security

**Container Scan** (`container-scan.yml`)
- Comprehensive container image security scanning
- Multiple tools: Trivy, Docker Scout, etc.
- Vulnerability detection, secret scanning, and compliance checks
- Supports Docker and OCI images

### Infrastructure Security

**Infrastructure Scan** (`infrastructure.yml`)
- Infrastructure-as-code security analysis
- Multiple tools: Trivy, Checkov, Terrascan
- Terraform, CloudFormation, Kubernetes manifest scanning
- Policy-as-code validation

### SAST (Static Application Security Testing)

**SAST Coordinator** (`sast.yml`)
- Coordinating workflow for all SAST scanners
- Runs CodeQL, Semgrep, and Bandit together
- Legacy workflow - consider using individual scanners for granular control

**CodeQL** (`sast/codeql.yml`)
- GitHub's semantic code analysis engine
- Supports multiple languages (Python, JavaScript, TypeScript, etc.)
- Highly accurate with low false positive rate
- Integrates with GitHub Security tab
- Configurable through `.github/codeql/codeql-config.yml`

**Semgrep** (`sast/semgrep.yml`)
- Fast, open-source static analysis tool
- Pattern-based security rule matching
- Supports many languages
- Free comprehensive security rules
- Good for finding common vulnerabilities

**Bandit** (`sast/bandit.yml`)
- Python-specific security linter
- Focuses on common Python security issues
- Fast and lightweight
- Configurable through `pyproject.toml` or `.bandit`

### Secrets Detection

**Gitleaks** (`secrets/gitleaks.yml`)
- Detects hardcoded secrets and credentials
- Scans entire git history
- Low false positive rate
- Essential for preventing credential leaks

## Usage

### As Part of Reusable Security Hardening Workflow

The scanners are automatically orchestrated by `reusable-security-hardening.yml`:

```yaml
jobs:
  security:
    uses: ./.github/workflows/reusable-security-hardening.yml
    with:
      scan_type: 'codeql-only'  # Run only CodeQL
      # OR use granular controls:
      enable_codeql: true
      enable_semgrep: false
      enable_bandit: true
      enable_gitleaks: true
```

### Standalone Usage

Each scanner can be called independently:

```yaml
jobs:
  codeql-scan:
    uses: ./.github/workflows/scanners/sast/codeql.yml
    with:
      codeql_languages: 'python,javascript'
      post_pr_comment: true
    permissions:
      contents: read
      security-events: write
      actions: read
      pull-requests: write
```

## Scan Type Options

When using `reusable-security-hardening.yml`, you can choose from:

- `full` - All scanners (default)
- `sast-only` - All SAST scanners (CodeQL, Semgrep, Bandit, Gitleaks)
- `codeql-only` - Only CodeQL scanner
- `container-only` - Only container security scans
- `infrastructure-only` - Only infrastructure security scans

## Granular Scanner Control

Override the scan type with explicit enable/disable flags:

```yaml
with:
  scan_type: 'full'
  # Disable specific scanners even in 'full' mode:
  enable_semgrep: false
  enable_bandit: false
```

Or cherry-pick scanners regardless of scan type:

```yaml
with:
  scan_type: 'container-only'  # Normally runs only container scans
  # But also enable CodeQL:
  enable_codeql: true
```

## Adding New Scanners

To add a new scanner:

1. Create a new workflow file in the appropriate category directory
2. Follow the pattern of existing scanners:
   - Support `workflow_call` trigger
   - Accept `post_pr_comment` input
   - Set appropriate permissions
   - Upload artifacts and SARIF results
   - Use `continue-on-error: true` for non-blocking scans

3. Update `reusable-security-hardening.yml`:
   - Add input parameter for the scanner
   - Add output in scan-coordinator
   - Add logic in scan determination step
   - Create a new job to call the scanner
   - Add the job to security-summary dependencies

4. Update this README with scanner details

## Scanner Outputs

All scanners produce:
- **SARIF files** - Uploaded to GitHub Code Scanning (if available)
- **JSON reports** - Machine-readable results
- **Text reports** - Human-readable results
- **Artifacts** - Available for download for 30 days

## Best Practices

- **Use `codeql-only` for rapid feedback** during active development
- **Use `full` for comprehensive scans** before merging to main
- **Use granular controls** when debugging specific security issues
- **Review artifacts** even when scans pass (they may contain warnings)
- **Enable GitHub Advanced Security** for integrated security dashboard

## Performance Considerations

Scanner execution times (approximate):
- **CodeQL**: 5-10 minutes (depends on codebase size and languages)
- **Semgrep**: 1-3 minutes (fast pattern matching)
- **Bandit**: 30 seconds - 2 minutes (Python only)
- **Gitleaks**: 1-2 minutes (depends on git history size)

Running scanners in parallel provides faster overall execution time.
