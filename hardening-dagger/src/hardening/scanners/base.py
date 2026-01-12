"""Base scanner interface."""

from abc import ABC, abstractmethod

import dagger
from dagger import dag

from scan_logging import LogLevel, ScannerLogger
from models import Finding, ScanResult


class BaseScanner(ABC):
    """Abstract base class for all scanners."""

    name: str = "base"
    description: str = "Base scanner"

    def __init__(self) -> None:
        """Initialize scanner with logger."""
        self._logger: ScannerLogger | None = None

    def _init_logger(self, log_level: str = "info") -> ScannerLogger:
        """Initialize or reinitialize the logger for a scan."""
        self._logger = ScannerLogger(
            scanner_name=self.name,
            log_level=LogLevel.from_string(log_level),
        )
        return self._logger

    @property
    def log(self) -> ScannerLogger:
        """Get the current logger, initializing if needed."""
        if self._logger is None:
            self._logger = ScannerLogger(
                scanner_name=self.name,
                log_level=LogLevel.INFO,
            )
        return self._logger

    @abstractmethod
    async def scan(
        self,
        source: dagger.Directory,
        **kwargs,
    ) -> ScanResult:
        """Execute the scan and return results."""
        pass

    @abstractmethod
    def parse_findings(self, output: str) -> list[Finding]:
        """Parse scanner output into findings."""
        pass

    def base_container(self, image: str) -> dagger.Container:
        """Create base container with common setup."""
        self.log.container_info(f"Creating container from image: {image}")
        return dag.container().from_(image).with_exec(["mkdir", "-p", "/reports"])

    def _add_logs_to_artifacts(self, artifacts: dagger.Directory) -> dagger.Directory:
        """Add log files to the artifacts directory."""
        # Add JSON log
        artifacts = artifacts.with_new_file(
            f"{self.name}-scan.log.json",
            self.log.to_json(),
        )
        # Add human-readable log
        artifacts = artifacts.with_new_file(
            f"{self.name}-scan.log",
            self.log.to_text(),
        )
        return artifacts

    def _create_error_result(self, error: Exception) -> "ScanResult":
        """Create a ScanResult with logs when an error occurs.

        This ensures logs are always available for debugging, even when
        the scanner fails mid-execution.
        """
        self.log.hardening_error("Scanner failed with exception", error=str(error))

        # Create minimal artifact directory with just the logs
        artifacts = dag.directory()
        artifacts = self._add_logs_to_artifacts(artifacts)

        return ScanResult(
            scanner=self.name,
            findings=[],
            artifacts=artifacts,
            exit_code=1,
            error_message=str(error),
        )
