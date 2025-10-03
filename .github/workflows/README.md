# Security Hardening Workflows

This directory contains comprehensive security workflows implementing multiple layers of security scanning and analysis.

## Overview

The security hardening pipeline consists of two main reusable workflows:

1. **Code Quality & Linting** - `linting.yml`
2. **Security Hardening** - `reusable-security-hardening.yml`

These workflows are designed to be called from other repositories, providing enterprise-grade security scanning with minimal configuration.

## Workflows Description

### 1. Linting Workflow (`linting.yml`)

Performs code quality checks and static analysis for style and best practices.

**Tools Used:**
- **Ruff**: Fast Python linter and formatter
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting
- **markdownlint**: Markdown style checking
- **yamllint**: YAML validation

**Features:**
- Language-specific linting with industry-standard tools
- Automatic code formatting validation
- PR comments with linting results
- Artifact generation for detailed reports

### 2. Security Hardening Workflow (`reusable-security-hardening.yml`)

Orchestrates comprehensive security scanning across your entire project.

**Security Scanners:**
- **CodeQL**: GitHub's semantic code analysis engine (SAST)
- **Semgrep**: Fast pattern-based security scanning (SAST)
- **Bandit**: Python-specific security linter (SAST)
- **Gitleaks**: Secrets detection in code and history
- **Trivy**: Container and infrastructure vulnerability scanning
- **Checkov**: Infrastructure as Code (IaC) security scanner
- **Terrascan**: Multi-cloud IaC security analysis

**Features:**
- **Granular Scanner Control**: Enable/disable individual scanners
- **Flexible Execution**: Full scan or selective scanning
- **Optional Linting**: Include code quality checks with `enable_linting: true`
- **Multi-language Support**: Python, JavaScript, Go, and more
- **Container Scanning**: Docker image vulnerability analysis
- **IaC Analysis**: Terraform, CloudFormation, Kubernetes manifests
- **SARIF Integration**: Results appear in GitHub Security tab
- **PR Comments**: Automatic security summaries on pull requests

## Usage Patterns

### Option 1: Separate Workflows (Recommended)

**Best for**: Maximum flexibility, parallel execution, clear separation of concerns

```yaml
name: CI Pipeline
on: [push, pull_request]

jobs:
  linting:
    name: Code Quality
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@v2
    permissions:
      contents: read
      pull-requests: write
      checks: write

  security:
    name: Security Scanning
    needs: linting  # Optional: run after linting
    if: always()    # Run even if linting fails
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@v2
    with:
      scan_type: 'full'
      enable_codeql: true
      enable_semgrep: true
      enable_bandit: true
      enable_gitleaks: true
    permissions:
      contents: read
      security-events: write
      pull-requests: write
```

### Option 2: Combined with enable_linting Flag

**Best for**: Simplicity, single job definition, straightforward pipelines

```yaml
name: Security Pipeline
on: [push, pull_request]

jobs:
  security:
    name: Security & Quality
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@v2
    with:
      enable_linting: true  # ✅ Include linting in this workflow
      scan_type: 'full'
      enable_codeql: true
      enable_semgrep: true
      enable_bandit: true
    permissions:
      contents: read
      security-events: write
      pull-requests: write
      checks: write
```

### Option 3: Security Only (No Linting)

**Best for**: Projects with existing linting, fast security-only scans, targeted scanning

```yaml
name: Security Only
on: [push, pull_request]

jobs:
  security:
    name: Security Scanning
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@v2
    with:
      enable_linting: false  # Default: no linting
      scan_type: 'full'
      enable_codeql: true
      enable_gitleaks: true
    permissions:
      contents: read
      security-events: write
      pull-requests: write
```

### Granular Scanner Control

Enable only the scanners you need:

```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@v2
    with:
      # Choose your scanners
      enable_codeql: true      # Deep semantic analysis
      enable_semgrep: false    # Skip pattern-based scanning
      enable_bandit: true      # Python security checks
      enable_gitleaks: true    # Secrets detection

      # Container/IaC scanning (triggered by file presence)
      # These run automatically if relevant files exist:
      # - Trivy: Scans Dockerfiles and IaC
      # - Checkov: Scans Terraform, CloudFormation
      # - Terrascan: Multi-cloud IaC analysis
```

## Setup Instructions

### Prerequisites

1. **GitHub Secrets Configuration (Optional)**
   ```
   SLACK_WEBHOOK_URL (optional) - For Slack notifications
   ```

2. **AWS IAM Role (Optional - Only for AWS Security Analysis)**
   - The workflows use OIDC for AWS authentication
   - **Required only if you want AWS security configuration analysis**
   - If not configured, the pipeline will continue without AWS analysis
   - Ensure the `github-oidc-role` has necessary permissions:
     - ECR read access for image scanning
     - Basic AWS resource read permissions for security assessment
   - Update `AWS_ACCOUNT_ID` in the workflow if different from default

3. **No AWS? No Problem!**
   - The hardening pipeline works perfectly without AWS components
   - All security scanning tools (SAST, container scanning, infrastructure analysis) work with any codebase
   - AWS analysis is only triggered for infrastructure scans on the main branch

### Configuration

1. **CodeQL Configuration**
   - Custom configuration in `.github/codeql/codeql-config.yml`
   - Excludes test files and focuses on security queries

2. **Workflow Customization**
   - Update branch names in workflow triggers if needed
   - Modify Slack channel in notification steps
   - Adjust scan schedules as required

