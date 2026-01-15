<div align=center>

# PR Testing Workflow Synchronization

To work around GitHub Actions' reusable workflow call limits while ensuring all scanners are tested in pull requests, we maintain two synchronized versions of the reusable security hardening workflow.
</div>

## Problem
GitHub Actions has a limit of 20 reusable workflow calls per workflow file. Testing all individual scanners plus the reusable workflow exceeded this limit.

## Solution
We maintain two versions of the reusable security hardening workflow:

### 1. **`reusable-security-hardening.yml`** (Production)
- Used by external consumers
- Uses pinned tags (`@2.3.1`) for scanner workflows
- Provides stable, versioned releases
- Example: `uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-syft.yml@2.11.0

### 2. **`pr-reusable-security-hardening.yml`** (PR Testing)
- Used only in PR verification
- Uses relative paths for scanner workflows
- Tests branch changes before merging
- Example: `uses: ./.github/workflows/scanner-syft.yml`

## Keeping Them in Sync

The workflows are **identical** except for the scanner workflow references:

| Production Workflow | PR Testing Workflow |
|---------------------|---------------------|
| `huntridge-labs/hardening-workflows/.github/workflows/scanner-*.yml@2.3.1` | `./.github/workflows/scanner-*.yml` |

### Automated Sync Validation

The `validate-workflow-sync` job in `pr-verification.yml` runs when either reusable workflow is modified and ensures they remain structurally identical.

## Updating the Workflows

When modifying the reusable workflow logic:

1. **Make changes to `reusable-security-hardening.yml`** first
2. **Manually apply the same changes to `pr-reusable-security-hardening.yml`**
3. **Ensure scanner references use the correct format**:
   - Production: `huntridge-labs/hardening-workflows/.github/workflows/scanner-*.yml@<version>`
   - PR Testing: `./.github/workflows/scanner-*.yml`
4. **Validate synchronization** before committing

### Validate Synchronization

Use the sync validation script to check if workflows are in sync:

```bash
bash .github/scripts/validate-reusable-workflow-sync.sh
```

**If workflows are out of sync:**
- The script will display structural differences
- Review the diff output to identify what needs to be updated
- Manually apply changes to keep workflows synchronized
- Re-run validation to confirm sync

**The validation script normalizes:**
- Comments and workflow names
- Scanner workflow paths and version tags
- Repository-specific checkout logic
- Job ID extraction differences

This ensures only actual structural differences are reported.

## Benefits

✅ **Complete Test Coverage** - All scanners tested with branch versions in PRs  
✅ **No Workflow Limit Issues** - Single reusable workflow call instead of 9+ individual scanners  
✅ **Stable External API** - Production workflow maintains pinned versions  
✅ **Automated Validation** - Sync check ensures workflows don't drift  
✅ **Clear Separation** - Production vs testing workflows are clearly named  

## Alternative Considered

We considered using composite actions or dynamic refs, but GitHub Actions doesn't support:
- Dynamic refs in `uses:` statements
- Variables in workflow references
- More than 20 reusable workflow calls per file

This two-workflow approach is the most maintainable solution within GitHub Actions' constraints.
