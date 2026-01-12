"""Structured logging for Hardening scanners.

Provides JSON-structured logs that clearly identify the source of each log entry:
- dagger: Dagger pipeline orchestration events
- container: Container setup and execution events
- scanner: Scanner tool output and results
- hardening: Hardening module events

Logs are collected during scan execution and written to the scanner's report directory.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LogLevel(Enum):
    """Log levels in order of verbosity."""

    ERROR = 0
    WARN = 1
    INFO = 2
    DEBUG = 3

    @classmethod
    def from_string(cls, level: str) -> "LogLevel":
        """Parse log level from string."""
        mapping = {
            "error": cls.ERROR,
            "warn": cls.WARN,
            "warning": cls.WARN,
            "info": cls.INFO,
            "debug": cls.DEBUG,
        }
        return mapping.get(level.lower(), cls.INFO)


class LogSource(Enum):
    """Source of the log entry."""

    DAGGER = "dagger"  # Dagger pipeline events
    CONTAINER = "container"  # Container setup/exec events
    SCANNER = "scanner"  # Scanner tool output
    HARDENING = "hardening"  # Hardening module events


@dataclass
class LogEntry:
    """A single structured log entry."""

    timestamp: str
    level: str
    source: str
    scanner: str
    message: str
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        entry = {
            "timestamp": self.timestamp,
            "level": self.level,
            "source": self.source,
            "scanner": self.scanner,
            "message": self.message,
        }
        if self.data:
            entry["data"] = self.data
        return entry

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    def to_text(self) -> str:
        """Convert to human-readable text format."""
        data_str = f" | {json.dumps(self.data)}" if self.data else ""
        return f"[{self.timestamp}] [{self.level:5}] [{self.source:10}] {self.scanner}: {self.message}{data_str}"


@dataclass
class ScannerLogger:
    """Structured logger for a scanner.

    Collects log entries during scan execution and provides methods
    to export logs in various formats.
    """

    scanner_name: str
    log_level: LogLevel = LogLevel.INFO
    entries: list[LogEntry] = field(default_factory=list)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if this level should be logged based on configured level."""
        return level.value <= self.log_level.value

    def _add_entry(
        self,
        level: LogLevel,
        source: LogSource,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Add a log entry if the level is enabled."""
        if not self._should_log(level):
            return

        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.name,
            source=source.value,
            scanner=self.scanner_name,
            message=message,
            data=data,
        )
        self.entries.append(entry)

    # Dagger pipeline events
    def dagger_info(self, message: str, **data: Any) -> None:
        """Log Dagger pipeline info event."""
        self._add_entry(LogLevel.INFO, LogSource.DAGGER, message, data or None)

    def dagger_debug(self, message: str, **data: Any) -> None:
        """Log Dagger pipeline debug event."""
        self._add_entry(LogLevel.DEBUG, LogSource.DAGGER, message, data or None)

    def dagger_error(self, message: str, **data: Any) -> None:
        """Log Dagger pipeline error event."""
        self._add_entry(LogLevel.ERROR, LogSource.DAGGER, message, data or None)

    # Container events
    def container_info(self, message: str, **data: Any) -> None:
        """Log container info event."""
        self._add_entry(LogLevel.INFO, LogSource.CONTAINER, message, data or None)

    def container_debug(self, message: str, **data: Any) -> None:
        """Log container debug event."""
        self._add_entry(LogLevel.DEBUG, LogSource.CONTAINER, message, data or None)

    def container_error(self, message: str, **data: Any) -> None:
        """Log container error event."""
        self._add_entry(LogLevel.ERROR, LogSource.CONTAINER, message, data or None)

    # Scanner tool events
    def scanner_info(self, message: str, **data: Any) -> None:
        """Log scanner tool info event."""
        self._add_entry(LogLevel.INFO, LogSource.SCANNER, message, data or None)

    def scanner_debug(self, message: str, **data: Any) -> None:
        """Log scanner tool debug event."""
        self._add_entry(LogLevel.DEBUG, LogSource.SCANNER, message, data or None)

    def scanner_warn(self, message: str, **data: Any) -> None:
        """Log scanner tool warning event."""
        self._add_entry(LogLevel.WARN, LogSource.SCANNER, message, data or None)

    def scanner_error(self, message: str, **data: Any) -> None:
        """Log scanner tool error event."""
        self._add_entry(LogLevel.ERROR, LogSource.SCANNER, message, data or None)

    # Hardening module events
    def hardening_info(self, message: str, **data: Any) -> None:
        """Log hardening module info event."""
        self._add_entry(LogLevel.INFO, LogSource.HARDENING, message, data or None)

    def hardening_debug(self, message: str, **data: Any) -> None:
        """Log hardening module debug event."""
        self._add_entry(LogLevel.DEBUG, LogSource.HARDENING, message, data or None)

    def hardening_warn(self, message: str, **data: Any) -> None:
        """Log hardening module warning event."""
        self._add_entry(LogLevel.WARN, LogSource.HARDENING, message, data or None)

    def hardening_error(self, message: str, **data: Any) -> None:
        """Log hardening module error event."""
        self._add_entry(LogLevel.ERROR, LogSource.HARDENING, message, data or None)

    # Export methods
    def to_json(self, pretty: bool = True) -> str:
        """Export all log entries as JSON."""
        entries = [e.to_dict() for e in self.entries]
        indent = 2 if pretty else None
        return json.dumps(
            {
                "scanner": self.scanner_name,
                "log_level": self.log_level.name,
                "entry_count": len(entries),
                "entries": entries,
            },
            indent=indent,
        )

    def to_jsonl(self) -> str:
        """Export all log entries as JSON Lines (one JSON object per line)."""
        return "\n".join(e.to_json() for e in self.entries)

    def to_text(self) -> str:
        """Export all log entries as human-readable text."""
        lines = [
            f"# {self.scanner_name} Scan Log",
            f"# Log Level: {self.log_level.name}",
            f"# Entries: {len(self.entries)}",
            "#" + "=" * 79,
            "",
        ]
        lines.extend(e.to_text() for e in self.entries)
        return "\n".join(lines)

    def get_errors(self) -> list[LogEntry]:
        """Get all error-level entries."""
        return [e for e in self.entries if e.level == "ERROR"]

    def get_warnings(self) -> list[LogEntry]:
        """Get all warning-level entries."""
        return [e for e in self.entries if e.level == "WARN"]

    def has_errors(self) -> bool:
        """Check if any errors were logged."""
        return any(e.level == "ERROR" for e in self.entries)
