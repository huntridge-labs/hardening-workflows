"""
Hardening - Security scanning pipeline that runs anywhere.

This Dagger module provides portable security scanning that works:
- Locally via `dagger call`
- In GitHub Actions (github.com or GHE)
- In GitLab CI
- In any CI system with Docker support

Usage:
    # Scan everything
    dagger call scan --source .

    # Specific scanners
    dagger call scan --source . --scanners "bandit,gitleaks,trivy-iac"

    # With severity threshold (fails if exceeded)
    dagger call scan --source . --severity-threshold high

    # Individual scanner
    dagger call bandit --source .
"""

import asyncio
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type

from github import GitHubIntegration
from models import HardeningReport, ScanResult, Severity
from report import ReportGenerator
from scanners import (
    BanditScanner,
    CheckovScanner,
    ClamAVScanner,
    CodeQLScanner,
    GitleaksScanner,
    GrypeScanner,
    OpenGrepScanner,
    TrivyContainerScanner,
    TrivyIacScanner,
    ZAPScanner,
)

# Scanner registry
SCANNERS = {
    "bandit": BanditScanner(),
    "gitleaks": GitleaksScanner(),
    "trivy-iac": TrivyIacScanner(),
    "trivy-container": TrivyContainerScanner(),
    "checkov": CheckovScanner(),
    "grype": GrypeScanner(),
    "opengrep": OpenGrepScanner(),
    "clamav": ClamAVScanner(),
    "codeql": CodeQLScanner(),
    "zap": ZAPScanner(),
}

# Scanner groups
# Note: codeql and zap are opt-in (not in "all") due to:
# - codeql: large container, requires significant resources
# - zap: requires a running target application (DAST)
SCANNER_GROUPS = {
    "all": {"bandit", "gitleaks", "trivy-iac", "checkov", "grype", "opengrep"},
    "full": {"bandit", "gitleaks", "trivy-iac", "checkov", "grype", "opengrep", "codeql", "clamav"},
    "sast": {"bandit", "opengrep", "gitleaks", "codeql"},
    "secrets": {"gitleaks"},
    "iac": {"trivy-iac", "checkov"},
    "container": {"trivy-container", "grype"},
    "dast": {"zap"},
}


