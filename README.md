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
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.5.0
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
- `iac_path`, `aws_region`, `enable_code_security`, `codeql_languages`, `clamav_scan_path` — optional knobs for specific scanners

### Outputs

- Artifact: `security-hardening-report-<job-id>.md`
- Optional PR comment containing the same summary

### Permissions & secrets

Minimum permissions shown in the example. Omit `AWS_ACCOUNT_ID` when you don’t run AWS checks—the workflow will skip that portion automatically.

## Linting workflow

Run consistent code quality checks with `.github/workflows/linting.yml`:

```yaml
jobs:
  lint:
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@main
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
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@main

  security:
    needs: linting
    if: always()
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.5.0
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
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-iac.yml@main
    with:
      iac_path: 'infrastructure'
      enable_code_security: true

  checkov:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-checkov.yml@main
    with:
      iac_path: 'infrastructure'
      framework: 'terraform'
```

### Container scanning

```yaml
jobs:
  trivy-container:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-container.yml@main
    with:
      image_ref: 'myapp:latest'
      enable_code_security: true

  grype:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-grype.yml@main
    with:
      image_ref: 'myapp:latest'

  sbom:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-syft.yml@main
    with:
      scan-path: 'some/dirOrFile/path'
      scan-image: 'myapp:latest'
```

### SAST scanning

```yaml
jobs:
  codeql:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-codeql.yml@main
    with:
      codeql_languages: 'python,javascript'
      enable_code_security: true

  opengrep:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-opengrep.yml@main

  bandit:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-bandit.yml@main

  gitleaks:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-gitleaks.yml@main
```

All individual scanners support `workflow_dispatch` for manual runs and `workflow_call` for reusable workflow integration.

## More examples

Check `QUICK-START.md` for curated recipes and browse the `examples/` directory for ready-to-copy snippets, from nightly runs to matrix fan-outs.

## License
This project is licensed under the [GNU Affero General Public License v3](./LICENSE.md).
