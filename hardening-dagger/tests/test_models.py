"""Tests for data models."""

from hardening.models import Finding, HardeningReport, Severity


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
        # Would need actual ScanResult with findings to test fully
        # This is a placeholder for integration tests
        report = HardeningReport()
        assert not report.exceeds_threshold(Severity.CRITICAL)
