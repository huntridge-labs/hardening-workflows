"""Grype vulnerability scanner."""

import json
import dagger
from dagger import dag

from .base import BaseScanner
from ..models import ScanResult, Finding, Severity


class GrypeScanner(BaseScanner):
    """Grype - vulnerability scanner for container images and filesystems."""

    name = "grype"
    description = "Scan for vulnerabilities in dependencies and container images"

    async def scan(
        self,
        source: dagger.Directory,
        image_ref: str | None = None,
        **kwargs,
    ) -> ScanResult:
        """Run Grype vulnerability scan."""
        container = (
            dag.container()
            .from_("anchore/grype:latest")
            .with_exec(["mkdir", "-p", "/reports"])
        )

        # Determine scan target
        if image_ref:
            target = image_ref
        else:
            # Scan filesystem
            container = container.with_mounted_directory("/src", source)
            target = "dir:/src"

        # SARIF output
        container = container.with_exec(
            [
                "grype", target,
                "--output", "sarif",
                "--file", "/reports/grype.sarif",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # JSON output for parsing
        container = container.with_exec(
            [
                "grype", target,
                "--output", "json",
                "--file", "/reports/grype.json",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # Parse findings
        try:
            json_content = await container.file("/reports/grype.json").contents()
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
        """Parse Grype JSON output into findings."""
        findings = []
        try:
            data = json.loads(output)
            for match in data.get("matches", []):
                vuln = match.get("vulnerability", {})
                artifact = match.get("artifact", {})
                severity = Severity.from_string(vuln.get("severity", "LOW"))

                # Get CVSS score if available
                cvss_score = None
                for cvss in vuln.get("cvss", []):
                    if cvss.get("version", "").startswith("3"):
                        cvss_score = cvss.get("metrics", {}).get("baseScore")
                        break

                findings.append(Finding(
                    rule_id=vuln.get("id", "UNKNOWN"),
                    severity=severity,
                    message=f"{artifact.get('name', '')}@{artifact.get('version', '')}: {vuln.get('description', '')[:100]}",
                    file_path=artifact.get("locations", [{}])[0].get("path", ""),
                    line_number=0,
                    scanner=self.name,
                    cvss_score=cvss_score,
                ))
        except json.JSONDecodeError:
            pass
        return findings
