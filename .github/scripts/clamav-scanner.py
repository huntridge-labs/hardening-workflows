#!/usr/bin/env python3
"""
ClamAV Malware Scanner with Archive Extraction

This script recursively extracts nested archives and scans all files with ClamAV
for malware detection. It supports various archive formats and provides detailed
reporting of scan results.
"""

import os
import sys
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

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        self.extracted_paths = []
        self.errors = []

    def is_archive(self, file_path: Path) -> bool:
        """Check if a file is a supported archive."""
        return file_path.suffix.lower().lstrip('.') in self.SUPPORTED_EXTENSIONS

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

    def extract_recursively(self, input_path: Path) -> List[Path]:
        """Recursively extract archives starting from input_path."""
        if not input_path.exists():
            logger.warning("Path does not exist: %s", input_path)
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
                            self.extract_recursively(item)
                else:
                    logger.error("Failed to extract %s", input_path)
            else:
                # Copy non-archive files to output directory
                self.output_dir.mkdir(parents=True, exist_ok=True)
                dest_file = self.output_dir / input_path.name
                shutil.copy2(input_path, dest_file)
                self.extracted_paths.append(dest_file)

        elif input_path.is_dir():
            # If the input is a directory, iterate over its contents
            for item in input_path.iterdir():
                self.extract_recursively(item)

        return self.extracted_paths

class ClamAVScanner:
    """
    ClamAV malware scanner that works with extracted archives.
    """

    def __init__(self, clamscan_path: str = 'clamscan'):
        self.clamscan_path = clamscan_path

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

    def scan_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Scan all files in a directory with ClamAV."""
        results = []
        infected_files = 0
        error_files = 0

        for file_path in dir_path.rglob('*'):
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

def main(input_paths: List[str], output_dir: str):
    """
    Main function to extract archives and scan files with ClamAV.

    Args:
        input_paths (List[str]): List of input file or directory paths.
        output_dir (str): Output directory for extracted files.
    """
    extractor = ArchiveExtractor(output_dir)
    scanner = ClamAVScanner()

    for input_path in input_paths:
        path = Path(input_path)
        if path.exists():
            logger.info("Processing %s", path)
            extracted_paths = extractor.extract_recursively(path)

            # Scan the extracted directory with ClamAV
            if extracted_paths:
                scan_results = scanner.scan_directory(extractor.output_dir)
                logger.info("Scan completed: %d files scanned, %d infected, %d errors",
                            scan_results['total_files'], scan_results['infected_files'], scan_results['error_files'])

                # Log infections
                for result in scan_results['results']:
                    if result['status'] == 'infected':
                        logger.warning("Infection found in %s: %s", result['file'], result.get('infection', 'Unknown'))
            else:
                logger.info("No archives found to extract in %s", path)
        else:
            logger.warning("Path does not exist: %s", path)

if __name__ == "__main__":
    parser = ArgumentParser(description="ClamAV Malware Scanner with Archive Extraction")
    parser.add_argument('input_paths', nargs='+', help="Input file or directory paths")
    parser.add_argument('--output_dir', help="Output directory for extracted files")
    args = parser.parse_args()

    main(args.input_paths, args.output_dir)
