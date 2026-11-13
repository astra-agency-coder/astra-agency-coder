# Playbooks

## PB-006 — Provision the seven department repositories
```bash
python3 ops/provision_repos.py --dry-run   # preview
python3 ops/provision_repos.py             # create/update all
```
Creates `dept-engineering`, `dept-marketing`, `dept-business-development`,
`dept-product`, `dept-operations`, `dept-quality`, `dept-research` — each
**private**, each with a README, a CHARTER, and `knowledge/` + `work/` folders.
Idempotent. Requires a token with repo-create + contents-write. Tested
2026-11-13: blocked by read-only token (403) — see lessons.

## PB-007 — Onboarding a new department
1. CEO decides the department is genuinely needed (record the decision).
2. `python3 ops/astra.py hire <dept>-manager --dept "<Dept>" --reports-to astra-ceo --tools terminal,file_editor,task_tracker,task_tool_set`
3. Add the department to `ops/provision_repos.py:DEPARTMENTS`.
4. Run PB-006 to create its private repository.
5. Create `company/departments/<slug>/` locally with README + CHARTER + knowledge/.
6. Update `company/ORG_DESIGN.md` and `company/roster.json`.
