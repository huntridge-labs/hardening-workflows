"""Checkov IaC security scanner."""

import json

import dagger
from dagger import dag

from models import Finding, ScanResult, Severity
from scanners.base import BaseScanner


class CheckovScanner(BaseScanner):
    """Checkov - Infrastructure as Code security scanner."""

    name = "checkov"
    description = "Policy-as-code scanner for Terraform, CloudFormation, Kubernetes, etc."

    async def scan(
        self,
        source: dagger.Directory,
        iac_path: str = ".",
        framework: str | None = None,
        log_level: str = "info",
        **kwargs,
    ) -> ScanResult:
        """Run Checkov IaC scan."""
        self._init_logger(log_level)
        self.log.hardening_info("Starting Checkov IaC scan")

        image = "bridgecrew/checkov:latest"
        self.log.dagger_info("Creating container", image=image)

        container = (
            dag.container()
            .from_(image)
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )

        scan_path = iac_path if iac_path else "."
        self.log.container_debug(
            "Container configured", workdir="/src", scan_path=scan_path, framework=framework
        )

        # Build SARIF command
        cmd = [
            "checkov", "-d", scan_path,
            "--output", "sarif",
            "--output-file-path", "/reports/",
            "--soft-fail",
        ]
        if framework:
            cmd.extend(["--framework", framework])

        self.log.scanner_debug("Executing SARIF scan", command=" ".join(cmd))
        container = container.with_exec(cmd)

        # Also generate JSON
        json_cmd = [
            "checkov", "-d", scan_path,
            "--output", "json",
            "--output-file-path", "/reports/",
            "--soft-fail",
        ]
        if framework:
            json_cmd.extend(["--framework", framework])

        self.log.scanner_debug("Executing JSON scan", command=" ".join(json_cmd))
        container = container.with_exec(json_cmd)

        # Parse findings
        findings = []
        try:
            self.log.scanner_info("Parsing scan results")
            # Checkov outputs to results_sarif.sarif and results_json.json
            json_content = await container.file("/reports/results_json.json").contents()
            findings = self.parse_findings(json_content)
            self.log.scanner_info("Scan completed", findings_count=len(findings))
        except Exception as e:
            self.log.scanner_error("Failed to parse results", error=str(e))

        if findings:
            severity_counts = {}
            for f in findings:
                sev = f.severity.name
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            self.log.hardening_warn(
                "Policy violations found", count=len(findings), by_severity=severity_counts
            )
        else:
            self.log.hardening_info("No policy violations found")

        reports = container.directory("/reports")
        reports = self._add_logs_to_artifacts(reports)

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
                    findings.append(
                        Finding(
                            rule_id=check.get("check_id", "UNKNOWN"),
                            severity=severity,
                            message=check.get("check_name", ""),
                            file_path=check.get("file_path", "").lstrip("/"),
                            line_number=check.get("file_line_range", [0])[0],
                            scanner=self.name,
                        )
                    )
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
