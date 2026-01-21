#!/usr/bin/env python3
"""
ATO Compliance Report Generator
Generates OSCAL and other format compliance reports from security scan results
Supports NIST 800-53 Rev 5 control mapping for continuous ATO
"""

import json
import os
import sys
import glob
import uuid
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


class ATOComplianceReportGenerator:
    """Generates ATO compliance reports in multiple formats"""

    SUPPORTED_FORMATS = ['oscal', 'oscal-json', 'markdown', 'json', 'csv', 'html']

    def __init__(self, mapping_file: str, output_dir: str, output_format: str = 'oscal'):
        self.mapping_file = mapping_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_format = output_format.lower()

        # Validate each format in comma-separated list
        formats = [f.strip() for f in self.output_format.split(',')]
        for fmt in formats:
            if fmt not in self.SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported format: {fmt}. Supported: {', '.join(self.SUPPORTED_FORMATS)}")

        with open(mapping_file, 'r') as f:
            self.mapping = json.load(f)

        self.scan_results = {}
        self.control_summary = {}
        self.system_uuid = str(uuid.uuid4())

    def load_sarif_results(self, pattern: str = "**/*.sarif"):
        """Load all SARIF files from artifacts"""
        sarif_files = glob.glob(pattern, recursive=True)

        print(f"🔍 Searching for SARIF files with pattern: {pattern}")
        print(f"📦 Found {len(sarif_files)} SARIF files")

        for sarif_file in sarif_files:
            try:
                with open(sarif_file, 'r') as f:
                    data = json.load(f)
                    scanner_name = self._extract_scanner_name(data, sarif_file)

                    print(f"  ✓ Processing {scanner_name} from {Path(sarif_file).name}")

                    if scanner_name not in self.scan_results:
                        self.scan_results[scanner_name] = {
                            'total_findings': 0,
                            'critical': 0,
                            'high': 0,
                            'medium': 0,
                            'low': 0,
                            'informational': 0,
                            'findings': [],
                            'sarif_file': sarif_file
                        }

                    # Count findings by severity
                    for run in data.get('runs', []):
                        for result in run.get('results', []):
                            self.scan_results[scanner_name]['total_findings'] += 1
                            severity = self._normalize_severity(result.get('level', 'note'))

                            self.scan_results[scanner_name][severity] += 1

                            self.scan_results[scanner_name]['findings'].append({
                                'rule_id': result.get('ruleId', 'unknown'),
                                'message': result.get('message', {}).get('text', 'No description'),
                                'severity': severity,
                                'locations': result.get('locations', [])
                            })
            except Exception as e:
                print(f"  ⚠️  Warning: Could not process {sarif_file}: {e}")

    def _normalize_severity(self, level: str) -> str:
        """Normalize SARIF severity levels to standard categories"""
        level = level.lower()
        mapping = {
            'error': 'critical',
            'warning': 'high',
            'note': 'medium',
            'none': 'low',
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
            'info': 'informational',
            'informational': 'informational'
        }
        return mapping.get(level, 'informational')

    def _extract_scanner_name(self, sarif_data: Dict, filepath: str) -> str:
        """Extract scanner name from SARIF data or filename"""
        try:
            tool_name = sarif_data['runs'][0]['tool']['driver']['name'].lower()
            # Normalize common scanner names
            if 'codeql' in tool_name:
                return 'codeql'
            elif 'trivy' in tool_name:
                if 'iac' in filepath.lower():
                    return 'trivy-iac'
                else:
                    return 'trivy-container'
            elif 'semgrep' in tool_name or 'opengrep' in tool_name:
                return 'opengrep'
            elif 'gitleaks' in tool_name:
                return 'gitleaks'
            elif 'checkov' in tool_name:
                return 'checkov'
            elif 'bandit' in tool_name:
                return 'bandit'
            elif 'grype' in tool_name:
                return 'grype'
            elif 'clamav' in tool_name:
                return 'clamav'
            return tool_name
        except:
            # Extract from filename
            filename = Path(filepath).stem.lower()
            for scanner in self.mapping['scanners'].keys():
                if scanner.replace('-', '') in filename.replace('-', ''):
                    return scanner
            return 'unknown'

    def generate_control_coverage(self) -> Dict[str, Any]:
        """Generate control coverage summary"""
        controls = {}

        for scanner, config in self.mapping['scanners'].items():
            for control in config.get('controls', []):
                control_id = control['control_id']

                if control_id not in controls:
                    controls[control_id] = {
                        'id': control_id,
                        'name': control.get('control_name', 'Unknown Control'),
                        'scanners': [],
                        'implementation_status': 'not-implemented',
                        'total_findings': 0,
                        'critical_findings': 0,
                        'high_findings': 0
                    }

                scanner_data = self.scan_results.get(scanner, {})

                controls[control_id]['scanners'].append({
                    'scanner': scanner,
                    'scanner_name': config.get('name', scanner),
                    'implementation': control.get('implementation_description', ''),
                    'status': control.get('implementation_status', 'not-implemented'),
                    'coverage_level': control.get('coverage_level', 'none'),
                    'test_method': control.get('test_method', 'automated'),
                    'test_frequency': control.get('test_frequency', 'on-commit'),
                    'findings': scanner_data.get('total_findings', 0),
                    'critical': scanner_data.get('critical', 0),
                    'high': scanner_data.get('high', 0),
                    'evidence_artifacts': control.get('evidence_artifacts', [])
                })

                controls[control_id]['total_findings'] += scanner_data.get('total_findings', 0)
                controls[control_id]['critical_findings'] += scanner_data.get('critical', 0)
                controls[control_id]['high_findings'] += scanner_data.get('high', 0)

                # Update overall control status (prefer implemented)
                if control.get('implementation_status') == 'implemented':
                    controls[control_id]['implementation_status'] = 'implemented'

        return controls

    def generate_oscal_assessment_results(self) -> Dict[str, Any]:
        """Generate OSCAL Assessment Results (AR) format"""
        controls = self.generate_control_coverage()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Generate observations for each finding
        observations = []
        observation_uuid_map = {}

        for scanner, results in self.scan_results.items():
            for idx, finding in enumerate(results.get('findings', [])):
                obs_uuid = str(uuid.uuid4())
                observation_uuid_map[f"{scanner}-{idx}"] = obs_uuid

                observations.append({
                    'uuid': obs_uuid,
                    'title': f"{scanner}: {finding['rule_id']}",
                    'description': finding['message'],
                    'methods': ['TEST-AUTOMATED'],
                    'types': ['finding'],
                    'collected': timestamp,
                    'props': [
                        {
                            'name': 'severity',
                            'value': finding['severity']
                        },
                        {
                            'name': 'scanner',
                            'value': scanner
                        }
                    ]
                })

        # Generate results for each control
        assessment_results = []
        for control_id, control_data in controls.items():
            result_uuid = str(uuid.uuid4())

            # Determine control satisfaction
            if control_data['critical_findings'] > 0 or control_data['high_findings'] > 0:
                finding_type = 'not-satisfied'
            elif control_data['total_findings'] > 0:
                finding_type = 'satisfied'
            else:
                finding_type = 'satisfied'

            result = {
                'uuid': result_uuid,
                'title': f"Assessment Result for {control_id}",
                'description': f"Automated assessment of {control_id}: {control_data['name']}",
                'start': timestamp,
                'end': timestamp,
                'reviewed-controls': {
                    'control-selections': [
                        {
                            'include-controls': [
                                {
                                    'control-id': control_id
                                }
                            ]
                        }
                    ]
                },
                'findings': [
                    {
                        'uuid': str(uuid.uuid4()),
                        'title': f"{control_id} Assessment Finding",
                        'description': f"Automated security scanning identified {control_data['total_findings']} findings for this control",
                        'target': {
                            'type': 'objective-id',
                            'target-id': control_id,
                            'status': {
                                'state': finding_type
                            }
                        },
                        'related-observations': [
                            {'observation-uuid': obs['uuid']}
                            for obs in observations[:min(50, len(observations))]  # Limit for performance
                        ]
                    }
                ]
            }

            assessment_results.append(result)

        # Build complete OSCAL AR document
        oscal_ar = {
            'assessment-results': {
                'uuid': str(uuid.uuid4()),
                'metadata': {
                    'title': f"Security Assessment Results - {self.mapping['system'].get('name', 'System')}",
                    'last-modified': timestamp,
                    'version': self.mapping.get('version', '1.0.0'),
                    'oscal-version': '1.0.4',
                    'roles': [
                        {
                            'id': 'security-automation',
                            'title': 'Security Automation System',
                            'description': 'Automated security scanning system'
                        }
                    ],
                    'parties': [
                        {
                            'uuid': str(uuid.uuid4()),
                            'type': 'organization',
                            'name': 'Security Automation Team'
                        }
                    ]
                },
                'import-ap': {
                    'href': '#assessment-plan-uuid'
                },
                'local-definitions': {
                    'assessment-assets': {
                        'assessment-platforms': [
                            {
                                'uuid': str(uuid.uuid4()),
                                'title': 'GitHub Actions Security Scanning Pipeline'
                            }
                        ]
                    }
                },
                'results': [
                    {
                        'uuid': str(uuid.uuid4()),
                        'title': 'Automated Security Scan Results',
                        'description': f"Continuous security scanning results for {self.mapping['system'].get('name')}",
                        'start': timestamp,
                        'end': timestamp,
                        'reviewed-controls': {
                            'control-selections': [
                                {
                                    'include-controls': [
                                        {'control-id': cid} for cid in controls.keys()
                                    ]
                                }
                            ]
                        },
                        'observations': observations,
                        'findings': []
                    }
                ]
            }
        }

        # Add findings summary to first result
        for control_id, control_data in controls.items():
            finding_uuid = str(uuid.uuid4())

            oscal_ar['assessment-results']['results'][0]['findings'].append({
                'uuid': finding_uuid,
                'title': f"{control_id}: {control_data['name']}",
                'description': f"Control implemented via automated scanning: {control_data['total_findings']} findings detected",
                'target': {
                    'type': 'objective-id',
                    'target-id': control_id,
                    'title': control_data['name'],
                    'status': {
                        'state': 'not-satisfied' if control_data['critical_findings'] > 0 or control_data['high_findings'] > 0 else 'satisfied'
                    }
                }
            })

        return oscal_ar

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown ATO compliance report"""
        controls = self.generate_control_coverage()
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

        report = f"""# ATO Compliance Report

