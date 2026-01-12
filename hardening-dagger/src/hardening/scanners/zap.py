"""ZAP DAST (Dynamic Application Security Testing) scanner.

ZAP (Zed Attack Proxy) is used for scanning running web applications.
This scanner supports multiple modes:

1. URL mode: Scan an already-running application at a URL
2. Docker mode: Start a container, scan it, then stop it
3. Compose mode: Start a docker-compose stack, scan it, then stop it

Scan types:
- baseline: Passive scanning only (fast, safe)
- full: Active scanning (thorough, may modify data)
- api: OpenAPI/Swagger API scanning
"""

import json

import dagger
from dagger import dag

from ..models import Finding, ScanResult, Severity
from .base import BaseScanner


class ZAPScanner(BaseScanner):
    """ZAP - OWASP Zed Attack Proxy for DAST scanning."""

    name = "zap"
    description = "Dynamic application security testing for web applications"

    async def scan(
        self,
        source: dagger.Directory,
        target_url: str = "",
        scan_type: str = "baseline",
        api_spec: str = "",
        max_duration_minutes: int = 10,
        **kwargs,
    ) -> ScanResult:
        """
        Run ZAP DAST scan against a target URL.

        Args:
            source: Source directory (used for compose files if needed)
            target_url: URL of the running application to scan
            scan_type: Type of scan - baseline, full, or api
            api_spec: OpenAPI/Swagger spec URL (required for api scan type)
            max_duration_minutes: Maximum scan duration per target

        Returns:
            ScanResult with findings and artifacts

        Note: The target application must be running and accessible.
        For containerized apps, use the zap_with_container() function instead.
        """
        if not target_url and scan_type != "api":
            return ScanResult(
                scanner=self.name,
                findings=[],
                artifacts=dag.directory(),
                exit_code=1,
                error_message="target_url is required for baseline/full scans",
            )

        if scan_type == "api" and not api_spec:
            return ScanResult(
                scanner=self.name,
                findings=[],
                artifacts=dag.directory(),
                exit_code=1,
                error_message="api_spec is required for API scans",
            )

        # Use official ZAP stable image
        # TODO: Consider pinning to a specific ZAP version
        container = (
            dag.container()
            .from_("ghcr.io/zaproxy/zaproxy:stable")
            .with_exec(["mkdir", "-p", "/zap/reports"])
        )

        # Build ZAP command based on scan type
        if scan_type == "baseline":
            container = await self._run_baseline_scan(container, target_url, max_duration_minutes)
        elif scan_type == "full":
            container = await self._run_full_scan(container, target_url, max_duration_minutes)
        elif scan_type == "api":
            container = await self._run_api_scan(
                container, api_spec, target_url, max_duration_minutes
            )
        else:
            return ScanResult(
                scanner=self.name,
                findings=[],
                artifacts=dag.directory(),
                exit_code=1,
                error_message=f"Unknown scan_type: {scan_type}",
            )

        # Parse results - report may not exist if scan failed
        findings = []
        try:
            json_content = await container.file("/zap/reports/zap-report.json").contents()
            findings = self.parse_findings(json_content)
        except Exception:  # noqa: S110
            pass  # Report file may not exist if scan didn't complete

        # Collect artifacts
        reports = container.directory("/zap/reports")

        return ScanResult(
            scanner=self.name,
            findings=findings,
            artifacts=reports,
            exit_code=0,
        )

    async def scan_with_service(
        self,
        source: dagger.Directory,
        app_image: str,
        app_port: int = 8080,
        scan_type: str = "baseline",
        max_duration_minutes: int = 10,
        **kwargs,
    ) -> ScanResult:
        """
        Run ZAP scan with a containerized application as a Dagger service.

        This starts the target application as a Dagger service, waits for it
        to be ready, then runs ZAP against it.

        Args:
            source: Source directory (mounted to app if needed)
            app_image: Container image of the application to scan
            app_port: Port the application listens on
            scan_type: Type of scan - baseline or full
            max_duration_minutes: Maximum scan duration
        """
        # Start the application as a service
        app_service = dag.container().from_(app_image).with_exposed_port(app_port).as_service()

        # Create ZAP container with service binding
        target_url = f"http://app:{app_port}"

        container = (
            dag.container()
            .from_("ghcr.io/zaproxy/zaproxy:stable")
            .with_service_binding("app", app_service)
            .with_exec(["mkdir", "-p", "/zap/reports"])
        )

        # Wait for app to be ready
        container = container.with_exec(
            [
                "bash",
                "-c",
                f"for i in $(seq 1 60); do curl -sf {target_url} && break || sleep 2; done",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # Run scan
        if scan_type == "baseline":
            container = await self._run_baseline_scan(container, target_url, max_duration_minutes)
        else:
            container = await self._run_full_scan(container, target_url, max_duration_minutes)

        # Parse results - report may not exist if scan failed
        findings = []
        try:
            json_content = await container.file("/zap/reports/zap-report.json").contents()
            findings = self.parse_findings(json_content)
        except Exception:  # noqa: S110
            pass  # Report file may not exist if scan didn't complete

        reports = container.directory("/zap/reports")

        return ScanResult(
            scanner=self.name,
            findings=findings,
            artifacts=reports,
            exit_code=0,
        )

    async def _run_baseline_scan(
        self,
        container: dagger.Container,
        target_url: str,
        max_duration: int,
    ) -> dagger.Container:
        """Run ZAP baseline (passive) scan."""
        return container.with_exec(
            [
                "zap-baseline.py",
                "-t",
                target_url,
                "-J",
                "/zap/reports/zap-report.json",
                "-r",
                "/zap/reports/zap-report.html",
                "-w",
                "/zap/reports/zap-report.md",
                "-x",
                "/zap/reports/zap-report.xml",
                "-m",
                str(max_duration),
                "-I",  # Don't fail on warnings
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

    async def _run_full_scan(
        self,
        container: dagger.Container,
        target_url: str,
        max_duration: int,
    ) -> dagger.Container:
        """Run ZAP full (active) scan."""
        return container.with_exec(
            [
                "zap-full-scan.py",
                "-t",
                target_url,
                "-J",
                "/zap/reports/zap-report.json",
                "-r",
                "/zap/reports/zap-report.html",
                "-w",
                "/zap/reports/zap-report.md",
                "-x",
                "/zap/reports/zap-report.xml",
                "-m",
                str(max_duration),
                "-I",  # Don't fail on warnings
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

    async def _run_api_scan(
        self,
        container: dagger.Container,
        api_spec: str,
        target_url: str,
        max_duration: int,
    ) -> dagger.Container:
        """Run ZAP API scan."""
        cmd = [
            "zap-api-scan.py",
            "-t",
            api_spec,
            "-f",
            "openapi",
            "-J",
            "/zap/reports/zap-report.json",
            "-r",
            "/zap/reports/zap-report.html",
            "-w",
            "/zap/reports/zap-report.md",
            "-x",
            "/zap/reports/zap-report.xml",
            "-I",  # Don't fail on warnings
        ]

        # Add target URL override if provided
        if target_url:
            cmd.extend(["-O", target_url])

        return container.with_exec(cmd, expect=dagger.Expect.SUCCESS_OR_FAILURE)

    def parse_findings(self, output: str) -> list[Finding]:
        """Parse ZAP JSON output into findings."""
        findings = []
        try:
            data = json.loads(output)

            # ZAP JSON structure varies - handle both formats
            sites = data.get("site", [])
            if not isinstance(sites, list):
                sites = [sites]

            for site in sites:
                alerts = site.get("alerts", [])
                for alert in alerts:
                    severity = self._map_risk_to_severity(alert.get("riskcode", "0"))

                    # Get instances for location info
                    instances = alert.get("instances", [])
                    uri = instances[0].get("uri", "") if instances else ""

                    desc = alert.get("desc", "")[:100]
                    findings.append(
                        Finding(
                            rule_id=alert.get("pluginid", alert.get("alertRef", "UNKNOWN")),
                            severity=severity,
                            message=f"{alert.get('name', 'Unknown')}: {desc}",
                            file_path=uri,
                            line_number=0,
                            scanner=self.name,
                            cwe=f"CWE-{alert.get('cweid')}" if alert.get("cweid") else None,
                        )
                    )

        except json.JSONDecodeError:
            pass

        return findings

    def _map_risk_to_severity(self, risk_code: str) -> Severity:
        """Map ZAP risk code to severity.

        ZAP risk codes:
        - 3: High
        - 2: Medium
        - 1: Low
        - 0: Informational
        """
        try:
            code = int(risk_code)
        except (ValueError, TypeError):
            return Severity.MEDIUM

        mapping = {
            3: Severity.HIGH,
            2: Severity.MEDIUM,
            1: Severity.LOW,
            0: Severity.NONE,
        }
        return mapping.get(code, Severity.MEDIUM)