@object_type
class Hardening:
    """Security hardening pipeline - runs anywhere."""

    @function
    def github(self) -> GitHubIntegration:
        """
        Access GitHub integration functions for PR comments and SARIF upload.

        Example:
            dagger call github post-pr-comment --token env:GITHUB_TOKEN ...
        """
        return GitHubIntegration()

    @function
    async def scan(
        self,
        source: Annotated[dagger.Directory, Doc("Source code directory to scan")],
        scanners: Annotated[
            str,
            Doc(
                "Comma-separated scanners or groups: "
                "bandit,gitleaks,trivy-iac,checkov,grype,opengrep,clamav,codeql,zap,"
                "all,full,sast,iac,dast"
            ),
        ] = "all",
        severity_threshold: Annotated[
            str, Doc("Fail if findings at or above: none, low, medium, high, critical")
        ] = "none",
        iac_path: Annotated[str, Doc("Path to infrastructure-as-code files")] = "infrastructure",
        output_format: Annotated[str, Doc("Output formats: markdown, json, sarif, all")] = "all",
        repository: Annotated[
            str, Doc("Repository name for report metadata (e.g., owner/repo)")
        ] = "",
        branch: Annotated[str, Doc("Branch name for report metadata")] = "",
        commit_sha: Annotated[str, Doc("Commit SHA for report metadata")] = "",
    ) -> dagger.Directory:
        """
        Run security scanners against source code.

        Returns a directory containing all scan reports. Use 'export --path <dir>'
        to write files to your local filesystem.

        Examples:
            dagger call scan --source . export --path ./reports
            dagger call scan --source . --scanners "bandit,gitleaks" export --path ./reports
            dagger call scan --source . --severity-threshold high export --path ./reports
        """
        # Resolve which scanners to run
        selected = self._resolve_scanners(scanners)

        if not selected:
            raise ValueError(f"No valid scanners found in: {scanners}")

        # Run all selected scanners concurrently
        results: list[ScanResult] = []
        tasks = []

        for scanner_name in selected:
            scanner = SCANNERS.get(scanner_name)
            if scanner:
                kwargs = {}
                if scanner_name in ("trivy-iac", "checkov"):
                    kwargs["iac_path"] = iac_path

                tasks.append(self._run_scanner(scanner, source, **kwargs))

        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and convert to ScanResult
        scan_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                scanner_name = list(selected)[i]
                scan_results.append(
                    ScanResult(
                        scanner=scanner_name,
                        findings=[],
                        artifacts=dag.directory(),
                        exit_code=1,
                        error_message=str(result),
                    )
                )
            else:
                scan_results.append(result)

        # Build combined report
        report = HardeningReport(
            results=scan_results,
            repository=repository,
            branch=branch,
            commit_sha=commit_sha,
        )

        # Generate output directory
        output_dir = dag.directory()

        # Add individual scanner artifacts
        for result in scan_results:
            output_dir = output_dir.with_directory(
                f"{result.scanner}-reports",
                result.artifacts,
            )

        # Generate reports
        generator = ReportGenerator(report)

        if output_format in ("markdown", "all"):
            md_content = generator.generate_markdown()
            output_dir = output_dir.with_new_file(
                "hardening-report.md",
                md_content,
            )

        if output_format in ("json", "all"):
            json_content = generator.generate_json()
            output_dir = output_dir.with_new_file(
                "hardening-report.json",
                json_content,
            )

        if output_format in ("sarif", "all"):
            sarif_content = generator.generate_sarif()
            output_dir = output_dir.with_new_file(
                "hardening-report.sarif",
                sarif_content,
            )

        # Check severity threshold
        threshold = Severity.from_string(severity_threshold)
        if report.exceeds_threshold(threshold):
            # Write failure marker file for CI to detect
            output_dir = output_dir.with_new_file(
                "THRESHOLD_EXCEEDED",
                f"Findings exceed severity threshold: {severity_threshold}\n"
                f"Critical: {report.critical_count}, High: {report.high_count}, "
                f"Medium: {report.medium_count}, Low: {report.low_count}",
            )

        return output_dir

    @function
    async def bandit(
        self,
        source: Annotated[dagger.Directory, Doc("Python source code to scan")],
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """Run Bandit Python security scanner."""
        scanner = BanditScanner()
        result = await scanner.scan(source, log_level=log_level)
        return result.artifacts

    @function
    async def gitleaks(
        self,
        source: Annotated[dagger.Directory, Doc("Source to scan for secrets")],
        config: Annotated[str | None, Doc("Path to gitleaks.toml")] = None,
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """Run Gitleaks secrets scanner."""
        scanner = GitleaksScanner()
        result = await scanner.scan(source, config_path=config, log_level=log_level)
        return result.artifacts

    @function
    async def trivy_iac(
        self,
        source: Annotated[dagger.Directory, Doc("IaC source to scan")],
        path: Annotated[str, Doc("Subdirectory with IaC files")] = ".",
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """Run Trivy infrastructure-as-code scanner."""
        scanner = TrivyIacScanner()
        result = await scanner.scan(source, iac_path=path, log_level=log_level)
        return result.artifacts

    @function
    async def trivy_container(
        self,
        image_ref: Annotated[str, Doc("Container image to scan (e.g., nginx:latest)")],
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """Run Trivy container vulnerability scanner."""
        scanner = TrivyContainerScanner()
        result = await scanner.scan(dag.directory(), image_ref=image_ref, log_level=log_level)
        return result.artifacts

    @function
    async def checkov(
        self,
        source: Annotated[dagger.Directory, Doc("IaC source to scan")],
        path: Annotated[str, Doc("Subdirectory with IaC files")] = ".",
        framework: Annotated[
            str | None, Doc("Specific framework: terraform, cloudformation, kubernetes")
        ] = None,
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """Run Checkov IaC scanner."""
        scanner = CheckovScanner()
        result = await scanner.scan(source, iac_path=path, framework=framework, log_level=log_level)
        return result.artifacts

    @function
    async def grype(
        self,
        source: Annotated[dagger.Directory, Doc("Source to scan for vulnerabilities")],
        image_ref: Annotated[
            str | None, Doc("Container image to scan instead of filesystem")
        ] = None,
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """Run Grype vulnerability scanner."""
        scanner = GrypeScanner()
        result = await scanner.scan(source, image_ref=image_ref, log_level=log_level)
        return result.artifacts

    @function
    async def opengrep(
        self,
        source: Annotated[dagger.Directory, Doc("Source code to scan")],
        config: Annotated[str, Doc("Semgrep config: auto, p/security-audit, etc.")] = "auto",
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """Run OpenGrep/Semgrep SAST scanner."""
        scanner = OpenGrepScanner()
        result = await scanner.scan(source, config=config, log_level=log_level)
        return result.artifacts

    @function
    async def clamav(
        self,
        source: Annotated[dagger.Directory, Doc("Files to scan for malware")],
        path: Annotated[str, Doc("Subdirectory to scan")] = ".",
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """Run ClamAV malware scanner."""
        scanner = ClamAVScanner()
        result = await scanner.scan(source, scan_path=path, log_level=log_level)
        return result.artifacts

    @function
    async def codeql(
        self,
        source: Annotated[dagger.Directory, Doc("Source code to scan")],
        languages: Annotated[
            str, Doc("Comma-separated languages: python,javascript,go,java,csharp,cpp,ruby")
        ] = "python,javascript",
        ghcr_username: Annotated[
            str | None, Doc("GHCR username for GitHub's official CodeQL image")
        ] = None,
        ghcr_token: Annotated[
            dagger.Secret | None, Doc("GHCR token (PAT with read:packages) - use env:GHCR_TOKEN")
        ] = None,
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """
        Run CodeQL semantic SAST analysis.

        Note: CodeQL analysis requires significant resources and time.
        For large codebases, GitHub Actions with CodeQL is recommended.

        Container images:
        - With GHCR credentials: Uses GitHub's official codeql-bundle (recommended)
        - Without credentials: Falls back to Microsoft's public container

        Examples:
            dagger call codeql --source . --languages python export --path ./reports/codeql
            dagger call codeql --source . --languages python --log-level debug export --path ./reports/codeql
        """
        scanner = CodeQLScanner()
        result = await scanner.scan(
            source,
            languages=languages,
            ghcr_username=ghcr_username,
            ghcr_token=ghcr_token,
            log_level=log_level,
        )
        return result.artifacts

    @function
    async def zap(
        self,
        target_url: Annotated[str, Doc("URL of the running application to scan")],
        scan_type: Annotated[
            str, Doc("Scan type: baseline (passive), full (active), api")
        ] = "baseline",
        api_spec: Annotated[str, Doc("OpenAPI/Swagger spec URL (required for api scan type)")] = "",
        max_duration: Annotated[int, Doc("Maximum scan duration in minutes")] = 10,
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """
        Run ZAP DAST (Dynamic Application Security Testing) scan.

        The target application must be running and accessible at target_url.

        Scan types:
        - baseline: Passive scanning only (fast, safe for production)
        - full: Active scanning (thorough, may modify data - use on test envs)
        - api: OpenAPI/Swagger-driven API scanning

        Examples:
            dagger call zap --target-url http://localhost:8080 export --path ./reports/zap
            dagger call zap --target-url http://app:3000 --scan-type full export --path ./reports/zap
            dagger call zap --scan-type api --api-spec http://localhost:8080/openapi.json export --path ./reports/zap
        """
        scanner = ZAPScanner()
        result = await scanner.scan(
            dag.directory(),  # ZAP doesn't need source for URL scans
            target_url=target_url,
            scan_type=scan_type,
            api_spec=api_spec,
            max_duration_minutes=max_duration,
            log_level=log_level,
        )
        return result.artifacts

    @function
    async def zap_with_service(
        self,
        app_image: Annotated[str, Doc("Container image of the application to scan")],
        app_port: Annotated[int, Doc("Port the application listens on")] = 8080,
        scan_type: Annotated[str, Doc("Scan type: baseline or full")] = "baseline",
        max_duration: Annotated[int, Doc("Maximum scan duration in minutes")] = 10,
        log_level: Annotated[str, Doc("Log level: error, warn, info, debug")] = "info",
    ) -> dagger.Directory:
        """
        Run ZAP DAST scan against a containerized application.

        This starts the specified container as a Dagger service, waits for
        it to be ready, then runs ZAP against it. The container is
        automatically stopped when the scan completes.

        Examples:
            dagger call zap-with-service --app-image nginx:latest --app-port 80 export --path ./reports/zap
            dagger call zap-with-service --app-image myapp:latest --scan-type full --log-level debug export --path ./reports/zap
        """
        scanner = ZAPScanner()
        result = await scanner.scan_with_service(
            dag.directory(),
            app_image=app_image,
            app_port=app_port,
            scan_type=scan_type,
            max_duration_minutes=max_duration,
            log_level=log_level,
        )
        return result.artifacts

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    async def _run_scanner(
        self,
        scanner,
        source: dagger.Directory,
        **kwargs,
    ) -> ScanResult:
        """Run a single scanner with error handling.

        Always ensures logs are captured and returned in the artifacts,
        even if the scanner fails mid-execution.
        """
        try:
            return await scanner.scan(source, **kwargs)
        except Exception as e:
            # Use the scanner's error handler to ensure logs are saved
            return scanner._create_error_result(e)

    def _resolve_scanners(self, scanners: str) -> set[str]:
        """Resolve scanner selection string to set of scanner names."""
        selected = set()

        for token in scanners.lower().replace(" ", "").split(","):
            token = token.strip()

            # Check if it's a group
            if token in SCANNER_GROUPS:
                selected.update(SCANNER_GROUPS[token])
            # Check if it's a scanner
            elif token in SCANNERS:
                selected.add(token)
            # Handle aliases
            elif token in ("semgrep", "sast-scanner"):
                selected.add("opengrep")
            elif token in ("secrets-scanner", "secret"):
                selected.add("gitleaks")
            elif token in ("terraform", "infra"):
                selected.update(SCANNER_GROUPS["iac"])
            elif token in ("code-ql", "codeql-sast"):
                selected.add("codeql")
            elif token in ("zap-dast", "owasp-zap", "zaproxy"):
                selected.add("zap")

        return selected
