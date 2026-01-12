"""Tests for scanner parsing logic."""

import json

from hardening.models import Severity
from hardening.scanners.bandit import BanditScanner
from hardening.scanners.checkov import CheckovScanner
from hardening.scanners.clamav import ClamAVScanner
from hardening.scanners.gitleaks import GitleaksScanner
from hardening.scanners.grype import GrypeScanner
from hardening.scanners.opengrep import OpenGrepScanner
from hardening.scanners.trivy import TrivyContainerScanner, TrivyIacScanner


class TestBanditParser:
    """Tests for Bandit JSON parsing."""

    def test_parse_valid_findings(self):
        """Test parsing valid Bandit JSON output."""
        scanner = BanditScanner()
        bandit_output = json.dumps(
            {
                "results": [
                    {
                        "test_id": "B101",
                        "issue_severity": "HIGH",
                        "issue_text": "Use of assert detected",
                        "filename": "./app.py",
                        "line_number": 42,
                        "issue_cwe": {"id": 703},
                    },
                    {
                        "test_id": "B105",
                        "issue_severity": "MEDIUM",
                        "issue_text": "Hardcoded password string",
                        "filename": "./config.py",
                        "line_number": 10,
                        "issue_cwe": {"id": 259},
                    },
                ]
            }
        )

        findings = scanner.parse_findings(bandit_output)

        assert len(findings) == 2
        assert findings[0].rule_id == "B101"
        assert findings[0].severity == Severity.HIGH
        assert findings[0].message == "Use of assert detected"
        assert findings[0].file_path == "app.py"  # Should strip ./
        assert findings[0].line_number == 42
        assert findings[0].cwe == "CWE-703"
        assert findings[0].scanner == "bandit"

        assert findings[1].rule_id == "B105"
        assert findings[1].severity == Severity.MEDIUM
        assert findings[1].cwe == "CWE-259"

    def test_parse_empty_results(self):
        """Test parsing Bandit output with no findings."""
        scanner = BanditScanner()
        bandit_output = json.dumps({"results": []})

        findings = scanner.parse_findings(bandit_output)

        assert len(findings) == 0

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns empty list."""
        scanner = BanditScanner()
        findings = scanner.parse_findings("not valid json")

        assert len(findings) == 0

    def test_parse_missing_cwe(self):
        """Test parsing findings without CWE data."""
        scanner = BanditScanner()
        bandit_output = json.dumps(
            {
                "results": [
                    {
                        "test_id": "B101",
                        "issue_severity": "LOW",
                        "issue_text": "Some issue",
                        "filename": "test.py",
                        "line_number": 1,
                    }
                ]
            }
        )

        findings = scanner.parse_findings(bandit_output)

        assert len(findings) == 1
        assert findings[0].cwe is None

    def test_severity_mapping(self):
        """Test Bandit severity mapping."""
        scanner = BanditScanner()

        assert scanner._map_severity("HIGH") == Severity.HIGH
        assert scanner._map_severity("MEDIUM") == Severity.MEDIUM
        assert scanner._map_severity("LOW") == Severity.LOW
        assert scanner._map_severity("high") == Severity.HIGH  # Case insensitive
        assert scanner._map_severity("UNKNOWN") == Severity.LOW  # Default


class TestGitleaksParser:
    """Tests for Gitleaks JSON parsing."""

    def test_parse_valid_findings(self):
        """Test parsing valid Gitleaks JSON output."""
        scanner = GitleaksScanner()
        gitleaks_output = json.dumps(
            [
                {
                    "RuleID": "aws-access-key-id",
                    "Description": "AWS Access Key ID",
                    "File": "./config/secrets.py",
                    "StartLine": 15,
                },
                {
                    "RuleID": "generic-api-key",
                    "Description": "Generic API Key",
                    "File": "api.py",
                    "StartLine": 42,
                },
            ]
        )

        findings = scanner.parse_findings(gitleaks_output)

        assert len(findings) == 2
        assert findings[0].rule_id == "aws-access-key-id"
        assert findings[0].severity == Severity.HIGH  # Secrets are always HIGH
        assert findings[0].message == "Secret detected: AWS Access Key ID"
        assert findings[0].file_path == "config/secrets.py"  # Strip ./
        assert findings[0].line_number == 15
        assert findings[0].scanner == "gitleaks"

    def test_parse_empty_array(self):
        """Test parsing empty array."""
        scanner = GitleaksScanner()
        findings = scanner.parse_findings("[]")

        assert len(findings) == 0

    def test_parse_non_array_json(self):
        """Test parsing non-array JSON returns empty."""
        scanner = GitleaksScanner()
        findings = scanner.parse_findings('{"not": "an array"}')

        assert len(findings) == 0

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns empty."""
        scanner = GitleaksScanner()
        findings = scanner.parse_findings("not json")

        assert len(findings) == 0


