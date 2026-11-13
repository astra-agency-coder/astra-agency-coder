# AGENTS.md — AI ASTRA AGENCY

Persistent repository memory for every agent working in this repo.

## What this repository is
The **durable company state** of AI ASTRA AGENCY: company documents, agent
definitions, the internal control plane, memory, integrations and tests. The
runtime is ephemeral (idle-recycled); this repo is not. Commit often.

## Orientation — read these first
1. `company/IDENTITY.md` — who the company is and its hard constraints.
2. `company/CEO_CHARTER.md` — the CEO's authority and operating loop.
3. `company/ORG_DESIGN.md` — departments, managers, reporting chain.
4. `company/ESCALATION_POLICY.md` — what to handle alone vs escalate.
5. `ops/memory/` — decisions, lessons, playbooks, revenue, risks.

## Environment facts (verified)
- OpenHands Agent Server **v1.62.0**, SDK **1.62.0**.
- Delegation works two ways: the **`task` tool** (synchronous, nested) and
  **child conversations** (`python3 ops/astra.py spawn`).
- File-based agents live in `.agents/agents/*.md` (YAML frontmatter: `name`,
  `description`, `department`, `reports_to`, `tools`, `model`).
- REST API auth: `X-Session-API-Key` from `SESSION_API_KEY` / `RUNTIME_URL`
  in `/proc/1/environ`. `ops/astra.py` handles this.
- The SDK is **not** installed locally and cannot be pip-installed (permission
  denied). Use the REST API, not `import openhands`.

## Commands you will use
```bash
python3 ops/astra.py status            # company + roster + tasks
python3 ops/astra.py roster            # agent list
python3 ops/astra.py hire <name> --dept <D> --reports-to <mgr> --tools a,b
python3 ops/astra.py spawn <agent> "<task>"    # run in a child conversation
python3 ops/astra.py fire <name> --reason "…"  # retire an agent
python3 ops/astra.py health            # component health (exit 1 if broken)
python3 ops/astra.py scan-secrets      # fail if a secret pattern is present
python3 ops/heal.py                    # diagnose + bounded self-repair
python3 ops/report.py owner --write    # Owner report
python3 ops/report.py board --write    # internal status board
python3 ops/tests/run_tests.py --live  # readiness tests
```

## Conventions
- **No secrets in this repo.** Run `scan-secrets` before every commit.
- Never claim a step you did not run; never fabricate results or capabilities.
- Wallet is **receive-only**; no agent holds keys or transfers funds.
- Bound retries to **3 attempts**, then change approach or escalate.
- Record durable knowledge in `ops/memory/` (or a department's `knowledge/`).
- No commercial activity until the Owner issues the first operational task.

## Verified capabilities & known limitations
| Capability | Status |
|---|---|
| Agent server + SDK v1.62.0 | Working |
| `task` tool nested delegation | Working (tested) |
| Child conversations | Working (tested) |
| File-based agents | Working (tested) |
| Session continuity across follow-ups | Working (tested) |
| GitHub **read** (identity, list repos) | Working |
| GitHub **write** (create repo, push) | **Blocked** — token is read-only (403) |
| Telegram / Gmail / Wallet | Prepared, awaiting Owner credentials |
| Durable scheduling | Must run as an OpenHands Cloud automation, not a local process |

## Git
- Remote: `astra-agency-coder/astra-agency-coder` (default branch `main`).
- Git identity for agent commits: `AI ASTRA AGENCY <agents@astra-agency.dev>`.
- Add `Co-authored-by: openhands <openhands@all-hands.dev>` to commits.
