<div align="center">

# ATO Compliance Reporting

Automated compliance reporting for continuous Authority to Operate (ATO) with NIST 800-53 Rev 5 control mapping.

</div>

## Overview

The ATO Compliance Reporting feature generates OSCAL-formatted assessment results and compliance evidence packages from automated security scanning. This enables continuous monitoring and automated evidence collection for federal ATO requirements.

**Key Features:**
- OSCAL 1.0.4 compliant assessment results
- NIST SP 800-53 Rev 5 control mapping
- Multiple output formats (OSCAL, Markdown, JSON, CSV, HTML)
- Automated evidence package generation
- 365-day evidence retention (configurable)
- FedRAMP and FISMA compatible

## Quick Start

### Basic Usage

Add ATO compliance reporting to your security workflow:

```yaml
name: Security Scan with ATO Compliance

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 2 * * 1'  # Weekly

jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/security-scan.yml@2.10.0
    with:
      scanners: all
      enable_code_security: true
      enable_ato_reporting: true  # Enable ATO compliance reporting
    secrets: inherit
```

This will:
1. Run all security scanners
2. Generate OSCAL assessment results
3. Create markdown compliance report
4. Package all evidence for audit

## Configuration

### Input Parameters

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `enable_ato_reporting` | Enable ATO compliance reporting | `false` | No |
| `ato_compliance_mapping_file` | Path to NIST 800-53 mapping config | `config/nist-800-53-mapping.json` | No |
| `ato_report_format` | Output format(s) | `oscal,markdown` | No |
| `ato_evidence_retention_days` | Evidence retention period | `365` | No |

### Output Formats

**Supported Formats:**

| Format | Description | Use Case |
|--------|-------------|----------|
| `oscal` | OSCAL 1.0.4 Assessment Results JSON | FedRAMP/FISMA submission, GRC tools |
| `markdown` | Human-readable compliance report | Management review, documentation |
| `json` | Machine-readable JSON | API integration, automation |
| `csv` | Spreadsheet format | Excel analysis, reporting |
| `html` | Interactive web dashboard | Stakeholder presentations |
| `all` | Generate all formats | Complete evidence package |

**Examples:**

```yaml
# OSCAL only (default for federal systems)
ato_report_format: 'oscal'

# OSCAL + Markdown for human review
ato_report_format: 'oscal,markdown'

# All formats for comprehensive evidence
ato_report_format: 'all'
```

## Setup

### 1. Create NIST 800-53 Mapping Configuration

Create `config/nist-800-53-mapping.json` in your repository:

```json
{
  "version": "1.0.0",
  "framework": "NIST-SP-800-53-rev5",
  "profile": "MODERATE",
  "system": {
    "name": "Your Application System",
    "description": "System description for ATO",
    "security_sensitivity_level": "moderate",
    "system_characteristics": {
      "authorization_boundary": "Application and CI/CD Pipeline",
      "network_architecture": "Cloud-hosted on AWS",
      "data_flow": "API-based microservices architecture"
    }
  },
  "scanners": {
    "codeql": {
      "name": "GitHub CodeQL",
      "type": "SAST",
      "vendor": "GitHub",
      "description": "Semantic code analysis engine",
      "controls": [
        {
          "control_id": "SA-11",
          "control_name": "Developer Testing and Evaluation",
          "implementation_status": "implemented",
          "implementation_description": "CodeQL performs automated SAST on all code commits",
          "coverage_level": "full",
          "test_method": "automated",
          "test_frequency": "on-commit"
        }
      ]
    }
  }
}
```

**💡 Tip:** Use the provided template in `config/nist-800-53-mapping.json` as a starting point.

### 2. Enable in Workflow

Update your workflow to enable ATO reporting:

```yaml
jobs:
  security-with-ato:
    uses: huntridge-labs/hardening-workflows/.github/workflows/security-scan.yml@2.10.0
    with:
      scanners: all
      enable_code_security: true
      enable_ato_reporting: true
      ato_report_format: 'oscal,markdown,json'
      ato_evidence_retention_days: 365
    secrets: inherit
```

### 3. Review Generated Reports

After workflow execution, download artifacts:

- `ato-compliance-reports-{run-id}` - All compliance reports
- `ato-evidence-package-{sha}` - Complete evidence bundle

## Report Contents

### OSCAL Assessment Results

**File:** `oscal-assessment-results.json`

OSCAL-formatted assessment results compatible with:
- FedRAMP submission requirements
- FISMA compliance systems
- GRC tools (e.g., GovReady, OSCAL Compass)

**Structure:**
```json
{
  "assessment-results": {
    "uuid": "...",
    "metadata": { ... },
    "results": [
      {
        "reviewed-controls": { ... },
        "observations": [ ... ],
        "findings": [ ... ]
      }
    ]
  }
}
```

### Markdown Compliance Report

**File:** `ato-compliance-report.md`

