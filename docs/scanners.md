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
