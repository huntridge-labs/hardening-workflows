"""Bandit Python security scanner."""

import json

import dagger
from dagger import dag

from models import Finding, ScanResult, Severity
from scanners.base import BaseScanner


class BanditScanner(BaseScanner):
    """Bandit - Python security linter."""

    name = "bandit"
    description = "Python security vulnerability scanner"

    async def scan(
        self,
        source: dagger.Directory,
        exclude_dirs: str = ".git,.venv,node_modules,__pycache__",
        log_level: str = "info",
        **kwargs,
    ) -> ScanResult:
        """Run Bandit security scan on Python code."""
        self._init_logger(log_level)
        self.log.hardening_info("Starting Bandit scan")

        image = "python:3.12-slim"
        self.log.dagger_info("Creating container", image=image)

        container = (
            dag.container()
            .from_(image)
            .with_exec(["pip", "install", "--no-cache-dir", "bandit[toml,sarif]>=1.7.5"])
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )
        self.log.container_debug("Container configured", workdir="/src", exclude_dirs=exclude_dirs)

        # Run scans - SARIF for GitHub integration, JSON for parsing
        sarif_cmd = [
            "bandit", "-r", ".", "--exclude", exclude_dirs,
            "-f", "sarif", "-o", "/reports/bandit.sarif", "--exit-zero",
        ]
        json_cmd = [
            "bandit", "-r", ".", "--exclude", exclude_dirs,
            "-f", "json", "-o", "/reports/bandit.json", "--exit-zero",
        ]

        self.log.scanner_debug("Executing SARIF scan", command=" ".join(sarif_cmd))
        container = container.with_exec(sarif_cmd)

        self.log.scanner_debug("Executing JSON scan", command=" ".join(json_cmd))
        container = container.with_exec(json_cmd)

        # Get JSON output for parsing
        findings = []
        try:
            self.log.scanner_info("Parsing scan results")
            json_content = await container.file("/reports/bandit.json").contents()
            findings = self.parse_findings(json_content)
            self.log.scanner_info("Scan completed", findings_count=len(findings))
        except Exception as e:
            self.log.scanner_error("Failed to parse results", error=str(e))

        # Log findings summary
        if findings:
            severity_counts = {}
            for f in findings:
                sev = f.severity.name
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            self.log.hardening_warn("Security issues found", count=len(findings), by_severity=severity_counts)
        else:
            self.log.hardening_info("No security issues found")

        reports = container.directory("/reports")
        reports = self._add_logs_to_artifacts(reports)

        return ScanResult(
            scanner=self.name,
            findings=findings,
            artifacts=reports,
            exit_code=0 if not findings else 1,
        )

    def parse_findings(self, output: str) -> list[Finding]:
        """Parse Bandit JSON output into findings."""
        findings = []
        try:
            data = json.loads(output)
            for result in data.get("results", []):
                severity = self._map_severity(result.get("issue_severity", "LOW"))
                cwe_data = result.get("issue_cwe", {})
                cwe = f"CWE-{cwe_data.get('id')}" if cwe_data.get("id") else None

                findings.append(
                    Finding(
                        rule_id=result.get("test_id", "UNKNOWN"),
                        severity=severity,
                        message=result.get("issue_text", ""),
                        file_path=result.get("filename", "").lstrip("./"),
                        line_number=result.get("line_number", 0),
                        scanner=self.name,
                        cwe=cwe,
                    )
                )
        except json.JSONDecodeError:
            pass
        return findings

    def _map_severity(self, bandit_severity: str) -> Severity:
        """Map Bandit severity to standard severity."""
        mapping = {
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
        }
        return mapping.get(bandit_severity.upper(), Severity.LOW)
