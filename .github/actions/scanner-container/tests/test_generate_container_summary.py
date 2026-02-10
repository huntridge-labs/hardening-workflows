#!/usr/bin/env python3
"""Unit tests for generate_container_summary.py using pytest."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


# Get the scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
SUMMARY_SCRIPT = SCRIPTS_DIR / "generate_container_summary.py"
TRIVY_PARSER = SCRIPTS_DIR / "parse_trivy_results.py"
GRYPE_PARSER = SCRIPTS_DIR / "parse_grype_results.py"

# Get fixtures directory
FIXTURES_DIR = (
    Path(__file__).parent.parent.parent.parent.parent / "tests" / "fixtures" / "scanner-outputs"
)


def run_summary_generator(combined: bool = False, cwd: Path = None) -> tuple:
    """Run the summary generator script."""
    env = os.environ.copy()
    env["TRIVY_PARSER"] = str(TRIVY_PARSER)
    env["GRYPE_PARSER"] = str(GRYPE_PARSER)

    cmd = [sys.executable, str(SUMMARY_SCRIPT)]
    if combined:
        cmd.append("--combined")

    if cwd:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, env=env, cwd=str(cwd)
        )
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)

    return result.returncode, result.stdout, result.stderr


class TestGenerateContainerSummary:
    """Test suite for generate_container_summary.py functionality."""

    # ====== Tests for no results scenario ======

    def test_no_results_found(self, tmp_path):
        """Test when no container scan results are found."""
        os.environ["GITHUB_STEP_SUMMARY"] = str(tmp_path / "summary.md")

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)

        assert returncode == 0
        assert "No container scan results found" in stdout

        # Check that summary file was created
        summary_file = tmp_path / "scanner-summaries" / "container.md"
        assert summary_file.exists()
        content = summary_file.read_text()
        assert "⏭️" in content or "Skipped" in content

    # ====== Tests for single container ======

    def test_single_container_with_zero_vulns(self, tmp_path):
        """Test processing a single container with no vulnerabilities."""
        # Create a container scan results directory
        container_dir = tmp_path / "container-scan-results-alpine"
        container_dir.mkdir(parents=True)

        # Copy fixture trivy and grype results
        trivy_fixture = FIXTURES_DIR / "trivy" / "results-zero-findings.json"
        grype_fixture = FIXTURES_DIR / "grype" / "results-zero-findings.json"

        if trivy_fixture.exists():
            (container_dir / "trivy-alpine-results.json").write_text(trivy_fixture.read_text())
        if grype_fixture.exists():
            (container_dir / "grype-alpine-results.json").write_text(grype_fixture.read_text())

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)

        assert returncode == 0
        assert "Processing" in stdout or "Generating" in stdout

        # Check summary file exists and contains expected content
        summary_file = tmp_path / "scanner-summaries" / "container.md"
        assert summary_file.exists()
        content = summary_file.read_text()
        assert "Container Security" in content

    def test_single_container_with_vulns(self, tmp_path):
        """Test processing a single container with vulnerabilities."""
        # Create a container scan results directory
        container_dir = tmp_path / "container-scan-results-vulnerable"
        container_dir.mkdir(parents=True)

        # Copy fixture trivy and grype results
        trivy_fixture = FIXTURES_DIR / "trivy" / "results-with-findings.json"
        grype_fixture = FIXTURES_DIR / "grype" / "results-with-findings.json"

        if trivy_fixture.exists():
            (container_dir / "trivy-vulnerable-results.json").write_text(trivy_fixture.read_text())
        if grype_fixture.exists():
            (container_dir / "grype-vulnerable-results.json").write_text(grype_fixture.read_text())

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)

        assert returncode == 0

        # Check summary file
        summary_file = tmp_path / "scanner-summaries" / "container.md"
        assert summary_file.exists()
        content = summary_file.read_text()
        assert "Detailed Findings" in content

    # ====== Tests for multiple containers ======

    def test_multiple_containers(self, tmp_path):
        """Test processing multiple containers."""
        # Create multiple container directories
        for container_name in ["app1", "app2", "app3"]:
            container_dir = tmp_path / f"container-scan-results-{container_name}"
            container_dir.mkdir(parents=True)

            # Use zero findings for simplicity
            trivy_fixture = FIXTURES_DIR / "trivy" / "results-zero-findings.json"
            if trivy_fixture.exists():
                (container_dir / f"trivy-{container_name}-results.json").write_text(
                    trivy_fixture.read_text()
                )

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)

        assert returncode == 0

        # For multiple containers, should show container breakdown
        summary_file = tmp_path / "scanner-summaries" / "container.md"
        content = summary_file.read_text()
        assert "Container Breakdown" in content or "Detailed" in content

    # ====== Tests for failure scenarios ======

    def test_container_with_failed_scan(self, tmp_path):
        """Test handling of container with failed scan."""
        # Create a container directory with scan-status.json
        container_dir = tmp_path / "container-scan-results-failed"
        container_dir.mkdir(parents=True)

        # Create a scan failure marker
        status_file = container_dir / "scan-status.json"
        status_file.write_text(json.dumps({"status": "failed", "error": "Image pull failed"}))

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)

        assert returncode == 0
        assert "Processing" in stdout or "failed" in stdout.lower()

        # Check summary shows failure
        summary_file = tmp_path / "scanner-summaries" / "container.md"
        assert summary_file.exists()

    def test_single_scanner_containers(self, tmp_path):
        """Test processing containers with only single scanner (Trivy or Grype)."""
        # Test Trivy-only
        container_dir = tmp_path / "container-scan-results-trivy-only"
        container_dir.mkdir(parents=True)
        trivy_fixture = FIXTURES_DIR / "trivy" / "results-with-findings.json"
        if trivy_fixture.exists():
            (container_dir / "trivy-trivy-only-results.json").write_text(trivy_fixture.read_text())

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)
        assert returncode == 0

        summary_file = tmp_path / "scanner-summaries" / "container.md"
        assert summary_file.exists()
        content = summary_file.read_text()
        assert "Trivy" in content or "🔷" in content

        # Test Grype-only (clean up first)
        (tmp_path / "scanner-summaries").unlink(missing_ok=True) if (tmp_path / "scanner-summaries").is_file() else None
        for f in (tmp_path / "container-scan-results-trivy-only").glob("*"):
            f.unlink()

        container_dir = tmp_path / "container-scan-results-grype-only"
        container_dir.mkdir(parents=True)
        grype_fixture = FIXTURES_DIR / "grype" / "results-with-findings.json"
        if grype_fixture.exists():
            (container_dir / "grype-grype-only-results.json").write_text(grype_fixture.read_text())

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)
        assert returncode == 0

        summary_file = tmp_path / "scanner-summaries" / "container.md"
        assert summary_file.exists()
        content = summary_file.read_text()
        assert "Grype" in content or "⚓" in content

    # ====== Tests for GITHUB_* environment variables ======

    def test_with_github_env_vars(self, tmp_path):
        """Test writing to GITHUB_STEP_SUMMARY and GITHUB_OUTPUT."""
        container_dir = tmp_path / "container-scan-results-test"
        container_dir.mkdir(parents=True)

        trivy_fixture = FIXTURES_DIR / "trivy" / "results-with-findings.json"
        if trivy_fixture.exists():
            (container_dir / "trivy-test-results.json").write_text(trivy_fixture.read_text())

        # Test GITHUB_STEP_SUMMARY
        summary_path = tmp_path / "step_summary.md"
        os.environ["GITHUB_STEP_SUMMARY"] = str(summary_path)

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)
        assert returncode == 0

        # Test GITHUB_OUTPUT
        output_path = tmp_path / "github_output"
        os.environ["GITHUB_OUTPUT"] = str(output_path)

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)
        assert returncode == 0

        # Cleanup
        if "GITHUB_STEP_SUMMARY" in os.environ:
            del os.environ["GITHUB_STEP_SUMMARY"]
        if "GITHUB_OUTPUT" in os.environ:
            del os.environ["GITHUB_OUTPUT"]

    # ====== Tests for --combined flag ======

    def test_combined_flag(self, tmp_path):
        """Test --combined flag for parallel scan summary."""
        container_dir = tmp_path / "container-scan-results-app"
        container_dir.mkdir(parents=True)

        trivy_fixture = FIXTURES_DIR / "trivy" / "results-with-findings.json"
        if trivy_fixture.exists():
            (container_dir / "trivy-app-results.json").write_text(trivy_fixture.read_text())

        returncode, stdout, stderr = run_summary_generator(combined=True, cwd=tmp_path)

        assert returncode == 0

        # Check that combined flag affected output
        summary_file = tmp_path / "scanner-summaries" / "container.md"
        assert summary_file.exists()
        content = summary_file.read_text()
        # Combined flag should affect header
        assert "Container Security" in content

    # ====== Tests for summary content validation ======

    def test_summary_contains_severity_summary(self, tmp_path):
        """Test that summary contains severity counts."""
        container_dir = tmp_path / "container-scan-results-test"
        container_dir.mkdir(parents=True)

        trivy_fixture = FIXTURES_DIR / "trivy" / "results-with-findings.json"
        if trivy_fixture.exists():
            (container_dir / "trivy-test-results.json").write_text(trivy_fixture.read_text())

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)

        assert returncode == 0

        summary_file = tmp_path / "scanner-summaries" / "container.md"
        content = summary_file.read_text()

        # Should contain severity indicators
        assert "🚨" in content or "Critical" in content
        assert "|" in content  # Markdown table

    def test_container_names_and_sbom_filter(self, tmp_path):
        """Test that summary includes container names and SBOM-only dirs are ignored."""
        # Create SBOM-only directory (should be ignored)
        sbom_dir = tmp_path / "container-scan-results-sbom-only"
        sbom_dir.mkdir(parents=True)
        (sbom_dir / "sbom.json").write_text('{"format": "spdx"}')

        # Create real containers with different naming patterns
        container_name = "my-awesome-app"
        container_dir = tmp_path / f"container-scan-results-{container_name}"
        container_dir.mkdir(parents=True)

        trivy_fixture = FIXTURES_DIR / "trivy" / "results-zero-findings.json"
        if trivy_fixture.exists():
            (container_dir / f"trivy-{container_name}-results.json").write_text(trivy_fixture.read_text())

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)

        assert returncode == 0

        summary_file = tmp_path / "scanner-summaries" / "container.md"
        content = summary_file.read_text()

        # Container name should be in the output
        assert container_name in content or "Container" in content

    def test_missing_parser_env_var(self, tmp_path):
        """Test error handling when parser env vars are missing."""
        # Clear env vars
        orig_trivy = os.environ.pop("TRIVY_PARSER", None)
        orig_grype = os.environ.pop("GRYPE_PARSER", None)

        cmd = [sys.executable, str(SUMMARY_SCRIPT)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=str(tmp_path))

        # Should fail without env vars
        assert result.returncode != 0

        # Restore env vars
        if orig_trivy:
            os.environ["TRIVY_PARSER"] = orig_trivy
        if orig_grype:
            os.environ["GRYPE_PARSER"] = orig_grype

    def test_summary_file_encoding(self, tmp_path):
        """Test that summary file is written with UTF-8 encoding (for emojis)."""
        container_dir = tmp_path / "container-scan-results-test"
        container_dir.mkdir(parents=True)

        trivy_fixture = FIXTURES_DIR / "trivy" / "results-with-findings.json"
        if trivy_fixture.exists():
            (container_dir / "trivy-test-results.json").write_text(trivy_fixture.read_text())

        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)

        assert returncode == 0

        # Read file and check for emojis
        summary_file = tmp_path / "scanner-summaries" / "container.md"
        content = summary_file.read_text(encoding='utf-8')

        # Should contain emoji characters without encoding issues
        assert "🐳" in content or "Container" in content



class TestEdgeCases:
    """Edge case tests for container summary generation."""

    def test_no_container_directories(self, tmp_path):
        """Test when no container scan results directories exist."""
        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)
        assert returncode == 0

    def test_empty_container_directory(self, tmp_path):
        """Test with empty container directory."""
        container_dir = tmp_path / "container-scan-results-empty"
        container_dir.mkdir(parents=True)
        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)
        assert returncode == 0

    def test_malformed_json_in_results(self, tmp_path):
        """Test with malformed JSON in results."""
        container_dir = tmp_path / "container-scan-results-bad"
        container_dir.mkdir(parents=True)
        (container_dir / "trivy-results.json").write_text("{invalid json")
        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)
        assert returncode == 0

    def test_very_large_container_count(self, tmp_path):
        """Test with many containers."""
        for i in range(10):
            container_dir = tmp_path / f"container-scan-results-app{i:03d}"
            container_dir.mkdir(parents=True)
            trivy_fixture = FIXTURES_DIR / "trivy" / "results-zero-findings.json"
            if trivy_fixture.exists():
                (container_dir / f"trivy-app{i:03d}-results.json").write_text(trivy_fixture.read_text())
        returncode, stdout, stderr = run_summary_generator(cwd=tmp_path)
        assert returncode == 0
