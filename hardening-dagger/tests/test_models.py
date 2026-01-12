"""Tests for data models."""

from unittest.mock import MagicMock

from hardening.models import Finding, HardeningReport, ScanResult, Severity


def create_mock_directory():
    """Create a mock dagger.Directory for testing."""
    return MagicMock()


class TestSeverity:
    """Tests for Severity enum."""

    def test_from_string_valid(self):
        """Test parsing valid severity strings."""
        assert Severity.from_string("critical") == Severity.CRITICAL
        assert Severity.from_string("HIGH") == Severity.HIGH
        assert Severity.from_string("Medium") == Severity.MEDIUM
        assert Severity.from_string("low") == Severity.LOW
        assert Severity.from_string("none") == Severity.NONE

    def test_from_string_invalid(self):
        """Test parsing invalid severity defaults to NONE."""
        assert Severity.from_string("invalid") == Severity.NONE
        assert Severity.from_string("") == Severity.NONE

    def test_from_cvss(self):
        """Test CVSS score to severity mapping."""
        assert Severity.from_cvss(9.5) == Severity.CRITICAL
        assert Severity.from_cvss(9.0) == Severity.CRITICAL
        assert Severity.from_cvss(8.0) == Severity.HIGH
        assert Severity.from_cvss(7.0) == Severity.HIGH
        assert Severity.from_cvss(5.0) == Severity.MEDIUM
        assert Severity.from_cvss(4.0) == Severity.MEDIUM
        assert Severity.from_cvss(2.0) == Severity.LOW
        assert Severity.from_cvss(0.0) == Severity.NONE

    def test_from_cvss_boundary_values(self):
        """Test CVSS boundary values."""
        # Boundary between HIGH and CRITICAL (9.0)
        assert Severity.from_cvss(8.9) == Severity.HIGH
        assert Severity.from_cvss(9.0) == Severity.CRITICAL

        # Boundary between MEDIUM and HIGH (7.0)
        assert Severity.from_cvss(6.9) == Severity.MEDIUM
        assert Severity.from_cvss(7.0) == Severity.HIGH

        # Boundary between LOW and MEDIUM (4.0)
        assert Severity.from_cvss(3.9) == Severity.LOW
        assert Severity.from_cvss(4.0) == Severity.MEDIUM

        # Boundary between NONE and LOW (0.0)
        assert Severity.from_cvss(0.1) == Severity.LOW
        assert Severity.from_cvss(0.0) == Severity.NONE

    def test_severity_enum_values(self):
        """Test severity enum numeric values are ordered correctly."""
        assert Severity.NONE.value < Severity.LOW.value
        assert Severity.LOW.value < Severity.MEDIUM.value
        assert Severity.MEDIUM.value < Severity.HIGH.value
        assert Severity.HIGH.value < Severity.CRITICAL.value