**System Name:** {self.mapping['system'].get('name', 'N/A')}
**Framework:** {self.mapping.get('framework', 'NIST-SP-800-53-rev5')}
**Security Level:** {self.mapping.get('profile', 'MODERATE').upper()}
**Generated:** {timestamp}
**Report Version:** {self.mapping.get('version', '1.0.0')}

---

## Executive Summary

This report provides evidence of continuous security monitoring and automated compliance
testing in support of Authority to Operate (ATO) requirements under NIST SP 800-53 Rev 5.

### System Information

**Authorization Boundary:** {self.mapping['system'].get('system_characteristics', {}).get('authorization_boundary', 'Not specified')}
**Network Architecture:** {self.mapping['system'].get('system_characteristics', {}).get('network_architecture', 'Not specified')}
**Security Sensitivity:** {self.mapping['system'].get('security_sensitivity_level', 'Not specified').upper()}

### Compliance Overview

"""

        total_controls = len(controls)
        implemented_controls = sum(1 for c in controls.values() if c['implementation_status'] == 'implemented')
        controls_satisfied = sum(1 for c in controls.values() if c['critical_findings'] == 0 and c['high_findings'] == 0)
        controls_with_findings = sum(1 for c in controls.values() if c['total_findings'] > 0)

        compliance_rate = (controls_satisfied / total_controls * 100) if total_controls > 0 else 0

        report += f"""
