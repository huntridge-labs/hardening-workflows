"""Trivy security scanner (IaC and Container)."""

import json

import dagger
from dagger import dag

from ..models import Finding, ScanResult, Severity
from .base import BaseScanner


class TrivyIacScanner(BaseScanner):
    """Trivy - Infrastructure as Code scanner."""

    name = "trivy-iac"
    description = "Scan Terraform, CloudFormation, Kubernetes manifests for misconfigurations"

    async def scan(
        self,
        source: dagger.Directory,
        iac_path: str = ".",
        **kwargs,
    ) -> ScanResult:
        """Run Trivy IaC scan."""
        # TODO: Consider pinning to a specific Trivy version
        container = (
            dag.container()
            .from_("aquasec/trivy:latest")
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )

        scan_path = f"/src/{iac_path}" if iac_path != "." else "/src"

        # SARIF output
        container = container.with_exec(
            [
                "trivy",
                "config",
                scan_path,
                "--format",
                "sarif",
                "--output",
                "/reports/trivy-iac.sarif",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # JSON output for parsing
        container = container.with_exec(
            [
                "trivy",
                "config",
                scan_path,
                "--format",
                "json",
                "--output",
                "/reports/trivy-iac.json",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # Parse findings
        try:
            json_content = await container.file("/reports/trivy-iac.json").contents()
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
        """Parse Trivy JSON output into findings."""
        findings = []
        try:
            data = json.loads(output)
            for result in data.get("Results", []):
                target = result.get("Target", "")
                for misconfig in result.get("Misconfigurations", []):
                    severity = self._map_severity(misconfig.get("Severity", "LOW"))
                    findings.append(
                        Finding(
                            rule_id=misconfig.get("ID", "UNKNOWN"),
                            severity=severity,
                            message=misconfig.get("Title", misconfig.get("Message", "")),
                            file_path=target.lstrip("./"),
                            line_number=misconfig.get("CauseMetadata", {}).get("StartLine", 0),
                            scanner=self.name,
                        )
                    )
        except json.JSONDecodeError:
            pass
        return findings

    def _map_severity(self, trivy_severity: str) -> Severity:
        """Map Trivy severity to standard severity."""
        mapping = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
        }
        return mapping.get(trivy_severity.upper(), Severity.LOW)


class TrivyContainerScanner(BaseScanner):
    """Trivy - Container image vulnerability scanner."""

    name = "trivy-container"
    description = "Scan container images for vulnerabilities"

    async def scan(
        self,
        source: dagger.Directory,
        image_ref: str = "",
        **kwargs,
    ) -> ScanResult:
        """Run Trivy container scan."""
        if not image_ref:
            # Try to detect Dockerfile and build, or skip
            return ScanResult(
                scanner=self.name,
                findings=[],
                artifacts=dag.directory(),
                exit_code=0,
                error_message="No image_ref provided",
            )

        container = (
            dag.container().from_("aquasec/trivy:latest").with_exec(["mkdir", "-p", "/reports"])
        )

        # SARIF output
        container = container.with_exec(
            [
                "trivy",
                "image",
                image_ref,
                "--format",
                "sarif",
                "--output",
                "/reports/trivy-container.sarif",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # JSON output
        container = container.with_exec(
            [
                "trivy",
                "image",
                image_ref,
                "--format",
                "json",
                "--output",
                "/reports/trivy-container.json",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        try:
            json_content = await container.file("/reports/trivy-container.json").contents()
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
        """Parse Trivy container JSON output."""
        findings = []
        try:
            data = json.loads(output)
            for result in data.get("Results", []):
                target = result.get("Target", "")
                for vuln in result.get("Vulnerabilities", []):
                    severity = Severity.from_string(vuln.get("Severity", "LOW"))
                    findings.append(
                        Finding(
                            rule_id=vuln.get("VulnerabilityID", "UNKNOWN"),
                            severity=severity,
                            message=f"{vuln.get('PkgName', '')}: {vuln.get('Title', '')}",
                            file_path=target,
                            line_number=0,
                            scanner=self.name,
                            cvss_score=vuln.get("CVSS", {}).get("nvd", {}).get("V3Score"),
                        )
                    )
        except json.JSONDecodeError:
            pass
        return findings
