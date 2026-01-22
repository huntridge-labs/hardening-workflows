# Get Job ID Composite Action

Resolve the current GitHub Actions job ID for consistent artifact naming.

## Overview

This action looks up the current job in the workflow run and returns a stable job identifier. If the job cannot be resolved, it falls back to a run-based identifier with a provided suffix.

## Usage

```yaml
- name: Resolve job ID
  id: job
  uses: huntridge-labs/hardening-workflows/.github/actions/get-job-id@feat/migrate-to-composite-actions
  with:
    job-name-pattern: 'YAML Linting'
    fallback-suffix: 'yaml'

- name: Use job ID
  run: echo "Job ID: ${{ steps.job.outputs.job-id }}"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `job-name-pattern` | Pattern to match in the job name | Yes | - |
| `fallback-suffix` | Suffix for fallback naming | Yes | - |

## Outputs

| Output | Description |
|--------|-------------|
| `job-id` | The job ID or fallback identifier |

## Requirements

- `GITHUB_TOKEN` is provided automatically to `actions/github-script`

## Support

- [Report Issues](https://github.com/huntridge-labs/hardening-workflows/issues)
- [Contributing Guide](../../CONTRIBUTING.md)
