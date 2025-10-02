#!/usr/bin/env python3
"""
Test file that should pass pre-commit hooks.
Clean code without security issues or formatting problems.
"""

import os
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CleanTestClass:
    """A clean test class following best practices."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize with optional configuration."""
        self.config_path = config_path
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, str]:
        """Load settings from environment variables."""
        return {
            'api_endpoint': os.getenv('API_ENDPOINT', 'https://api.example.com'),
            'timeout': os.getenv('REQUEST_TIMEOUT', '30'),
            'max_retries': os.getenv('MAX_RETRIES', '3'),
        }

    def process_data(self, data: List[Dict]) -> List[Dict]:
        """Process a list of data items."""
        if not data:
            return []

        processed = []
        for item in data:
            if self._validate_item(item):
                processed_item = self._transform_item(item)
                processed.append(processed_item)
            else:
                logger.warning("Invalid item skipped: %s", item.get('id', 'unknown'))

        return processed

    def _validate_item(self, item: Dict) -> bool:
        """Validate a single data item."""
        required_fields = ['id', 'name', 'type']
        return all(field in item for field in required_fields)

    def _transform_item(self, item: Dict) -> Dict:
        """Transform a data item."""
        return {
            'id': item['id'],
            'name': item['name'].strip().title(),
            'type': item['type'].lower(),
            'processed': True,
        }

    def get_summary(self) -> Dict[str, int]:
        """Get processing summary."""
        return {
            'total_processed': 0,
            'errors': 0,
            'warnings': 0,
        }


def main() -> None:
    """Main function."""
    processor = CleanTestClass()
    test_data = [
        {'id': '1', 'name': 'test item', 'type': 'SAMPLE'},
        {'id': '2', 'name': 'another item', 'type': 'EXAMPLE'},
    ]

    result = processor.process_data(test_data)
    logger.info("Processed %d items", len(result))

    summary = processor.get_summary()
    logger.info("Summary: %s", summary)


if __name__ == "__main__":
    main()
