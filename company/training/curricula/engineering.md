# Curriculum — Engineering (intensive)

Objective: turn the Engineering department into a team that reads real codebases,
understands how software is actually built, and ships reviewed, tested code.

## Module E1 — Read real projects (study, do not copy)
- Pick 3 open-source projects (small, medium, large). For each, produce a short
  architecture note: entry points, module boundaries, data flow, test strategy,
  build/run commands. Write to `knowledge/code-reading/<project>.md`.
- Check: each note has concrete file paths and a reproducible run command.

## Module E2 — Reproduce a build
- Clone one project, install deps in a throwaway venv, run its test suite.
  Record exact commands and the real pass/fail output.
- Check: `knowledge/repro/<project>.txt` contains the actual command output.

## Module E3 — Build to spec
- Implement a small tool from a written spec (CLI + tests). Enforce: input
  validation, error handling, no dead code, tests that run.
- Check: `pytest` (or equivalent) passes; output pasted verbatim.

## Module E4 — Review
- Review another team member's code against a checklist (correctness, security,
  edge cases, clarity). Produce findings with line references.
- Check: at least one real defect or a justified "no defects" with reasoning.

## Module E5 — Deliver
- Package one artifact: README, run instructions, license note, version tag.
- Check: a fresh clone runs it in one command.

## Acceptance
All five modules have artifacts in the department repo, each with real command
output. No module counts without its check.