## Security Artifacts

The workflows generate comprehensive security reports:

### SARIF Files
- Uploaded to GitHub Security tab for centralized vulnerability management
- Compatible with GitHub Advanced Security features

### Artifact Reports
- **SAST Reports**: Bandit, Safety, Checkov, Hadolint, Gitleaks results
- **Container Reports**: Trivy, Grype, AWS ECR scan results
- **Infrastructure Reports**: Trivy, Terrascan, Checkov results
- **License Reports**: pip-licenses compliance reports
- **Security Summary**: Comprehensive overview report

**Note**: All reports generated by open-source tools only

## Input Parameters

### Security Hardening Workflow Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_linting` | boolean | `false` | Include code quality checks in security workflow |
| `scan_type` | string | `'full'` | Type of scan: `full`, `quick`, `targeted` |
| `enable_codeql` | boolean | `true` | Enable CodeQL semantic analysis |
| `enable_semgrep` | boolean | `true` | Enable Semgrep pattern scanning |
| `enable_bandit` | boolean | `true` | Enable Bandit Python security checks |
| `enable_gitleaks` | boolean | `true` | Enable Gitleaks secrets detection |
| `python_version` | string | `'3.11'` | Python version for security tools |
| `node_version` | string | `'20'` | Node.js version for JavaScript scanning |

### Linting Workflow Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `python_version` | string | `'3.11'` | Python version for linting tools |
| `node_version` | string | `'20'` | Node.js version for JavaScript linting |

## Viewing Results

1. **GitHub Security Tab**: View SARIF results for all security findings
2. **Workflow Artifacts**: Download detailed reports from workflow runs
3. **PR Comments**: Automatic security and linting summaries on pull requests
4. **Actions Summary**: View scan results in the workflow run summary

## Security Coverage

### SAST (Static Application Security Testing)

| Tool | Purpose | Languages |
|------|---------|-----------|
| **CodeQL** | Deep semantic code analysis | Python, JavaScript, TypeScript, Go, Java, C++ |
| **Semgrep** | Fast pattern-based security scanning | 30+ languages |
| **Bandit** | Python-specific security issues | Python |

### Secrets Detection

| Tool | Purpose | Coverage |
|------|---------|----------|
| **Gitleaks** | Find hardcoded secrets | Git history, current code |

### Container Security

| Tool | Purpose | Formats |
|------|---------|---------|
| **Trivy** | Container vulnerability scanning | Docker, OCI images |

### Infrastructure as Code (IaC)

| Tool | Purpose | Platforms |
|------|---------|-----------|
| **Checkov** | IaC security scanning | Terraform, CloudFormation, Kubernetes, Docker |
| **Terrascan** | Multi-cloud IaC analysis | Terraform, Kubernetes, Helm, Dockerfiles |
| **Trivy** | Config file security | Terraform, CloudFormation, Kubernetes |

### Compliance Features

- **SARIF Support**: Industry-standard security report format integrated with GitHub Security
- **Audit Trail**: All security scans logged and tracked in workflow runs
- **Granular Control**: Enable/disable individual scanners based on project needs
- **Multi-language**: Supports Python, JavaScript, TypeScript, Go, and more
- **PR Integration**: Automatic security summaries on pull requests

## Troubleshooting

### Common Issues

1. **CodeQL Analysis Timeout**
   - Increase timeout in workflow if needed
   - Exclude unnecessary paths in CodeQL config

2. **Container Build Failures**
   - Check Dockerfile syntax and dependencies
   - Verify base image availability

3. **AWS Credentials Issues**
   - **"Credentials could not be loaded"** - This is expected if you don't have AWS resources
   - The pipeline will continue and generate a report explaining the situation
   - To enable AWS analysis:
     - Set up AWS OIDC role for your repository
     - Update `AWS_ACCOUNT_ID` in the workflow environment variables
     - Ensure the role has read permissions for security analysis
   - **"Missing id-token permission"** - Already fixed in this version

4. **Pull Request Comment Issues**
   - **"Resource not accessible by integration"** - This is expected when:
     - Running from a forked repository (GitHub security restriction)
     - Missing `pull-requests: write` permission (already fixed)
     - Repository settings restrict PR comments
   - The pipeline continues normally and reports are available in artifacts
   - All security scanning results are preserved regardless of commenting issues

5. **Not All Pipelines Need AWS**
   - Many security hardening workflows don't require AWS components
   - SAST, container scanning, and infrastructure analysis work without AWS
   - AWS analysis only runs on main branch for infrastructure scans

### Debug Steps

1. Enable workflow debug logging:
   ```
   ACTIONS_RUNNER_DEBUG: true
   ACTIONS_STEP_DEBUG: true
   ```

2. Review workflow artifacts for detailed logs
3. Check individual tool documentation for specific issues

## Continuous Improvement

### Metrics to Track

- Number of vulnerabilities by severity
- Time to remediation
- Scan coverage and effectiveness
- False positive rates

### Regular Maintenance

- Update security tool versions quarterly
- Review and tune security policies
- Update ignore/allowlist configurations
- Training on new security features

## Contributing

When adding new security tools or configurations:

1. Test changes in feature branches
2. Update documentation
3. Consider impact on scan performance
4. Ensure SARIF compatibility for GitHub integration

## Resources

- [GitHub Advanced Security Documentation](https://docs.github.com/en/code-security)
- [SARIF Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
