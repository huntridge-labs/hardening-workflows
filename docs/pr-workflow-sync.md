# PR Testing Workflow Synchronization

## Problem
GitHub Actions has a limit of 20 reusable workflow calls per workflow file. Testing all individual scanners plus the reusable workflow exceeded this limit.

## Solution
We maintain two versions of the reusable security hardening workflow:

### 1. **`reusable-security-hardening.yml`** (Production)
- Used by external consumers
- Uses pinned tags (`@2.3.1`) for scanner workflows
- Provides stable, versioned releases
- Example: `uses: huntridge-labs/hardening-workflows/.github/workflows/scanner-syft.yml@2.3.1`

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
2. **Copy changes to `pr-reusable-security-hardening.yml`**
3. **Update scanner references** in the PR version to use relative paths
4. **Commit both files** together

### Quick Update Command

```bash
# Copy the production workflow
cp .github/workflows/reusable-security-hardening.yml .github/workflows/pr-reusable-security-hardening.yml

# Update the name and comments
sed -i '' '1s|^.*$|# PR Testing Version - Uses Relative Paths for Branch Testing\n# This workflow is identical to reusable-security-hardening.yml but uses relative paths\n# to test scanner changes in PRs. DO NOT use this for production - external consumers\n# should use reusable-security-hardening.yml with pinned tags.\n|' .github/workflows/pr-reusable-security-hardening.yml
sed -i '' 's|name: Reusable Security Hardening Pipeline|name: PR Testing - Reusable Security Hardening Pipeline|' .github/workflows/pr-reusable-security-hardening.yml

# Replace all pinned versions with relative paths
sed -i '' 's|huntridge-labs/hardening-workflows/.github/workflows/scanner-\([^@]*\)@2.3.1|./.github/workflows/scanner-\1|g' .github/workflows/pr-reusable-security-hardening.yml
```

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
