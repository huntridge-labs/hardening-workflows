"""Grype vulnerability scanner."""

import json

import dagger
from dagger import dag

from models import Finding, ScanResult, Severity
from scanners.base import BaseScanner


class GrypeScanner(BaseScanner):
    """Grype - vulnerability scanner for container images and filesystems."""

    name = "grype"
    description = "Scan for vulnerabilities in dependencies and container images"

    async def scan(
        self,
        source: dagger.Directory,
        image_ref: str | None = None,
        log_level: str = "info",
        **kwargs,
    ) -> ScanResult:
        """Run Grype vulnerability scan."""
        self._init_logger(log_level)
        self.log.hardening_info("Starting Grype vulnerability scan")

        image = "anchore/grype:latest"
        self.log.dagger_info("Creating container", image=image)

        container = (
            dag.container().from_(image).with_exec(["mkdir", "-p", "/reports"])
        )

        # Determine scan target
        if image_ref:
            target = image_ref
            self.log.container_debug("Scanning container image", target=target)
        else:
            # Scan filesystem
            container = container.with_mounted_directory("/src", source)
            target = "dir:/src"
            self.log.container_debug("Scanning filesystem", target=target)

        # SARIF output
        sarif_cmd = ["grype", target, "--output", "sarif", "--file", "/reports/grype.sarif"]
        self.log.scanner_debug("Executing SARIF scan", command=" ".join(sarif_cmd))
        container = container.with_exec(sarif_cmd, expect=dagger.ReturnType.ANY)

        # JSON output for parsing
        json_cmd = ["grype", target, "--output", "json", "--file", "/reports/grype.json"]
        self.log.scanner_debug("Executing JSON scan", command=" ".join(json_cmd))
        container = container.with_exec(json_cmd, expect=dagger.ReturnType.ANY)

        # Parse findings
        findings = []
        try:
            self.log.scanner_info("Parsing scan results")
            json_content = await container.file("/reports/grype.json").contents()
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
                "Vulnerabilities found", count=len(findings), by_severity=severity_counts
            )
        else:
            self.log.hardening_info("No vulnerabilities found")

        reports = container.directory("/reports")
        reports = self._add_logs_to_artifacts(reports)

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

                desc = vuln.get("description", "")[:100]
                findings.append(
                    Finding(
                        rule_id=vuln.get("id", "UNKNOWN"),
                        severity=severity,
                        message=f"{artifact.get('name', '')}@{artifact.get('version', '')}: {desc}",
                        file_path=artifact.get("locations", [{}])[0].get("path", ""),
                        line_number=0,
                        scanner=self.name,
                        cvss_score=cvss_score,
                    )
                )
        except json.JSONDecodeError:
            pass
        return findings
