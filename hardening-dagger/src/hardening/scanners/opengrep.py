"""OpenGrep (Semgrep) SAST scanner."""

import json

import dagger
from dagger import dag

from models import Finding, ScanResult, Severity
from scanners.base import BaseScanner


class OpenGrepScanner(BaseScanner):
    """OpenGrep/Semgrep - Static Application Security Testing."""

    name = "opengrep"
    description = "SAST scanner using Semgrep rules"

    async def scan(
        self,
        source: dagger.Directory,
        config: str = "auto",
        log_level: str = "info",
        **kwargs,
    ) -> ScanResult:
        """Run OpenGrep/Semgrep scan."""
        self._init_logger(log_level)
        self.log.hardening_info("Starting OpenGrep/Semgrep scan")

        image = "semgrep/semgrep:latest"
        self.log.dagger_info("Creating container", image=image)

        container = (
            dag.container()
            .from_(image)
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )
        self.log.container_debug("Container configured", workdir="/src", config=config)

        # SARIF output
        sarif_cmd = [
            "semgrep", "scan", "--config", config,
            "--sarif", "--output", "/reports/opengrep.sarif",
        ]
        self.log.scanner_debug("Executing SARIF scan", command=" ".join(sarif_cmd))
        container = container.with_exec(sarif_cmd, expect=dagger.ReturnType.ANY)

        # JSON output for parsing
        json_cmd = [
            "semgrep", "scan", "--config", config,
            "--json", "--output", "/reports/opengrep.json",
        ]
        self.log.scanner_debug("Executing JSON scan", command=" ".join(json_cmd))
        container = container.with_exec(json_cmd, expect=dagger.ReturnType.ANY)

        # Parse findings
        findings = []
        try:
            self.log.scanner_info("Parsing scan results")
            json_content = await container.file("/reports/opengrep.json").contents()
            findings = self.parse_findings(json_content)
            self.log.scanner_info("Scan completed", findings_count=len(findings))
        except Exception as e:
            self.log.scanner_error("Failed to parse results", error=str(e))

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
            exit_code=0,
        )

    def parse_findings(self, output: str) -> list[Finding]:
        """Parse Semgrep JSON output into findings."""
        findings = []
        try:
            data = json.loads(output)
            for result in data.get("results", []):
                severity = self._map_severity(result.get("extra", {}).get("severity", "WARNING"))

                # Extract CWE if present
                cwe = None
                metadata = result.get("extra", {}).get("metadata", {})
                cwe_list = metadata.get("cwe", [])
                if cwe_list:
                    cwe = cwe_list[0] if isinstance(cwe_list, list) else cwe_list

                findings.append(
                    Finding(
                        rule_id=result.get("check_id", "UNKNOWN"),
                        severity=severity,
                        message=result.get("extra", {}).get("message", ""),
                        file_path=result.get("path", "").lstrip("./"),
                        line_number=result.get("start", {}).get("line", 0),
                        scanner=self.name,
                        cwe=cwe,
                    )
                )
        except json.JSONDecodeError:
            pass
        return findings

    def _map_severity(self, semgrep_severity: str) -> Severity:
        """Map Semgrep severity to standard severity."""
        mapping = {
            "ERROR": Severity.HIGH,
            "WARNING": Severity.MEDIUM,
            "INFO": Severity.LOW,
        }
        return mapping.get(semgrep_severity.upper(), Severity.MEDIUM)