| Metric | Value | Status |
|--------|-------|--------|
| Total Controls Mapped | {total_controls} | - |
| Automated Controls | {implemented_controls} | {'✅' if implemented_controls > 0 else '⚠️'} |
| Controls Satisfied | {controls_satisfied} | {'✅' if compliance_rate >= 90 else '⚠️'} |
| Controls with Findings | {controls_with_findings} | {'⚠️' if controls_with_findings > 0 else '✅'} |
| Compliance Rate | {compliance_rate:.1f}% | {'✅' if compliance_rate >= 90 else '⚠️'} |
| Active Scanners | {len(self.scan_results)} | {'✅' if len(self.scan_results) > 0 else '❌'} |

### Scanner Execution Summary

| Scanner | Total | Critical | High | Medium | Low | Status |
|---------|-------|----------|------|--------|-----|--------|
"""

        total_critical = 0
        total_high = 0

        for scanner in sorted(self.scan_results.keys()):
            results = self.scan_results[scanner]
            status = "✅ Pass" if results['critical'] == 0 and results['high'] == 0 else "❌ Fail"
            report += f"| {self.mapping['scanners'].get(scanner, {}).get('name', scanner)} "
            report += f"| {results['total_findings']} "
            report += f"| {results['critical']} "
            report += f"| {results['high']} "
            report += f"| {results['medium']} "
            report += f"| {results['low']} "
            report += f"| {status} |\n"

            total_critical += results['critical']
            total_high += results['high']

        report += "\n---\n\n## ATO Assessment\n\n"

        if total_critical > 0:
            report += "### ❌ ATO RECOMMENDATION: NOT READY\n\n"
            report += f"**Critical Issues Found:** {total_critical} critical severity findings must be remediated before ATO approval.\n\n"
        elif total_high > 0:
            report += "### ⚠️ ATO RECOMMENDATION: CONDITIONAL\n\n"
            report += f"**High Severity Issues:** {total_high} high severity findings require review. May proceed with ATO pending risk acceptance.\n\n"
        else:
            report += "### ✅ ATO RECOMMENDATION: READY\n\n"
            report += "**No Critical/High Issues:** System meets automated security requirements for ATO consideration.\n\n"

        report += "---\n\n## Control Family Coverage\n\n"

        # Group by control family
        families = defaultdict(list)
        for control_id, control_data in controls.items():
            family = control_id.split('-')[0]
            families[family].append((control_id, control_data))

        family_names = {
            'AC': 'Access Control',
            'AU': 'Audit and Accountability',
            'AT': 'Awareness and Training',
            'CA': 'Assessment, Authorization, and Monitoring',
            'CM': 'Configuration Management',
            'CP': 'Contingency Planning',
            'IA': 'Identification and Authentication',
            'IR': 'Incident Response',
            'MA': 'Maintenance',
            'MP': 'Media Protection',
            'PE': 'Physical and Environmental Protection',
            'PL': 'Planning',
            'PS': 'Personnel Security',
            'PT': 'PII Processing and Transparency',
            'RA': 'Risk Assessment',
            'SA': 'System and Services Acquisition',
            'SC': 'System and Communications Protection',
            'SI': 'System and Information Integrity',
            'SR': 'Supply Chain Risk Management'
        }

        for family_code in sorted(families.keys()):
            family_name = family_names.get(family_code, family_code)
            family_controls = families[family_code]

            family_satisfied = sum(1 for _, c in family_controls if c['critical_findings'] == 0 and c['high_findings'] == 0)
            family_total = len(family_controls)
            family_status = "✅" if family_satisfied == family_total else "⚠️"

            report += f"### {family_status} {family_code}: {family_name}\n\n"
            report += f"**Coverage:** {family_satisfied}/{family_total} controls satisfied\n\n"

            for control_id, control_data in sorted(family_controls):
                status_icon = "✅" if (control_data['critical_findings'] == 0 and control_data['high_findings'] == 0) else "❌"
                report += f"#### {status_icon} {control_id}: {control_data['name']}\n\n"

                report += f"**Implementation Status:** `{control_data['implementation_status'].upper()}`  \n"
                report += f"**Total Findings:** {control_data['total_findings']} "
                report += f"(Critical: {control_data['critical_findings']}, High: {control_data['high_findings']})\n\n"

                if control_data['scanners']:
                    report += "**Implementation Details:**\n\n"
                    report += "| Scanner | Method | Frequency | Coverage | Findings | C | H |\n"
                    report += "|---------|--------|-----------|----------|----------|---|---|\n"

                    for scanner_info in control_data['scanners']:
                        report += f"| {scanner_info['scanner_name']} "
                        report += f"| {scanner_info['test_method']} "
                        report += f"| {scanner_info['test_frequency']} "
                        report += f"| {scanner_info['coverage_level']} "
                        report += f"| {scanner_info['findings']} "
                        report += f"| {scanner_info['critical']} "
                        report += f"| {scanner_info['high']} |\n"

                    report += "\n**Implementation Description:**\n\n"
                    for scanner_info in control_data['scanners']:
                        report += f"- **{scanner_info['scanner_name']}:** {scanner_info['implementation']}\n"

                    report += "\n"

        report += """---

