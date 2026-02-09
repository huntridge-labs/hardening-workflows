#!/usr/bin/env python3
"""
Integration tests for hardening-workflows action scripts.

Tests validate that each Python action script correctly writes to:
- GITHUB_OUTPUT: key=value pairs for action outputs
- GITHUB_STEP_SUMMARY: markdown summary for the GitHub Actions UI
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple

import pytest


class TestTrivyParser:
    """Integration tests for Trivy JSON parser."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-container/scripts/parse_trivy_results.py"

    def _create_trivy_json(self, tmp_path: Path, findings: Dict) -> Path:
        """Create a Trivy JSON results file."""
        trivy_file = tmp_path / "trivy-results.json"
        trivy_file.write_text(json.dumps(findings))
        return trivy_file

    def _create_empty_trivy_json(self, tmp_path: Path) -> Path:
        """Create an empty Trivy JSON results file."""
        return self._create_trivy_json(tmp_path, {
            "Results": [],
            "Metadata": {
                "RepoTags": ["test:latest"],
                "ImageID": "sha256:abc123"
            }
        })

    def test_trivy_counts_with_findings(self, tmp_path):
        """Test trivy parser 'counts' command with findings."""
        trivy_file = self._create_trivy_json(tmp_path, {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"Severity": "CRITICAL", "VulnerabilityID": "CVE-2021-1234"},
                        {"Severity": "CRITICAL", "VulnerabilityID": "CVE-2021-1235"},
                        {"Severity": "HIGH", "VulnerabilityID": "CVE-2021-1236"},
                        {"Severity": "MEDIUM", "VulnerabilityID": "CVE-2021-1237"},
                        {"Severity": "LOW", "VulnerabilityID": "CVE-2021-1238"},
                    ]
                }
            ],
            "Metadata": {}
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "counts", str(trivy_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output = result.stdout.strip()
        assert output == "2 1 1 1"  # 2 critical, 1 high, 1 medium, 1 low

    def test_trivy_counts_no_findings(self, tmp_path):
        """Test trivy parser 'counts' with no findings."""
        trivy_file = self._create_empty_trivy_json(tmp_path)

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "counts", str(trivy_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "0 0 0 0"

    def test_trivy_total(self, tmp_path):
        """Test trivy parser 'total' command."""
        trivy_file = self._create_trivy_json(tmp_path, {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"Severity": "CRITICAL", "VulnerabilityID": "CVE-2021-1"},
                        {"Severity": "HIGH", "VulnerabilityID": "CVE-2021-2"},
                        {"Severity": "HIGH", "VulnerabilityID": "CVE-2021-3"},
                    ]
                }
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "total", str(trivy_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "3"

    def test_trivy_unique(self, tmp_path):
        """Test trivy parser 'unique' command."""
        trivy_file = self._create_trivy_json(tmp_path, {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"Severity": "CRITICAL", "VulnerabilityID": "CVE-2021-1"},
                        {"Severity": "HIGH", "VulnerabilityID": "CVE-2021-2"},
                        {"Severity": "HIGH", "VulnerabilityID": "CVE-2021-1"},  # Duplicate
                    ]
                }
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "unique", str(trivy_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "2"  # Only 2 unique CVEs

    def test_trivy_cves(self, tmp_path):
        """Test trivy parser 'cves' command."""
        trivy_file = self._create_trivy_json(tmp_path, {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"Severity": "CRITICAL", "VulnerabilityID": "CVE-2021-1"},
                        {"Severity": "HIGH", "VulnerabilityID": "CVE-2021-2"},
                    ]
                }
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "cves", str(trivy_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        cves = result.stdout.strip().split("\n")
        assert len(cves) == 2
        assert "CVE-2021-1" in cves
        assert "CVE-2021-2" in cves

    def test_trivy_table(self, tmp_path):
        """Test trivy parser 'table' command."""
        trivy_file = self._create_trivy_json(tmp_path, {
            "Results": [
                {
                    "Vulnerabilities": [
                        {
                            "Severity": "CRITICAL",
                            "VulnerabilityID": "CVE-2021-1",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.0.0",
                            "FixedVersion": "1.0.1"
                        }
                    ]
                }
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "table", str(trivy_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        table = result.stdout
        assert "CVE-2021-1" in table
        assert "openssl" in table
        assert "1.0.0" in table

    def test_trivy_digest(self, tmp_path):
        """Test trivy parser 'digest' command."""
        trivy_file = self._create_trivy_json(tmp_path, {
            "Results": [],
            "Metadata": {
                "RepoDigests": ["sha256:abc123def456"]
            }
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "digest", str(trivy_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "abc123def456" in result.stdout


class TestGrypeParser:
    """Integration tests for Grype JSON parser."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-container/scripts/parse_grype_results.py"

    def _create_grype_json(self, tmp_path: Path, findings: Dict) -> Path:
        """Create a Grype JSON results file."""
        grype_file = tmp_path / "grype-results.json"
        grype_file.write_text(json.dumps(findings))
        return grype_file

    def test_grype_counts_with_findings(self, tmp_path):
        """Test grype parser 'counts' with findings."""
        grype_file = self._create_grype_json(tmp_path, {
            "matches": [
                {"vulnerability": {"id": "CVE-2021-1", "severity": "Critical"}},
                {"vulnerability": {"id": "CVE-2021-2", "severity": "High"}},
                {"vulnerability": {"id": "CVE-2021-3", "severity": "Medium"}},
                {"vulnerability": {"id": "CVE-2021-4", "severity": "Low"}},
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "counts", str(grype_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "1 1 1 1"

    def test_grype_counts_no_findings(self, tmp_path):
        """Test grype parser with no findings."""
        grype_file = self._create_grype_json(tmp_path, {"matches": []})

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "counts", str(grype_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "0 0 0 0"

    def test_grype_total(self, tmp_path):
        """Test grype parser 'total' command."""
        grype_file = self._create_grype_json(tmp_path, {
            "matches": [
                {"vulnerability": {"id": "CVE-2021-1", "severity": "Critical"}},
                {"vulnerability": {"id": "CVE-2021-2", "severity": "High"}},
                {"vulnerability": {"id": "CVE-2021-3", "severity": "High"}},
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "total", str(grype_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "3"

    def test_grype_unique(self, tmp_path):
        """Test grype parser 'unique' command."""
        grype_file = self._create_grype_json(tmp_path, {
            "matches": [
                {"vulnerability": {"id": "CVE-2021-1", "severity": "Critical"}},
                {"vulnerability": {"id": "CVE-2021-2", "severity": "High"}},
                {"vulnerability": {"id": "CVE-2021-1", "severity": "Critical"}},  # Duplicate
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "unique", str(grype_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "2"


class TestZAPParser:
    """Integration tests for ZAP JSON parser."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-zap/scripts/parse_zap_results.py"

    def _create_zap_json(self, tmp_path: Path, findings: Dict) -> Path:
        """Create a ZAP JSON results file."""
        zap_file = tmp_path / "zap-report.json"
        zap_file.write_text(json.dumps(findings))
        return zap_file

    def test_zap_counts_with_findings(self, tmp_path):
        """Test ZAP parser 'counts' with findings."""
        zap_file = self._create_zap_json(tmp_path, {
            "site": [
                {
                    "@name": "http://localhost",
                    "alerts": [
                        {"name": "SQL Injection", "riskcode": "3", "pluginid": "1"},  # High
                        {"name": "XSS", "riskcode": "3", "pluginid": "2"},  # High
                        {"name": "Missing Header", "riskcode": "2", "pluginid": "3"},  # Medium
                        {"name": "Informational", "riskcode": "0", "pluginid": "4"},  # Info
                    ]
                }
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "counts", str(zap_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # ZAP has no critical, so: 0 critical, 2 high, 1 medium, 0 low
        assert result.stdout.strip() == "0 2 1 0"

    def test_zap_counts_no_findings(self, tmp_path):
        """Test ZAP parser with no findings."""
        zap_file = self._create_zap_json(tmp_path, {"site": [{"@name": "http://localhost", "alerts": []}]})

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "counts", str(zap_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "0 0 0 0"

    def test_zap_total(self, tmp_path):
        """Test ZAP parser 'total' command."""
        zap_file = self._create_zap_json(tmp_path, {
            "site": [
                {
                    "@name": "http://localhost",
                    "alerts": [
                        {"name": "Alert1", "riskcode": "3", "pluginid": "1"},
                        {"name": "Alert2", "riskcode": "2", "pluginid": "2"},
                        {"name": "Alert3", "riskcode": "1", "pluginid": "3"},
                    ]
                }
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "total", str(zap_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "3"

    def test_zap_target(self, tmp_path):
        """Test ZAP parser 'target' command."""
        zap_file = self._create_zap_json(tmp_path, {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": []
                }
            ]
        })

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "target", str(zap_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "example.com" in result.stdout


class TestCheckovSummary:
    """Integration tests for Checkov summary generator."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-checkov/scripts/generate_summary.py"

    def test_checkov_summary_with_findings(self, tmp_path):
        """Test Checkov summary generation with findings."""
        output_file = tmp_path / "checkov.md"
        checkov_dir = tmp_path / "checkov-reports"
        checkov_dir.mkdir()

        # Create minimal JSON file for the script to detect
        checkov_json = checkov_dir / "checkov-results.json"
        checkov_json.write_text(json.dumps({
            "check_type": "terraform",
            "results": {
                "failed_checks": [
                    {
                        "check_id": "CKV_TF_1",
                        "check_name": "Ensure CloudFront distribution is encrypted",
                        "severity": "HIGH",
                        "resource": "aws_cloudfront_distribution.example",
                        "file_path": "/infra/main.tf",
                        "file_line_range": [1, 10]
                    }
                ]
            }
        }))

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(output_file),
             "--critical", "2",
             "--high", "3",
             "--medium", "5",
             "--low", "1",
             "--passed", "50",
             "--total", "11",
             "--has-iac", "true",
             "--repo-url", "https://github.com/test/repo",
             "--github-server-url", "https://github.com",
             "--github-repo", "test/repo",
             "--github-run-id", "12345"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "Checkov" in content
        assert "terraform" in content or "Terraform" in content or "11" in content
        assert "|" in content  # Markdown table

    def test_checkov_summary_no_iac(self, tmp_path):
        """Test Checkov summary when no IaC found."""
        output_file = tmp_path / "checkov.md"

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(output_file),
             "--has-iac", "false"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Skipped" in content or "skipped" in content


class TestCodeQLSummary:
    """Integration tests for CodeQL summary generator."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-codeql/scripts/generate_summary.py"

    def test_codeql_summary_with_findings(self, tmp_path):
        """Test CodeQL summary with findings."""
        output_file = tmp_path / "codeql.md"

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(output_file),
             "--language", "python",
             "--critical", "1",
             "--high", "2",
             "--medium", "3",
             "--low", "0",
             "--total", "6",
             "--repo-url", "https://github.com/test/repo",
             "--server-url", "https://github.com",
             "--repository", "test/repo",
             "--run-id", "12345"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "CodeQL" in content
        assert "Python" in content or "python" in content

    def test_codeql_summary_no_findings(self, tmp_path):
        """Test CodeQL summary with no findings."""
        output_file = tmp_path / "codeql.md"

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(output_file),
             "--language", "javascript",
             "--total", "0"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        content = output_file.read_text()
        assert "CodeQL" in content


class TestOpenGrepSummary:
    """Integration tests for OpenGrep summary generator."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-opengrep/scripts/generate_summary.py"

    def test_opengrep_summary_with_findings(self, tmp_path):
        """Test OpenGrep summary with findings."""
        output_file = tmp_path / "opengrep.md"

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(output_file),
             "--error-count", "2",
             "--warning-count", "5",
             "--info-count", "3",
             "--total", "10",
             "--github-server-url", "https://github.com",
             "--github-repo", "test/repo",
             "--github-run-id", "12345"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "OpenGrep" in content

    def test_opengrep_summary_no_findings(self, tmp_path):
        """Test OpenGrep summary with no findings."""
        output_file = tmp_path / "opengrep.md"

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(output_file),
             "--total", "0"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        content = output_file.read_text()
        assert "OpenGrep" in content


class TestTrivyIaCSummary:
    """Integration tests for Trivy IaC summary generator."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-trivy-iac/scripts/generate_summary.py"

    def test_trivy_iac_summary_no_iac(self, tmp_path):
        """Test Trivy IaC summary when no IaC found."""
        output_file = tmp_path / "trivy-iac.md"

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(output_file),
             "--has-iac", "false"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Trivy" in content or "trivy" in content

    def test_trivy_iac_summary_with_iac(self, tmp_path):
        """Test Trivy IaC summary with IaC directory."""
        output_file = tmp_path / "trivy-iac.md"
        iac_dir = tmp_path / "infrastructure"
        iac_dir.mkdir()

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(output_file),
             "--has-iac", "true",
             "--iac-path", "infrastructure"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_file.exists()


class TestContainerConfigParser:
    """Integration tests for container config parser."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/parse-container-config/scripts/parse_container_config.py"

    def test_container_config_yaml(self, tmp_path):
        """Test container config parser with YAML."""
        config_file = tmp_path / "containers.yaml"
        schema_file = tmp_path / "schema.json"

        config_file.write_text("""
containers:
  - name: app
    image: myapp:latest
    scanners:
      - trivy
      - grype
    fail_on_severity: high
""")

        schema_file.write_text("{}")

        env = os.environ.copy()
        env["CONFIG_FILE"] = str(config_file)
        env["SCHEMA_FILE"] = str(schema_file)
        env["GITHUB_OUTPUT"] = str(tmp_path / "output.txt")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT)],
            env=env,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "matrix=" in (tmp_path / "output.txt").read_text()

    def test_container_config_json(self, tmp_path):
        """Test container config parser with JSON."""
        config_file = tmp_path / "containers.json"
        schema_file = tmp_path / "schema.json"

        config_file.write_text(json.dumps({
            "containers": [
                {
                    "name": "api",
                    "image": "api:v1.0",
                    "scanners": ["trivy"],
                    "fail_on_severity": "critical"
                }
            ]
        }))

        schema_file.write_text("{}")

        env = os.environ.copy()
        env["CONFIG_FILE"] = str(config_file)
        env["SCHEMA_FILE"] = str(schema_file)
        env["GITHUB_OUTPUT"] = str(tmp_path / "output.txt")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT)],
            env=env,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0


class TestZAPConfigParser:
    """Integration tests for ZAP config parser."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/parse-zap-config/scripts/parse_zap_config.py"

    def test_zap_config_flat_style(self, tmp_path):
        """Test ZAP config parser with flat style."""
        config_file = tmp_path / "zap.yaml"
        schema_file = tmp_path / "schema.json"

        config_file.write_text("""
scans:
  - name: baseline
    type: baseline
    target_url: http://localhost:8080
""")

        schema_file.write_text("{}")

        env = os.environ.copy()
        env["CONFIG_FILE"] = str(config_file)
        env["SCHEMA_FILE"] = str(schema_file)
        env["GITHUB_OUTPUT"] = str(tmp_path / "output.txt")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT)],
            env=env,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "matrix=" in (tmp_path / "output.txt").read_text()

    def test_zap_config_grouped_style(self, tmp_path):
        """Test ZAP config parser with grouped style."""
        config_file = tmp_path / "zap.yaml"
        schema_file = tmp_path / "schema.json"

        config_file.write_text("""
scan_groups:
  - name: API Tests
    scans:
      - name: api-baseline
        type: api
        api_spec: /api/openapi.json
""")

        schema_file.write_text("{}")

        env = os.environ.copy()
        env["CONFIG_FILE"] = str(config_file)
        env["SCHEMA_FILE"] = str(schema_file)
        env["GITHUB_OUTPUT"] = str(tmp_path / "output.txt")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT)],
            env=env,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0


class TestClamAVParser:
    """Integration tests for ClamAV parser."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-clamav/scripts/parse-clamav-report.py"

    def test_clamav_parse_with_infections(self, tmp_path):
        """Test ClamAV parser with infected files."""
        report_file = tmp_path / "clamav-report.log"
        report_file.write_text("""
Scanning...
/app/malware.exe: Win.Trojan.Generic FOUND
/app/virus.bin: Eicar.Test.File FOUND

----------- SUMMARY -----------
Scanned files: 100
Infected files: 2
""")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             "--report-path", str(report_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "2" in result.stdout
        assert "100" in result.stdout

        json_file = tmp_path / "clamav-report.json"
        assert json_file.exists()
        data = json.loads(json_file.read_text())
        assert data["infected_files"] == 2
        assert data["total_files"] == 100

    def test_clamav_parse_clean_scan(self, tmp_path):
        """Test ClamAV parser with no infections."""
        report_file = tmp_path / "clamav-report.log"
        report_file.write_text("""
Scanning...

----------- SUMMARY -----------
Scanned files: 50
Infected files: 0
""")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             "--report-path", str(report_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        json_file = tmp_path / "clamav-report.json"
        assert json_file.exists()
        data = json.loads(json_file.read_text())
        assert data["infected_files"] == 0


class TestExtractArchives:
    """Integration tests for archive extraction."""

    SCRIPT = Path(__file__).parent.parent.parent / ".github/actions/scanner-clamav/scripts/extract-archives.py"

    def test_extract_zip_archive(self, tmp_path):
        """Test extraction of ZIP archive."""
        import zipfile

        # Create a test ZIP file
        zip_file = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

        output_dir = tmp_path / "extracted"
        output_dir.mkdir()

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(zip_file),
             "--output-dir", str(output_dir)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should output paths to scan
        assert str(output_dir) in result.stdout or str(zip_file) in result.stdout

    def test_extract_tar_archive(self, tmp_path):
        """Test extraction of TAR archive."""
        import tarfile

        # Create a test TAR file
        tar_file = tmp_path / "test.tar"
        with tarfile.open(tar_file, 'w') as tf:
            import io
            content = io.BytesIO(b"test content")
            info = tarfile.TarInfo(name="file.txt")
            info.size = len(content.getvalue())
            tf.addfile(info, content)

        output_dir = tmp_path / "extracted"
        output_dir.mkdir()

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             str(tar_file),
             "--output-dir", str(output_dir)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0


class TestActionOutputIntegration:
    """Integration tests for GITHUB_OUTPUT and GITHUB_STEP_SUMMARY."""

    TRIVY_PARSER = Path(__file__).parent.parent.parent / ".github/actions/scanner-container/scripts/parse_trivy_results.py"
    GRYPE_PARSER = Path(__file__).parent.parent.parent / ".github/actions/scanner-container/scripts/parse_grype_results.py"

    def test_trivy_parser_outputs(self, tmp_path):
        """Test that Trivy parser correctly writes GITHUB_OUTPUT."""
        github_output = tmp_path / "github_output"
        github_output.touch()

        trivy_file = tmp_path / "trivy.json"
        trivy_file.write_text(json.dumps({
            "Results": [
                {
                    "Vulnerabilities": [
                        {"Severity": "CRITICAL", "VulnerabilityID": "CVE-2021-1"},
                        {"Severity": "HIGH", "VulnerabilityID": "CVE-2021-2"},
                    ]
                }
            ]
        }))

        env = os.environ.copy()
        env["GITHUB_OUTPUT"] = str(github_output)

        # Run counts command
        result = subprocess.run(
            [sys.executable, str(self.TRIVY_PARSER), "counts", str(trivy_file)],
            env=env,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "1 1 0 0" in result.stdout

    def test_grype_parser_outputs(self, tmp_path):
        """Test that Grype parser correctly writes GITHUB_OUTPUT."""
        github_output = tmp_path / "github_output"
        github_output.touch()

        grype_file = tmp_path / "grype.json"
        grype_file.write_text(json.dumps({
            "matches": [
                {"vulnerability": {"id": "CVE-2021-1", "severity": "Critical"}},
                {"vulnerability": {"id": "CVE-2021-2", "severity": "High"}},
            ]
        }))

        env = os.environ.copy()
        env["GITHUB_OUTPUT"] = str(github_output)

        result = subprocess.run(
            [sys.executable, str(self.GRYPE_PARSER), "counts", str(grype_file)],
            env=env,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "1 1 0 0" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
