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
name: Security Hardening Pipeline

on:
  # Trigger on push to main branch
  push:
    branches: [ main ]

  # Trigger on pull requests to main
  pull_request:
    branches: [ main ]

  # Allow manual workflow runs
  workflow_dispatch:

  # Optional: Run weekly full scans on Sundays at 2 AM UTC
  schedule:
    - cron: '0 2 * * 0'

permissions:
  contents: read
  security-events: write
  pull-requests: write
  actions: read
  checks: write
  id-token: write

jobs:
  hardening:
    name: Security Hardening
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.9.0
    with:
      scanners: all
      python_version: '3.12'
      post_pr_comment: true
    secrets:
      AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }} # optional
      GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }} # required for organization repos
      # Required for private GitHub Enterprise Server installations:
      # HARDENING_WORKFLOWS_CHECKOUT_TOKEN: ${{ secrets.HARDENING_WORKFLOWS_CHECKOUT_TOKEN }}
```

### Workflow trigger recommendations

**For optimal scanner behavior:**

- **`pull_request`**: Essential for PR-scoped scanning. Gitleaks and other scanners will analyze all changes in the PR.
- **`push`**: Scans commits as they land on your main branch. Gitleaks scans only new commits.
- **`workflow_dispatch`**: Enables manual runs. Gitleaks performs full repository history scans when triggered manually.
- **`schedule`**: Useful for periodic full repository audits (recommended weekly).

**Why include multiple triggers?** Different event types provide different scan coverage:
- Pull requests get full diff analysis
- Push events catch direct commits to main
- Manual/scheduled runs enable comprehensive historical scans

### Example selector patterns

- **Full coverage:** `scanners: all`
- **Single scanner:** `scanners: opengrep`
- **SAST only:** `scanners: codeql,opengrep,bandit,gitleaks`
- **Infrastructure only:** `scanners: trivy-iac,checkov`
- **Container only:** `scanners: trivy-container,grype,sbom`
- **Malware only:** `scanners: clamav`
- **Focused mix:** `scanners: container,infrastructure,gitleaks`

### Common inputs

- `scanners` *(string)* — comma-separated list or `all`
- `python_version` *(string, default `3.12`)* — runtime for Python-based tools
- `post_pr_comment` *(boolean, default `true`)* — leave a summary on PRs
- `allow_failure` *(boolean, default `true`)* — when `false`, scanners will fail the job if vulnerabilities at or above `severity_threshold` are detected
- `severity_threshold` *(string, default `high`)* — minimum severity level that triggers job failure when `allow_failure` is `false`. Options: `low`, `medium`, `high`, `critical`

### Failure control

By default, security scans report findings but don't fail the workflow. To enforce security gates:

```yaml
jobs:
  hardening:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.9.0
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

## Scanner configuration

<details>
<summary><strong>🔍 CodeQL</strong> - GitHub's semantic code analysis engine</summary>

### Description
CodeQL analyzes code to find security vulnerabilities and coding errors. Supports multiple languages with deep semantic analysis.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `codeql_languages` | Comma-separated list of languages to analyze (e.g., `python,javascript`) | `python,javascript` | No |
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `true` | No |

### Example usage

```yaml
with:
  scanners: codeql
  codeql_languages: 'python,javascript,go'
  enable_code_security: true
```

### Supported languages
`python`, `javascript`, `typescript`, `java`, `csharp`, `cpp`, `go`, `ruby`

</details>

<details>
<summary><strong>🔐 Gitleaks</strong> - Secrets detection scanner</summary>

### Description
Scans git history and code for hardcoded secrets, API keys, passwords, and tokens.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `gitleaks_enable_comments` | Enable inline PR comments (requires license for orgs) | `true` | No |
| `gitleaks_notify_user_list` | Comma-separated list of users to notify (e.g., `@user1,@user2`) | `''` | No |
| `gitleaks_enable_summary` | Enable job summary | `true` | No |
| `gitleaks_enable_upload_artifact` | Upload SARIF artifact on detection | `true` | No |
| `gitleaks_config` | Path to custom config file (e.g., `path/to/gitleaks.toml`) | `''` | No |
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `fail_on_severity` | Fail on any secret detection (use any value except `none`) | `none` | No |

### Required secrets