## Remediation Recommendations

### Immediate Actions (Critical Priority)

"""

        critical_controls = sorted(
            [(cid, c) for cid, c in controls.items() if c['critical_findings'] > 0],
            key=lambda x: x[1]['critical_findings'],
            reverse=True
        )

        if critical_controls:
            for control_id, control_data in critical_controls:
                report += f"- **{control_id}**: {control_data['critical_findings']} CRITICAL findings - immediate remediation required\n"
        else:
            report += "- ✅ No critical findings identified\n"

        report += "\n### High Priority Actions\n\n"

        high_controls = sorted(
            [(cid, c) for cid, c in controls.items() if c['high_findings'] > 0 and c['critical_findings'] == 0],
            key=lambda x: x[1]['high_findings'],
            reverse=True
        )[:10]

        if high_controls:
            for control_id, control_data in high_controls:
                report += f"- **{control_id}**: {control_data['high_findings']} high severity findings require review\n"
        else:
            report += "- ✅ No high severity findings identified\n"

        report += """

---

## ATO Evidence Package

This automated compliance report serves as continuous monitoring evidence for:

### Documented Controls
"""

        for family_code in sorted(families.keys()):
            family_name = family_names.get(family_code, family_code)
            report += f"- **{family_code}** ({family_name}): {len(families[family_code])} controls\n"

        report += """
