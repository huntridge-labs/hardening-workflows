# Prompting Guide for AI Assistants

This file helps humans ask better questions about this project.

## The Core Problem

When you ask: "How do I use this?"

AI must:
1. Guess what "this" refers to
2. Guess your experience level
3. Guess your environment (GHES? github.com?)
4. Guess your goal (scanning? contributing? debugging?)

That's 4 dimensions of uncertainty = suboptimal response.

---

## Better Question Patterns

### Pattern: CONTEXT → GOAL → CONSTRAINTS

```
CONTEXT: I'm setting up CI/CD for a Python web app on github.com
GOAL: I want to scan for vulnerabilities on every PR
CONSTRAINTS: Scans must complete in under 5 minutes
```

vs.

```
How do I add security scanning?
```

The first question eliminates 90% of clarification back-and-forth.

---

### Pattern: WHAT I TRIED → WHAT HAPPENED → WHAT I EXPECTED

```
TRIED: Added reusable-security-hardening workflow with scanners: all
HAPPENED: Workflow times out after 30 minutes
EXPECTED: Complete in ~10 minutes like the docs suggest
```

vs.

```
The scan is too slow
```

---

### Pattern: ENVIRONMENT + VERSION

```
Environment: GHES 3.9, private repo, no internet access
Version: hardening-workflows@2.12.0
```

This immediately tells AI whether v2.x will even work for you.

---

## Question Templates

### "Help me set up scanning"

```
PROJECT TYPE: [language/framework]
HOSTING: [github.com | GHES version | self-hosted runner]
GOAL: [what you want to detect]
TIMELINE: [how fast scans need to be]
EXISTING SETUP: [any current CI/CD]
```

### "Something is broken"

```
WORKFLOW FILE: [paste relevant section or link]
ERROR MESSAGE: [exact error text]
WHEN IT HAPPENS: [push? PR? scheduled?]
WORKED BEFORE?: [yes/no, what changed?]
```

### "Help me choose"

```
OPTIONS I'M CONSIDERING: [A, B, C]
MY PRIORITIES: [speed? coverage? cost?]
CONSTRAINTS: [GHES? air-gapped? specific compliance?]
```

---

## Anti-Patterns (Questions That Waste Tokens)

### ❌ Vague scope
"Can you help me with security?"

### ❌ XY Problem
"How do I parse SARIF files?"
(when real goal is "I want to fail builds on critical findings" - which is built-in)

### ❌ Missing context
"Why doesn't it work?"

### ❌ Assumed knowledge
"Use the same setup as last time"
(AI doesn't remember previous sessions by default)

---

## Project-Specific Context to Include

When asking about this project, always clarify:

| Dimension | Options |
|-----------|---------|
| Implementation | v2.x workflows / v3.0 actions |
| Environment | github.com / GHES / air-gapped |
| Role | User (consuming) / Contributor (developing) |
| Scanner focus | SAST / Secrets / Container / IaC / All |

---

## Example: Good vs. Better vs. Best

### Good
"How do I scan container images?"

### Better
"How do I scan container images with trivy using hardening-workflows on github.com?"

### Best
```
CONTEXT: I have 5 container images built in a matrix job
GOAL: Scan each image for CVEs, fail if critical found
ENVIRONMENT: github.com, public repo
CONSTRAINT: Images are in ghcr.io, built in same workflow
QUESTION: How do I configure container-scan-from-config for this?
```

---

## Why This Matters

Every clarifying question the AI asks = tokens spent on meta-conversation instead of solving your problem.

Structured input → Direct answer → Faster iteration

---

## For AI Reading This

When a human asks a vague question about this project:

1. Check `.ai/context.yaml` for likely answers
2. If ambiguous, ask ONE multi-part clarifying question covering all dimensions
3. Don't ask "What version?" then "What environment?" separately - batch them
4. Suggest the better question pattern in your response so human learns
