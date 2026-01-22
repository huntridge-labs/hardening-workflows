# Checkov Scanner Composite Action

Run Checkov infrastructure-as-code security scanning and generate reports.

## Overview

This composite action analyzes IaC for security misconfigurations using Checkov. It supports multiple frameworks including Terraform, CloudFormation, Kubernetes, and more. Results integrate with the security summary aggregator.

## Usage

### Basic Example

```yaml
- name: Checkout code
  uses: actions/checkout@v6

- name: Run Checkov
  uses: huntridge-labs/hardening-workflows/.github/actions/scanner-checkov@feat/migrate-to-composite-actions
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    iac_path: 'infrastructure'
    framework: 'terraform'
    fail_on_severity: 'high'
```

### Multiple Frameworks

```yaml
strategy:
  matrix:
    config:
      - path: 'terraform'
        framework: 'terraform'
      - path: 'kubernetes'
        framework: 'kubernetes'
steps:
  - uses: actions/checkout@v6
  - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-checkov@feat/migrate-to-composite-actions
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    with:
      iac_path: ${{ matrix.config.path }}
      framework: ${{ matrix.config.framework }}
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `iac_path` | Relative path to the IaC directory to scan | No | `infrastructure` |
| `framework` | IaC framework (terraform, cloudformation, kubernetes, etc.) | No | `terraform` |
| `enable_code_security` | Upload SARIF to GitHub Security tab | No | `false` |
| `post_pr_comment` | Post results as PR comment | No | `true` |
| `fail_on_severity` | Fail at or above severity: none, low, medium, high, critical. Note: Checkov doesn't natively support severity filtering; any value other than "none" will fail on any failed check. | No | `none` |

## Outputs

| Output | Description |
|--------|-------------|
| `critical_count` | Number of critical severity findings |
| `high_count` | Number of high severity findings |
| `medium_count` | Number of medium severity findings |
| `low_count` | Number of low severity findings |
| `total_count` | Total number of failed checks |
| `passed_count` | Number of passed checks |
| `has_iac` | Whether IaC directory was found and scanned |

## Artifacts

- `checkov-reports`: SARIF, JSON, and text reports
- `scanner-summary-checkov`: summary artifact used by security-summary

## Supported Frameworks

Checkov supports:
- Terraform
- CloudFormation
- Kubernetes
- Helm
- Serverless
- ARM Templates
- Dockerfile
- Docker Compose
- And many more...

## Requirements

- Repository must be checked out before running this action
- `GITHUB_TOKEN` environment variable
- IaC directory must exist (action will skip if not found)

## Example with Security Summary

```yaml
jobs:
  checkov-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-checkov@feat/migrate-to-composite-actions
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          iac_path: 'terraform'
          fail_on_severity: 'high'

  security-summary:
    runs-on: ubuntu-latest
    needs: [checkov-scan]
    if: always()
    steps:
      - uses: huntridge-labs/hardening-workflows/.github/actions/security-summary@feat/migrate-to-composite-actions
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Notes

- Checkov does not natively support severity-based filtering like other scanners
- Setting `fail_on_severity` to anything other than "none" will cause the job to fail if any check fails
- The action parses severity information from Checkov's JSON output when available
- Results are organized by severity in the summary for easier review

## Support

- [Report Issues](https://github.com/huntridge-labs/hardening-workflows/issues)
- [Contributing Guide](../../../CONTRIBUTING.md)