### Evidence Artifacts

All security scan results are retained as artifacts for audit purposes:

"""

        for scanner, config in sorted(self.mapping['scanners'].items()):
            if scanner in self.scan_results:
                report += f"- **{config['name']}** ({config['type']}): SARIF reports, scan summaries\n"

        report += """
### Compliance Frameworks

This report demonstrates compliance monitoring for:
- NIST SP 800-53 Rev 5
- FedRAMP Moderate Baseline
- FISMA Requirements

---

## Continuous Monitoring

**Assessment Method:** Automated security scanning via CI/CD pipeline
**Monitoring Frequency:** On every code commit and pull request
**Scheduled Assessments:** Weekly comprehensive scans
**Evidence Retention:** 365 days (configurable)

---

## Attestation

This report was automatically generated from security scanning results collected on {timestamp}.
All findings represent the actual state of the system at the time of assessment.

**Assessment Platform:** GitHub Actions Security Scanning Pipeline
**OSCAL Version:** 1.0.4
**Report Format:** Markdown (Human-Readable)

---

*Generated by Hardening Workflows ATO Compliance Automation*
*For questions or audit requests, contact your security team*
"""

        return report

    def generate_json_report(self) -> Dict[str, Any]:
        """Generate machine-readable JSON compliance report"""
        controls = self.generate_control_coverage()

        return {
            'metadata': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'framework': self.mapping.get('framework'),
                'system_name': self.mapping['system'].get('name'),
                'security_level': self.mapping.get('profile'),
                'version': self.mapping.get('version'),
                'report_format': 'json'
            },
            'system': self.mapping.get('system', {}),
            'summary': {
                'total_controls': len(controls),
                'implemented_controls': sum(1 for c in controls.values() if c['implementation_status'] == 'implemented'),
                'controls_satisfied': sum(1 for c in controls.values() if c['critical_findings'] == 0 and c['high_findings'] == 0),
                'controls_with_findings': sum(1 for c in controls.values() if c['total_findings'] > 0),
                'total_scanners': len(self.scan_results),
                'total_findings': sum(s['total_findings'] for s in self.scan_results.values()),
                'critical_findings': sum(s['critical'] for s in self.scan_results.values()),
                'high_findings': sum(s['high'] for s in self.scan_results.values())
            },
            'scanners': self.scan_results,
            'controls': controls,
            'ato_recommendation': self._get_ato_recommendation()
        }

    def generate_csv_report(self) -> str:
        """Generate CSV format compliance report"""
        controls = self.generate_control_coverage()

        csv = "Control ID,Control Name,Implementation Status,Total Findings,Critical,High,Medium,Low,Scanners\n"

        for control_id, control_data in sorted(controls.items()):
            scanners = ';'.join([s['scanner'] for s in control_data['scanners']])
            csv += f'"{control_id}","{control_data["name"]}","{control_data["implementation_status"]}",'
            csv += f'{control_data["total_findings"]},{control_data["critical_findings"]},{control_data["high_findings"]},'
            csv += f'0,0,"{scanners}"\n'

        return csv

    def generate_html_report(self) -> str:
        """Generate HTML compliance report"""
        controls = self.generate_control_coverage()
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

        total_critical = sum(s['critical'] for s in self.scan_results.values())
        total_high = sum(s['high'] for s in self.scan_results.values())

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATO Compliance Report - {self.mapping['system'].get('name', 'System')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #ecf0f1; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .summary-card.critical {{ border-left-color: #e74c3c; }}
        .summary-card.warning {{ border-left-color: #f39c12; }}
        .summary-card.success {{ border-left-color: #27ae60; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #34495e; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status-pass {{ color: #27ae60; font-weight: bold; }}
        .status-fail {{ color: #e74c3c; font-weight: bold; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; }}
        .badge-critical {{ background: #e74c3c; color: white; }}
        .badge-high {{ background: #f39c12; color: white; }}
        .badge-medium {{ background: #f39c12; color: white; }}
        .badge-low {{ background: #95a5a6; color: white; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ATO Compliance Report</h1>

        <div style="margin: 20px 0;">
            <strong>System:</strong> {self.mapping['system'].get('name', 'N/A')}<br>
            <strong>Framework:</strong> {self.mapping.get('framework', 'NIST-SP-800-53-rev5')}<br>
            <strong>Security Level:</strong> {self.mapping.get('profile', 'MODERATE').upper()}<br>
            <strong>Generated:</strong> {timestamp}
        </div>

        <h2>Summary</h2>
        <div class="summary">
            <div class="summary-card">
                <h3>Total Controls</h3>
                <div style="font-size: 2em; font-weight: bold;">{len(controls)}</div>
            </div>
            <div class="summary-card {'success' if total_critical == 0 else 'critical'}">
                <h3>Critical Findings</h3>
                <div style="font-size: 2em; font-weight: bold;">{total_critical}</div>
            </div>
            <div class="summary-card {'success' if total_high == 0 else 'warning'}">
                <h3>High Findings</h3>
                <div style="font-size: 2em; font-weight: bold;">{total_high}</div>
            </div>
            <div class="summary-card success">
                <h3>Active Scanners</h3>
                <div style="font-size: 2em; font-weight: bold;">{len(self.scan_results)}</div>
            </div>
        </div>

        <h2>Scanner Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Scanner</th>
                    <th>Total</th>
                    <th>Critical</th>
                    <th>High</th>
                    <th>Medium</th>
                    <th>Low</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""

        for scanner in sorted(self.scan_results.keys()):
            results = self.scan_results[scanner]
            status = "Pass" if results['critical'] == 0 and results['high'] == 0 else "Fail"
            status_class = "status-pass" if status == "Pass" else "status-fail"

            html += f"""
                <tr>
                    <td>{self.mapping['scanners'].get(scanner, {}).get('name', scanner)}</td>
                    <td>{results['total_findings']}</td>
                    <td><span class="badge badge-critical">{results['critical']}</span></td>
                    <td><span class="badge badge-high">{results['high']}</span></td>
                    <td><span class="badge badge-medium">{results['medium']}</span></td>
                    <td><span class="badge badge-low">{results['low']}</span></td>
                    <td class="{status_class}">{status}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>

        <h2>Control Coverage</h2>
        <table>
            <thead>
                <tr>
                    <th>Control ID</th>
                    <th>Control Name</th>
                    <th>Status</th>
                    <th>Findings</th>
                    <th>Scanners</th>
                </tr>
            </thead>
            <tbody>
