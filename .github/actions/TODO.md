---

## Future Enhancements

### Action API Consistency

- [ ] **Add `post_pr_comment` input to linters and OpenGrep scanner**
  - **Context**: Scanner actions (Bandit, Gitleaks, Trivy, etc.) support `post_pr_comment` for flexibility - each can post individual results to PRs, or be disabled when aggregating via security-summary action
  - **Problem**: Linter actions and scanner-opengrep are missing this input, creating API inconsistency
  - **Affected actions**:
    - [ ] `.github/actions/scanner-opengrep/action.yml`
    - [ ] `.github/actions/linter-dockerfile/action.yml`
    - [ ] `.github/actions/linter-python/action.yml`
    - [ ] `.github/actions/linter-yaml/action.yml`
  - **Implementation**:
    1. Add `post_pr_comment` input to each action.yml (default: 'false')
    2. Add PR comment logic to shell scripts (similar to scanner actions)
    3. Update action documentation and examples
    4. Update test-actions.yml to test both modes (individual + aggregated)

  - **Detailed Plan**:

    ### 1. scanner-opengrep/action.yml
    - Add `post_pr_comment` input after `fail_on_severity` (line ~45)
    - No script changes needed - generate-summary.sh already handles `is_pr_comment` parameter

    ### 2. linter-dockerfile/action.yml
    - Add `post_pr_comment` input after `ignore_rules` (line ~33)
    - Modify "Generate linter summary" step to:
      - Always generate `<details>` wrapper to `linter-summaries/dockerfile.md` (for PR aggregation)
      - Add job summary output to `$GITHUB_STEP_SUMMARY` with `##` header format (no `<details>`)

    ### 3. linter-python/action.yml
    - Add `post_pr_comment` input after `flake8_ignore` (line ~38)
    - Same summary generation changes as linter-dockerfile

    ### 4. linter-yaml/action.yml
    - Add `post_pr_comment` input after `python_version` (line ~34)
    - Same summary generation changes as linter-dockerfile

    ### Input Definition (same for all 4 actions)
    ```yaml
    post_pr_comment:
      description: 'Whether to post PR comments'
      required: false
      default: 'false'
    ```

    ### Summary Generation Pattern
    Each linter will generate TWO summaries (matching scanner pattern):
    1. **PR comment artifact** (`linter-summaries/{name}.md`) - uses `<details>` wrapper
    2. **Job summary** (`$GITHUB_STEP_SUMMARY`) - uses `##` headers, no `<details>`
  - **Benefits**: Consistent API across all scanner/linter actions, flexible reporting options
  - **Priority**: Medium (nice to have, not blocking)
