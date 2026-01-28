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
  - **Benefits**: Consistent API across all scanner/linter actions, flexible reporting options
  - **Priority**: Medium (nice to have, not blocking)