| Secret | Description | Required |
|--------|-------------|----------|
| `GITLEAKS_LICENSE` | License key from [gitleaks.io](https://gitleaks.io) | **Yes** (for organizations) |

### Example usage

```yaml
with:
  scanners: gitleaks
  gitleaks_enable_comments: true
  gitleaks_notify_user_list: '@security-team,@admin'
  fail_on_severity: critical  # Fail if any secret found
secrets:
  GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

### Scan behavior by event type
- **`pull_request`**: Scans all changes in the PR
- **`push`**: Scans only new commits in the push
- **`workflow_dispatch`/`schedule`**: Full repository history scan

</details>

<details>
<summary><strong>🐍 Bandit</strong> - Python security linter</summary>

### Description
Finds common security issues in Python code using static analysis.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `true` | No |
| `fail_on_severity` | Fail on any finding (Bandit doesn't support severity filtering) | `none` | No |

### Example usage

```yaml
with:
  scanners: bandit
  enable_code_security: true
  fail_on_severity: high  # Fail on any finding
```

### Note
Bandit analyzes only Python files and supports severity levels: LOW, MEDIUM, HIGH.

</details>

<details>
<summary><strong>🔬 OpenGrep (Semgrep)</strong> - Multi-language SAST scanner</summary>

### Description
Fast, customizable static analysis with extensive rule sets for multiple languages.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `true` | No |
| `fail_on_severity` | Fail if findings match severity (`none`, `low`, `medium`, `high`) | `none` | No |

### Example usage

```yaml
with:
  scanners: opengrep
  enable_code_security: true
  fail_on_severity: medium  # Fail on medium or higher
```

</details>

<details>
<summary><strong>🏗️ Trivy IaC</strong> - Infrastructure-as-Code scanner</summary>

### Description
Scans IaC files (Terraform, CloudFormation, Kubernetes, etc.) for misconfigurations and security issues.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `iac_path` | Path to IaC directory | `infrastructure` | No |
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `false` | No |
| `fail_on_severity` | Severity threshold to fail (`none`, `low`, `medium`, `high`, `critical`) | `none` | No |

### Example usage

```yaml
with:
  scanners: trivy-iac
  iac_path: 'terraform/'
  enable_code_security: true
  fail_on_severity: high
```

### Supported frameworks
Terraform, CloudFormation, Kubernetes, Dockerfile, and more.

</details>

<details>
<summary><strong>☑️ Checkov</strong> - Policy-as-Code scanner</summary>

### Description
Scans cloud infrastructure configurations for security and compliance issues with extensive built-in policies.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `iac_path` | Path to IaC directory | `infrastructure` | No |
| `framework` | IaC framework (`terraform`, `cloudformation`, `kubernetes`, etc.) | `terraform` | No |
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `false` | No |
| `fail_on_severity` | Fail on any check failure (no severity filtering) | `none` | No |

### Example usage

```yaml
with:
  scanners: checkov
  iac_path: 'infrastructure/'
  framework: terraform
  enable_code_security: true
```

</details>

<details>
<summary><strong>🐳 Trivy Container</strong> - Container image vulnerability scanner</summary>

### Description
Comprehensive vulnerability scanner for container images and filesystems.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `image_ref` | Container image to scan (e.g., `nginx:latest`) | - | **Yes** |
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `false` | No |
| `fail_on_severity` | Severity threshold to fail (`none`, `low`, `medium`, `high`, `critical`) | `none` | No |

### Example usage

```yaml
with:
  scanners: trivy-container
  image_ref: 'myapp:latest'
  enable_code_security: true
  fail_on_severity: critical
```

### Note
For use with the reusable workflow, you'll need to build your image first in a previous job.

</details>

<details>
<summary><strong>🦅 Grype</strong> - Fast vulnerability scanner</summary>

### Description
Fast, accurate vulnerability scanner for container images and filesystems with excellent detection rates.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `image_ref` | Container image to scan | - | **Yes** |
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `false` | No |
| `fail_on_severity` | Severity threshold to fail (`none`, `low`, `medium`, `high`, `critical`) | `none` | No |

### Example usage

```yaml
with:
  scanners: grype
  image_ref: 'myapp:latest'
  fail_on_severity: high
```

</details>

<details>
<summary><strong>📦 Syft (SBOM)</strong> - Software Bill of Materials generator</summary>

### Description
Generates detailed Software Bill of Materials (SBOM) for images and filesystems.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `scan-path` | Directory or file path to scan | `.` | No |
| `scan-image` | Container image to scan | - | No |
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |

### Example usage

```yaml
# Scan filesystem
with:
  scanners: sbom
  scan-path: 'dist/'

# Scan container image
with:
  scanners: sbom
  scan-image: 'myapp:latest'
```

</details>

<details>
<summary><strong>🦠 ClamAV</strong> - Malware scanner</summary>

### Description
Industry-standard open-source antivirus engine for detecting trojans, viruses, malware, and other malicious threats.

### Configuration inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `clamav_scan_path` | Path to scan (file, directory, or archive) | `.` | No |
| `enable_code_security` | Upload results to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `true` | No |
| `fail_on_severity` | Fail if malware detected (use any value except `none`) | `none` | No |

### Example usage

```yaml
# Scan entire repository
with:
  scanners: clamav

# Scan specific directory
with:
  scanners: clamav
  clamav_scan_path: 'uploads/'

# Scan archive file
with:
  scanners: clamav
  clamav_scan_path: 'dist/release.tar.gz'
  fail_on_severity: critical
```

### Note
ClamAV updates virus definitions before each scan and can scan archives, compressed files, and executables.

</details>


## Outputs & artifacts

- **Consolidated report**: `security-hardening-report-<job-id>.md` artifact
- **Individual scanner results**: Each scanner uploads its own detailed reports
- **PR comments**: Optional summary comment on pull requests (when `post_pr_comment: true`)
- **GitHub Security tab**: SARIF uploads when `enable_code_security: true`

## Permissions & secrets

### Required permissions

```yaml
permissions:
  contents: read          # Read repository contents
  security-events: write  # Upload SARIF to Security tab
  actions: read          # Read workflow artifacts
  pull-requests: write   # Post PR comments
  checks: write         # Update check runs
  id-token: write       # For AWS authentication (if using infrastructure scans)
```

### Optional secrets

| Secret | Purpose | Required When |
|--------|---------|---------------|
| `AWS_ACCOUNT_ID` | AWS infrastructure scanning | Using infrastructure scanners |
| `GITLEAKS_LICENSE` | Organization license key from [gitleaks.io](https://gitleaks.io) | **Running Gitleaks in GitHub organizations** |
| `HARDENING_WORKFLOWS_CHECKOUT_TOKEN` | Access private workflow repository | Using private GitHub Enterprise Server |

#### GitLeaks organization license

If you're running GitLeaks scans in a GitHub organization, you'll need to provide a `GITLEAKS_LICENSE` secret. Obtain a license key from [gitleaks.io](https://gitleaks.io) and add it as an organization or repository secret.

```yaml
secrets:
  GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

For personal repositories, GitLeaks will run without a license.

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
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@2.9.0
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
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@2.9.0

  security:
    needs: linting
    if: always()
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.9.0
    with:
      scanners: all
```

## Individual scanner workflows

For more granular control, call individual scanner workflows directly. Each scanner's configuration is detailed in the [Scanner Configuration](#scanner-configuration) section above.

### Quick reference

```yaml
# SAST scanners
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-codeql.yml@2.9.0
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-opengrep.yml@2.9.0
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-bandit.yml@2.9.0
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-gitleaks.yml@2.9.0

# Infrastructure scanners
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-iac.yml@2.9.0
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-checkov.yml@2.9.0

# Container scanners
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-container.yml@2.9.0
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-grype.yml@2.9.0
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-syft.yml@2.9.0

# Malware scanner
uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-clamav.yml@2.9.0
```

All individual scanners support `workflow_dispatch` for manual runs and `workflow_call` for reusable workflow integration.

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
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-iac.yml@2.8.1
    with:
      iac_path: 'infrastructure'
      enable_code_security: true
      fail_on_severity: high  # Fail on high or critical findings

  checkov:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-checkov.yml@2.8.1
    with:
      iac_path: 'infrastructure'
      framework: 'terraform'
```

### Container scanning

All container scanners support both public and private registries (Docker Hub, GHCR, AWS ECR, GCR, etc.).

```yaml
jobs:
  # Public image - no authentication needed
  trivy-public:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-container.yml@2.8.1
    with:
      image_ref: 'nginx:alpine'
      fail_on_severity: high

  # GitHub Container Registry (GHCR) with authentication
  grype-ghcr:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-grype.yml@2.8.1
    with:
      image_ref: 'ghcr.io/myorg/myapp:latest'
      registry_username: ${{ github.actor }}
      fail_on_severity: high
    secrets:
      registry_password: ${{ secrets.GITHUB_TOKEN }}

  # AWS ECR with authentication
  trivy-ecr:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-container.yml@2.8.1
    with:
      image_ref: '123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest'
      registry_username: 'AWS'
    secrets:
      registry_password: ${{ secrets.ECR_PASSWORD }}

  # Docker Hub with authentication
  grype-dockerhub:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-grype.yml@2.8.1
    with:
      image_ref: 'docker.io/myorg/myapp:latest'
      registry_username: ${{ secrets.DOCKERHUB_USERNAME }}
    secrets:
      registry_password: ${{ secrets.DOCKERHUB_TOKEN }}

  # SBOM generation - supports paths and images
  sbom:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-syft.yml@2.8.1
    with:
      scan-image: 'myapp:latest'  # Can scan local or remote images
      # OR scan-path: 'src/'      # Can also scan directories/files
```

### SAST scanning

```yaml
jobs:
  codeql:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-codeql.yml@2.8.1
    with:
      codeql_languages: 'python,javascript'
      enable_code_security: true

  opengrep:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-opengrep.yml@2.8.1
    with:
      fail_on_severity: medium  # Fail on medium or higher

  bandit:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-bandit.yml@2.8.1
    with:
      fail_on_severity: high  # Fail on high findings (Bandit's highest level)

  gitleaks:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-gitleaks.yml@2.8.1
    with:
      fail_on_severity: critical  # Any secret detection fails
```

All individual scanners support `workflow_dispatch` for manual runs and `workflow_call` for reusable workflow integration.

## Config-driven matrix container scanning
<details>
  <summary>Scan multiple containers across registries using a config file</summary>

When you need to scan multiple containers across different registries, use the config-driven matrix workflow instead of calling individual scanner workflows multiple times.

### When to use this workflow

**Use the matrix workflow when:**
- Scanning 3+ containers regularly
- Managing containers across multiple registries (GHCR, ECR, Docker Hub, etc.)
- You want centralized configuration for all container scans
- Running the same scanners against multiple containers

**Use individual scanner workflows when:**
- Scanning 1-2 containers
- Need different scanner combinations per container
- One-off or ad-hoc scanning needs

### Setup instructions

This workflow is designed to be **copied to your repository** (not called remotely) so you can add custom registry secrets.

**1. Copy the workflow template**

Copy [.github/workflows/container-scan-from-config.yml](https://github.com/huntridge-labs/hardening-workflows/blob/main/.github/workflows/container-scan-from-config.yml) to your repository's `.github/workflows/` directory.

**2. Add your registry secrets**

Edit the copied workflow's `env:` block in the `parse-config` job to include your registry secrets:

```yaml
env:
  CONFIG_FILE: ${{ inputs.config_file }}
  SCHEMA_FILE: .hardening-workflows/.github/schemas/container-config.schema.json
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  # Add your custom secrets here:
  GHCR_USERNAME: ${{ secrets.GHCR_USERNAME }}
  ECR_PASSWORD: ${{ secrets.ECR_PASSWORD }}
  DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
  DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
  MY_CUSTOM_SECRET: ${{ secrets.MY_CUSTOM_SECRET }}
```

**3. Create your container config file**

Create a config file (YAML, JSON, or JavaScript) defining your containers. See [examples/container-config.example.yml](https://github.com/huntridge-labs/hardening-workflows/blob/main/examples/container-config.example.yml) for reference.

### Config file format

Config files support three formats: YAML, JSON, or JavaScript (CommonJS).

**YAML example:**

```yaml
containers:
  - name: my-api
    image: ghcr.io/myorg/api:latest
    registry_username: ${GHCR_USERNAME}
    registry_password: ${GITHUB_TOKEN}
    scanners:
      - trivy
      - grype
      - syft
    fail_on_severity: high
    enable_code_security: true
    post_pr_comment: true

  - name: my-worker
    image: 123456789.dkr.ecr.us-east-1.amazonaws.com/worker:latest
    registry_username: AWS
    registry_password: ${ECR_PASSWORD}
    scanners:
      - trivy
    fail_on_severity: critical
    enable_code_security: true
    post_pr_comment: false
```

**JSON example:**

```json
{
  "containers": [
    {
      "name": "nginx-public",
      "image": "nginx:alpine",
      "scanners": ["trivy", "grype"],
      "fail_on_severity": "high",
      "enable_code_security": true,
      "post_pr_comment": true
    }
  ]
}
```

**JavaScript example:**

```javascript
module.exports = {
  containers: [
    {
      name: 'my-app',
      image: 'myapp:latest',
      registry_username: process.env.DOCKERHUB_USERNAME,
      registry_password: process.env.DOCKERHUB_TOKEN,
      scanners: ['trivy', 'syft'],
      fail_on_severity: 'medium',
      enable_code_security: true,
      post_pr_comment: true
    }
  ]
};
```

### Config file properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Unique identifier (alphanumeric, dashes, underscores) |
| `image` | string | Yes | Full container image reference (registry/repo:tag) |
| `registry_username` | string | No | Username for authentication (use `${SECRET_NAME}` syntax) |
| `registry_password` | string | No | Password/token for authentication (use `${SECRET_NAME}` syntax) |
| `scanners` | array | Yes | List of scanners to run: `trivy`, `grype`, `syft` |
| `fail_on_severity` | string | No | Fail threshold: `none`, `low`, `medium`, `high`, `critical` (default: `none`) |
| `enable_code_security` | boolean | No | Upload SARIF to GitHub Security tab (default: `false`) |
| `post_pr_comment` | boolean | No | Post results as PR comment (default: `false`) |

### Environment variable expansion

Use `${SECRET_NAME}` syntax in your config file to reference secrets. The workflow expands these at runtime:

```yaml
registry_username: ${GHCR_USERNAME}      # References GHCR_USERNAME from env block
registry_password: ${GITHUB_TOKEN}       # References GITHUB_TOKEN from env block
registry_password: ${MY_CUSTOM_SECRET}   # References MY_CUSTOM_SECRET from env block
```

**Important:** Every secret referenced in your config file **must** be defined in the workflow's `env:` block.

### Schema validation

Config files are validated against [.github/schemas/container-config.schema.json](https://github.com/huntridge-labs/hardening-workflows/blob/main/.github/schemas/container-config.schema.json) before execution. The workflow will fail early if:
- Required fields are missing
- Field values are invalid (wrong type, invalid enum values)
- JSON/YAML syntax is malformed

### Usage examples

**Manual trigger:**

```yaml
# Trigger from GitHub UI or gh CLI
gh workflow run container-scan-from-config.yml \
  -f config_file=config/production-containers.yml
```

**Scheduled scanning:**

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2am
  workflow_dispatch:
    inputs:
      config_file:
        description: 'Container config file path'
        default: 'config/containers.yml'
```

**Multiple config files:**

Create separate workflows or use `workflow_dispatch` with different config files:

```bash
# Scan production containers
gh workflow run container-scan-from-config.yml -f config_file=config/prod.yml

# Scan development containers
gh workflow run container-scan-from-config.yml -f config_file=config/dev.yml
```

### Matrix execution

The workflow automatically generates a matrix combining each container with its specified scanners. For example, with 3 containers each using 2 scanners, you'll get 6 parallel scan jobs:

```
Container A × Trivy
Container A × Grype
Container B × Trivy
Container B × Syft
Container C × Grype
Container C × Syft
```

Each combination runs independently, allowing parallel execution and granular results.

### Updating the template

The workflow template includes a version comment that tracks updates:

```yaml
# Template Version: 1.0.0 - Check for updates at:
# https://github.com/huntridge-labs/hardening-workflows/blob/main/.github/workflows/container-scan-from-config.yml
ref: '2.8.1'
```

Dependabot will automatically update the `ref` value. Check the template URL periodically for new features or improvements to the workflow structure itself.
</details>

## More examples

Check `QUICK-START.md` for curated recipes and browse the `examples/` directory for ready-to-copy snippets, from nightly runs to matrix fan-outs.

## License
This project is licensed under the [GNU Affero General Public License v3](./LICENSE.md).
