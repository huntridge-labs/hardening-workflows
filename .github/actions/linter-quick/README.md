# linter-quick

Lightweight composite action that validates YAML and JSON files in the repository using Python.

Inputs
- `fail_on_issues` (string): `true` or `false` — when `true` the action exits with non-zero on any parse errors.

How it works
- Checks all `**/*.yml`, `**/*.yaml`, and `**/*.json` files (skips `.github/` files).
- Uses `pyyaml` for YAML parsing and the Python stdlib `json` module for JSON.

Usage in a workflow (local reference)
```yaml
- name: Run quick linter
  uses: ./.github/actions/linter-quick
  with:
    fail_on_issues: 'true'
```
