"""ClamAV malware scanner."""

import re

import dagger
from dagger import dag

from models import Finding, ScanResult, Severity
from scanners.base import BaseScanner


class ClamAVScanner(BaseScanner):
    """ClamAV - Open source antivirus/malware scanner."""

    name = "clamav"
    description = "Scan for malware, viruses, and trojans"

    async def scan(
        self,
        source: dagger.Directory,
        scan_path: str = ".",
        log_level: str = "info",
        **kwargs,
    ) -> ScanResult:
        """Run ClamAV malware scan."""
        self._init_logger(log_level)
        self.log.hardening_info("Starting ClamAV malware scan")

        image = "clamav/clamav:latest"
        self.log.dagger_info("Creating container", image=image)

        container = (
            dag.container()
            .from_(image)
            .with_mounted_directory("/src", source)
            .with_exec(["mkdir", "-p", "/reports"])
        )

        # Update virus definitions
        self.log.scanner_info("Updating virus definitions")
        container = container.with_exec(
            ["freshclam", "--quiet"],
            expect=dagger.ReturnType.ANY,
        )

        target_path = f"/src/{scan_path}" if scan_path != "." else "/src"
        self.log.container_debug("Container configured", scan_path=target_path)

        # Run scan
        scan_cmd = [
            "clamscan", "-r", target_path,
            "--infected", "--log=/reports/clamav.log", "--no-summary",
        ]
        self.log.scanner_debug("Executing scan", command=" ".join(scan_cmd))
        container = container.with_exec(scan_cmd, expect=dagger.ReturnType.ANY)

        # Also get summary
        summary_cmd = ["clamscan", "-r", target_path, "--infected", "-o"]
        self.log.scanner_debug("Executing summary scan", command=" ".join(summary_cmd))
        container = container.with_exec(summary_cmd, expect=dagger.ReturnType.ANY)

        # Parse findings from log
        findings = []
        try:
            self.log.scanner_info("Parsing scan results")
            log_content = await container.file("/reports/clamav.log").contents()
            findings = self.parse_findings(log_content)
            self.log.scanner_info("Scan completed", findings_count=len(findings))
        except Exception as e:
            self.log.scanner_error("Failed to parse results", error=str(e))

        if findings:
            self.log.hardening_warn(
                "Malware detected",
                count=len(findings),
                signatures=list(set(f.rule_id for f in findings)),
            )
        else:
            self.log.hardening_info("No malware detected")

        # Create a simple JSON report for consistency
        json_report = self._create_json_report(findings)
        container = container.with_new_file("/reports/clamav.json", json_report)

        reports = container.directory("/reports")
        reports = self._add_logs_to_artifacts(reports)

        return ScanResult(
            scanner=self.name,
            findings=findings,
            artifacts=reports,
            exit_code=0,
        )

    def parse_findings(self, output: str) -> list[Finding]:
        """Parse ClamAV log output into findings."""
        findings = []

        # ClamAV output format: /path/to/file: SignatureName FOUND
        pattern = r"^(.+?):\s+(.+?)\s+FOUND$"

        for line in output.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                file_path = match.group(1)
                if file_path.startswith("/src/"):
                    file_path = file_path[5:]  # Remove /src/ prefix
                signature = match.group(2)

                findings.append(
                    Finding(
                        rule_id=signature,
                        severity=Severity.CRITICAL,  # Malware is always critical
                        message=f"Malware detected: {signature}",
                        file_path=file_path,
                        line_number=0,
                        scanner=self.name,
                    )
                )

        return findings

    def _create_json_report(self, findings: list[Finding]) -> str:
        """Create JSON report from findings."""
        import json

        return json.dumps(
            {
                "scanner": self.name,
                "findings": [f.to_dict() for f in findings],
                "total": len(findings),
            },
            indent=2,
        )
