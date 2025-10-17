# Security Hardening Workflows

One reusable GitHub Actions workflow, many scanners. Pick the components you need, and we ship a consolidated report plus an optional PR comment.

## Reusable pipeline

**Workflow:** `.github/workflows/reusable-security-hardening.yml`

**Available scanners:** `codeql`, `opengrep`, `bandit`, `gitleaks`, `container`, `infrastructure`, `lint`

### Quick start

```yaml
# .github/workflows/security.yml
name: security
on: [push, pull_request]

jobs:
  hardening:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.1.1
    with:
      scanners: all
      python_version: '3.12'
      post_pr_comment: true
    permissions:
      contents: read
      security-events: write
      pull-requests: write
    secrets:
      AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }} # optional
```

### Example selector patterns

- **Full coverage:** `scanners: all`
- **Single scanner:** `scanners: opengrep`
- **Focused mix:** `scanners: container,infrastructure,gitleaks`

### Inputs at a glance

- `scanners` *(string)* — comma-separated list or `all`
- `python_version` *(string, default `3.12`)* — runtime for Python-based tools
- `post_pr_comment` *(boolean, default `true`)* — leave a summary on PRs
- `iac_path`, `aws_region`, `enable_code_security`, `codeql_languages` — optional knobs for specific scanners

### Outputs

- Artifact: `security-hardening-report-<job-id>.md`
- Optional PR comment containing the same summary

### Permissions & secrets

Minimum permissions shown in the example. Omit `AWS_ACCOUNT_ID` when you don’t run AWS checks—the workflow will skip that portion automatically.

## Linting workflow

Run consistent code quality checks with `.github/workflows/linting.yml`:

```yaml
jobs:
  lint:
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@main
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
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@main

  security:
    needs: linting
    if: always()
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@2.1.1
    with:
      scanners: all
```

## Results location

- GitHub Security tab for SARIF uploads (CodeQL/OpenGrep/Bandit)
- Workflow artifacts for each scanner plus combined Markdown report
- Optional PR comment summarizing the run

## More examples

Check `QUICK-START.md` for curated recipes and browse the `examples/` directory for ready-to-copy snippets, from nightly runs to matrix fan-outs.

## License
This project is licensed under the [GNU Affero General Public License v3](./LICENSE.md).
