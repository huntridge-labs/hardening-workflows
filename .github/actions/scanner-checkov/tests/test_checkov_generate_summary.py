#!/usr/bin/env python3
"""
Unit tests for scanner-checkov/scripts/generate_summary.py
Tests markdown generation for Checkov IaC security scan results
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
GENERATOR_SCRIPT = SCRIPTS_DIR / "generate_summary.py"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "scanner-outputs" / "checkov"


class TestCheckovGenerateSummary:
    """Test cases for scanner-checkov generate-summary.sh"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test workspace for each test."""
        self.workspace = tmp_path
        self.checkov_reports = tmp_path / "checkov-reports"
        self.checkov_reports.mkdir(parents=True)
        self.output_file = tmp_path / "summary.md"
        # Change to workspace directory
        self.original_dir = os.getcwd()
        os.chdir(tmp_path)
        yield
        os.chdir(self.original_dir)

    def run_generator(
        self,
        output_file=None,
        is_pr_comment="false",
        has_iac="true",
        iac_path="infrastructure",
        critical="0",
        high="0",
        medium="0",
        low="0",
        passed="0",
        total="0",
        repo_url="https://github.com/test/repo/blob/main",
        github_server_url="https://github.com",
        github_repo="test/repo",
        github_run_id="12345",
    ):
        """Helper to run the generator script with arguments."""
        if output_file is None:
            output_file = str(self.output_file)

        cmd = [
            sys.executable,
            str(GENERATOR_SCRIPT),
            str(output_file),
            "--is-pr-comment", is_pr_comment,
            "--has-iac", has_iac,
            "--iac-path", iac_path,
            "--critical", critical,
            "--high", high,
            "--medium", medium,
            "--low", low,
            "--passed", passed,
            "--total", total,
            "--repo-url", repo_url,
            "--github-server-url", github_server_url,
            "--github-repo", github_repo,
            "--github-run-id", github_run_id,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.workspace,
        )
        return result

    def test_script_exists(self):
        """Verify generator script exists."""
        assert GENERATOR_SCRIPT.exists(), f"Script not found: {GENERATOR_SCRIPT}"

    def test_fixtures_exist(self):
        """Verify required fixtures exist."""
        assert FIXTURES_DIR.exists(), f"Fixtures not found: {FIXTURES_DIR}"
        assert (FIXTURES_DIR / "results-with-findings.json").exists()
        assert (FIXTURES_DIR / "results-zero-findings.json").exists()

    def test_missing_output_file_argument(self):
        """Test error when output file argument is missing."""
        result = subprocess.run(
            [sys.executable, str(GENERATOR_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=self.workspace,
        )
        assert result.returncode != 0
        assert "required: output_file" in result.stderr or "the following arguments are required: output_file" in result.stderr

    def test_generates_summary_with_findings(self):
        """Test generating summary with findings."""
        # Copy fixture
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        # Run generator (5 findings: 2 HIGH, 2 MEDIUM, 1 LOW)
        result = self.run_generator(
            has_iac="true",
            critical="0",
            high="2",
            medium="2",
            low="1",
            passed="8",
            total="5",
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert self.output_file.exists(), "Output file not created"

        content = self.output_file.read_text()

        # Check for key elements
        assert "Checkov IaC Security" in content
        assert "Check Summary" in content
        # Check table row with counts
        assert "| **0** | **2** | **2** | **1** | **5** | **8** |" in content

    def test_generates_summary_zero_findings(self):
        """Test generating summary with zero findings."""
        shutil.copy(
            FIXTURES_DIR / "results-zero-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            has_iac="true",
            critical="0",
            high="0",
            medium="0",
            low="0",
            passed="12",
            total="0",
        )

        assert result.returncode == 0
        assert self.output_file.exists()

        content = self.output_file.read_text()
        assert "All 12 security checks passed" in content

    def test_skipped_no_iac_directory(self):
        """Test skipped status when no IaC directory."""
        result = self.run_generator(
            has_iac="false",
            iac_path="",
        )

        assert result.returncode == 0
        assert self.output_file.exists()

        content = self.output_file.read_text()
        assert "Skipped" in content
        assert "no IaC directory" in content

    def test_pr_comment_format_collapsible(self):
        """Test PR comment format uses collapsible sections."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            is_pr_comment="true",
            has_iac="true",
            high="2",
            medium="2",
            low="1",
            passed="8",
            total="5",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()

        # PR comment should use collapsible format
        assert "<details>" in content
        assert "<summary>" in content
        assert "</details>" in content

    def test_high_severity_priority_message(self):
        """Test HIGH severity priority message appears."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            has_iac="true",
            critical="0",
            high="2",
            medium="0",
            low="0",
            passed="8",
            total="2",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        assert "HIGH" in content
        assert "2 high severity issues" in content

    def test_critical_severity_priority_message(self):
        """Test CRITICAL severity priority message appears."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            has_iac="true",
            critical="3",
            high="2",
            medium="0",
            low="0",
            passed="8",
            total="5",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        assert "CRITICAL" in content
        assert "3 critical severity issues" in content

    def test_failed_checks_details_section(self):
        """Test failed checks details section is present."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            has_iac="true",
            high="2",
            medium="2",
            low="1",
            passed="8",
            total="5",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        assert "Failed Check Details" in content
        assert "Check ID" in content
        assert "Check Name" in content

    def test_artifact_link_present(self):
        """Test artifact link is present in output."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            has_iac="true",
            github_repo="test/repo",
            github_run_id="12345",
            total="5",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        assert "https://github.com/test/repo/actions/runs/12345" in content

    def test_handles_missing_json_file(self):
        """Test handles missing JSON file gracefully."""
        # Don't copy any JSON file
        result = self.run_generator(has_iac="true")

        assert result.returncode == 0
        assert self.output_file.exists()

        content = self.output_file.read_text()
        assert "No results" in content or "No Checkov results" in content

    def test_severity_grouping_with_data(self):
        """Test severity grouping when severity data is available."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            has_iac="true",
            high="2",
            medium="2",
            low="1",
            passed="8",
            total="5",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()

        # With severity data in fixture, should group by severity levels
        assert "HIGH Severity" in content
        assert "MEDIUM Severity" in content

    def test_framework_info_displayed(self):
        """Test framework info is displayed."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            has_iac="true",
            total="5",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        assert "Framework:" in content

    def test_non_pr_format_has_heading(self):
        """Test non-PR format uses heading instead of details tag."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.json",
            self.checkov_reports / "checkov-results.json",
        )

        result = self.run_generator(
            is_pr_comment="false",
            has_iac="true",
            total="5",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()

        # Non-PR format should have ## heading
        assert "## " in content
        assert "Checkov IaC Security Scan Summary" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
