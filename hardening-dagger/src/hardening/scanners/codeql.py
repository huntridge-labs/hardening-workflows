"""CodeQL SAST scanner.

Note: CodeQL has some limitations when running outside of GitHub Actions:
- The full CodeQL CLI is large (~500MB) and requires database creation
- Language detection and autobuild work best with build system context
- For best results, CodeQL is still recommended to run via GitHub Actions

This scanner provides a containerized CodeQL experience that works anywhere,
with support for the most common languages (Python, JavaScript/TypeScript, Go, Java).
"""

import json

import dagger
from dagger import dag

from ..models import Finding, ScanResult, Severity
from .base import BaseScanner


class CodeQLScanner(BaseScanner):
    """CodeQL - GitHub's semantic code analysis engine."""

    name = "codeql"
    description = "Deep semantic SAST analysis for multiple languages"

    # CodeQL language identifiers
    SUPPORTED_LANGUAGES = {
        "python": "python",
        "javascript": "javascript",
        "typescript": "javascript",  # TypeScript uses JavaScript extractor
        "js": "javascript",
        "ts": "javascript",
        "go": "go",
        "golang": "go",
        "java": "java",
        "csharp": "csharp",
        "c#": "csharp",
        "cpp": "cpp",
        "c++": "cpp",
        "c": "cpp",
        "ruby": "ruby",
    }

    async def scan(
        self,
        source: dagger.Directory,
        languages: str = "python,javascript",
        **kwargs,
    ) -> ScanResult:
        """
        Run CodeQL analysis.

        Args:
            source: Source code directory to scan
            languages: Comma-separated list of languages to analyze

        Note: CodeQL requires significant resources. For large codebases,
        consider running via GitHub Actions where CodeQL is optimized.
        """
        # Parse and validate languages
        lang_list = self._parse_languages(languages)
        if not lang_list:
            return ScanResult(
                scanner=self.name,
                findings=[],
                artifacts=dag.directory(),
                exit_code=0,
                error_message=f"No supported languages in: {languages}",
            )

        # Use the official CodeQL container
        # This container includes the CLI and standard query packs
        # TODO: Consider pinning to a specific CodeQL version
        container = (
            dag.container()
            .from_("ghcr.io/github/codeql-action/codeql-bundle:latest")
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["mkdir", "-p", "/reports", "/codeql-dbs"])
        )

        all_findings: list[Finding] = []
        artifacts = dag.directory()

        # Process each language
        for lang in lang_list:
            try:
                result_container, lang_findings = await self._scan_language(container, lang)
                all_findings.extend(lang_findings)

                # Export language-specific reports
                try:
                    sarif_content = await result_container.file(
                        f"/reports/codeql-{lang}.sarif"
                    ).contents()
                    artifacts = artifacts.with_new_file(f"codeql-{lang}.sarif", sarif_content)
                except Exception:  # noqa: S110
                    pass  # SARIF file may not exist if analysis produced no results

            except Exception as e:
                # Log error but continue with other languages
                print(f"CodeQL {lang} analysis failed: {e}")

        # Create combined SARIF
        combined_sarif = self._create_combined_sarif(all_findings)
        artifacts = artifacts.with_new_file("codeql-combined.sarif", combined_sarif)

        # Create JSON summary
        json_report = json.dumps(
            {
                "scanner": self.name,
                "languages": lang_list,
                "findings": [f.to_dict() for f in all_findings],
                "total": len(all_findings),
            },
            indent=2,
        )
        artifacts = artifacts.with_new_file("codeql-report.json", json_report)

        return ScanResult(
            scanner=self.name,
            findings=all_findings,
            artifacts=artifacts,
            exit_code=0 if not all_findings else 1,
        )

    async def _scan_language(
        self,
        base_container: dagger.Container,
        language: str,
    ) -> tuple[dagger.Container, list[Finding]]:
        """Run CodeQL analysis for a single language."""
        db_path = f"/codeql-dbs/{language}"
        sarif_path = f"/reports/codeql-{language}.sarif"

        # Create database
        container = base_container.with_exec(
            [
                "codeql",
                "database",
                "create",
                db_path,
                f"--language={language}",
                "--source-root=/src",
                "--overwrite",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # Run analysis with security queries
        container = container.with_exec(
            [
                "codeql",
                "database",
                "analyze",
                db_path,
                "--format=sarifv2.1.0",
                f"--output={sarif_path}",
                "--",  # Query packs after this
                f"{language}-security-extended",
            ],
            expect=dagger.Expect.SUCCESS_OR_FAILURE,
        )

        # Parse results
        findings = []
        try:
            sarif_content = await container.file(sarif_path).contents()
            findings = self.parse_findings(sarif_content)
        except Exception:  # noqa: S110
            pass  # SARIF file may not exist if no issues found

        return container, findings

    def parse_findings(self, output: str) -> list[Finding]:
        """Parse CodeQL SARIF output into findings."""
        findings = []
        try:
            data = json.loads(output)

            for run in data.get("runs", []):
                rules = {r["id"]: r for r in run.get("tool", {}).get("driver", {}).get("rules", [])}

                for result in run.get("results", []):
                    rule_id = result.get("ruleId", "UNKNOWN")
                    rule = rules.get(rule_id, {})

                    # Get severity from security-severity property
                    severity = self._get_severity(rule, result)

                    # Get location
                    locations = result.get("locations", [])
                    if locations:
                        loc = locations[0].get("physicalLocation", {})
                        file_path = loc.get("artifactLocation", {}).get("uri", "")
                        line = loc.get("region", {}).get("startLine", 0)
                    else:
                        file_path = ""
                        line = 0

                    # Get CWE if available
                    cwe = None
                    tags = rule.get("properties", {}).get("tags", [])
                    for tag in tags:
                        if tag.startswith("external/cwe/cwe-"):
                            cwe = tag.replace("external/cwe/", "").upper()
                            break

                    findings.append(
                        Finding(
                            rule_id=rule_id,
                            severity=severity,
                            message=result.get("message", {}).get("text", ""),
                            file_path=file_path.lstrip("./"),
                            line_number=line,
                            scanner=self.name,
                            cwe=cwe,
                        )
                    )

        except json.JSONDecodeError:
            pass

        return findings

    def _parse_languages(self, languages: str) -> list[str]:
        """Parse and validate language string."""
        result = []
        for lang in languages.lower().replace(" ", "").split(","):
            normalized = self.SUPPORTED_LANGUAGES.get(lang)
            if normalized and normalized not in result:
                result.append(normalized)
        return result

    def _get_severity(self, rule: dict, result: dict) -> Severity:
        """Extract severity from CodeQL rule/result."""
        # Check security-severity property (CVSS score)
        sec_sev = rule.get("properties", {}).get("security-severity")
        if sec_sev:
            try:
                score = float(sec_sev)
                return Severity.from_cvss(score)
            except ValueError:
                pass

        # Fall back to SARIF level
        level = result.get("level", "warning")
        mapping = {
            "error": Severity.HIGH,
            "warning": Severity.MEDIUM,
            "note": Severity.LOW,
        }
        return mapping.get(level, Severity.MEDIUM)

    def _create_combined_sarif(self, findings: list[Finding]) -> str:
        """Create a combined SARIF report from all findings."""
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "CodeQL (via Hardening)",
                            "version": "2.10.0",
                            "informationUri": "https://github.com/huntridge-labs/hardening-workflows",
                        }
                    },
                    "results": [
                        {
                            "ruleId": f.rule_id,
                            "level": self._severity_to_sarif_level(f.severity),
                            "message": {"text": f.message},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": f.file_path},
                                        "region": {"startLine": max(1, f.line_number)},
                                    }
                                }
                            ],
                        }
                        for f in findings
                    ],
                }
            ],
        }
        return json.dumps(sarif, indent=2)

    def _severity_to_sarif_level(self, severity: Severity) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.NONE: "none",
        }
        return mapping.get(severity, "warning")