class TestFinding:
    """Tests for Finding dataclass."""

    def test_finding_creation(self):
        """Test creating a finding."""
        finding = Finding(
            rule_id="B101",
            severity=Severity.HIGH,
            message="Hardcoded password",
            file_path="app.py",
            line_number=42,
            scanner="bandit",
            cwe="CWE-798",
        )
        assert finding.rule_id == "B101"
        assert finding.severity == Severity.HIGH
        assert finding.line_number == 42
        assert finding.cwe == "CWE-798"

    def test_finding_to_dict(self):
        """Test converting finding to dictionary."""
        finding = Finding(
            rule_id="B101",
            severity=Severity.HIGH,
            message="Test",
            file_path="app.py",
            line_number=1,
            scanner="bandit",
        )
        d = finding.to_dict()
        assert d["rule_id"] == "B101"
        assert d["severity"] == "HIGH"
        assert d["scanner"] == "bandit"

    def test_finding_to_dict_complete(self):
        """Test to_dict includes all fields."""
        finding = Finding(
            rule_id="CVE-2023-1234",
            severity=Severity.CRITICAL,
            message="Critical vulnerability",
            file_path="requirements.txt",
            line_number=10,
            scanner="grype",
            cwe="CWE-400",
            cvss_score=9.8,
        )
        d = finding.to_dict()

        assert d["rule_id"] == "CVE-2023-1234"
        assert d["severity"] == "CRITICAL"
        assert d["message"] == "Critical vulnerability"
        assert d["file_path"] == "requirements.txt"
        assert d["line_number"] == 10
        assert d["scanner"] == "grype"
        assert d["cwe"] == "CWE-400"
        assert d["cvss_score"] == 9.8

    def test_finding_optional_fields_default_to_none(self):
        """Test optional fields default to None."""
        finding = Finding(
            rule_id="TEST",
            severity=Severity.LOW,
            message="Test",
            file_path="test.py",
            line_number=1,
            scanner="test",
        )
        assert finding.cwe is None
        assert finding.cvss_score is None


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_success_property_true(self):
        """Test success is True when exit_code is 0 and no error."""
        result = ScanResult(
            scanner="bandit",
            findings=[],
            artifacts=create_mock_directory(),
            exit_code=0,
            error_message=None,
        )
        assert result.success is True

    def test_success_property_false_exit_code(self):
        """Test success is False when exit_code is non-zero."""
        result = ScanResult(
            scanner="bandit",
            findings=[],
            artifacts=create_mock_directory(),
            exit_code=1,
            error_message=None,
        )
        assert result.success is False

    def test_success_property_false_error_message(self):
        """Test success is False when error_message is set."""
        result = ScanResult(
            scanner="bandit",
            findings=[],
            artifacts=create_mock_directory(),
            exit_code=0,
            error_message="Scanner crashed",
        )
        assert result.success is False

    def test_finding_counts_empty(self):
        """Test finding_counts with no findings."""
        result = ScanResult(
            scanner="bandit",
            findings=[],
            artifacts=create_mock_directory(),
        )
        counts = result.finding_counts

        assert counts["critical"] == 0
        assert counts["high"] == 0
        assert counts["medium"] == 0
        assert counts["low"] == 0
        assert counts["none"] == 0

    def test_finding_counts_with_findings(self):
        """Test finding_counts with various severities."""
        findings = [
            Finding(
                rule_id="C1",
                severity=Severity.CRITICAL,
                message="Critical",
                file_path="a.py",
                line_number=1,
                scanner="test",
            ),
            Finding(
                rule_id="C2",
                severity=Severity.CRITICAL,
                message="Critical 2",
                file_path="b.py",
                line_number=2,
                scanner="test",
            ),
            Finding(
                rule_id="H1",
                severity=Severity.HIGH,
                message="High",
                file_path="c.py",
                line_number=3,
                scanner="test",
            ),
            Finding(
                rule_id="M1",
                severity=Severity.MEDIUM,
                message="Medium",
                file_path="d.py",
                line_number=4,
                scanner="test",
            ),
            Finding(
                rule_id="L1",
                severity=Severity.LOW,
                message="Low",
                file_path="e.py",
                line_number=5,
                scanner="test",
            ),
            Finding(
                rule_id="L2",
                severity=Severity.LOW,
                message="Low 2",
                file_path="f.py",
                line_number=6,
                scanner="test",
            ),
        ]
        result = ScanResult(
            scanner="test",
            findings=findings,
            artifacts=create_mock_directory(),
        )
        counts = result.finding_counts

        assert counts["critical"] == 2
        assert counts["high"] == 1
        assert counts["medium"] == 1
        assert counts["low"] == 2
        assert counts["none"] == 0


