# Granular Scanner Control

## Quick Reference

| Scan Type | Use Case | Scanners Enabled |
|-----------|----------|------------------|
| `codeql-only` | Fast dev feedback | CodeQL only |
| `sast-only` | All static analysis | CodeQL, Semgrep, Bandit, Gitleaks |
| `full` | Comprehensive scan | All scanners |
| `container-only` | Docker/containers | Container scanning |
| `infrastructure-only` | Terraform/IaC | Infrastructure scanning |

## Granular Control

Override scan type by explicitly enabling/disabling scanners:

```yaml
with:
  enable_codeql: true      # Override on
  enable_semgrep: false    # Override off
  # Others follow scan_type
```

## Common Scenarios

**Fast development feedback:**
```yaml
scan_type: 'codeql-only'
```

**Pre-merge comprehensive:**
```yaml
scan_type: 'full'
```

**Python project:**
```yaml
enable_codeql: true
enable_bandit: true
enable_gitleaks: true
```

**Secrets audit:**
```yaml
enable_gitleaks: true
enable_codeql: false
```

**Cost-optimized:**
```yaml
enable_codeql: true      # Primary
enable_gitleaks: true    # Essential
enable_semgrep: false    # Skip
```

## Scanner Details

| Scanner | Category | Speed | Best For |
|---------|----------|-------|----------|
| CodeQL | SAST | 5-10 min | High-accuracy analysis |
| Semgrep | SAST | 1-3 min | Pattern matching |
| Bandit | SAST | <2 min | Python security |
| Gitleaks | Secrets | 1-2 min | Credential detection |

## Direct Scanner Calls

Call scanners independently for maximum flexibility:

```yaml
uses: ./.github/workflows/scanners/sast/codeql.yml
```

See [Scanner README](../.github/workflows/scanners/README.md) for details.
