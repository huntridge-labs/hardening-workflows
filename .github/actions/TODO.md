---

## Future Enhancements

### Action API Consistency

- [x] **Add `post_pr_comment` input to linters and OpenGrep scanner** ✅
  - **Context**: Scanner actions (Bandit, Gitleaks, Trivy, etc.) support `post_pr_comment` for flexibility - each can post individual results to PRs, or be disabled when aggregating via security-summary action
  - **Problem**: Linter actions and scanner-opengrep are missing this input, creating API inconsistency
  - **Affected actions**:
    - [x] `.github/actions/scanner-opengrep/action.yml`
    - [x] `.github/actions/linter-dockerfile/action.yml`
    - [x] `.github/actions/linter-python/action.yml`
    - [x] `.github/actions/linter-yaml/action.yml`
  - **Implementation**:
    1. ✅ Add `post_pr_comment` input to each action.yml (default: 'false')
    2. ✅ Add job summary output to linters (similar to scanner actions)
    3. Update action documentation and examples (future)
    4. Update test-actions.yml to test both modes (future)
  - **Benefits**: Consistent API across all scanner/linter actions, flexible reporting options
  - **Priority**: Medium (nice to have, not blocking)
