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
- Company site: `deliveries/astra-site/` (canonical public site). Served by
  `server.py` on `ASTRA_SITE_PORT` (default 12000); `serve.sh` restarts it
  idempotently (log `/tmp/astra_site_new.log`), `healthcheck.sh` checks it,
  `verify_site.py` verifies it, and `ops/heal.py` self-heals the `astra_site`
  check. Public URL: `https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/`.
- Astra Trading deck: `deliveries/astra-trading/` (gold analysis SaaS, ar/en/tr).
  The API (`api/app.py`, FastAPI) also serves the deck's static files, so the
  whole product is **one origin on one port** — no CORS, no second deployment.
  Run it on **12001** (`uvicorn app:app --port 12001`); 12000 stays the company
  site because `ops/heal.py` and `deliveries/astra-site/healthcheck.sh` both
  assume `ASTRA_SITE_PORT=12000`. Public URL:
  `https://work-2-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/`.
- Department repos: one **private** GitHub repo per department
  (`dept-engineering`, `dept-security`, …), each reachable only by its own
  manager's deploy key. Map: `company/departments/{repos,access}.json`.
  Tools: `ops/provision_repos.py`, `ops/provision_access.py`, `ops/deptrepo.py`.
  Isolation is verified: cross-department `git ls-remote` is rejected.

## Commands you will use
```bash
./up.sh                                # bring up site (12000) + trading (12001)
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
| GitHub **write** (create repo, push) | Working — via `GITHUB_TOKEN_WRITE` in the secret store |
| Telegram / Gmail / Wallet | Prepared, awaiting Owner credentials |
| Durable scheduling | Must run as an OpenHands Cloud automation, not a local process |

## Department repositories (private)
Each department has its own private GitHub repository under `astra-agency-coder`:
`dept-engineering`, `dept-marketing`, `dept-business-development`, `dept-product`,
`dept-operations`, `dept-quality`, `dept-research`. Each holds `README.md`,
`CHARTER.md`, `knowledge/` (durable department memory) and `work/` (in-flight work).
Specialists do not get their own repos; they work under `work/<agent>/` inside their
department repo. Provision or refresh all of them with `python3 ops/provision_repos.py`.

## Payments (receive-only, multi-network)
Wallet addresses live in `company/finance/wallets.json` (public data, not secrets):
USDT-TRC20 (primary) `TFBEwXbB4iTyaPC2mtwu5yXSeDjEegJmE6`, USDT-BEP20 + Ethereum
`0x3321D9…d5C045`, Solana `3WqqQAa…81DwR`, Bitcoin `bc1q9ez…h2t`.
- List networks: `python3 ops/integrations/wallet.py`
- Validate all: `python3 -c "import sys;sys.path.insert(0,'ops');from integrations import wallet;print(wallet.validate_all())"`
- Verify a payment: `wallet.verify_payment(txid, amount, network)` — on-chain only.
- The company holds **no keys, signs nothing, transfers nothing, spends nothing**.
- Never treat a screenshot or chat link as payment proof.

## Scoped manager access (least privilege)
Each manager holds its OWN SSH keypair, registered as a **write-enabled deploy key on
exactly one repository** — its department repo. GitHub binds a deploy key to a single
repository, so a manager cannot read or push any other repo, and no manager ever holds
the company-wide token.

- Provision/refresh: `python3 ops/provision_access.py`
- Prove isolation: `python3 ops/provision_access.py --verify` (own repo reachable,
  every other repo denied)
- Managers work through `python3 ops/deptrepo.py {clone,pull,save,ls} <manager>`
- Private keys live only in `~/.astra/keys/` (0600) and the runtime secret store.
  They are never committed, never printed, never put in a report.

## Git
- Canonical private company repo: `astra-agency-coder/ai-astra-agency` (branch `master`).
- Public profile repo: `astra-agency-coder/astra-agency-coder` (branch `main`).
- Push with `bash ops/gitpush.sh <remote> <branch>` — it uses an ephemeral credential
  helper so the token is never written to `.git/config`.
- Git identity for agent commits: `AI ASTRA AGENCY <agents@astra-agency.dev>`.
- Add `Co-authored-by: openhands <openhands@all-hands.dev>` to commits.
