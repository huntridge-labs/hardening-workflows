"""Gitleaks secrets scanner."""

import json
import dagger
from dagger import dag

from .base import BaseScanner
from ..models import ScanResult, Finding, Severity


class GitleaksScanner(BaseScanner):
    """Gitleaks - secrets detection scanner."""

    name = "gitleaks"
    description = "Detect secrets and sensitive data in code"

    async def scan(
        self,
        source: dagger.Directory,
        config_path: str | None = None,
        **kwargs,
    ) -> ScanResult:
        """Run Gitleaks secrets detection."""
        # TODO: Consider pinning to a specific Gitleaks version
        container = (
            dag.container()
            .from_("zricethezav/gitleaks:latest")
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )

        # Build command
        # TODO: Support git history scanning
        base_cmd = [
            "gitleaks", "detect",
            "--source", ".",
            "--no-git",  # Scan files, not git history (for mounted dirs)
        ]

        if config_path:
            base_cmd.extend(["--config", config_path])

        # SARIF output
        sarif_cmd = base_cmd + [
            "--report-format", "sarif",
            "--report-path", "/reports/gitleaks.sarif",
            "--exit-code", "0",
        ]

        # JSON output for parsing
        json_cmd = base_cmd + [
            "--report-format", "json",
            "--report-path", "/reports/gitleaks.json",
            "--exit-code", "0",
        ]

        container = container.with_exec(sarif_cmd)
        container = container.with_exec(json_cmd)

        # Parse findings
        try:
            json_content = await container.file("/reports/gitleaks.json").contents()
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
        """Parse Gitleaks JSON output into findings."""
        findings = []
        try:
            data = json.loads(output)
            if not isinstance(data, list):
                return findings

            for result in data:
                findings.append(Finding(
                    rule_id=result.get("RuleID", "secret-detected"),
                    severity=Severity.HIGH,  # Secrets are always high severity
                    message=f"Secret detected: {result.get('Description', 'Potential secret')}",
                    file_path=result.get("File", "").lstrip("./"),
                    line_number=result.get("StartLine", 0),
                    scanner=self.name,
                ))
        except json.JSONDecodeError:
            pass
        return findings
