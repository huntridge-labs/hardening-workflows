require 'simplecov'
require 'simplecov-cobertura'

# Configure cobertura formatter for bash coverage (used by bashcov)
SimpleCov.formatters = SimpleCov::Formatter::MultiFormatter.new([
  SimpleCov::Formatter::HTMLFormatter,
  SimpleCov::Formatter::CoberturaFormatter
])

# Configure output paths
SimpleCov.coverage_dir 'coverage/bash'

# Use relative paths for Codecov compatibility
SimpleCov.use_merging true
SimpleCov.merge_timeout 3600

# Note: Python coverage is handled separately by pytest-cov
SimpleCov.start
