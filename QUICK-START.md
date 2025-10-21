# Quick start

Kick off the reusable workflow with these minimal snippets.

## Fast SAST (dev branches)

```yaml
name: security-dev
on: [push]

jobs:
  sast:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.4.0
    with:
      scanners: codeql
    permissions:
      contents: read
      security-events: write
```

## Full coverage on PRs

```yaml
name: security-pr
on: [pull_request]

jobs:
  hardening:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.4.0
    with:
      scanners: all
      post_pr_comment: true
    permissions:
      contents: read
      security-events: write
      pull-requests: write
```

## Targeted mix

```yaml
name: security-mix
on: [push]

jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.4.0
    with:
      scanners: container,infrastructure,gitleaks
      aws_region: us-west-2
    secrets:
      AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
```

## Nightly deep scan

```yaml
name: security-nightly
on:
  schedule:
    - cron: '0 4 * * *'

jobs:
  nightly:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.4.0
    with:
      scanners: all
      post_pr_comment: false
```

## Individual scanner workflows

Use standalone scanners for more granular control:

### Infrastructure scanning

```yaml
name: iac-security
on: [pull_request]

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
```

### Container scanning

```yaml
name: container-security
on:
  push:
    branches: [main]

jobs:
  scan-image:
    uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-trivy-container.yml@main
    with:
      image_ref: 'myapp:${{ github.sha }}'
      enable_code_security: true
```

More examples in the `examples/` directory. See `README.md` for the complete scanner reference.
