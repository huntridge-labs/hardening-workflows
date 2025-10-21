#!/usr/bin/env python3
"""
ClamAV Malware Scanner with Archive Extraction

This script recursively extracts nested archives and scans all files with ClamAV
for malware detection. It supports various archive formats and provides detailed
reporting of scan results.
"""

import json
import shutil
import logging
import subprocess
import tempfile
from pathlib import Path
from argparse import ArgumentParser
import tarfile
import gzip
import zipfile
try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArchiveExtractor:
    """
    A class for recursively extracting nested archives of various formats.
    """

    SUPPORTED_EXTENSIONS = {
        # Tar formats
        'tar', 'tgz', 'tbz', 'tb2', 'tar.gz', 'tar.bz2', 'tar.xz',
        # Zip formats
        'zip',
        # Rar formats
        'rar',
        # Gzip
        'gz'
    }

    def __init__(self, output_dir: str = None, base_path: Path = None):
        self.output_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_paths = []
        self.errors = []
        # Base directories/patterns to exclude from scanning
        self.exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.venv', 'venv', '.tox',
            '.pytest_cache', 'htmlcov', 'coverage', '.coverage',
            'tests', 'test', '__tests__', 'spec', 'specs'
        }
        # Load additional exclusions from ignore files
        self.exclude_patterns = set()
        if base_path:
            self._load_ignore_files(base_path)

    def is_archive(self, file_path: Path) -> bool:
        """Check if a file is a supported archive."""
        return file_path.suffix.lower().lstrip('.') in self.SUPPORTED_EXTENSIONS

    def _load_ignore_files(self, base_path: Path) -> None:
        """Load patterns from .gitignore and .dockerignore files."""
        ignore_files = ['.gitignore', '.dockerignore']

        for ignore_file in ignore_files:
            ignore_path = base_path / ignore_file
            if ignore_path.exists():
                try:
                    with open(ignore_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            # Skip comments and empty lines
                            if line and not line.startswith('#'):
                                # Remove leading/trailing slashes for consistency
                                pattern = line.strip('/')
                                self.exclude_patterns.add(pattern)
                    logger.info("Loaded exclusions from %s", ignore_file)
                except (OSError, UnicodeDecodeError) as e:
                    logger.warning("Failed to read %s: %s", ignore_file, e)

    def _should_exclude(self, path: Path, base_path: Path = None) -> bool:
        """Check if a path should be excluded based on patterns and directory names."""
        # Check if any parent directory matches exclude_dirs
        if any(part in self.exclude_dirs for part in path.parts):
            return True

        # Check against patterns from ignore files
        if base_path and self.exclude_patterns:
            try:
                rel_path = path.relative_to(base_path)
                rel_path_str = str(rel_path)

                for pattern in self.exclude_patterns:
                    # Simple pattern matching (not full gitignore spec, but covers common cases)
                    if pattern in rel_path_str or rel_path_str.startswith(pattern):
                        return True
                    # Check if any component matches
                    if pattern in path.parts:
                        return True
            except ValueError:
                # Path is not relative to base_path
                pass

        return False

    def extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """Extract a single archive file."""
        try:
            if archive_path.suffix.lower() in ['.tar', '.tgz', '.tbz', '.tb2', '.tar.gz', '.tar.bz2', '.tar.xz']:
                return self._extract_tar(archive_path, extract_to)
            elif archive_path.suffix.lower() == '.zip':
                return self._extract_zip(archive_path, extract_to)
            elif archive_path.suffix.lower() == '.rar':
                return self._extract_rar(archive_path, extract_to)
            elif archive_path.suffix.lower() == '.gz':
                return self._extract_gz(archive_path, extract_to)
            else:
                logger.warning("Unsupported archive format: %s", archive_path)
                return False
        except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as e:
            logger.error("Failed to extract %s: %s", archive_path, e)
            self.errors.append(str(e))
            return False

    def _extract_tar(self, archive_path: Path, extract_to: Path) -> bool:
        """Extract tar archives."""
        try:
            with tarfile.open(archive_path, 'r:*') as tar:
                tar.extractall(extract_to)
            return True
        except (OSError, tarfile.TarError) as e:
            logger.error("Failed to extract tar %s: %s", archive_path, e)
            return False

    def _extract_zip(self, archive_path: Path, extract_to: Path) -> bool:
        """Extract zip archives."""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            return True
        except (OSError, zipfile.BadZipFile) as e:
            logger.error("Failed to extract zip %s: %s", archive_path, e)
            return False

    def _extract_rar(self, archive_path: Path, extract_to: Path) -> bool:
        """Extract rar archives."""
        if not HAS_RARFILE:
            logger.warning("rarfile module not available, skipping RAR extraction: %s", archive_path)
            return False
        try:
            with rarfile.RarFile(archive_path, 'r') as rar:
                rar.extractall(extract_to)
            return True
        except (OSError, rarfile.Error) as e:
            logger.error("Failed to extract rar %s: %s", archive_path, e)
            return False

    def _extract_gz(self, archive_path: Path, extract_to: Path) -> bool:
        """Extract gzipped files."""
        try:
            output_file = extract_to / archive_path.stem
            with gzip.open(archive_path, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except (OSError, gzip.BadGzipFile) as e:
            logger.error("Failed to extract gz %s: %s", archive_path, e)
            return False

    def extract_recursively(self, input_path: Path, base_path: Path = None) -> List[Path]:
        """Recursively extract archives starting from input_path.

        Args:
            input_path: Path to extract from
            base_path: Base path for relative pattern matching (usually the original scan root)
        """
        if not input_path.exists():
            logger.warning("Path does not exist: %s", input_path)
            return []

        # Resolve to absolute path to properly compare with output_dir
        input_path = input_path.resolve()
        output_dir_resolved = self.output_dir.resolve()

        # Skip if this path is inside the output directory (prevent infinite loops)
        try:
            input_path.relative_to(output_dir_resolved)
            logger.debug("Skipping path inside output directory: %s", input_path)
            return []
        except ValueError:
            # Path is not relative to output_dir, continue processing
            pass

        # Skip excluded paths
        if self._should_exclude(input_path, base_path):
            logger.debug("Skipping excluded path: %s", input_path)
            return []

        if input_path.is_file():
            if self.is_archive(input_path):
                extract_dir = self.output_dir / f"extracted_{input_path.stem}_{len(self.extracted_paths)}"
                extract_dir.mkdir(parents=True, exist_ok=True)

                if self.extract_archive(input_path, extract_dir):
                    self.extracted_paths.append(extract_dir)
                    logger.info("Extracted %s to %s", input_path, extract_dir)

                    # Recursively extract any archives found in the extracted content
                    for item in extract_dir.rglob('*'):
                        if item.is_file() and self.is_archive(item):
                            self.extract_recursively(item, base_path)
                else:
                    logger.error("Failed to extract %s", input_path)
            # Note: Non-archive files are NOT copied - they'll be scanned in place

        elif input_path.is_dir():
            # If the input is a directory, iterate over its contents
            # Only process archives, skip excluded directories
            for item in input_path.iterdir():
                # Skip excluded paths
                if self._should_exclude(item, base_path):
                    logger.debug("Skipping excluded path: %s", item)
                    continue

                # Only recursively process if it's an archive or a directory (to find archives)
                if item.is_file():
                    if self.is_archive(item):
                        self.extract_recursively(item, base_path)
                    # Skip non-archive files - they'll be scanned directly
                elif item.is_dir():
                    self.extract_recursively(item, base_path)

        return self.extracted_paths

class ClamAVScanner:
    """
    ClamAV malware scanner that works with extracted archives.
    """

    def __init__(self, clamscan_path: str = 'clamscan', exclude_dirs: set = None, exclude_patterns: set = None):
        self.clamscan_path = clamscan_path
        self.exclude_dirs = exclude_dirs or {
            '.git', 'node_modules', '__pycache__', '.venv', 'venv', '.tox',
            '.pytest_cache', 'htmlcov', 'coverage', '.coverage',
            'tests', 'test', '__tests__', 'spec', 'specs'
        }
        self.exclude_patterns = exclude_patterns or set()

    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Scan a single file with ClamAV."""
        try:
            result = subprocess.run(
                [self.clamscan_path, '--no-summary', str(file_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per file
                check=False  # Don't raise exception on non-zero exit
            )

            if result.returncode == 0:
                return {'status': 'clean', 'file': str(file_path)}
            elif result.returncode == 1:
                # Infected file
                infection_info = self._parse_infection(result.stdout)
                return {
                    'status': 'infected',
                    'file': str(file_path),
                    'infection': infection_info
                }
            else:
                return {
                    'status': 'error',
                    'file': str(file_path),
                    'error': result.stderr.strip()
                }
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'file': str(file_path),
                'error': 'Scan timeout'
            }
        except (OSError, subprocess.SubprocessError) as e:
            return {
                'status': 'error',
                'file': str(file_path),
                'error': str(e)
            }

    def _should_exclude(self, path: Path, base_path: Path = None) -> bool:
        """Check if a path should be excluded based on patterns and directory names."""
        # Check if any parent directory matches exclude_dirs
        if any(part in self.exclude_dirs for part in path.parts):
            return True

        # Check against patterns
        if base_path and self.exclude_patterns:
            try:
                rel_path = path.relative_to(base_path)
                rel_path_str = str(rel_path)

                for pattern in self.exclude_patterns:
                    # Simple pattern matching
                    if pattern in rel_path_str or rel_path_str.startswith(pattern):
                        return True
                    # Check if any component matches
                    if pattern in path.parts:
                        return True
            except ValueError:
                # Path is not relative to base_path
                pass

        return False

    def scan_directory(self, dir_path: Path, exclude_paths: List[Path] = None, base_path: Path = None) -> Dict[str, Any]:
        """Scan all files in a directory with ClamAV.

        Args:
            dir_path: Directory to scan
            exclude_paths: List of paths to exclude from scanning
            base_path: Base path for relative pattern matching
        """
        results = []
        infected_files = 0
        error_files = 0

        dir_path = dir_path.resolve()
        exclude_paths_resolved = [p.resolve() for p in (exclude_paths or [])]

        for file_path in dir_path.rglob('*'):
            # Skip excluded directories/patterns
            if self._should_exclude(file_path, base_path or dir_path):
                continue

            # Skip excluded paths
            skip = False
            for exclude_path in exclude_paths_resolved:
                try:
                    file_path.relative_to(exclude_path)
                    skip = True
                    break
                except ValueError:
                    continue

            if skip:
                continue

            if file_path.is_file():
                result = self.scan_file(file_path)
                results.append(result)

                if result['status'] == 'infected':
                    infected_files += 1
                elif result['status'] == 'error':
                    error_files += 1

        return {
            'total_files': len(results),
            'infected_files': infected_files,
            'error_files': error_files,
            'results': results
        }

    def _parse_infection(self, clamscan_output: str) -> str:
        """Parse infection information from clamscan output."""
        lines = clamscan_output.strip().split('\n')
        for line in lines:
            if 'FOUND' in line:
                return line.split(':')[1].strip() if ':' in line else line.strip()
        return 'Unknown infection'

def main(input_paths: List[str], output_dir: str, json_report: str = None, text_report: str = None):
    """
    Main function to extract archives and scan files with ClamAV.

    Args:
        input_paths (List[str]): List of input file or directory paths.
        output_dir (str): Output directory for extracted files.
        json_report (str): Path to save JSON report.
        text_report (str): Path to save text report.
    """
    all_scan_results = []
    total_scanned = 0
    total_infected = 0
    total_errors = 0

    for input_path in input_paths:
        path = Path(input_path).resolve()
        if path.exists():
            logger.info("Processing %s", path)

            # Determine base path for exclusion patterns
            base_path = path if path.is_dir() else path.parent

            # Create extractor and scanner with shared exclusions
            extractor = ArchiveExtractor(output_dir, base_path=base_path)
            scanner = ClamAVScanner(
                exclude_dirs=extractor.exclude_dirs,
                exclude_patterns=extractor.exclude_patterns
            )

            # Step 1: Extract any archives found
            extracted_paths = extractor.extract_recursively(path, base_path=base_path)

            if extracted_paths:
                logger.info("Found and extracted %d archive(s)", len(extracted_paths))

            # Step 2: Scan extracted archives
            if extracted_paths:
                logger.info("Scanning extracted archives in %s", extractor.output_dir)
                scan_results = scanner.scan_directory(extractor.output_dir)
                logger.info("Extracted archives scan: %d files scanned, %d infected, %d errors",
                            scan_results['total_files'], scan_results['infected_files'], scan_results['error_files'])

                all_scan_results.extend(scan_results['results'])
                total_scanned += scan_results['total_files']
                total_infected += scan_results['infected_files']
                total_errors += scan_results['error_files']

                # Log infections
                for result in scan_results['results']:
                    if result['status'] == 'infected':
                        logger.warning("Infection found in %s: %s", result['file'], result.get('infection', 'Unknown'))

            # Step 3: Scan the original input path (non-archive files)
            if path.is_dir():
                logger.info("Scanning original directory %s", path)
                # Exclude the output directory from scanning to prevent scanning extracted files twice
                original_scan = scanner.scan_directory(path, exclude_paths=[extractor.output_dir], base_path=base_path)
                logger.info("Original directory scan: %d files scanned, %d infected, %d errors",
                            original_scan['total_files'], original_scan['infected_files'], original_scan['error_files'])

                all_scan_results.extend(original_scan['results'])
                total_scanned += original_scan['total_files']
                total_infected += original_scan['infected_files']
                total_errors += original_scan['error_files']

                # Log infections
                for result in original_scan['results']:
                    if result['status'] == 'infected':
                        logger.warning("Infection found in %s: %s", result['file'], result.get('infection', 'Unknown'))
            elif path.is_file() and not extractor.is_archive(path):
                # Scan individual non-archive file
                logger.info("Scanning file %s", path)
                result = scanner.scan_file(path)
                all_scan_results.append(result)
                total_scanned += 1
                if result['status'] == 'infected':
                    total_infected += 1
                    logger.warning("Infection found in %s: %s", result['file'], result.get('infection', 'Unknown'))
                elif result['status'] == 'error':
                    total_errors += 1
        else:
            logger.warning("Path does not exist: %s", path)

    # Save JSON report if requested
    if json_report:
        json_data = {
            'total_files': total_scanned,
            'infected_files': total_infected,
            'error_files': total_errors,
            'results': all_scan_results
        }
        json_path = Path(json_report)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        logger.info("JSON report saved to %s", json_report)

    # Save text report if requested
    if text_report:
        text_path = Path(text_report)
        text_path.parent.mkdir(parents=True, exist_ok=True)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write("ClamAV Malware Scan Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total files scanned: {total_scanned}\n")
            f.write(f"Infected files: {total_infected}\n")
            f.write(f"Errors: {total_errors}\n\n")

            if total_infected > 0:
                f.write("Infected Files:\n")
                f.write("-" * 60 + "\n")
                for result in all_scan_results:
                    if result['status'] == 'infected':
                        f.write(f"File: {result['file']}\n")
                        f.write(f"Infection: {result.get('infection', 'Unknown')}\n\n")

            if total_errors > 0:
                f.write("\nErrors:\n")
                f.write("-" * 60 + "\n")
                for result in all_scan_results:
                    if result['status'] == 'error':
                        f.write(f"File: {result['file']}\n")
                        f.write(f"Error: {result.get('error', 'Unknown')}\n\n")

        logger.info("Text report saved to %s", text_report)

if __name__ == "__main__":
    parser = ArgumentParser(description="ClamAV Malware Scanner with Archive Extraction")
    parser.add_argument('input_paths', nargs='+', help="Input file or directory paths")
    parser.add_argument('--output_dir', help="Output directory for extracted files")
    parser.add_argument('--json-report', dest='json_report', help="Path to save JSON report")
    parser.add_argument('--text-report', dest='text_report', help="Path to save text report")
    args = parser.parse_args()

    main(args.input_paths, args.output_dir, args.json_report, args.text_report)