class TestGrypeParser:
    """Tests for Grype JSON parsing."""

    def test_parse_valid_findings(self):
        """Test parsing valid Grype JSON output."""
        scanner = GrypeScanner()
        grype_output = json.dumps(
            {
                "matches": [
                    {
                        "vulnerability": {
                            "id": "CVE-2023-1234",
                            "severity": "Critical",
                            "description": "A critical vulnerability in some package",
                            "cvss": [
                                {
                                    "version": "3.1",
                                    "metrics": {"baseScore": 9.8},
                                }
                            ],
                        },
                        "artifact": {
                            "name": "requests",
                            "version": "2.28.0",
                            "locations": [{"path": "/app/requirements.txt"}],
                        },
                    }
                ]
            }
        )

        findings = scanner.parse_findings(grype_output)

        assert len(findings) == 1
        assert findings[0].rule_id == "CVE-2023-1234"
        assert findings[0].severity == Severity.CRITICAL
        assert "requests@2.28.0" in findings[0].message
        assert findings[0].file_path == "/app/requirements.txt"
        assert findings[0].cvss_score == 9.8
        assert findings[0].scanner == "grype"

    def test_parse_with_cvss2_only(self):
        """Test parsing when only CVSS v2 is available."""
        scanner = GrypeScanner()
        grype_output = json.dumps(
            {
                "matches": [
                    {
                        "vulnerability": {
                            "id": "CVE-2020-5678",
                            "severity": "High",
                            "cvss": [
                                {
                                    "version": "2.0",
                                    "metrics": {"baseScore": 7.5},
                                }
                            ],
                        },
                        "artifact": {
                            "name": "urllib3",
                            "version": "1.26.0",
                            "locations": [{"path": "/requirements.txt"}],
                        },
                    }
                ]
            }
        )

        findings = scanner.parse_findings(grype_output)

        assert len(findings) == 1
        assert findings[0].cvss_score is None  # Only v3 is extracted

    def test_parse_empty_matches(self):
        """Test parsing with no matches."""
        scanner = GrypeScanner()
        findings = scanner.parse_findings(json.dumps({"matches": []}))

        assert len(findings) == 0


