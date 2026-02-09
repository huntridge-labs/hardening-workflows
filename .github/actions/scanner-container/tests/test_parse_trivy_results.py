#!/usr/bin/env python3
"""Unit tests for parse_trivy_results.py using pytest."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# Get the scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
PARSER_SCRIPT = SCRIPTS_DIR / "parse_trivy_results.py"

# Get fixtures directory
FIXTURES_DIR = (
    Path(__file__).parent.parent.parent.parent.parent / "tests" / "fixtures" / "scanner-outputs" / "trivy"
)


def run_parser(command: str, json_file: Path, *args) -> str:
    """Run the parser script and return output."""
    cmd = [sys.executable, str(PARSER_SCRIPT), command, str(json_file)]
    cmd.extend(args)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()


class TestParseTrivyResults:
    """Test suite for parse_trivy_results.py functionality."""

    # ====== Tests for 'counts' command ======

    def test_counts_zero_findings(self):
        """Test counts command with zero findings."""
        result = run_parser("counts", FIXTURES_DIR / "results-zero-findings.json")
        assert result == "0 0 0 0"

    def test_counts_with_findings(self):
        """Test counts command with mixed severities."""
        result = run_parser("counts", FIXTURES_DIR / "results-with-findings.json")
        assert result == "1 1 1 1"

    def test_counts_nonexistent_file(self):
        """Test counts with nonexistent file."""
        result = run_parser("counts", Path("/nonexistent/file.json"))
        assert result == "0 0 0 0"

    def test_counts_empty_file(self, tmp_path):
        """Test counts with empty file."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")
        result = run_parser("counts", empty_file)
        assert result == "0 0 0 0"

    def test_counts_invalid_json(self, tmp_path):
        """Test counts with invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json")
        result = run_parser("counts", bad_file)
        assert result == "0 0 0 0"

    # ====== Tests for 'total' command ======

    def test_total_zero_findings(self):
        """Test total command with zero findings."""
        result = run_parser("total", FIXTURES_DIR / "results-zero-findings.json")
        assert result == "0"

    def test_total_with_findings(self):
        """Test total command with findings."""
        result = run_parser("total", FIXTURES_DIR / "results-with-findings.json")
        assert result == "4"

    def test_total_nonexistent_file(self):
        """Test total with nonexistent file."""
        result = run_parser("total", Path("/nonexistent/file.json"))
        assert result == "0"

    # ====== Tests for 'unique' command ======

    def test_unique_zero_findings(self):
        """Test unique command with zero findings."""
        result = run_parser("unique", FIXTURES_DIR / "results-zero-findings.json")
        assert result == "0"

    def test_unique_with_findings(self):
        """Test unique command with findings."""
        result = run_parser("unique", FIXTURES_DIR / "results-with-findings.json")
        assert result == "4"

    def test_unique_with_duplicates(self, tmp_path):
        """Test unique count with duplicate CVE IDs."""
        json_file = tmp_path / "duplicates.json"
        data = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"VulnerabilityID": "CVE-2023-1111", "Severity": "HIGH"},
                        {"VulnerabilityID": "CVE-2023-1111", "Severity": "HIGH"},  # duplicate
                        {"VulnerabilityID": "CVE-2023-2222", "Severity": "MEDIUM"},
                    ]
                }
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("unique", json_file)
        assert result == "2"

    # ====== Tests for 'unique-by-severity' command ======

    def test_unique_by_severity_zero_findings(self):
        """Test unique-by-severity with zero findings."""
        result = run_parser("unique-by-severity", FIXTURES_DIR / "results-zero-findings.json")
        assert result == "0 0 0 0"

    def test_unique_by_severity_with_findings(self):
        """Test unique-by-severity with findings."""
        result = run_parser("unique-by-severity", FIXTURES_DIR / "results-with-findings.json")
        assert result == "1 1 1 1"

    # ====== Tests for 'cves' command ======

    def test_cves_zero_findings(self):
        """Test cves command with zero findings."""
        result = run_parser("cves", FIXTURES_DIR / "results-zero-findings.json")
        assert result == ""

    def test_cves_with_findings(self):
        """Test cves command returns CVE IDs."""
        result = run_parser("cves", FIXTURES_DIR / "results-with-findings.json")
        lines = result.split("\n")
        assert len(lines) == 4
        assert "CVE-2023-1234" in result
        assert "CVE-2023-5678" in result

    def test_cves_sorted_and_unique(self, tmp_path):
        """Test that cves output is sorted and unique."""
        json_file = tmp_path / "cves.json"
        data = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"VulnerabilityID": "CVE-2023-3333"},
                        {"VulnerabilityID": "CVE-2023-1111"},
                        {"VulnerabilityID": "CVE-2023-3333"},  # duplicate
                        {"VulnerabilityID": "CVE-2023-2222"},
                    ]
                }
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("cves", json_file)
        lines = result.split("\n")
        assert len(lines) == 3
        assert lines == sorted(lines)  # Check sorting

    # ====== Tests for 'cves-by-severity' command ======

    def test_cves_by_severity_critical(self):
        """Test cves-by-severity for CRITICAL severity."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "CRITICAL")
        assert "CVE-2023-1234" in result

    def test_cves_by_severity_high(self):
        """Test cves-by-severity for HIGH severity."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "HIGH")
        assert "CVE-2023-5678" in result

    def test_cves_by_severity_medium(self):
        """Test cves-by-severity for MEDIUM severity."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "MEDIUM")
        assert "CVE-2023-9012" in result

    def test_cves_by_severity_low(self):
        """Test cves-by-severity for LOW severity."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "LOW")
        assert "CVE-2024-0001" in result

    def test_cves_by_severity_none(self):
        """Test cves-by-severity when none found."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "UNKNOWN")
        assert result == ""

    def test_cves_by_severity_missing_flag(self):
        """Test cves-by-severity without severity flag."""
        cmd = [sys.executable, str(PARSER_SCRIPT), "cves-by-severity", str(FIXTURES_DIR / "results-with-findings.json")]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        assert result.returncode != 0

    # ====== Tests for 'table' command ======

    def test_table_zero_findings(self):
        """Test table command with zero findings."""
        result = run_parser("table", FIXTURES_DIR / "results-zero-findings.json")
        assert "No data" in result

    def test_table_with_findings(self):
        """Test table command generates markdown."""
        result = run_parser("table", FIXTURES_DIR / "results-with-findings.json")
        # Should contain pipe separators
        assert "|" in result
        # Should contain CVE IDs
        assert "CVE-2023-1234" in result or "CVE-" in result

    def test_table_limit(self):
        """Test table command respects limit."""
        result = run_parser("table", FIXTURES_DIR / "results-with-findings.json", "-l", "2")
        lines = [l for l in result.split("\n") if "|" in l and "CVE" in l]
        assert len(lines) <= 2

    def test_table_contains_severity_emoji(self):
        """Test that table output contains severity emojis."""
        result = run_parser("table", FIXTURES_DIR / "results-with-findings.json")
        # Check for at least one severity emoji
        assert any(emoji in result for emoji in ["🚨", "⚠️", "🟡", "🔵"])

    # ====== Tests for 'digest' command ======

    def test_digest_with_findings(self):
        """Test digest extraction."""
        result = run_parser("digest", FIXTURES_DIR / "results-with-findings.json")
        assert result != "unknown"
        assert "sha256:" in result or len(result) > 10

    def test_digest_zero_findings(self):
        """Test digest with zero findings (alpine:latest)."""
        result = run_parser("digest", FIXTURES_DIR / "results-zero-findings.json")
        assert result != "unknown"

    def test_digest_nonexistent_file(self):
        """Test digest with nonexistent file."""
        result = run_parser("digest", Path("/nonexistent/file.json"))
        assert result == "unknown"

    # ====== Tests for 'image' command ======

    def test_image_with_findings(self):
        """Test image ref extraction."""
        result = run_parser("image", FIXTURES_DIR / "results-with-findings.json")
        assert result != "unknown"
        assert ":" in result  # Should be image:tag format

    def test_image_zero_findings(self):
        """Test image ref with zero findings."""
        result = run_parser("image", FIXTURES_DIR / "results-zero-findings.json")
        assert result != "unknown"
        assert "alpine" in result.lower()

    def test_image_nonexistent_file(self):
        """Test image with nonexistent file."""
        result = run_parser("image", Path("/nonexistent/file.json"))
        assert result == "unknown"

    # ====== Integration tests ======

    def test_malformed_results_structure(self, tmp_path):
        """Test with malformed Results structure."""
        json_file = tmp_path / "malformed.json"
        data = {"Results": "not a list"}  # Wrong type
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        assert result == "0 0 0 0"

    def test_missing_fields(self, tmp_path):
        """Test with missing expected fields."""
        json_file = tmp_path / "missing_fields.json"
        data = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"VulnerabilityID": "CVE-2023-1111"}  # Missing Severity
                    ]
                }
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        # Should default missing Severity to LOW
        assert result == "0 0 0 1"

    def test_empty_results(self, tmp_path):
        """Test with empty Results array."""
        json_file = tmp_path / "empty_results.json"
        data = {"Results": []}
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        assert result == "0 0 0 0"

    def test_multiple_result_entries(self, tmp_path):
        """Test aggregation across multiple Result entries."""
        json_file = tmp_path / "multi_result.json"
        data = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"VulnerabilityID": "CVE-2023-1111", "Severity": "CRITICAL"}
                    ]
                },
                {
                    "Vulnerabilities": [
                        {"VulnerabilityID": "CVE-2023-2222", "Severity": "HIGH"}
                    ]
                },
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        assert result == "1 1 0 0"

    def test_help_command(self):
        """Test help flag."""
        cmd = [sys.executable, str(PARSER_SCRIPT), "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        assert "counts" in result.stdout

    def test_unknown_command(self):
        """Test unknown command."""
        cmd = [sys.executable, str(PARSER_SCRIPT), "unknown", str(FIXTURES_DIR / "results-zero-findings.json")]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        assert result.returncode != 0
        assert "Unknown command" in result.stderr
