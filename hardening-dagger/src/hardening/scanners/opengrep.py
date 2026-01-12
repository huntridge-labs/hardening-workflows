"""OpenGrep (Semgrep) SAST scanner."""

import json
import dagger
from dagger import dag

from .base import BaseScanner
from ..models import ScanResult, Finding, Severity


class OpenGrepScanner(BaseScanner):
    """OpenGrep/Semgrep - Static Application Security Testing."""

    name = "opengrep"
    description = "SAST scanner using Semgrep rules"

    async def scan(
        self,
        source: dagger.Directory,
        config: str = "auto",
        **kwargs,
    ) -> ScanResult:
        """Run OpenGrep/Semgrep scan."""
        container = (
            dag.container()
            .from_("semgrep/semgrep:latest")
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )

        # SARIF output
        container = container.with_exec(
            [
                "semgrep", "scan",
                "--config", config,
                "--sarif",
                "--output", "/reports/opengrep.sarif",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # JSON output for parsing
        container = container.with_exec(
            [
                "semgrep", "scan",
                "--config", config,
                "--json",
                "--output", "/reports/opengrep.json",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # Parse findings
        try:
            json_content = await container.file("/reports/opengrep.json").contents()
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

                findings.append(Finding(
                    rule_id=result.get("check_id", "UNKNOWN"),
                    severity=severity,
                    message=result.get("extra", {}).get("message", ""),
                    file_path=result.get("path", "").lstrip("./"),
                    line_number=result.get("start", {}).get("line", 0),
                    scanner=self.name,
                    cwe=cwe,
                ))
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