class TestTrivyIacParser:
    """Tests for Trivy IaC JSON parsing."""

    def test_parse_valid_findings(self):
        """Test parsing valid Trivy IaC JSON output."""
        scanner = TrivyIacScanner()
        trivy_output = json.dumps(
            {
                "Results": [
                    {
                        "Target": "./terraform/main.tf",
                        "Misconfigurations": [
                            {
                                "ID": "AVD-AWS-0086",
                                "Severity": "HIGH",
                                "Title": "S3 bucket without encryption",
                                "CauseMetadata": {"StartLine": 10},
                            },
                            {
                                "ID": "AVD-AWS-0087",
                                "Severity": "MEDIUM",
                                "Message": "Public access enabled",
                                "CauseMetadata": {"StartLine": 15},
                            },
                        ],
                    }
                ]
            }
        )

        findings = scanner.parse_findings(trivy_output)

        assert len(findings) == 2
        assert findings[0].rule_id == "AVD-AWS-0086"
        assert findings[0].severity == Severity.HIGH
        assert findings[0].message == "S3 bucket without encryption"
        assert findings[0].file_path == "terraform/main.tf"  # Strip ./
        assert findings[0].line_number == 10
        assert findings[0].scanner == "trivy-iac"

    def test_parse_empty_results(self):
        """Test parsing with no results."""
        scanner = TrivyIacScanner()
        findings = scanner.parse_findings(json.dumps({"Results": []}))

        assert len(findings) == 0

    def test_severity_mapping(self):
        """Test Trivy severity mapping."""
        scanner = TrivyIacScanner()

        assert scanner._map_severity("CRITICAL") == Severity.CRITICAL
        assert scanner._map_severity("HIGH") == Severity.HIGH
        assert scanner._map_severity("MEDIUM") == Severity.MEDIUM
        assert scanner._map_severity("LOW") == Severity.LOW
        assert scanner._map_severity("UNKNOWN") == Severity.LOW  # Default


class TestTrivyContainerParser:
    """Tests for Trivy Container JSON parsing."""

    def test_parse_valid_findings(self):
        """Test parsing valid Trivy container JSON output."""
        scanner = TrivyContainerScanner()
        trivy_output = json.dumps(
            {
                "Results": [
                    {
                        "Target": "python:3.12-slim (debian 12.4)",
                        "Vulnerabilities": [
                            {
                                "VulnerabilityID": "CVE-2023-9999",
                                "Severity": "CRITICAL",
                                "PkgName": "openssl",
                                "Title": "Buffer overflow in OpenSSL",
                                "CVSS": {
                                    "nvd": {"V3Score": 9.1},
                                },
                            }
                        ],
                    }
                ]
            }
        )

        findings = scanner.parse_findings(trivy_output)

        assert len(findings) == 1
        assert findings[0].rule_id == "CVE-2023-9999"
        assert findings[0].severity == Severity.CRITICAL
        assert "openssl" in findings[0].message
        assert findings[0].cvss_score == 9.1
        assert findings[0].scanner == "trivy-container"

    def test_parse_without_cvss(self):
        """Test parsing without CVSS scores."""
        scanner = TrivyContainerScanner()
        trivy_output = json.dumps(
            {
                "Results": [
                    {
                        "Target": "image:latest",
                        "Vulnerabilities": [
                            {
                                "VulnerabilityID": "CVE-2023-1111",
                                "Severity": "LOW",
                                "PkgName": "some-package",
                                "Title": "Minor issue",
                            }
                        ],
                    }
                ]
            }
        )

        findings = scanner.parse_findings(trivy_output)

        assert len(findings) == 1
        assert findings[0].cvss_score is None


class TestCheckovParser:
    """Tests for Checkov JSON parsing."""

    def test_parse_valid_findings(self):
        """Test parsing valid Checkov JSON output."""
        scanner = CheckovScanner()
        checkov_output = json.dumps(
            {
                "results": {
                    "failed_checks": [
                        {
                            "check_id": "CKV_AWS_18",
                            "check_name": "Ensure the S3 bucket has access logging enabled",
                            "file_path": "/terraform/s3.tf",
                            "file_line_range": [5, 10],
                            "guideline": "https://docs.bridgecrew.io/docs/s3_13-enable-logging",
                        },
                        {
                            "check_id": "CKV_AWS_19",
                            "check_name": "Ensure the S3 bucket has server-side encryption enabled",
                            "file_path": "/terraform/s3.tf",
                            "file_line_range": [5, 10],
                        },
                    ]
                }
            }
        )

        findings = scanner.parse_findings(checkov_output)

        assert len(findings) == 2
        assert findings[0].rule_id == "CKV_AWS_18"
        assert findings[0].severity == Severity.MEDIUM  # Checkov defaults to MEDIUM
        assert "access logging" in findings[0].message
        assert findings[0].file_path == "terraform/s3.tf"  # Strip leading /
        assert findings[0].line_number == 5
        assert findings[0].scanner == "checkov"

    def test_parse_empty_failures(self):
        """Test parsing with no failed checks."""
        scanner = CheckovScanner()
        findings = scanner.parse_findings(
            json.dumps({"results": {"failed_checks": []}})
        )

        assert len(findings) == 0

    def test_parse_invalid_structure(self):
        """Test parsing with invalid structure."""
        scanner = CheckovScanner()
        findings = scanner.parse_findings(json.dumps({"wrong": "structure"}))

        assert len(findings) == 0


