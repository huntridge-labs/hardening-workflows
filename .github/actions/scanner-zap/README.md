# ZAP DAST Scanner Composite Action

Dynamic Application Security Testing (DAST) using [OWASP ZAP](https://www.zaproxy.org/).

## Overview

This composite action runs OWASP ZAP (Zed Attack Proxy) to scan running web applications for security vulnerabilities. This is an **MVP/Phase 1** implementation supporting URL-based baseline scanning.

**Current Features (Phase 1):**
- ✅ URL mode (target already running)
- ✅ Baseline scan
- ✅ SARIF output for GitHub Security

**Coming in Phase 2:**
- ⏳ Docker-run mode (start app in container)
- ⏳ Compose mode (multi-container apps)
- ⏳ Full/API scans
- ⏳ Multi-target support

## Usage

### Basic Example

```yaml
- name: Checkout code
  uses: actions/checkout@v6

# Start your application
- name: Start web application
  run: |
    docker-compose up -d
    sleep 10  # Wait for app to be ready

- name: Run ZAP Scanner
  uses: huntridge-labs/hardening-workflows/.github/actions/scanner-zap@feat/migrate-to-composite-actions
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    target_url: 'http://localhost:8080'
    fail_on_severity: 'high'
```

### Advanced Example

```yaml
- name: DAST scan with custom settings
  uses: huntridge-labs/hardening-workflows/.github/actions/scanner-zap@feat/migrate-to-composite-actions
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    target_url: 'https://staging.example.com'
    scan_name: 'api-gateway'
    enable_code_security: true
    post_pr_comment: true
    fail_on_severity: 'medium'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `target_url` | Target URL for baseline scan (must be already running) | **Yes** | - |
| `scan_name` | Name for scan artifacts | No | `zap-scan` |
| `post_pr_comment` | Post results as PR comment | No | `true` |
| `enable_code_security` | Upload SARIF to GitHub Security tab | No | `false` |
| `fail_on_severity` | Fail on severity: `none`, `low`, `medium`, `high` | No | `none` |

## Outputs

| Output | Description |
|--------|-------------|
| `high_count` | Number of high risk alerts |
| `medium_count` | Number of medium risk alerts |
| `low_count` | Number of low risk alerts |
| `info_count` | Number of informational alerts |
| `total_count` | Total number of alerts |

## Features

- ✅ OWASP ZAP baseline scanning
- ✅ SARIF output for GitHub Security
- ✅ JSON, HTML, and Markdown reports
- ✅ Configurable risk thresholds
- ✅ PR comments with findings
- ✅ Detailed vulnerability information

## Reports Generated

The action generates multiple report formats:
- `zap-report.sarif` - GitHub Security integration
- `zap-report.json` - Detailed JSON with findings
- `zap-report.html` - Human-readable HTML report
- `zap-report.md` - Markdown summary

All reports are uploaded as artifacts: `zap-reports-{scan_name}`

## Examples

### Scan Localhost Application

```yaml
jobs:
  zap-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Build and start app
        run: |
          docker build -t myapp .
          docker run -d -p 8080:8080 myapp
          sleep 5

      - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-zap@feat/migrate-to-composite-actions
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          target_url: 'http://localhost:8080'
```

### Scan Multiple Endpoints

Use a matrix strategy:

```yaml
jobs:
  zap-scan:
    strategy:
      matrix:
        target:
          - { url: 'http://localhost:8080', name: 'web' }
          - { url: 'http://localhost:3000', name: 'api' }
    steps:
      - uses: actions/checkout@v6

      # Start your services...

      - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-zap@feat/migrate-to-composite-actions
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          target_url: ${{ matrix.target.url }}
          scan_name: ${{ matrix.target.name }}
```

### Fail on Medium Risk

```yaml
- uses: huntridge-labs/hardening-workflows/.github/actions/scanner-zap@feat/migrate-to-composite-actions
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    target_url: 'http://localhost:8080'
    fail_on_severity: 'medium'  # Fails on MEDIUM and HIGH
```

## Understanding Risk Levels

ZAP reports four risk levels:
- **HIGH**: Critical vulnerabilities requiring immediate attention
- **MEDIUM**: Important issues that should be addressed
- **LOW**: Minor issues or security improvements
- **INFO**: Informational findings (not vulnerabilities)

## Important Prerequisites

### Application Must Be Running

ZAP scans running applications. Before using this action:

1. **Start your application:**
   ```yaml
   - name: Start application
     run: docker-compose up -d
   ```

2. **Wait for application to be ready:**
   ```yaml
   - name: Wait for app
     run: sleep 10
   ```

3. **Then run ZAP scan**

### Network Access

- For localhost: Use `http://localhost:PORT`
- For Docker containers: Use container networking or exposed ports
- For remote targets: Ensure network access from GitHub runners

## Baseline Scan Details

The baseline scan:
- ✅ Spiders the target (follows links)
- ✅ Passive scanning (safe, non-intrusive)
- ✅ Basic active scanning
- ❌ Does NOT perform full penetration testing
- ❌ Does NOT test authenticated areas (Phase 2)

For more comprehensive scanning, see upcoming Phase 2 features.

## Requirements

- Repository must be checked out before running this action
- `GITHUB_TOKEN` environment variable (automatically available)
- Target application must be running and accessible
- Network connectivity to target URL

## Related Documentation

- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [ZAP Baseline Scan](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [Complete Example Workflow](../../examples/composite-actions-example.yml)
- [ZAP Podinfo Example](../../examples/scanner-zap-podinfo.yml)

## Troubleshooting

### Connection Refused

If ZAP can't connect to your application:
- Verify the application is running: `curl http://localhost:PORT`
- Check port mapping if using Docker
- Ensure sufficient startup time before scanning
- Verify firewall/network settings

### Scan Takes Too Long

Baseline scans can take 5-15 minutes. To optimize:
- Limit the scope of URLs to scan
- Use authentication to skip login pages (Phase 2)
- Consider time limits in workflow

### No Vulnerabilities Found

If ZAP finds nothing:
- Verify the target URL is accessible
- Check that links are being followed (review logs)
- Consider that your app might be secure!

### False Positives

If ZAP reports false positives:
- Review findings carefully - not all alerts are vulnerabilities
- Use ZAP configuration files to tune scanning (Phase 2)
- Document accepted risks

## Phase 2 Roadmap

Coming features:
- **Docker-run mode**: Start app from Dockerfile for scanning
- **Compose mode**: Multi-container app support
- **Authentication**: Scan authenticated areas
- **Full/API scans**: More comprehensive testing
- **Custom configurations**: ZAP config file support
- **Multi-target**: Scan multiple URLs in one job

## Support

- [Report Issues](https://github.com/huntridge-labs/hardening-workflows/issues)
- [OWASP ZAP Community](https://groups.google.com/group/zaproxy-users)
- [View Changelog](../../CHANGELOG.md)