Human-readable report including:

- **Executive Summary** - Control coverage, scanner status, compliance rate
- **ATO Assessment** - Readiness determination (READY/CONDITIONAL/NOT_READY)
- **Control Family Coverage** - Detailed breakdown by NIST 800-53 family
- **Scanner Execution Results** - Finding counts by severity
- **Remediation Recommendations** - Prioritized action items
- **Evidence Artifacts** - List of all supporting evidence

### Evidence Package

**Directory:** `ato-evidence-package/`

Contains:
- All compliance reports (OSCAL, MD, JSON, CSV, HTML)
- SARIF files from all security scanners
- Scanner summaries and metadata
- Evidence manifest with package metadata

## NIST 800-53 Control Coverage

The default mapping covers these control families:

| Family | Controls | Scanners |
|--------|----------|----------|
| **AC** - Access Control | AC-3, AC-6 | Gitleaks, Checkov |
| **AU** - Audit and Accountability | AU-9 | Gitleaks |
| **CM** - Configuration Management | CM-2, CM-6, CM-8 | Trivy IaC, Checkov, Trivy Container, SBOM |
| **IA** - Identification and Authentication | IA-5, IA-5(1) | Gitleaks |
| **RA** - Risk Assessment | RA-5, RA-5(5) | Trivy Container, Grype |
| **SA** - System and Services Acquisition | SA-11, SA-11(1), SA-15(9) | CodeQL, Bandit, OpenGrep, SBOM |
| **SC** - System and Communications Protection | SC-7, SC-7(3), SC-28 | Trivy IaC, Checkov, Gitleaks |
| **SI** - System and Information Integrity | SI-2, SI-3, SI-4, SI-10, SI-16 | Trivy, Grype, ClamAV, CodeQL, Bandit |
| **SR** - Supply Chain Risk Management | SR-4, SR-4(1), SR-11 | SBOM (Syft) |

## Usage Examples

### Example 1: Basic ATO Compliance

```yaml
name: ATO Compliance Scanning

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly scans for continuous monitoring

permissions:
  contents: read
  security-events: write
  actions: read

jobs:
  ato-compliance:
    uses: huntridge-labs/hardening-workflows/.github/workflows/security-scan.yml@2.10.0
    with:
      scanners: all
      enable_code_security: true
      enable_ato_reporting: true
    secrets: inherit
```

### Example 2: Custom Configuration

```yaml
jobs:
  federal-ato:
    uses: huntridge-labs/hardening-workflows/.github/workflows/security-scan.yml@2.10.0
    with:
      scanners: all
      enable_code_security: true
      enable_ato_reporting: true
      ato_compliance_mapping_file: '.github/compliance/fedramp-moderate.json'
      ato_report_format: 'oscal,markdown,json'
      ato_evidence_retention_days: 730  # 2 years
      fail_on_severity: high  # Enforce security gates
    secrets: inherit
```

### Example 3: Standalone ATO Report Generation

```yaml
name: Generate ATO Compliance Report

on:
  workflow_dispatch:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  ato-report:
    uses: huntridge-labs/hardening-workflows/.github/workflows/ato-compliance-reporting.yml@2.10.0
    with:
      mapping_file: 'config/nist-800-53-mapping.json'
      output_format: 'all'
      retention_days: 365
```

### Example 4: Pre-Deployment ATO Check

```yaml
name: Pre-Deployment ATO Validation

on:
  pull_request:
    branches: [main]

jobs:
  security-scan:
    uses: huntridge-labs/hardening-workflows/.github/workflows/security-scan.yml@2.10.0
    with:
      scanners: all
      enable_code_security: true
      enable_ato_reporting: true
      ato_report_format: 'oscal,markdown'
      fail_on_severity: high
    secrets: inherit

  validate-ato-status:
    needs: security-scan
    runs-on: ubuntu-latest
    steps:
      - name: Check ATO Readiness
        run: |
          if [ "${{ needs.security-scan.outputs.ato_status }}" != "READY" ]; then
            echo "❌ ATO Status: ${{ needs.security-scan.outputs.ato_status }}"
            echo "Cannot deploy - ATO requirements not met"
            exit 1
          fi
          echo "✅ ATO Status: READY - Deployment approved"
```

## Customizing Control Mappings

### Adding Custom Controls

Edit `config/nist-800-53-mapping.json` to add controls:

```json
{
  "scanners": {
    "your-scanner": {
      "name": "Custom Security Scanner",
      "type": "SAST",
      "vendor": "Your Org",
      "controls": [
        {
          "control_id": "AC-2",
          "control_name": "Account Management",
          "implementation_status": "implemented",
          "control_origination": "service-provider-system-specific",
          "implementation_description": "Scanner validates user account configurations",
          "responsible_role": "security-automation",
          "test_method": "automated",
          "test_frequency": "on-commit",
          "coverage_level": "partial",
          "evidence_artifacts": ["custom-scanner-sarif"]
        }
      ]
    }
  }
}
```

