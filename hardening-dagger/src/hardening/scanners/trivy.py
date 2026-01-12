"""Trivy security scanner (IaC and Container)."""

import json

import dagger
from dagger import dag

from models import Finding, ScanResult, Severity
from scanners.base import BaseScanner


class TrivyIacScanner(BaseScanner):
    """Trivy - Infrastructure as Code scanner."""

    name = "trivy-iac"
    description = "Scan Terraform, CloudFormation, Kubernetes manifests for misconfigurations"

    async def scan(
        self,
        source: dagger.Directory,
        iac_path: str = ".",
        log_level: str = "info",
        **kwargs,
    ) -> ScanResult:
        """Run Trivy IaC scan."""
        self._init_logger(log_level)
        self.log.hardening_info("Starting Trivy IaC scan")

        image = "aquasec/trivy:latest"
        self.log.dagger_info("Creating container", image=image)

        container = (
            dag.container()
            .from_(image)
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports"])
        )

        scan_path = f"/src/{iac_path}" if iac_path != "." else "/src"
        self.log.container_debug("Container configured", workdir="/src", scan_path=scan_path)

        # SARIF output
        sarif_cmd = ["trivy", "config", scan_path, "--format", "sarif", "--output", "/reports/trivy-iac.sarif"]
        self.log.scanner_debug("Executing SARIF scan", command=" ".join(sarif_cmd))
        container = container.with_exec(sarif_cmd, expect=dagger.ReturnType.ANY)

        # JSON output for parsing
        json_cmd = ["trivy", "config", scan_path, "--format", "json", "--output", "/reports/trivy-iac.json"]
        self.log.scanner_debug("Executing JSON scan", command=" ".join(json_cmd))
        container = container.with_exec(json_cmd, expect=dagger.ReturnType.ANY)

        # Parse findings
        findings = []
        try:
            self.log.scanner_info("Parsing scan results")
            json_content = await container.file("/reports/trivy-iac.json").contents()
            findings = self.parse_findings(json_content)
            self.log.scanner_info("Scan completed", findings_count=len(findings))
        except Exception as e:
            self.log.scanner_error("Failed to parse results", error=str(e))

        if findings:
            severity_counts = {}
            for f in findings:
                sev = f.severity.name
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            self.log.hardening_warn("Misconfigurations found", count=len(findings), by_severity=severity_counts)
        else:
            self.log.hardening_info("No misconfigurations found")

        reports = container.directory("/reports")
        reports = self._add_logs_to_artifacts(reports)

        return ScanResult(
            scanner=self.name,
            findings=findings,
            artifacts=reports,
            exit_code=0 if not findings else 1,
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
        log_level: str = "info",
        **kwargs,
    ) -> ScanResult:
        """Run Trivy container scan."""
        self._init_logger(log_level)
        self.log.hardening_info("Starting Trivy container scan")

        if not image_ref:
            self.log.hardening_warn("No image_ref provided, skipping scan")
            return ScanResult(
                scanner=self.name,
                findings=[],
                artifacts=dag.directory(),
                exit_code=0,
                error_message="No image_ref provided",
            )

        image = "aquasec/trivy:latest"
        self.log.dagger_info("Creating container", image=image)
        self.log.container_debug("Target image", image_ref=image_ref)

        container = (
            dag.container().from_(image).with_exec(["mkdir", "-p", "/reports"])
        )

        # SARIF output
        sarif_cmd = [
            "trivy", "image", image_ref,
            "--format", "sarif",
            "--output", "/reports/trivy-container.sarif",
        ]
        self.log.scanner_debug("Executing SARIF scan", command=" ".join(sarif_cmd))
        container = container.with_exec(sarif_cmd, expect=dagger.ReturnType.ANY)

        # JSON output
        json_cmd = [
            "trivy", "image", image_ref,
            "--format", "json",
            "--output", "/reports/trivy-container.json",
        ]
        self.log.scanner_debug("Executing JSON scan", command=" ".join(json_cmd))
        container = container.with_exec(json_cmd, expect=dagger.ReturnType.ANY)

        findings = []
        try:
            self.log.scanner_info("Parsing scan results")
            json_content = await container.file("/reports/trivy-container.json").contents()
            findings = self.parse_findings(json_content)
            self.log.scanner_info("Scan completed", findings_count=len(findings))
        except Exception as e:
            self.log.scanner_error("Failed to parse results", error=str(e))

        if findings:
            severity_counts = {}
            for f in findings:
                sev = f.severity.name
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            self.log.hardening_warn("Vulnerabilities found", count=len(findings), by_severity=severity_counts)
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
