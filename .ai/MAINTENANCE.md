# AICaC Maintenance Guide

This document ensures `.ai/` stays synchronized with the codebase.

## For AI Assistants

**IMPORTANT**: When you make changes to this project, you MUST update the relevant `.ai/` files.

### Update Triggers

| When you... | Update... |
|-------------|-----------|
| Add/remove a component | `architecture.yaml` → `components` |
| Add/remove a scanner | `architecture.yaml` → `scanners` |
| Change data flow | `architecture.yaml` → `data_flow` |
| Add a new task/command | `workflows.yaml` → appropriate section |
| Make an architectural decision | `decisions.yaml` → add new ADR |
| Fix a common error | `errors.yaml` → add error pattern |
| Add a new dependency | `architecture.yaml` → `dependencies` |
| Change project version | `context.yaml` → `project.version` |
| Add a glossary term | `context.yaml` → `glossary` |

### Update Checklist (Copy This)

After completing work, ask yourself:

```markdown
## .ai/ Update Checklist
- [ ] Did I add/remove/rename a component? → Update architecture.yaml
- [ ] Did I add/change a workflow or command? → Update workflows.yaml
- [ ] Did I make a significant design decision? → Add to decisions.yaml
- [ ] Did I encounter/fix a common error? → Add to errors.yaml
- [ ] Did I change project metadata? → Update context.yaml
```

### How to Update

**Adding a new scanner:**
```yaml
# In architecture.yaml, add to scanners section:
scanners:
  sast:
    - name: new-scanner
      purpose: "Description"
      languages: [list]

# In workflows.yaml, add to valid scanner list if needed
```

**Adding a new error pattern:**
```yaml
# In errors.yaml:
error_patterns:
  - pattern: "exact error message or regex"
    category: permissions|configuration|scanner|etc
    context: "When this occurs"
    root_cause: "Why it happens"
    solution:
      steps:
        - "Step 1"
        - "Step 2"
```

**Adding an ADR:**
```yaml
# In decisions.yaml:
decisions:
  - id: ADR-XXX
    title: "Decision title"
    date: "YYYY-MM-DD"
    status: accepted|proposed|deprecated
    context: "Why this decision was needed"
    decision: "What we decided"
    alternatives_considered:
      - name: "Option A"
        rejected_because: "Reason"
    consequences:
      positive: [list]
      negative: [list]
```

## For Human Developers

### When to Update .ai/

Update `.ai/` files when you:

1. **Add or remove features** - Update architecture and workflows
2. **Change how something works** - Update architecture data flow
3. **Make design decisions** - Document in decisions.yaml
4. **Discover common errors** - Add to errors.yaml
5. **Change commands or processes** - Update workflows.yaml

### PR Checklist

Add this to your PR description:

```markdown
## AI Context Updates
- [ ] Reviewed `.ai/` files for needed updates
- [ ] Updated relevant `.ai/` files (or N/A)
- [ ] Ran `npm run validate:ai` (when available)
```

### Quick Reference

```bash
# Files to check before PR
.ai/context.yaml      # Project metadata changed?
.ai/architecture.yaml # Components/structure changed?
.ai/workflows.yaml    # Commands/tasks changed?
.ai/decisions.yaml    # Made a design decision?
.ai/errors.yaml       # Fixed a common issue?
```

## Staleness Detection

### Manual Check

Look for these staleness indicators:

1. **File references that don't exist**
   ```bash
   # Check if referenced files exist
   grep -r "location:" .ai/*.yaml | while read line; do
     path=$(echo "$line" | grep -oP '(?<=location: ")[^"]+')
     [ ! -e "$path" ] && echo "STALE: $path referenced but doesn't exist"
   done
   ```

2. **Version mismatch**
   ```bash
   # Compare versions
   grep "version:" .ai/context.yaml
   cat version.yaml
   ```

3. **Scanner list mismatch**
   ```bash
   # Compare scanners in .ai/ vs actual actions
   ls .github/actions/scanner-* | wc -l
   grep -c "name: scanner-" .ai/architecture.yaml
   ```

### Automated Validation (Future)

```bash
# Future tooling
aicac validate .ai/           # Schema validation
aicac lint --check-refs       # Check file references exist
aicac diff --code .           # Detect drift from codebase
```

## Sync Points

### After Major Changes

Run this checklist after:
- [ ] Adding a new scanner
- [ ] Changing workflow structure
- [ ] Modifying build/test commands
- [ ] Making architectural changes
- [ ] Releasing a new version

### During Release

The release process should:
1. Update `context.yaml` version
2. Verify all file references are valid
3. Check for TODO/FIXME in .ai/ files

## Ownership

| File | Primary Owner | Update Frequency |
|------|--------------|------------------|
| context.yaml | Release manager | Each release |
| architecture.yaml | Tech lead | When structure changes |
| workflows.yaml | Any contributor | When tasks change |
| decisions.yaml | Tech lead | When decisions made |
| errors.yaml | Support/contributors | When issues resolved |
| prompting.md | Documentation owner | Quarterly review |