class TestHardeningReport:
    """Tests for HardeningReport."""

    def test_empty_report(self):
        """Test empty report has zero counts."""
        report = HardeningReport()
        assert report.total_findings == 0
        assert report.critical_count == 0
        assert report.high_count == 0
        assert report.medium_count == 0
        assert report.low_count == 0

    def test_exceeds_threshold_none(self):
        """Test that NONE threshold never exceeds."""
        report = HardeningReport()
        assert not report.exceeds_threshold(Severity.NONE)

    def test_exceeds_threshold_with_findings(self):
        """Test threshold checking with findings."""
        findings = [
            Finding(
                rule_id="H1",
                severity=Severity.HIGH,
                message="High issue",
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

        # Should exceed HIGH and below
        assert report.exceeds_threshold(Severity.HIGH) is True
        assert report.exceeds_threshold(Severity.MEDIUM) is True
        assert report.exceeds_threshold(Severity.LOW) is True

        # Should not exceed CRITICAL
        assert report.exceeds_threshold(Severity.CRITICAL) is False

    def test_total_findings_multiple_scanners(self):
        """Test total_findings aggregates across scanners."""
        findings1 = [
            Finding(
                rule_id="B1",
                severity=Severity.HIGH,
                message="Test",
                file_path="a.py",
                line_number=1,
                scanner="bandit",
            ),
            Finding(
                rule_id="B2",
                severity=Severity.MEDIUM,
                message="Test",
                file_path="b.py",
                line_number=2,
                scanner="bandit",
            ),
        ]
        findings2 = [
            Finding(
                rule_id="G1",
                severity=Severity.HIGH,
                message="Secret",
                file_path="c.py",
                line_number=3,
                scanner="gitleaks",
            ),
        ]

        report = HardeningReport(
            results=[
                ScanResult(
                    scanner="bandit",
                    findings=findings1,
                    artifacts=create_mock_directory(),
                ),
                ScanResult(
                    scanner="gitleaks",
                    findings=findings2,
                    artifacts=create_mock_directory(),
                ),
            ]
        )

        assert report.total_findings == 3
        assert report.high_count == 2
        assert report.medium_count == 1

    def test_severity_counts_with_all_severities(self):
        """Test all severity counts work correctly."""
        findings = [
            Finding(
                rule_id="C1",
                severity=Severity.CRITICAL,
                message="Critical",
                file_path="a.py",
                line_number=1,
                scanner="test",
            ),
            Finding(
                rule_id="H1",
                severity=Severity.HIGH,
                message="High",
                file_path="b.py",
                line_number=2,
                scanner="test",
            ),
            Finding(
                rule_id="M1",
                severity=Severity.MEDIUM,
                message="Medium",
                file_path="c.py",
                line_number=3,
                scanner="test",
            ),
            Finding(
                rule_id="L1",
                severity=Severity.LOW,
                message="Low",
                file_path="d.py",
                line_number=4,
                scanner="test",
            ),
        ]
        report = HardeningReport(
            results=[
                ScanResult(
                    scanner="test",
                    findings=findings,
                    artifacts=create_mock_directory(),
                )
            ]
        )

        assert report.critical_count == 1
        assert report.high_count == 1
        assert report.medium_count == 1
        assert report.low_count == 1
        assert report.total_findings == 4

    def test_report_metadata(self):
        """Test report metadata fields."""
        report = HardeningReport(
            results=[],
            repository="owner/repo",
            branch="feature-branch",
            commit_sha="abc123def456",
        )

        assert report.repository == "owner/repo"
        assert report.branch == "feature-branch"
        assert report.commit_sha == "abc123def456"

    def test_exceeds_threshold_with_critical_finding(self):
        """Test exceeds_threshold with critical findings."""
        findings = [
            Finding(
                rule_id="CVE-9999",
                severity=Severity.CRITICAL,
                message="Critical vulnerability",
                file_path="app.py",
                line_number=1,
                scanner="grype",
            )
        ]
        report = HardeningReport(
            results=[
                ScanResult(
                    scanner="grype",
                    findings=findings,
                    artifacts=create_mock_directory(),
                )
            ]
        )

        assert report.exceeds_threshold(Severity.CRITICAL) is True
        assert report.exceeds_threshold(Severity.HIGH) is True
        assert report.exceeds_threshold(Severity.MEDIUM) is True
        assert report.exceeds_threshold(Severity.LOW) is True
        assert report.exceeds_threshold(Severity.NONE) is False
