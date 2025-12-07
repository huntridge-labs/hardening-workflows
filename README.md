# Security Hardening Workflows

One reusable GitHub Actions workflow, many scanners. Pick the components you need, and we ship a consolidated report plus an optional PR comment.

## Reusable pipeline

**Workflow:** `.github/workflows/reusable-security-hardening.yml`

**Available scanners:**
- **SAST:** `codeql`, `opengrep`, `bandit`, `gitleaks`
- **Container:** `container`, `trivy-container`, `grype`, `sbom`
- **Infrastructure:** `infrastructure`, `trivy-iac`, `checkov`
- **Malware:** `clamav`
- **Linting:** `lint`

### Quick start

```yaml
# .github/workflows/security.yml
name: security
on: [push, pull_request]

jobs:
  hardening:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.6.0
    with:
      scanners: all
      python_version: '3.12'
      post_pr_comment: true
    permissions:
      contents: read
      security-events: write
      pull-requests: write
    secrets:
      AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }} # optional
      # Required for private GitHub Enterprise Server installations:
      # HARDENING_WORKFLOWS_CHECKOUT_TOKEN: ${{ secrets.HARDENING_WORKFLOWS_CHECKOUT_TOKEN }}
```

#### ClamAV malware scanning examples

```yaml
# Scan entire repository (default)
with:
  scanners: clamav

# Scan specific directory
with:
  scanners: clamav
  clamav_scan_path: 'src/'

# Scan a specific archive file
with:
  scanners: clamav
  clamav_scan_path: 'dist/my-app.tar.gz'

# Scan multiple paths (use workflow_dispatch to specify)
with:
  scanners: clamav
  clamav_scan_path: 'build/ dist/'
```

### Example selector patterns

- **Full coverage:** `scanners: all`
- **Single scanner:** `scanners: opengrep`
- **SAST only:** `scanners: codeql,opengrep,bandit,gitleaks`
- **Infrastructure only:** `scanners: trivy-iac,checkov`
- **Container only:** `scanners: trivy-container,grype,sbom`
- **Malware only:** `scanners: clamav`
- **Focused mix:** `scanners: container,infrastructure,gitleaks`

### Inputs at a glance

- `scanners` *(string)* — comma-separated list or `all`
- `python_version` *(string, default `3.12`)* — runtime for Python-based tools
- `post_pr_comment` *(boolean, default `true`)* — leave a summary on PRs
- `allow_failure` *(boolean, default `true`)* — when `false`, scanners will fail the job if vulnerabilities at or above `severity_threshold` are detected
- `severity_threshold` *(string, default `high`)* — minimum severity level that triggers job failure when `allow_failure` is `false`. Options: `low`, `medium`, `high`, `critical`
- `iac_path`, `aws_region`, `enable_code_security`, `codeql_languages`, `clamav_scan_path` — optional knobs for specific scanners

### Failure Control

By default, security scans report findings but don't fail the workflow. To enforce security gates:

```yaml
jobs:
  hardening:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.6.0
    with:
      scanners: all
      allow_failure: false          # Fail on vulnerabilities
      severity_threshold: high      # Fail on high or critical issues
```

**Severity levels** (from least to most severe): `low` → `medium` → `high` → `critical`

When `allow_failure: false`:
- Scanners check findings against the `severity_threshold`
- Jobs fail if any finding meets or exceeds the threshold
- Example: `severity_threshold: medium` fails on medium, high, or critical findings

**Note:** Some scanners map severities differently:
- **Bandit** only has HIGH/MEDIUM/LOW (no critical) — HIGH is treated as critical equivalent
- **Gitleaks** treats any secret detection as critical
- **ClamAV** treats any malware detection as critical

### Outputs

- Artifact: `security-hardening-report-<job-id>.md`
- Optional PR comment containing the same summary

### Permissions & secrets

Minimum permissions shown in the example. Omit `AWS_ACCOUNT_ID` when you don't run AWS checks—the workflow will skip that portion automatically.

#### GitHub Enterprise Server (GHE)

If you're using a private GitHub Enterprise Server and have forked or mirrored this repository, you'll need to provide a `HARDENING_WORKFLOWS_CHECKOUT_TOKEN` secret with read access to your private/internal hardening-workflows repository. This token is used to check out shared actions and scripts.

```yaml
secrets:
  HARDENING_WORKFLOWS_CHECKOUT_TOKEN: ${{ secrets.HARDENING_WORKFLOWS_CHECKOUT_TOKEN }}
```

For public GitHub.com usage, this secret is not required.

## Linting workflow

Run consistent code quality checks with `.github/workflows/linting.yml`:

```yaml
jobs:
  lint:
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@2.6.0
    permissions:
      contents: read
      pull-requests: write
      checks: write
```

Runs Ruff, ESLint, Prettier, markdownlint, and yamllint.

## Pairing workflows

```yaml
jobs:
  linting:
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@2.6.0

  security:
    needs: linting
    if: always()
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.6.0
    with:
      scanners: all
```

## Results location

- GitHub Security tab for SARIF uploads (CodeQL/OpenGrep/Bandit)
- Workflow artifacts for each scanner plus combined Markdown report
- Optional PR comment summarizing the run

## Individual scanner workflows

For more granular control, you can call individual scanner workflows directly:

### Infrastructure scanning

```yaml
jobs:
  trivy-iac:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-iac.yml@2.6.0
    with:
      iac_path: 'infrastructure'
      enable_code_security: true
      fail_on_severity: high  # Fail on high or critical findings

  checkov:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-checkov.yml@2.6.0
    with:
      iac_path: 'infrastructure'
      framework: 'terraform'
```

### Container scanning

```yaml
jobs:
  trivy-container:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-container.yml@2.6.0
    with:
      image_ref: 'myapp:latest'
      enable_code_security: true
      fail_on_severity: critical  # Only fail on critical vulnerabilities

  grype:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-grype.yml@2.6.0
    with:
      image_ref: 'myapp:latest'
      fail_on_severity: high  # Fail on high or critical

  sbom:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-syft.yml@2.6.0
    with:
      scan-path: 'some/dirOrFile/path'
      scan-image: 'myapp:latest'
```

### SAST scanning

```yaml
jobs:
  codeql:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-codeql.yml@2.6.0
    with:
      codeql_languages: 'python,javascript'
      enable_code_security: true

  opengrep:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-opengrep.yml@2.6.0
    with:
      fail_on_severity: medium  # Fail on medium or higher

  bandit:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-bandit.yml@2.6.0
    with:
      fail_on_severity: high  # Fail on high findings (Bandit's highest level)

  gitleaks:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-gitleaks.yml@2.6.0
    with:
      fail_on_severity: critical  # Any secret detection fails
```

All individual scanners support `workflow_dispatch` for manual runs and `workflow_call` for reusable workflow integration.

## More examples

Check `QUICK-START.md` for curated recipes and browse the `examples/` directory for ready-to-copy snippets, from nightly runs to matrix fan-outs.

## License
This project is licensed under the [GNU Affero General Public License v3](./LICENSE.md).