### Custom Security Frameworks

You can create mappings for other frameworks:

```json
{
  "framework": "FedRAMP-Moderate",
  "profile": "MODERATE",
  // ... customize controls per FedRAMP requirements
}
```

Or for other standards:
- NIST Cybersecurity Framework (CSF)
- ISO 27001
- SOC 2
- PCI DSS

## Outputs

The workflow provides outputs for automation:

```yaml
outputs:
  ato_status:
    description: 'ATO readiness: READY, CONDITIONAL, or NOT_READY'
  critical_findings:
    description: 'Number of critical severity findings'
  high_findings:
    description: 'Number of high severity findings'
```

**Example usage:**

```yaml
jobs:
  security:
    uses: huntridge-labs/hardening-workflows/.github/workflows/security-scan.yml@2.10.0
    with:
      enable_ato_reporting: true

  deploy:
    needs: security
    if: needs.security.outputs.ato_status == 'READY'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying - ATO requirements satisfied"
```

## ATO Readiness Determination

The system automatically determines ATO readiness:

| Status | Criteria | Action Required |
|--------|----------|----------------|
| **READY** | No critical or high findings | Proceed with ATO package |
| **CONDITIONAL** | High severity findings present | Obtain risk acceptance |
| **NOT_READY** | Critical findings present | Remediate before ATO |

## Best Practices

### 1. Regular Scanning

```yaml
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 2 * * 1'  # Weekly for continuous monitoring
```

### 2. Evidence Retention

```yaml
with:
  ato_evidence_retention_days: 365  # Minimum for most ATOs
```

For FedRAMP or high-sensitivity systems:
```yaml
ato_evidence_retention_days: 1095  # 3 years
```

### 3. Severity Thresholds

```yaml
with:
  fail_on_severity: high
  allow_failure: false
```

### 4. Complete Scanner Coverage

```yaml
with:
  scanners: all  # Maximize control coverage
```

### 5. Version Control Mapping Files

Keep `nist-800-53-mapping.json` in version control to track control implementation changes over time.

## Troubleshooting

### No SARIF Files Found

**Issue:** "No SARIF files found" in compliance report

**Solution:**
```yaml
with:
  enable_code_security: true  # Required for SARIF generation
```

### Mapping File Not Found

**Issue:** "Mapping file not found" error

**Solution:** Ensure `config/nist-800-53-mapping.json` exists or specify correct path:
```yaml
with:
  ato_compliance_mapping_file: '.github/ato-mapping.json'
```

### OSCAL Validation Errors

**Issue:** OSCAL file doesn't validate

**Solution:** Ensure mapping configuration follows schema in template. Validate UUIDs and required fields.

## Integration with GRC Tools

### GovReady

Import OSCAL assessment results:
```bash
govready import oscal-assessment-results.json
```

### OSCAL Compass

```bash
oscal-cli compliance-as-code convert \
  --input oscal-assessment-results.json \
  --output fedramp-sar.json
```

## Compliance Frameworks

This feature supports:

- ✅ **NIST SP 800-53 Rev 5** - Default
- ✅ **FedRAMP** - Moderate, High baselines
- ✅ **FISMA** - All categorizations
- ✅ **NIST Cybersecurity Framework** - Custom mapping
- ⚠️ **ISO 27001** - Custom mapping required
- ⚠️ **SOC 2** - Custom mapping required

## Frequently Asked Questions

**Q: Is this a complete ATO package?**
A: No, this provides continuous monitoring evidence and assessment results. A complete ATO package requires System Security Plan (SSP), POA&M, and other documentation.

**Q: Does this replace manual security assessments?**
A: No, this supplements continuous monitoring. Manual assessments are still required for many controls.

**Q: How often should I generate reports?**
A: Minimum weekly for continuous monitoring. More frequent for high-change systems.

**Q: Can I customize control implementations?**
A: Yes, edit `config/nist-800-53-mapping.json` to match your implementation.

**Q: Is the OSCAL output FedRAMP compatible?**
A: Yes, the OSCAL 1.0.4 Assessment Results format is compatible with FedRAMP requirements.

## Support

- **Documentation:** [docs/ato-compliance-reporting.md](./ato-compliance-reporting.md)
- **Issues:** [GitHub Issues](https://github.com/huntridge-labs/hardening-workflows/issues)
- **Example Config:** `config/nist-800-53-mapping.json`

## References

- [NIST SP 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [OSCAL Documentation](https://pages.nist.gov/OSCAL/)
- [FedRAMP OSCAL Resources](https://github.com/GSA/fedramp-automation)
- [Continuous ATO (cATO) Guide](https://www.fedramp.gov/assets/resources/documents/CSP_Continuous_Monitoring_Strategy_Guide.pdf)