"""

        for control_id, control_data in sorted(controls.items()):
            status = "✅ Satisfied" if (control_data['critical_findings'] == 0 and control_data['high_findings'] == 0) else "❌ Not Satisfied"
            scanners = ', '.join([s['scanner'] for s in control_data['scanners']])

            html += f"""
                <tr>
                    <td><strong>{control_id}</strong></td>
                    <td>{control_data['name']}</td>
                    <td>{status}</td>
                    <td>{control_data['total_findings']}</td>
                    <td>{scanners}</td>
                </tr>
"""

        html += f"""
            </tbody>
        </table>

        <div class="footer">
            <p>Generated by Hardening Workflows ATO Compliance Automation</p>
            <p>Report Format: HTML | OSCAL Version: 1.0.4</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def _get_ato_recommendation(self) -> Dict[str, Any]:
        """Determine ATO recommendation based on findings"""
        total_critical = sum(s['critical'] for s in self.scan_results.values())
        total_high = sum(s['high'] for s in self.scan_results.values())

        if total_critical > 0:
            return {
                'status': 'NOT_READY',
                'reason': f'{total_critical} critical findings must be remediated',
                'action': 'Remediate all critical findings before ATO approval'
            }
        elif total_high > 0:
            return {
                'status': 'CONDITIONAL',
                'reason': f'{total_high} high severity findings require review',
                'action': 'Review high severity findings and obtain risk acceptance if needed'
            }
        else:
            return {
                'status': 'READY',
                'reason': 'No critical or high severity findings detected',
                'action': 'System meets automated security requirements for ATO consideration'
            }

    def save_reports(self):
        """Save reports in requested format(s)"""
        print(f"\n📝 Generating compliance reports in {self.output_format} format...")

        formats = self.output_format.split(',')

        for fmt in formats:
            fmt = fmt.strip().lower()

            if fmt in ['oscal', 'oscal-json']:
                oscal_ar = self.generate_oscal_assessment_results()
                oscal_path = self.output_dir / 'oscal-assessment-results.json'
                with open(oscal_path, 'w') as f:
                    json.dump(oscal_ar, f, indent=2)
                print(f"✅ OSCAL Assessment Results: {oscal_path}")

            if fmt == 'markdown':
                md_report = self.generate_markdown_report()
                md_path = self.output_dir / 'ato-compliance-report.md'
                with open(md_path, 'w') as f:
                    f.write(md_report)
                print(f"✅ Markdown Report: {md_path}")

            if fmt == 'json':
                json_report = self.generate_json_report()
                json_path = self.output_dir / 'ato-compliance-report.json'
                with open(json_path, 'w') as f:
                    json.dump(json_report, f, indent=2)
                print(f"✅ JSON Report: {json_path}")

            if fmt == 'csv':
                csv_report = self.generate_csv_report()
                csv_path = self.output_dir / 'ato-compliance-report.csv'
                with open(csv_path, 'w') as f:
                    f.write(csv_report)
                print(f"✅ CSV Report: {csv_path}")

            if fmt == 'html':
                html_report = self.generate_html_report()
                html_path = self.output_dir / 'ato-compliance-report.html'
                with open(html_path, 'w') as f:
                    f.write(html_report)
                print(f"✅ HTML Report: {html_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate ATO compliance reports from security scan results'
    )
    parser.add_argument(
        '--mapping-file',
        default=os.getenv('COMPLIANCE_MAPPING_FILE', 'config/nist-800-53-mapping.json'),
        help='Path to NIST 800-53 mapping configuration file'
    )
    parser.add_argument(
        '--output-dir',
        default=os.getenv('COMPLIANCE_REPORT_DIR', './compliance-reports'),
        help='Output directory for compliance reports'
    )
    parser.add_argument(
        '--format',
        default=os.getenv('COMPLIANCE_REPORT_FORMAT', 'oscal,markdown'),
        choices=ATOComplianceReportGenerator.SUPPORTED_FORMATS + ['all'],
        help='Output format(s) - comma-separated or "all"'
    )
    parser.add_argument(
        '--sarif-pattern',
        default='**/*.sarif',
        help='Glob pattern for finding SARIF files'
    )

    args = parser.parse_args()

    # Handle 'all' format option
    if args.format == 'all':
        args.format = ','.join(ATOComplianceReportGenerator.SUPPORTED_FORMATS)

    print("🚀 ATO Compliance Report Generator")
    print(f"📋 Mapping File: {args.mapping_file}")
    print(f"📁 Output Directory: {args.output_dir}")
    print(f"📊 Output Format(s): {args.format}")
    print("")

    try:
        generator = ATOComplianceReportGenerator(
            args.mapping_file,
            args.output_dir,
            args.format
        )

        generator.load_sarif_results(args.sarif_pattern)
        generator.save_reports()

        print("\n✅ ATO compliance reports generated successfully!")
        print(f"📂 Reports saved to: {args.output_dir}")

        # Print ATO recommendation
        recommendation = generator._get_ato_recommendation()
        print(f"\n🎯 ATO Recommendation: {recommendation['status']}")
        print(f"   {recommendation['reason']}")
        print(f"   Action: {recommendation['action']}")

        return 0

    except Exception as e:
        print(f"\n❌ Error generating compliance reports: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
