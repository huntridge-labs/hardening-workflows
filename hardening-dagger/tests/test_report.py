"""Tests for report generation."""

import json
from unittest.mock import MagicMock

from hardening.models import Finding, HardeningReport, ScanResult, Severity
from hardening.report import ReportGenerator


def create_mock_directory():
    """Create a mock dagger.Directory for testing."""
    return MagicMock()


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_empty_report_markdown(self):
        """Test markdown generation with no findings."""
        report = HardeningReport(
            results=[],
            repository="test/repo",
            branch="main",
            commit_sha="abc123def456",
        )
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown()

        assert "# Security Hardening Report" in markdown
        assert "test/repo" in markdown
        assert "main" in markdown
        assert "abc123de" in markdown  # Truncated commit
        assert "| Critical | 0 |" in markdown
        assert "| **Total** | **0** |" in markdown
        assert "All scans passed with no findings" in markdown

    def test_report_with_critical_findings(self):
        """Test markdown with critical findings shows action required."""
        findings = [
            Finding(
                rule_id="B101",
                severity=Severity.CRITICAL,
                message="Critical security issue",
                file_path="app.py",
                line_number=10,
                scanner="bandit",
            )
        ]
        result = ScanResult(
            scanner="bandit",
            findings=findings,
            artifacts=create_mock_directory(),
            exit_code=0,
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown()

        assert "| Critical | 1 |" in markdown
        assert "Action required" in markdown
        assert "B101" in markdown

    def test_report_with_high_findings(self):
        """Test markdown with high severity findings."""
        findings = [
            Finding(
                rule_id="HIGH-001",
                severity=Severity.HIGH,
                message="High severity issue",
                file_path="config.py",
                line_number=5,
                scanner="test",
            )
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown()

        assert "| High | 1 |" in markdown
        assert "Action required" in markdown

    def test_report_with_medium_low_findings(self):
        """Test markdown with only medium/low findings shows review recommended."""
        findings = [
            Finding(
                rule_id="MED-001",
                severity=Severity.MEDIUM,
                message="Medium issue",
                file_path="utils.py",
                line_number=20,
                scanner="test",
            ),
            Finding(
                rule_id="LOW-001",
                severity=Severity.LOW,
                message="Low issue",
                file_path="helpers.py",
                line_number=30,
                scanner="test",
            ),
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown()

        assert "| Medium | 1 |" in markdown
        assert "| Low | 1 |" in markdown
        assert "Review recommended" in markdown

    def test_markdown_truncates_long_messages(self):
        """Test that long messages are truncated in markdown."""
        long_message = "A" * 100
        findings = [
            Finding(
                rule_id="TEST",
                severity=Severity.MEDIUM,
                message=long_message,
                file_path="test.py",
                line_number=1,
                scanner="test",
            )
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown(include_details=True)

        # Message should be truncated to 60 chars + "..."
        assert "A" * 60 + "..." in markdown

    def test_markdown_escapes_pipe_characters(self):
        """Test that pipe characters in messages are escaped."""
        findings = [
            Finding(
                rule_id="TEST",
                severity=Severity.MEDIUM,
                message="Choice A | Choice B",
                file_path="test.py",
                line_number=1,
                scanner="test",
            )
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown(include_details=True)

        assert "\\|" in markdown

    def test_markdown_limits_findings_to_50(self):
        """Test that markdown limits displayed findings to 50."""
        findings = [
            Finding(
                rule_id=f"TEST-{i}",
                severity=Severity.LOW,
                message=f"Issue {i}",
                file_path="test.py",
                line_number=i,
                scanner="test",
            )
            for i in range(60)
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown(include_details=True)

        assert "10 more findings" in markdown

    def test_markdown_without_details(self):
        """Test markdown generation without finding details."""
        findings = [
            Finding(
                rule_id="TEST",
                severity=Severity.HIGH,
                message="Issue",
                file_path="test.py",
                line_number=1,
                scanner="test",
            )
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown(include_details=False)

        assert "<details>" not in markdown
        assert "| Severity | Rule |" not in markdown

    def test_markdown_with_scanner_error(self):
        """Test markdown shows scanner errors."""
        result = ScanResult(
            scanner="failed-scanner",
            findings=[],
            artifacts=create_mock_directory(),
            exit_code=1,
            error_message="Scanner crashed",
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        markdown = generator.generate_markdown()

        assert "Error" in markdown
        assert "Scanner crashed" in markdown

    def test_json_report_structure(self):
        """Test JSON report has correct structure."""
        findings = [
            Finding(
                rule_id="B101",
                severity=Severity.HIGH,
                message="Test issue",
                file_path="app.py",
                line_number=10,
                scanner="bandit",
                cwe="CWE-123",
            )
        ]
        result = ScanResult(
            scanner="bandit",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(
            results=[result],
            repository="test/repo",
            branch="main",
            commit_sha="abc123",
        )
        generator = ReportGenerator(report)
        json_str = generator.generate_json()
        data = json.loads(json_str)

        assert data["metadata"]["repository"] == "test/repo"
        assert data["metadata"]["branch"] == "main"
        assert data["summary"]["total_findings"] == 1
        assert data["summary"]["high"] == 1
        assert len(data["scanners"]) == 1
        assert data["scanners"][0]["name"] == "bandit"
        assert data["scanners"][0]["finding_count"] == 1

    def test_sarif_report_structure(self):
        """Test SARIF report has correct structure."""
        findings = [
            Finding(
                rule_id="B101",
                severity=Severity.HIGH,
                message="Hardcoded password",
                file_path="app.py",
                line_number=42,
                scanner="bandit",
            )
        ]
        result = ScanResult(
            scanner="bandit",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        sarif_str = generator.generate_sarif()
        sarif = json.loads(sarif_str)

        assert sarif["version"] == "2.1.0"
        assert "$schema" in sarif
        assert len(sarif["runs"]) == 1

        run = sarif["runs"][0]
        assert run["tool"]["driver"]["name"] == "hardening-bandit"
        assert len(run["tool"]["driver"]["rules"]) == 1
        assert run["tool"]["driver"]["rules"][0]["id"] == "B101"
        assert len(run["results"]) == 1
        assert run["results"][0]["ruleId"] == "B101"
        assert run["results"][0]["level"] == "error"

    def test_sarif_severity_mapping(self):
        """Test SARIF severity level mapping."""
        findings = [
            Finding(
                rule_id="CRIT",
                severity=Severity.CRITICAL,
                message="Critical",
                file_path="a.py",
                line_number=1,
                scanner="test",
            ),
            Finding(
                rule_id="HIGH",
                severity=Severity.HIGH,
                message="High",
                file_path="b.py",
                line_number=2,
                scanner="test",
            ),
            Finding(
                rule_id="MED",
                severity=Severity.MEDIUM,
                message="Medium",
                file_path="c.py",
                line_number=3,
                scanner="test",
            ),
            Finding(
                rule_id="LOW",
                severity=Severity.LOW,
                message="Low",
                file_path="d.py",
                line_number=4,
                scanner="test",
            ),
            Finding(
                rule_id="NONE",
                severity=Severity.NONE,
                message="None",
                file_path="e.py",
                line_number=5,
                scanner="test",
            ),
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        sarif_str = generator.generate_sarif()
        sarif = json.loads(sarif_str)

        results = sarif["runs"][0]["results"]
        levels = {r["ruleId"]: r["level"] for r in results}

        assert levels["CRIT"] == "error"
        assert levels["HIGH"] == "error"
        assert levels["MED"] == "warning"
        assert levels["LOW"] == "note"
        assert levels["NONE"] == "none"

    def test_sarif_line_number_minimum(self):
        """Test SARIF uses minimum line number of 1."""
        findings = [
            Finding(
                rule_id="TEST",
                severity=Severity.LOW,
                message="Test",
                file_path="test.py",
                line_number=0,  # Invalid line number
                scanner="test",
            )
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        report = HardeningReport(results=[result])
        generator = ReportGenerator(report)
        sarif_str = generator.generate_sarif()
        sarif = json.loads(sarif_str)

        # Line number should be at least 1
        line = sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"]
        assert line == 1

    def test_status_icon_for_different_results(self):
        """Test status icons for different scanner results."""
        generator = ReportGenerator(HardeningReport())

        # Error case
        error_result = ScanResult(
            scanner="test",
            findings=[],
            artifacts=create_mock_directory(),
            error_message="Failed",
        )
        assert generator._get_status_icon(error_result) == "Error"

        # Passed case
        passed_result = ScanResult(
            scanner="test",
            findings=[],
            artifacts=create_mock_directory(),
        )
        assert generator._get_status_icon(passed_result) == "Passed"

        # Failed case (critical findings)
        critical_finding = Finding(
            rule_id="TEST",
            severity=Severity.CRITICAL,
            message="Critical",
            file_path="test.py",
            line_number=1,
            scanner="test",
        )
        failed_result = ScanResult(
            scanner="test",
            findings=[critical_finding],
            artifacts=create_mock_directory(),
        )
        assert generator._get_status_icon(failed_result) == "Failed"

        # Warning case (medium findings only)
        medium_finding = Finding(
            rule_id="TEST",
            severity=Severity.MEDIUM,
            message="Medium",
            file_path="test.py",
            line_number=1,
            scanner="test",
        )
        warning_result = ScanResult(
            scanner="test",
            findings=[medium_finding],
            artifacts=create_mock_directory(),
        )
        assert generator._get_status_icon(warning_result) == "Warning"

    def test_severity_to_cvss_mapping(self):
        """Test severity to CVSS score mapping."""
        generator = ReportGenerator(HardeningReport())

        assert generator._severity_to_cvss(Severity.CRITICAL) == 9.5
        assert generator._severity_to_cvss(Severity.HIGH) == 7.5
        assert generator._severity_to_cvss(Severity.MEDIUM) == 5.0
        assert generator._severity_to_cvss(Severity.LOW) == 2.5
        assert generator._severity_to_cvss(Severity.NONE) == 0.0

    def test_multiple_scanners_in_report(self):
        """Test report with multiple scanners."""
        bandit_findings = [
            Finding(
                rule_id="B101",
                severity=Severity.HIGH,
                message="Bandit issue",
                file_path="app.py",
                line_number=10,
                scanner="bandit",
            )
        ]
        gitleaks_findings = [
            Finding(
                rule_id="aws-access-key",
                severity=Severity.HIGH,
                message="Secret found",
                file_path="config.py",
                line_number=5,
                scanner="gitleaks",
            )
        ]

        report = HardeningReport(
            results=[
                ScanResult(
                    scanner="bandit",
                    findings=bandit_findings,
                    artifacts=create_mock_directory(),
                ),
                ScanResult(
                    scanner="gitleaks",
                    findings=gitleaks_findings,
                    artifacts=create_mock_directory(),
                ),
            ]
        )

        generator = ReportGenerator(report)
        markdown = generator.generate_markdown()

        assert "### " in markdown and "bandit" in markdown
        assert "### " in markdown and "gitleaks" in markdown
        assert "| High | 2 |" in markdown
        assert "| **Total** | **2** |" in markdown
