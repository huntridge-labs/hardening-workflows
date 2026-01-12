"""Bandit Python security scanner."""

import json

import dagger
from dagger import dag

from ..models import Finding, ScanResult, Severity
from .base import BaseScanner


class BanditScanner(BaseScanner):
    """Bandit - Python security linter."""

    name = "bandit"
    description = "Python security vulnerability scanner"

    async def scan(
        self,
        source: dagger.Directory,
        exclude_dirs: str = ".git,.venv,node_modules,__pycache__",
        **kwargs,
    ) -> ScanResult:
        """Run Bandit security scan on Python code."""
        container = (
            dag.container()
            .from_("python:3.12-slim")
            .with_exec(["pip", "install", "--no-cache-dir", "bandit[toml,sarif]>=1.7.5"])
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )

        # Run scans - SARIF for GitHub integration, JSON for parsing
        container = container.with_exec(
            [
                "bandit",
                "-r",
                ".",
                "--exclude",
                exclude_dirs,
                "-f",
                "sarif",
                "-o",
                "/reports/bandit.sarif",
                "--exit-zero",
            ],
        )

        container = container.with_exec(
            [
                "bandit",
                "-r",
                ".",
                "--exclude",
                exclude_dirs,
                "-f",
                "json",
                "-o",
                "/reports/bandit.json",
                "--exit-zero",
            ],
        )

        # Get JSON output for parsing
        json_content = await container.file("/reports/bandit.json").contents()
        findings = self.parse_findings(json_content)

        reports = container.directory("/reports")

        return ScanResult(
            scanner=self.name,
            findings=findings,
            artifacts=reports,
            exit_code=0,
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
