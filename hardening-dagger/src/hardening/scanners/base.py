"""Base scanner interface."""

from abc import ABC, abstractmethod

import dagger
from dagger import dag

from models import Finding, ScanResult


class BaseScanner(ABC):
    """Abstract base class for all scanners."""

    name: str = "base"
    description: str = "Base scanner"

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
        return dag.container().from_(image).with_exec(["mkdir", "-p", "/reports"])