class TestOpenGrepParser:
    """Tests for OpenGrep (Semgrep) JSON parsing."""

    def test_parse_valid_findings(self):
        """Test parsing valid OpenGrep JSON output."""
        scanner = OpenGrepScanner()
        opengrep_output = json.dumps(
            {
                "results": [
                    {
                        "check_id": "python.security.sql-injection",
                        "path": "app/db.py",
                        "start": {"line": 25},
                        "extra": {
                            "message": "Possible SQL injection",
                            "severity": "ERROR",
                            "metadata": {"cwe": ["CWE-89"]},
                        },
                    },
                    {
                        "check_id": "python.security.xss",
                        "path": "app/views.py",
                        "start": {"line": 42},
                        "extra": {
                            "message": "Potential XSS vulnerability",
                            "severity": "WARNING",
                        },
                    },
                ]
            }
        )

        findings = scanner.parse_findings(opengrep_output)

        assert len(findings) == 2
        assert findings[0].rule_id == "python.security.sql-injection"
        assert findings[0].severity == Severity.HIGH  # ERROR maps to HIGH
        assert findings[0].message == "Possible SQL injection"
        assert findings[0].file_path == "app/db.py"
        assert findings[0].line_number == 25
        assert findings[0].cwe == "CWE-89"
        assert findings[0].scanner == "opengrep"

        assert findings[1].severity == Severity.MEDIUM  # WARNING maps to MEDIUM

    def test_parse_empty_results(self):
        """Test parsing with no results."""
        scanner = OpenGrepScanner()
        findings = scanner.parse_findings(json.dumps({"results": []}))

        assert len(findings) == 0

    def test_severity_mapping(self):
        """Test OpenGrep severity mapping."""
        scanner = OpenGrepScanner()

        assert scanner._map_severity("ERROR") == Severity.HIGH
        assert scanner._map_severity("WARNING") == Severity.MEDIUM
        assert scanner._map_severity("INFO") == Severity.LOW
        assert scanner._map_severity("UNKNOWN") == Severity.MEDIUM  # Default


class TestClamAVParser:
    """Tests for ClamAV output parsing."""

    def test_parse_valid_findings(self):
        """Test parsing valid ClamAV output."""
        scanner = ClamAVScanner()
        clamav_output = """/src/uploads/malware.exe: Trojan.GenericKD.12345 FOUND
/src/uploads/clean.txt: OK
/src/downloads/virus.bin: Win.Malware.Agent-1234 FOUND
"""

        findings = scanner.parse_findings(clamav_output)

        assert len(findings) == 2
        assert findings[0].rule_id == "Trojan.GenericKD.12345"
        assert findings[0].severity == Severity.CRITICAL  # Malware is always critical
        assert "Malware detected" in findings[0].message
        assert findings[0].file_path == "uploads/malware.exe"  # /src/ stripped
        assert findings[0].scanner == "clamav"

        assert findings[1].rule_id == "Win.Malware.Agent-1234"
        assert findings[1].file_path == "downloads/virus.bin"

    def test_parse_no_malware(self):
        """Test parsing output with no malware found."""
        scanner = ClamAVScanner()
        clamav_output = """/src/file1.txt: OK
/src/file2.py: OK
"""

        findings = scanner.parse_findings(clamav_output)

        assert len(findings) == 0

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        scanner = ClamAVScanner()
        findings = scanner.parse_findings("")

        assert len(findings) == 0
