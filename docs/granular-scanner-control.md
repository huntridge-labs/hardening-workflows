# Granular Scanner Control

## Quick Reference

| Scan Type | Use Case | Scanners Enabled |
|-----------|----------|------------------|
| `codeql-only` | Fast dev feedback | CodeQL only |
| `sast-only` | All static analysis | CodeQL, Semgrep, Bandit, Gitleaks |
| `full` | Comprehensive scan | All scanners |
| `container-only` | Docker/containers | Container scanning |
| `infrastructure-only` | Terraform/IaC | Infrastructure scanning |

## New Scanner List Approach (Recommended)

Use the `scanners` input to specify exactly which scanners to run:

```yaml
with:
  scanners: 'codeql,semgrep,gitleaks'  # Run only these three scanners
```

### Available Scanner Tokens

| Token | Description | Category |
|-------|-------------|----------|
| `codeql` | GitHub CodeQL analysis | SAST |
| `semgrep` | Semgrep/OpenGrep analysis | SAST |
| `bandit` | Bandit Python security | SAST |
| `gitleaks` | Gitleaks secrets detection | Secrets |
| `container` | Container/Docker scanning | Container |
| `infrastructure` | Terraform/IaC scanning | Infrastructure |
| `lint` | Code quality and linting | Code Quality |
| `all` | All available scanners | All |
| `sast` | All SAST scanners | SAST |
| `secrets` | Secrets scanning only | Secrets |
| `none` | No scanners | None |

### GitHub Code Security Integration

**Important:** CodeQL scanning requires GitHub Code Security to be enabled for your repository.

```yaml
with:
  scanners: 'codeql'
  enable_code_security: true  # Required for CodeQL scanning
```

If Code Security is not enabled, CodeQL will be automatically disabled with a warning.

### Examples

**Fast development feedback:**
```yaml
scanners: 'codeql'
```

**Python project with secrets:**
```yaml
scanners: 'codeql,bandit,gitleaks'
```

**Infrastructure focus:**
```yaml
scanners: 'infrastructure'
```

**Everything except Semgrep:**
```yaml
scanners: 'all'
# Note: 'all' includes all scanners, but you can exclude by not listing them
```

## Legacy Granular Control (Deprecated)

The old `enable_*` flags are deprecated but still supported for backward compatibility:

```yaml
with:
  enable_codeql: true
  enable_semgrep: false
  # ... other enable_* flags
```

## Scanner Details

| Scanner | Category | Speed | Best For |
|---------|----------|-------|----------|
| CodeQL | SAST | 5-10 min | High-accuracy analysis |
| Semgrep | SAST | 1-3 min | Pattern matching |
| Bandit | SAST | <2 min | Python security |
| Gitleaks | Secrets | 1-2 min | Credential detection |
| Container | Container | 2-5 min | Docker security |
| Infrastructure | IaC | 3-7 min | Terraform security |
| Linting | Code Quality | 1-3 min | Code standards |

## Direct Scanner Calls

Call scanners independently for maximum flexibility:

```yaml
uses: ./.github/workflows/scanners/sast/codeql.yml
```

See [Scanner README](../.github/workflows/scanners/README.md) for details.
