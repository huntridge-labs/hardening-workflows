"""ClamAV malware scanner."""

import re
import dagger
from dagger import dag

from .base import BaseScanner
from ..models import ScanResult, Finding, Severity


class ClamAVScanner(BaseScanner):
    """ClamAV - Open source antivirus/malware scanner."""

    name = "clamav"
    description = "Scan for malware, viruses, and trojans"

    async def scan(
        self,
        source: dagger.Directory,
        scan_path: str = ".",
        **kwargs,
    ) -> ScanResult:
        """Run ClamAV malware scan."""
        container = (
            dag.container()
            .from_("clamav/clamav:latest")
            .with_mounted_directory("/src", source)
            .with_exec(["mkdir", "-p", "/reports"])
        )

        # Update virus definitions
        container = container.with_exec(
            ["freshclam", "--quiet"],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        target_path = f"/src/{scan_path}" if scan_path != "." else "/src"

        # Run scan
        container = container.with_exec(
            [
                "clamscan",
                "-r", target_path,
                "--infected",
                "--log=/reports/clamav.log",
                "--no-summary",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,  # ClamAV exits 1 on findings
        )

        # Also get summary
        container = container.with_exec(
            [
                "clamscan",
                "-r", target_path,
                "--infected",
                "-o",  # Only print infected files
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # Parse findings from log
        try:
            log_content = await container.file("/reports/clamav.log").contents()
            findings = self.parse_findings(log_content)
        except Exception:
            findings = []

        # Create a simple JSON report for consistency
        json_report = self._create_json_report(findings)
        container = container.with_new_file("/reports/clamav.json", json_report)

        reports = container.directory("/reports")

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
                file_path = match.group(1).lstrip("/src/")
                signature = match.group(2)

                findings.append(Finding(
                    rule_id=signature,
                    severity=Severity.CRITICAL,  # Malware is always critical
                    message=f"Malware detected: {signature}",
                    file_path=file_path,
                    line_number=0,
                    scanner=self.name,
                ))

        return findings

    def _create_json_report(self, findings: list[Finding]) -> str:
        """Create JSON report from findings."""
        import json
        return json.dumps({
            "scanner": self.name,
            "findings": [f.to_dict() for f in findings],
            "total": len(findings),
        }, indent=2)
