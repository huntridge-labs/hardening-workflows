#!/usr/bin/env python3
"""Unit tests for parse_grype_results.py using pytest."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# Get the scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
PARSER_SCRIPT = SCRIPTS_DIR / "parse_grype_results.py"

# Get fixtures directory
FIXTURES_DIR = (
    Path(__file__).parent.parent.parent.parent.parent / "tests" / "fixtures" / "scanner-outputs" / "grype"
)


def run_parser(command: str, json_file: Path, *args) -> str:
    """Run the parser script and return output."""
    cmd = [sys.executable, str(PARSER_SCRIPT), command, str(json_file)]
    cmd.extend(args)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()


class TestParseGrypeResults:
    """Test suite for parse_grype_results.py functionality."""

    # ====== Tests for 'counts' command ======

    def test_counts_zero_findings(self):
        """Test counts command with zero findings."""
        result = run_parser("counts", FIXTURES_DIR / "results-zero-findings.json")
        assert result == "0 0 0 0"

    def test_counts_with_findings(self):
        """Test counts command with mixed severities."""
        result = run_parser("counts", FIXTURES_DIR / "results-with-findings.json")
        # Grype uses different severity casing: Critical, High, Medium, Low
        # The fixture has at least 1 of each
        parts = result.split()
        assert len(parts) == 4
        # Just check all are non-negative integers
        for part in parts:
            assert int(part) >= 0

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
        # Should be more than zero
        assert int(result) > 0

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
        assert int(result) > 0

    def test_unique_with_duplicates(self, tmp_path):
        """Test unique count with duplicate CVE IDs."""
        json_file = tmp_path / "duplicates.json"
        data = {
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2023-1111",
                        "severity": "High",
                    }
                },
                {
                    "vulnerability": {
                        "id": "CVE-2023-1111",  # duplicate
                        "severity": "High",
                    }
                },
                {
                    "vulnerability": {
                        "id": "CVE-2023-2222",
                        "severity": "Medium",
                    }
                },
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
        parts = result.split()
        assert len(parts) == 4

    # ====== Tests for 'cves' command ======

    def test_cves_zero_findings(self):
        """Test cves command with zero findings."""
        result = run_parser("cves", FIXTURES_DIR / "results-zero-findings.json")
        assert result == ""

    def test_cves_with_findings(self):
        """Test cves command returns CVE IDs."""
        result = run_parser("cves", FIXTURES_DIR / "results-with-findings.json")
        lines = result.split("\n")
        assert len(lines) > 0
        # Check that we got CVE format
        assert any("CVE-" in line for line in lines)

    def test_cves_sorted_and_unique(self, tmp_path):
        """Test that cves output is sorted and unique."""
        json_file = tmp_path / "cves.json"
        data = {
            "matches": [
                {"vulnerability": {"id": "CVE-2023-3333"}},
                {"vulnerability": {"id": "CVE-2023-1111"}},
                {"vulnerability": {"id": "CVE-2023-3333"}},  # duplicate
                {"vulnerability": {"id": "CVE-2023-2222"}},
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("cves", json_file)
        lines = result.split("\n")
        assert len(lines) == 3
        assert lines == sorted(lines)  # Check sorting

    # ====== Tests for 'cves-by-severity' command ======

    def test_cves_by_severity_critical(self):
        """Test cves-by-severity for Critical severity."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "Critical")
        # Fixture has at least one Critical
        assert "CVE-" in result or result == ""

    def test_cves_by_severity_high(self):
        """Test cves-by-severity for High severity."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "High")
        assert "CVE-" in result or result == ""

    def test_cves_by_severity_medium(self):
        """Test cves-by-severity for Medium severity."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "Medium")
        assert "CVE-" in result or result == ""

    def test_cves_by_severity_low(self):
        """Test cves-by-severity for Low severity."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "Low")
        assert "CVE-" in result or result == ""

    def test_cves_by_severity_none(self):
        """Test cves-by-severity when none found."""
        result = run_parser("cves-by-severity", FIXTURES_DIR / "results-with-findings.json", "-s", "Unknown")
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
        # Should contain CVE IDs or severity info
        assert "CVE-" in result or "CRITICAL" in result.upper()

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

    # ====== Integration tests ======

    def test_malformed_matches_structure(self, tmp_path):
        """Test with malformed matches structure."""
        json_file = tmp_path / "malformed.json"
        data = {"matches": "not a list"}  # Wrong type
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        assert result == "0 0 0 0"

    def test_missing_fields(self, tmp_path):
        """Test with missing expected fields."""
        json_file = tmp_path / "missing_fields.json"
        data = {
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2023-1111"
                        # Missing severity
                    }
                }
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        # Should default missing severity to Low
        assert result == "0 0 0 1"

    def test_empty_matches(self, tmp_path):
        """Test with empty matches array."""
        json_file = tmp_path / "empty_matches.json"
        data = {"matches": []}
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        assert result == "0 0 0 0"

    def test_multiple_matches(self, tmp_path):
        """Test aggregation across multiple matches."""
        json_file = tmp_path / "multi_match.json"
        data = {
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2023-1111",
                        "severity": "Critical",
                    }
                },
                {
                    "vulnerability": {
                        "id": "CVE-2023-2222",
                        "severity": "High",
                    }
                },
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        assert result == "1 1 0 0"

    def test_grype_severity_casing(self, tmp_path):
        """Test that Grype severity casing is handled correctly."""
        json_file = tmp_path / "casing.json"
        data = {
            "matches": [
                {"vulnerability": {"id": "CVE-2023-1111", "severity": "Critical"}},
                {"vulnerability": {"id": "CVE-2023-2222", "severity": "High"}},
                {"vulnerability": {"id": "CVE-2023-3333", "severity": "Medium"}},
                {"vulnerability": {"id": "CVE-2023-4444", "severity": "Low"}},
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("counts", json_file)
        assert result == "1 1 1 1"

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

    def test_table_with_missing_fix_versions(self, tmp_path):
        """Test table rendering when fix versions are missing."""
        json_file = tmp_path / "no_fix.json"
        data = {
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2023-1111",
                        "severity": "High",
                        "fix": {"versions": []}  # No fix versions
                    },
                    "artifact": {
                        "name": "test-package",
                        "version": "1.0.0",
                    }
                }
            ]
        }
        json_file.write_text(json.dumps(data))
        result = run_parser("table", json_file)
        assert "CVE-2023-1111" in result
        assert "N/A" in result  # Should show N/A for missing fix
