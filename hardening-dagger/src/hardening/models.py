"""Data models for scan results and findings."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import dagger


class Severity(Enum):
    """Severity levels for findings."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Parse severity from string."""
        mapping = {
            "none": cls.NONE,
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "high": cls.HIGH,
            "critical": cls.CRITICAL,
        }
        return mapping.get(value.lower(), cls.NONE)

    @classmethod
    def from_cvss(cls, score: float) -> "Severity":
        """Convert CVSS score to severity level."""
        if score >= 9.0:
            return cls.CRITICAL
        elif score >= 7.0:
            return cls.HIGH
        elif score >= 4.0:
            return cls.MEDIUM
        elif score > 0:
            return cls.LOW
        return cls.NONE


@dataclass
class Finding:
    """A single security finding from a scanner."""
    rule_id: str
    severity: Severity
    message: str
    file_path: str
    line_number: int
    scanner: str
    cwe: str | None = None
    cvss_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.name,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "scanner": self.scanner,
            "cwe": self.cwe,
            "cvss_score": self.cvss_score,
        }


@dataclass
class ScanResult:
    """Results from a single scanner run."""
    scanner: str
    findings: list[Finding]
    artifacts: dagger.Directory
    exit_code: int = 0
    error_message: str | None = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and self.error_message is None

    @property
    def finding_counts(self) -> dict[str, int]:
        """Count findings by severity."""
        counts = {s.name.lower(): 0 for s in Severity}
        for f in self.findings:
            counts[f.severity.name.lower()] += 1
        return counts


@dataclass
class HardeningReport:
    """Combined report from all scanners."""
    results: list[ScanResult] = field(default_factory=list)
    repository: str = ""
    branch: str = ""
    commit_sha: str = ""

    @property
    def total_findings(self) -> int:
        return sum(len(r.findings) for r in self.results)

    @property
    def critical_count(self) -> int:
        return sum(
            1 for r in self.results
            for f in r.findings
            if f.severity == Severity.CRITICAL
        )

    @property
    def high_count(self) -> int:
        return sum(
            1 for r in self.results
            for f in r.findings
            if f.severity == Severity.HIGH
        )

    @property
    def medium_count(self) -> int:
        return sum(
            1 for r in self.results
            for f in r.findings
            if f.severity == Severity.MEDIUM
        )

    @property
    def low_count(self) -> int:
        return sum(
            1 for r in self.results
            for f in r.findings
            if f.severity == Severity.LOW
        )

    def exceeds_threshold(self, threshold: Severity) -> bool:
        """Check if any finding meets or exceeds the severity threshold."""
        if threshold == Severity.NONE:
            return False
        for result in self.results:
            for finding in result.findings:
                if finding.severity.value >= threshold.value:
                    return True
        return False
