"""Checkov IaC security scanner."""

import json
import dagger
from dagger import dag

from .base import BaseScanner
from ..models import ScanResult, Finding, Severity


class CheckovScanner(BaseScanner):
    """Checkov - Infrastructure as Code security scanner."""

    name = "checkov"
    description = "Policy-as-code scanner for Terraform, CloudFormation, Kubernetes, etc."

    async def scan(
        self,
        source: dagger.Directory,
        iac_path: str = ".",
        framework: str | None = None,
        **kwargs,
    ) -> ScanResult:
        """Run Checkov IaC scan."""
        container = (
            dag.container()
            .from_("bridgecrew/checkov:latest")
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )

        scan_path = iac_path if iac_path else "."

        # Build command
        cmd = [
            "checkov",
            "-d", scan_path,
            "--output", "sarif",
            "--output-file-path", "/reports/",
            "--soft-fail",  # Don't exit non-zero on findings
        ]

        if framework:
            cmd.extend(["--framework", framework])

        container = container.with_exec(cmd)

        # Also generate JSON
        json_cmd = [
            "checkov",
            "-d", scan_path,
            "--output", "json",
            "--output-file-path", "/reports/",
            "--soft-fail",
        ]
        if framework:
            json_cmd.extend(["--framework", framework])

        container = container.with_exec(json_cmd)

        # Parse findings
        try:
            # Checkov outputs to results_sarif.sarif and results_json.json
            json_content = await container.file("/reports/results_json.json").contents()
            findings = self.parse_findings(json_content)
        except Exception:
            findings = []

        reports = container.directory("/reports")

        return ScanResult(
            scanner=self.name,
            findings=findings,
            artifacts=reports,
            exit_code=0,
        )

    def parse_findings(self, output: str) -> list[Finding]:
        """Parse Checkov JSON output into findings."""
        findings = []
        try:
            data = json.loads(output)

            # Checkov can return a list or dict depending on frameworks scanned
            results_list = data if isinstance(data, list) else [data]

            for results in results_list:
                for check in results.get("results", {}).get("failed_checks", []):
                    severity = self._map_severity(check.get("check_result", {}).get("severity"))
                    findings.append(Finding(
                        rule_id=check.get("check_id", "UNKNOWN"),
                        severity=severity,
                        message=check.get("check_name", ""),
                        file_path=check.get("file_path", "").lstrip("/"),
                        line_number=check.get("file_line_range", [0])[0],
                        scanner=self.name,
                    ))
        except json.JSONDecodeError:
            pass
        return findings

    def _map_severity(self, checkov_severity: str | None) -> Severity:
        """Map Checkov severity to standard severity."""
        if not checkov_severity:
            return Severity.MEDIUM  # Default for Checkov

        mapping = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
        }
        return mapping.get(checkov_severity.upper(), Severity.MEDIUM)
