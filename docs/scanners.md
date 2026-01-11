<div align=center>

# Scanner Configuration Reference

Complete configuration reference for all available security scanners.

</div>

## Table of Contents

- [SAST Scanners](#sast-scanners)
  - [CodeQL](#codeql)
  - [Gitleaks](#gitleaks)
  - [Bandit](#bandit)
  - [OpenGrep (Semgrep)](#opengrep-semgrep)
- [Container Scanners](#container-scanners)
  - [Trivy Container](#trivy-container)
  - [Grype](#grype)
  - [Syft (SBOM)](#syft-sbom)
- [Infrastructure Scanners](#infrastructure-scanners)
  - [Trivy IaC](#trivy-iac)
  - [Checkov](#checkov)
- [Malware Scanner](#malware-scanner)
  - [ClamAV](#clamav)
- [DAST Scanners](#dast-scanners)
  - [ZAP](#zap)

## SAST Scanners

### CodeQL

GitHub's semantic code analysis engine for finding security vulnerabilities and coding errors.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `codeql_languages` | Comma-separated list of languages | `python,javascript` | No |
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `true` | No |

**Supported languages:** `python`, `javascript`, `typescript`, `java`, `csharp`, `cpp`, `go`, `ruby`

**Example:**

```yaml
with:
  scanners: codeql
  codeql_languages: 'python,javascript,go'
  enable_code_security: true
```

### Gitleaks

Scans git history and code for hardcoded secrets, API keys, passwords, and tokens.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `gitleaks_enable_comments` | Enable inline PR comments | `true` | No |
| `gitleaks_notify_user_list` | Users to notify (e.g., `@user1,@user2`) | `''` | No |
| `gitleaks_enable_summary` | Enable job summary | `true` | No |
| `gitleaks_enable_upload_artifact` | Upload SARIF artifact | `true` | No |
| `gitleaks_config` | Path to custom config file | `''` | No |
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `fail_on_severity` | Fail on any secret detection | `none` | No |

**Required secrets:**

| Secret | Description | Required |
|--------|-------------|----------|
| `GITLEAKS_LICENSE` | License key from [gitleaks.io](https://gitleaks.io) | Yes (for organizations) |

**Scan behavior by event type:**
- `pull_request`: Scans all changes in the PR
- `push`: Scans only new commits
- `workflow_dispatch`/`schedule`: Full repository history scan

**Example:**

```yaml
with:
  scanners: gitleaks
  gitleaks_enable_comments: true
  gitleaks_notify_user_list: '@security-team'
  fail_on_severity: critical
secrets:
  GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

### Bandit

Python security linter for finding common security issues using static analysis.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `true` | No |
| `fail_on_severity` | Fail on any finding | `none` | No |

**Severity levels:** LOW, MEDIUM, HIGH

**Example:**

```yaml
with:
  scanners: bandit
  enable_code_security: true
  fail_on_severity: high
```

### OpenGrep (Semgrep)

Fast, customizable static analysis with extensive rule sets for multiple languages.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `true` | No |
| `fail_on_severity` | Severity threshold | `none` | No |

**Example:**

```yaml
with:
  scanners: opengrep
  enable_code_security: true
  fail_on_severity: medium
```

## Container Scanners

### Trivy Container

Comprehensive vulnerability scanner for container images and filesystems.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `image_ref` | Container image to scan | - | Yes |
| `registry_username` | Username for private registry authentication | `''` | No |
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `false` | No |
| `fail_on_severity` | Severity threshold | `none` | No |

**Required secrets (for private registries):**

| Secret | Description | Required |
|--------|-------------|----------|
| `registry_password` | Password/token for registry authentication | No |

**Example:**

```yaml
# Public image
with:
  scanners: trivy-container
  image_ref: 'nginx:latest'
  enable_code_security: true
  fail_on_severity: critical

# Private registry
with:
  scanners: trivy-container
  image_ref: 'ghcr.io/myorg/myapp:latest'
  registry_username: ${{ github.actor }}
  enable_code_security: true
  fail_on_severity: critical
secrets:
  registry_password: ${{ secrets.GITHUB_TOKEN }}
```

### Grype

Fast, accurate vulnerability scanner with excellent detection rates.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `image_ref` | Container image to scan | - | Yes |
| `registry_username` | Username for private registry authentication | `''` | No |
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `false` | No |
| `fail_on_severity` | Severity threshold | `none` | No |

**Required secrets (for private registries):**

| Secret | Description | Required |
|--------|-------------|----------|
| `registry_password` | Password/token for registry authentication | No |

**Example:**

```yaml
# Public image
with:
  scanners: grype
  image_ref: 'nginx:latest'
  fail_on_severity: high

# Private registry
with:
  scanners: grype
  image_ref: 'ghcr.io/myorg/myapp:latest'
  registry_username: ${{ github.actor }}
  fail_on_severity: high
secrets:
  registry_password: ${{ secrets.GITHUB_TOKEN }}
```

### Syft (SBOM)

Generates detailed Software Bill of Materials (SBOM) for images and filesystems.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `scan-path` | Directory or file path to scan | `.` | No |
| `scan-image` | Container image to scan | - | No |
| `registry_username` | Username for private registry authentication | `''` | No |
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |

**Required secrets (for private registries):**

| Secret | Description | Required |
|--------|-------------|----------|
| `registry_password` | Password/token for registry authentication | No |

**Example:**

```yaml
# Scan filesystem
with:
  scanners: sbom
  scan-path: 'dist/'

# Scan public container image
with:
  scanners: sbom
  scan-image: 'nginx:latest'

# Scan private container image
with:
  scanners: sbom
  scan-image: 'ghcr.io/myorg/myapp:latest'
  registry_username: ${{ github.actor }}
secrets:
  registry_password: ${{ secrets.GITHUB_TOKEN }}
```

## Infrastructure Scanners

### Trivy IaC

Scans Infrastructure as Code files for misconfigurations and security issues.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `iac_path` | Path to IaC directory | `infrastructure` | No |
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `false` | No |
| `fail_on_severity` | Severity threshold | `none` | No |

**Supported frameworks:** Terraform, CloudFormation, Kubernetes, Dockerfile

**Example:**

```yaml
with:
  scanners: trivy-iac
  iac_path: 'terraform/'
  enable_code_security: true
  fail_on_severity: high
```

### Checkov

Policy as Code scanner for cloud infrastructure configurations.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `iac_path` | Path to IaC directory | `infrastructure` | No |
| `framework` | IaC framework | `terraform` | No |
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `false` | No |
| `fail_on_severity` | Fail on any check failure | `none` | No |

**Example:**

```yaml
with:
  scanners: checkov
  iac_path: 'infrastructure/'
  framework: terraform
  enable_code_security: true
```

## Malware Scanner

### ClamAV

Open-source antivirus engine for detecting trojans, viruses, and malware.

**Configuration:**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `clamav_scan_path` | Path to scan | `.` | No |
| `enable_code_security` | Upload to GitHub Security tab | `false` | No |
| `post_pr_comment` | Post findings as PR comments | `true` | No |
| `fail_on_severity` | Fail if malware detected | `none` | No |

**Example:**

```yaml
# Scan entire repository
with:
  scanners: clamav

# Scan specific directory
with:
  scanners: clamav
  clamav_scan_path: 'uploads/'
  fail_on_severity: critical
```

## Common Configuration Patterns

### Enable GitHub Security Tab

Upload SARIF results for all scanners:

```yaml
with:
  scanners: all
  enable_code_security: true
```

### Disable PR Comments

Useful for scheduled scans:

```yaml
with:
  scanners: all
  post_pr_comment: false
```

### Scanner Selection Patterns

- Full coverage: `scanners: all`
- SAST only: `scanners: codeql,opengrep,bandit,gitleaks`
- Infrastructure only: `scanners: trivy-iac,checkov`
- Container only: `scanners: trivy-container,grype,sbom`
- Focused mix: `scanners: container,infrastructure,gitleaks`

## DAST Scanners

### ZAP

ZAP provides Dynamic Application Security Testing (DAST) for running web applications and APIs.

This integration supports:
- **URL-only**: scan endpoints that are already running
- **Single container**: start one container on the GitHub runner and scan its exposed port(s)
- **Docker Compose**: start a multi-container stack and scan one or more published endpoints

**Configuration (via the reusable workflow):**

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `scanners` | Include `zap` (opt-in; not included in `all`) | - | Yes (to run ZAP) |
| `zap_config_file` | Path to a ZAP config file (YAML/JSON). When set, it drives targets/matrixing and overrides other `zap_*` inputs. | `''` | No |
| `zap_scan_mode` | `url`, `docker-run`, or `compose` | `url` | No |
| `zap_target_urls` | Comma-separated list of URLs to scan | `''` | Yes (unless `docker-run` derives targets) |
| `zap_healthcheck_url` | Optional URL to wait on before scanning | `''` | No |
| `zap_scan_type` | `baseline`, `full`, or `api` | `baseline` | No |
| `zap_api_spec` | URL or file path to OpenAPI/Swagger spec | `''` | Yes (when `zap_scan_type=api`) |
| `zap_max_duration_minutes` | Max minutes for ZAP per scan | `10` | No |
| `zap_app_image_ref` | Image to run (when `zap_scan_mode=docker-run`) | `''` | Yes (when `docker-run`) |
| `zap_app_ports` | Port mappings (when `zap_scan_mode=docker-run`) | `8080:8080` | No |
| `zap_compose_file` | Compose file path (when `zap_scan_mode=compose`) | `docker-compose.yml` | Yes (when `compose`) |
| `allow_failure` + `severity_threshold` | Controls failing the workflow on ZAP findings | `true` + `high` | No |

**Recommended: config-file driven ZAP**

Use a config file to avoid passing many inputs and to define multiple targets for matrix scanning.

Example config file (YAML or JSON), e.g. `.zap/zap.yml`:

```yaml
zap:
  scan_mode: url
  # targets can be a list or a comma-separated string
  target_urls:
    - http://127.0.0.1:8080
    - http://127.0.0.1:3000
  healthcheck_url: http://127.0.0.1:8080/health
  scan_type: baseline
  zap_max_duration_minutes: 10
  # Optional: pass-through to official zaproxy/action-* rules_file_name
  rules_file_name: .zap/rules.tsv
  # Optional: additional pass-through to ZAP scripts
  cmd_options: "-a"
```

For `scan_mode: docker-run`, the config can build a local Dockerfile from the caller repo (no assumptions; you must point to it):

```yaml
zap:
  scan_mode: docker-run
  # Either set app_image_ref to a prebuilt image, OR set these two to build locally
  app_build_context: .
  app_dockerfile: ./Dockerfile
  # Optional; defaults to local-dast-app:${GITHUB_SHA}
  app_image_tag: my-app-dast:${GITHUB_SHA}
  app_ports: "8080:8080"
  target_urls:
    - http://127.0.0.1:8080
  scan_type: baseline
```

And call the workflow like:

```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.10.0
    with:
      scanners: zap
      zap_config_file: .zap/zap.yml
      allow_failure: false
      severity_threshold: medium
```

**Example: URL-only (caller starts containers/services)**

```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.10.0
    with:
      scanners: zap
      zap_scan_mode: url
      zap_target_urls: http://127.0.0.1:8080
      allow_failure: false
      severity_threshold: medium
```

**Example: Single container (run and scan)**

```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.10.0
    with:
      scanners: zap
      zap_scan_mode: docker-run
      zap_app_image_ref: ghcr.io/myorg/myapp:latest
      zap_app_ports: 8080:8080
      allow_failure: false
      severity_threshold: high
```

**Example: Multi-container via docker compose**

```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.10.0
    with:
      scanners: zap
      zap_scan_mode: compose
      zap_compose_file: docker-compose.yml
      zap_target_urls: http://127.0.0.1:8080,http://127.0.0.1:3000
      zap_healthcheck_url: http://127.0.0.1:8080/health
      allow_failure: false
      severity_threshold: medium
```
