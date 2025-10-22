#!/usr/bin/env python3
"""Parse ClamAV scan report and generate JSON summary."""

import json
import re
from pathlib import Path

report_file = Path("clamav-reports/clamav-report.txt")
if report_file.exists():
    content = report_file.read_text(encoding='utf-8')

    # Parse the summary line
    infected = 0
    scanned = 0

    if "Infected files:" in content:
        match = re.search(r'Infected files: (\d+)', content)
        if match:
            infected = int(match.group(1))

    if "Scanned files:" in content:
        match = re.search(r'Scanned files: (\d+)', content)
        if match:
            scanned = int(match.group(1))

    # Find infected file details
    infected_files = []
    for line in content.split('\n'):
        if 'FOUND' in line:
            infected_files.append(line.strip())

    json_data = {
        "total_files": scanned,
        "infected_files": infected,
        "clean_files": scanned - infected,
        "infections": infected_files
    }

    Path("clamav-reports/clamav-report.json").write_text(json.dumps(json_data, indent=2), encoding='utf-8')
    print(f"✅ Scan complete: {scanned} files scanned, {infected} infected")
else:
    print("⚠️  No scan report found")
