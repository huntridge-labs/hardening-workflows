#!/usr/bin/env python3
"""
Unit tests for scanner-codeql/scripts/generate-summary.sh
Tests markdown generation for CodeQL SAST scan results
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
GENERATOR_SCRIPT = SCRIPTS_DIR / "generate-summary.sh"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "scanner-outputs" / "codeql"


class TestCodeQLGenerateSummary:
    """Test cases for scanner-codeql generate-summary.sh"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test workspace for each test."""
        self.workspace = tmp_path
        self.codeql_reports = tmp_path / "codeql-reports"
        self.sarif_dir = self.codeql_reports / "sarif"
        self.sarif_dir.mkdir(parents=True)
        self.output_file = tmp_path / "summary.md"
        self.original_dir = os.getcwd()
        os.chdir(tmp_path)
        yield
        os.chdir(self.original_dir)

    def run_generator(
        self,
        output_file=None,
        is_pr_comment="false",
        language="python",
        critical="0",
        high="0",
        medium="0",
        low="0",
        total="0",
        repo_url="https://github.com/test/repo/blob/main",
        server_url="https://github.com",
        repository="test/repo",
        run_id="12345",
    ):
        """Helper to run the generator script with arguments."""
        if output_file is None:
            output_file = str(self.output_file)

        cmd = [
            "bash",
            str(GENERATOR_SCRIPT),
            str(output_file),
            is_pr_comment,
            language,
            critical,
            high,
            medium,
            low,
            total,
            repo_url,
            server_url,
            repository,
            run_id,
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
        assert (FIXTURES_DIR / "results-with-findings.sarif").exists()
        assert (FIXTURES_DIR / "results-zero-findings.sarif").exists()

    def test_generates_summary_with_findings(self):
        """Test generating summary with findings."""
        # Copy SARIF fixture
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        # Run generator (3 findings based on fixture: 1 high=8.8, 1 high=7.5, 1 medium=5.0)
        result = self.run_generator(
            language="python",
            critical="0",
            high="2",
            medium="1",
            low="0",
            total="3",
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert self.output_file.exists(), "Output file not created"

        content = self.output_file.read_text()

        # Check for key elements
        assert "CodeQL SAST" in content
        assert "python" in content.lower()  # Language appears in output
        assert "Findings Summary" in content

    def test_generates_summary_zero_findings(self):
        """Test generating summary with zero findings."""
        shutil.copy(
            FIXTURES_DIR / "results-zero-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        result = self.run_generator(
            language="python",
            critical="0",
            high="0",
            medium="0",
            low="0",
            total="0",
        )

        assert result.returncode == 0
        assert self.output_file.exists()

        content = self.output_file.read_text()
        assert "No security findings" in content

    def test_pr_comment_format_collapsible(self):
        """Test PR comment format uses collapsible sections."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        result = self.run_generator(
            is_pr_comment="true",
            language="python",
            total="3",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()

        # PR comment should use collapsible format
        assert "<details>" in content
        assert "<summary>" in content
        assert "</details>" in content

    def test_critical_severity_message(self):
        """Test CRITICAL severity priority message appears."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        result = self.run_generator(
            language="python",
            critical="2",
            total="2",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        assert "CRITICAL" in content
        assert "2 critical-severity findings" in content

    def test_high_severity_message(self):
        """Test HIGH severity priority message appears."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        result = self.run_generator(
            language="python",
            critical="0",
            high="2",
            total="2",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        assert "HIGH" in content
        assert "2 high-severity findings" in content

    def test_finding_details_section(self):
        """Test finding details section is present with findings."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        result = self.run_generator(
            language="python",
            high="2",
            medium="1",
            total="3",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()

        # Should have finding details
        assert "Finding Details" in content
        assert "Severity" in content
        assert "Rule" in content
        assert "Location" in content

    def test_artifact_link_present(self):
        """Test artifact link is present in output."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        result = self.run_generator(
            language="python",
            repository="test/repo",
            run_id="12345",
            total="3",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        assert "https://github.com/test/repo/actions/runs/12345" in content

    def test_handles_no_sarif_directory(self):
        """Test handles missing SARIF directory gracefully."""
        # Remove the SARIF directory
        shutil.rmtree(self.sarif_dir)

        result = self.run_generator(
            language="python",
            total="0",
        )

        assert result.returncode == 0
        assert self.output_file.exists()

        content = self.output_file.read_text()
        # Should still generate output but indicate no findings/skipped
        assert "CodeQL" in content

    def test_non_pr_format_has_heading(self):
        """Test non-PR format uses heading instead of details tag."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        result = self.run_generator(
            is_pr_comment="false",
            language="python",
            total="3",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()

        # Non-PR format should have ## heading
        assert "## CodeQL SAST Scan" in content

    def test_language_in_output(self):
        """Test language name appears in output."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "javascript.sarif",
        )

        result = self.run_generator(
            language="javascript",
            total="3",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()
        # Language should appear in output
        assert "javascript" in content.lower()

    def test_summary_table_format(self):
        """Test summary table has correct format."""
        shutil.copy(
            FIXTURES_DIR / "results-with-findings.sarif",
            self.sarif_dir / "python.sarif",
        )

        result = self.run_generator(
            language="python",
            critical="1",
            high="2",
            medium="3",
            low="4",
            total="10",
        )

        assert result.returncode == 0
        content = self.output_file.read_text()

        # Check table headers
        assert "| Critical | High | Medium | Low | Total |" in content
        # Check table row with counts
        assert "| **1** | **2** | **3** | **4** | **10** |" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
