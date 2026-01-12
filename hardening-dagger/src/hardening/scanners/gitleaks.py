"""Gitleaks secrets scanner."""

import json

import dagger
from dagger import dag

from models import Finding, ScanResult, Severity
from scanners.base import BaseScanner


class GitleaksScanner(BaseScanner):
    """Gitleaks - secrets detection scanner."""

    name = "gitleaks"
    description = "Detect secrets and sensitive data in code"

    async def scan(
        self,
        source: dagger.Directory,
        config_path: str | None = None,
        log_level: str = "info",
        **kwargs,
    ) -> ScanResult:
        """Run Gitleaks secrets detection."""
        # Initialize logger for this scan
        self._init_logger(log_level)
        self.log.hardening_info("Starting Gitleaks scan")

        # Use official gitleaks image but clear the entrypoint to allow shell commands
        image = "zricethezav/gitleaks:v8.18.4"
        self.log.dagger_info("Creating container", image=image)

        container = (
            dag.container()
            .from_(image)
            .with_entrypoint([])  # Clear entrypoint to allow arbitrary commands
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )
        self.log.container_debug("Container configured", workdir="/src", reports_dir="/reports")

        # Build command
        base_cmd = [
            "gitleaks",
            "detect",
            "--source",
            ".",
            "--no-git",  # Scan files, not git history (for mounted dirs)
        ]

        if config_path:
            base_cmd.extend(["--config", config_path])
            self.log.scanner_info("Using custom config", config_path=config_path)

        # SARIF output
        sarif_cmd = base_cmd + [
            "--report-format",
            "sarif",
            "--report-path",
            "/reports/gitleaks.sarif",
            "--exit-code",
            "0",
        ]

        # JSON output for parsing
        json_cmd = base_cmd + [
            "--report-format",
            "json",
            "--report-path",
            "/reports/gitleaks.json",
            "--exit-code",
            "0",
        ]

        self.log.scanner_debug("Executing SARIF scan", command=" ".join(sarif_cmd))
        container = container.with_exec(sarif_cmd, expect=dagger.ReturnType.ANY)

        self.log.scanner_debug("Executing JSON scan", command=" ".join(json_cmd))
        container = container.with_exec(json_cmd, expect=dagger.ReturnType.ANY)

        # Parse findings
        findings = []
        try:
            self.log.scanner_info("Parsing scan results")
            json_content = await container.file("/reports/gitleaks.json").contents()
            findings = self.parse_findings(json_content)
            self.log.scanner_info("Scan completed", findings_count=len(findings))
        except Exception as e:
            self.log.scanner_error("Failed to parse results", error=str(e))
            findings = []

        # Log summary of findings
        if findings:
            self.log.hardening_warn(
                "Secrets detected",
                count=len(findings),
                files=list(set(f.file_path for f in findings)),
            )
        else:
            self.log.hardening_info("No secrets detected")

        # Get reports and add logs
        reports = container.directory("/reports")
        reports = self._add_logs_to_artifacts(reports)

        return ScanResult(
            scanner=self.name,
            findings=findings,
            artifacts=reports,
            exit_code=0 if not findings else 1,
        )

    def parse_findings(self, output: str) -> list[Finding]:
        """Parse Gitleaks JSON output into findings."""
        findings = []
        try:
            data = json.loads(output)
            if not isinstance(data, list):
                return findings

            for result in data:
                findings.append(
                    Finding(
                        rule_id=result.get("RuleID", "secret-detected"),
                        severity=Severity.HIGH,  # Secrets are always high severity
                        message=f"Secret detected: {result.get('Description', 'Potential secret')}",
                        file_path=result.get("File", "").lstrip("./"),
                        line_number=result.get("StartLine", 0),
                        scanner=self.name,
                    )
                )
        except json.JSONDecodeError:
            pass
        return findings
