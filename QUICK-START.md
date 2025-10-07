# Quick start

Kick off the reusable workflow with these minimal snippets.

## Fast SAST (dev branches)

```yaml
name: security-dev
on: [push]

jobs:
  sast:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
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
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
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
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
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
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
    with:
      scanners: all
      post_pr_comment: false
```

More examples in the `examples/` directory. See `README.md` for the complete scanner reference.
