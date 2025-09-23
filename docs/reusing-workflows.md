# 🛡️ Reusing the Security Hardening Pipeline

This repository provides several ways to reuse the security hardening pipeline in other projects without copy-pasting code.

## 📋 Table of Contents

1. [Reusable Workflow (Recommended)](#reusable-workflow-recommended)
2. [Composite Action](#composite-action)
3. [Workflow Templates](#workflow-templates)
4. [Configuration Options](#configuration-options)
5. [Examples](#examples)

## 🔄 Reusable Workflow (Recommended)

The cleanest approach is to use the reusable workflow. This allows you to call the entire security pipeline from another repository.

### ✅ Advantages
- ✨ Single source of truth - updates automatically propagate
- 🔧 Centralized maintenance and improvements
- 🎛️ Configurable inputs for different project needs
- 📊 Consistent security standards across all projects
- 🚀 Easy to upgrade - just change the version tag

### 📝 Usage

Create a workflow file in your target repository (e.g., `.github/workflows/security.yml`):

```yaml
name: Security Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      scan_type:
        description: 'Type of security scan'
        required: true
        default: 'full'
        type: choice
        options: [full, sast-only, container-only, infrastructure-only]

jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@0.1.0
    with:
      scan_type: ${{ github.event.inputs.scan_type || 'full' }}
      python_version: '3.11'
      aws_region: 'us-west-2'
      post_pr_comment: true
    secrets:
      AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
    permissions:
      contents: read
      security-events: write
      actions: read
      pull-requests: write
      checks: write
      id-token: write
```

### 🎛️ Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scan_type` | string | `'full'` | Type of scan: `full`, `sast-only`, `container-only`, `infrastructure-only` |
| `python_version` | string | `'3.12'` | Python version to use for scans |
| `aws_region` | string | `'us-east-1'` | AWS region for infrastructure scans |
| `post_pr_comment` | boolean | `true` | Whether to post security summary as PR comment |
| `codeql_languages` | string | `'python,javascript'` | Comma-separated list of languages for CodeQL analysis (e.g., `'python'`, `'javascript'`, `'python,javascript'`) |

### 🔐 Required Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `AWS_ACCOUNT_ID` | Optional | AWS Account ID for infrastructure scans |

**Note:** `GITHUB_TOKEN` is automatically provided by GitHub Actions and doesn't need to be explicitly passed.

## 🧩 Composite Action

For more granular control, you can create composite actions for specific security tools.

### Example: SAST-only Composite Action

```yaml
# .github/actions/sast-scan/action.yml
name: 'SAST Security Scan'
description: 'Run Static Application Security Testing'
inputs:
  python-version:
    description: 'Python version'
    required: false
    default: '3.12'
  post-results:
    description: 'Post results to PR'
    required: false
    default: 'true'

runs:
  using: 'composite'
  steps:
    - uses: huntridge-labs/hardening-workflows/.github/actions/sast-scan@0.1.0
      with:
        python-version: ${{ inputs.python-version }}
        post-results: ${{ inputs.post-results }}
```

## 📄 Workflow Templates

GitHub also supports workflow templates for organization-wide standards.

### Setup in your organization:

1. Create a `.github` repository in your organization
2. Add workflow templates in `.github/workflow-templates/`
3. Members can then use these templates when creating new repositories

Example template (`security-hardening.yml`):

```yaml
name: Security Hardening
on:
  push:
    branches: [ $default-branch ]
  pull_request:
    branches: [ $default-branch ]

jobs:
  security:
    uses: your-org/hardening-workflows/.github/workflows/reusable-security-hardening.yml@0.1.0
    with:
      scan_type: 'full'
    secrets: inherit
    permissions:
      contents: read
      security-events: write
      pull-requests: write
```

## 🎯 Version Pinning Best Practices

### 🏷️ Use Specific Tags (Recommended for Production)
```yaml
uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@v1.0.0
```

### 🌿 Use Branch (Good for Development)
```yaml
uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
```

### 📌 Use Commit SHA (Maximum Security)
```yaml
uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@a1b2c3d4
```

## 🏢 Organization-Wide Adoption

### Strategy 1: Gradual Rollout
1. Start with pilot projects
2. Gather feedback and iterate
3. Document lessons learned
4. Roll out to more teams

### Strategy 2: Template-Based
1. Create organization workflow templates
2. Make security scanning a requirement for new repos
3. Provide migration guides for existing projects

### Strategy 3: Policy-Based
1. Use GitHub's branch protection rules
2. Require security checks to pass before merging
3. Set up organization-wide security policies

## 🐕 Dogfooding Example

This repository itself demonstrates the reusable workflow in action! Check out:
- **Main workflow**: `.github/workflows/security-hardening.yml` (reference implementation)
- **Reusable demo**: `.github/workflows/security-reusable-demo.yml` (uses the reusable workflow)

You can manually run the demo workflow to see the reusable workflow in action and compare results.

## 🔧 Customization Examples

### Example 1: Python-only Project
```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@0.1.0
    with:
      scan_type: 'sast-only'
      python_version: '3.11'
      post_pr_comment: true
```

### Example 2: Infrastructure-heavy Project
```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@0.1.0
    with:
      scan_type: 'infrastructure-only'
      aws_region: 'us-west-2'
    secrets:
      AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
```

### Example 3: Container-focused Project
```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@0.1.0
    with:
      scan_type: 'container-only'
      post_pr_comment: false  # Handle reporting differently
```

### Example 4: Python-only Project (Skip JavaScript CodeQL)
```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@0.1.0
    with:
      scan_type: 'full'
      codeql_languages: 'python'  # Only analyze Python code
      python_version: '3.11'
```

### Example 5: JavaScript/TypeScript Project
```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@0.1.0
    with:
      scan_type: 'sast-only'
      codeql_languages: 'javascript'  # Only analyze JavaScript/TypeScript
```

## 🚀 Getting Started

1. **Choose your approach**: Reusable workflow is recommended for most cases
2. **Set up secrets**: Configure any required secrets in your target repository
3. **Create the workflow**: Add the security workflow to `.github/workflows/`
4. **Test it**: Run the workflow manually first to ensure everything works
5. **Monitor results**: Review security reports and adjust configuration as needed

## 📚 Additional Resources

- [GitHub Actions: Reusing Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Creating Composite Actions](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action)
- [Organization Workflow Templates](https://docs.github.com/en/actions/using-workflows/creating-starter-workflows-for-your-organization)

## 🆘 Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure the calling workflow has the required permissions
2. **Secret Access**: Secrets must be explicitly passed to reusable workflows
3. **Path Issues**: Use relative paths in the reusable workflow, absolute paths in calling workflows
4. **Version Conflicts**: Pin to specific versions to avoid breaking changes

### Getting Help

- 📋 Check the [Issues](https://github.com/huntridge-labs/hardening-workflows/issues) page
- 💬 Start a [Discussion](https://github.com/huntridge-labs/hardening-workflows/discussions)
- 📖 Review the [workflow runs](https://github.com/huntridge-labs/hardening-workflows/actions) for examples