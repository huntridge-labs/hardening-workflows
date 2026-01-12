# Hardening Dagger Module

A portable security scanning pipeline that runs **anywhere** - locally, in GitHub Actions, GitLab CI, or any system with Docker.

## Why Dagger?

The traditional GitHub Actions reusable workflows have limitations:
- Require checkout access to the hardening-workflows repository
- Don't work on GHE servers where the repo is private or doesn't exist
- Difficult to test locally (ACT has many compatibility issues)
- Platform-locked to GitHub

This Dagger module solves all of these problems by packaging the entire hardening pipeline into a container.

## Quick Start

### Local Usage

```bash
# Install Dagger CLI
curl -fsSL https://dl.dagger.io/dagger/install.sh | sh

# Run a full scan
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  scan --source . --scanners all

# Run specific scanners
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  scan --source . --scanners "bandit,gitleaks,trivy-iac"

# Export reports to local directory
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  scan --source . --scanners all \
  export --path ./reports
```

### GitHub Actions (github.com or GHE)

```yaml
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Dagger
        run: curl -fsSL https://dl.dagger.io/dagger/install.sh | sh

      - name: Run hardening scan
        run: |
          dagger call -m ghcr.io/huntridge-labs/hardening:latest \
            scan --source . --scanners all \
            export --path ./reports

      - uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: reports/
```

### GitLab CI

```yaml
security-scan:
  image: docker:24-dind
  services: [docker:24-dind]
  script:
    - curl -fsSL https://dl.dagger.io/dagger/install.sh | sh
    - ./bin/dagger call -m ghcr.io/huntridge-labs/hardening:latest \
        scan --source . export --path ./reports
  artifacts:
    paths: [reports/]
    reports:
      sast: reports/hardening-report.sarif
```

## Available Scanners

| Scanner | Type | Description |
|---------|------|-------------|
| `bandit` | SAST | Python security linter |
| `gitleaks` | Secrets | Detect hardcoded secrets |
| `opengrep` | SAST | Semgrep-based code analysis |
| `codeql` | SAST | GitHub's semantic code analysis (Python, JS, Go, Java, C#, C++, Ruby) |
| `trivy-iac` | IaC | Terraform/CloudFormation misconfigs |
| `checkov` | IaC | Policy-as-code for IaC |
| `grype` | SCA | Dependency vulnerabilities |
| `clamav` | Malware | Virus/malware detection |
| `trivy-container` | Container | Container image vulnerabilities |
| `zap` | DAST | OWASP ZAP dynamic web application scanning |

### Scanner Groups

- `all` - Default scanners (bandit, gitleaks, trivy-iac, checkov, grype, opengrep)
- `full` - All SAST scanners including CodeQL and ClamAV
- `sast` - bandit, opengrep, gitleaks, codeql
- `secrets` - gitleaks
- `iac` - trivy-iac, checkov
- `container` - trivy-container, grype
- `dast` - zap (requires running target application)

## Configuration Options

```bash
dagger call -m ghcr.io/huntridge-labs/hardening:latest scan \
  --source .                          # Source directory (required)
  --scanners "all"                    # Scanners to run
  --severity-threshold "none"         # Fail threshold: none|low|medium|high|critical
  --iac-path "infrastructure"         # Path to IaC files
  --output-format "all"               # Output: markdown|json|sarif|all
  --repository "owner/repo"           # For report metadata
  --branch "main"                     # For report metadata
  --commit-sha "abc123"               # For report metadata
```

## GitHub Integration

### Post PR Comment

```bash
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  github post-pr-comment \
  --token env:GITHUB_TOKEN \
  --repository "owner/repo" \
  --pr-number 123 \
  --report ./reports/hardening-report.md
```

### Upload SARIF to Code Scanning

```bash
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  github upload-sarif \
  --token env:GITHUB_TOKEN \
  --repository "owner/repo" \
  --sarif-file ./reports/hardening-report.sarif \
  --ref "refs/heads/main" \
  --commit-sha "abc123def456..."
```

### For GHE Servers

Add `--api-url` to point to your GHE API:

```bash
--api-url "https://ghe.company.com/api/v3"
```

## Using on GHE Without External Access

1. **Mirror the container image** to your GHE's container registry:
   ```bash
   docker pull ghcr.io/huntridge-labs/hardening:2.10.0
   docker tag ghcr.io/huntridge-labs/hardening:2.10.0 \
     ghe.company.com/security/hardening:2.10.0
   docker push ghe.company.com/security/hardening:2.10.0
   ```

2. **Use the local image** in your workflows:
   ```yaml
   env:
     HARDENING_IMAGE: ghe.company.com/security/hardening:2.10.0
   ```

See [examples/mirror-to-ghe.sh](examples/mirror-to-ghe.sh) for automation.

## Individual Scanner Functions

Run scanners individually for more control:

```bash
# Just Bandit
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  bandit --source .

# Just Gitleaks with custom config
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  gitleaks --source . --config ".gitleaks.toml"

# Trivy IaC with custom path
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  trivy-iac --source . --path "terraform/"

# Scan a container image
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  trivy-container --image-ref "nginx:latest"

# CodeQL analysis (Python and JavaScript)
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  codeql --source . --languages "python,javascript"

# ZAP DAST scan against a running application
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  zap --target-url "http://localhost:8080" --scan-type baseline

# ZAP scan with auto-started container
dagger call -m ghcr.io/huntridge-labs/hardening:latest \
  zap-with-service --app-image "myapp:latest" --app-port 8080
```

## Output Files

After running `scan ... export --path ./reports`:

```
reports/
├── hardening-report.md      # Human-readable summary
├── hardening-report.json    # Machine-readable full report
├── hardening-report.sarif   # For GitHub Code Scanning / IDE integration
├── THRESHOLD_EXCEEDED       # Present if findings exceed threshold
├── bandit-reports/          # Raw Bandit output
├── gitleaks-reports/        # Raw Gitleaks output
├── trivy-iac-reports/       # Raw Trivy output
└── ...                      # Other scanner outputs
```

## Development

```bash
# Clone and enter the module directory
cd hardening-dagger

# Run locally during development
dagger call scan --source ../test-project --scanners bandit

# Build the module
dagger build

# Publish to a registry
dagger publish ghcr.io/huntridge-labs/hardening:dev
```

## Migration from Reusable Workflows

If you're currently using the reusable workflows:

**Before (reusable workflow):**
```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.10.0
    with:
      scanners: "bandit,gitleaks"
```

**After (Dagger module):**
```yaml
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: curl -fsSL https://dl.dagger.io/dagger/install.sh | sh
      - run: |
          dagger call -m ghcr.io/huntridge-labs/hardening:2.10.0 \
            scan --source . --scanners "bandit,gitleaks" \
            export --path ./reports
```

The Dagger approach:
- Works on any GHE server (just mirror the container)
- Runs identically locally
- No repository checkout permissions needed
- Simpler debugging (run exact same command locally)
