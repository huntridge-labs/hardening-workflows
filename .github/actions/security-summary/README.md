# Security Summary Action

Automatically aggregates and displays all security scan results in a unified, formatted report.

## Features

- **Zero Configuration** - Automatically discovers all scanner summaries
- **Works with Any Scanners** - Compatible with all hardening-workflows scanner actions
- **Flexible** - Works with 1 scanner or 10+ scanners
- **Metadata Rich** - Shows workflow run, branch, and commit information
- **Graceful Degradation** - Helpful messages when no summaries are found

## Usage

### Basic Usage

Add this to the end of your security scanning workflow:

```yaml
security-summary:
  name: Security Scan Summary
  runs-on: ubuntu-latest
  needs: [bandit-scan, gitleaks-scan, trivy-iac-scan, clamav-scan]
  if: always()

  steps:
    - uses: huntridge-labs/hardening-workflows/.github/actions/security-summary@main
```

That's it! The action will automatically find and combine all scanner summaries.

### With Custom Settings

```yaml
- uses: huntridge-labs/hardening-workflows/.github/actions/security-summary@main
  with:
    title: '🛡️ Custom Security Report'
    show_metadata: true
    show_stats: true
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `summary_pattern` | Artifact pattern to match scanner summaries | No | `scanner-summary-*` |
| `title` | Title for the summary report | No | `🔒 Security Scan Summary` |
| `show_metadata` | Show workflow metadata (run, branch, commit) | No | `true` |
| `show_stats` | Show scanner execution statistics | No | `true` |

## Compatible Scanners

This action works with all hardening-workflows scanner composite actions:

- scanner-bandit (Python security)
- scanner-gitleaks (Secrets detection)
- scanner-trivy-iac (IaC security)
- scanner-clamav (Malware detection)
- scanner-zap (DAST)
- scanner-container (Container security)

## Example Output

The action generates a formatted GitHub Step Summary showing:

1. **Header** - Title and metadata
2. **Statistics** - Number of scanners executed
3. **Scanner Results** - Individual collapsible sections for each scanner
4. **Footer** - Link to hardening-workflows

## Complete Workflow Example

```yaml
name: Security Scanning

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  security-events: write

jobs:
  bandit-scan:
    runs-on: ubuntu-latest
    continue-on-error: true
    steps:
      - uses: actions/checkout@v6
      - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-bandit@main

  gitleaks-scan:
    runs-on: ubuntu-latest
    continue-on-error: true
    steps:
      - uses: actions/checkout@v6
      - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-gitleaks@main

  security-summary:
    runs-on: ubuntu-latest
    needs: [bandit-scan, gitleaks-scan]
    if: always()
    steps:
      - uses: huntridge-labs/hardening-workflows/.github/actions/scanner-summary@main
```

## Tips

- **Use `continue-on-error: true`** on scanner jobs so they don't block the summary
- **Use `if: always()`** on the summary job so it runs even if scanners fail
- **Add all scanner jobs to `needs`** so the summary waits for them
- **Keep the default pattern** unless you have custom artifact names

## Troubleshooting

### No summaries found

If you see "No scanner summaries found":
1. Check that scanner jobs are uploading summary artifacts
2. Verify scanner jobs have `scanner-summary-*` artifact names
3. Ensure summary job has `needs` listing all scanner jobs
4. Check scanner job logs for errors

### Missing scanners in summary

If some scanners don't appear:
1. Verify the scanner job completed (check `needs` list)
2. Check if the scanner uploaded its summary artifact
3. Ensure artifact names match the `summary_pattern` input
