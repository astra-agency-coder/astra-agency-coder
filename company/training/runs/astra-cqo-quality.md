# Training run — astra-cqo — quality

- conversation: 89a11510-c68b-4719-8955-730c90268047
- status: finished
- elapsed_s: 1025.7

## Result
Training run complete. Here is the concise final report.

## Training run — astra-cqo — Quality curriculum

**Subject verified:** `citriage` v0.1.0 — deterministic offline CI-log triage CLI (Product dept deliverable). Verdict: **FAIL (conditional)** — 13 PASS / 4 FAIL.

| Module | Artifact | Check |
|---|---|---|
| 1 · Acceptance discipline | `company/training/artifacts/cqo-quality-round2/acceptance-criteria.md` (17 ACs frozen **before** inspection) | **PASS** |
| 2 · Reproduce | `.../reproduction.md` | **PASS** (6/6 headline claims reproduced) |
| 3 · Break it | `.../edge-case-report.md` (+ `edge-findings.md`) | **FAIL** (4 crashes + 3 correctness defects) |
| 4 · Security pass | `.../security-pass.md` | **PASS on core claims · FAIL on robustness** |
| 5 · Verdict | `.../verdict.md` | **FAIL** (AC4, AC6, AC11, AC15) |

Run log: `company/training/runs/astra-cqo-quality.md` · dept repo: `dept-quality@df0d3d7` · company repo: `ce27c42` (both pushed).

**Real findings (each reproduced by ≥2 independent parties):**
- **BLOCKER** — unreadable file/dir (`chmod 000`) → `PermissionError` traceback, exit **1** (docs say 2).
- **MAJOR** — malformed `--profile` (invalid regex / non-string) → traceback + exit 1.
- **MAJOR** — **UUID normalization broken**: `signature.py` orders the 7–64 hex rule before the UUID rule, so UUIDs are only partially normalized → same root cause can split into different clusters.
- **MAJOR** — pytest **inline** failures drop the error text → different errors merge into one cluster.
- **MAJOR** — **ReDoS** via `--profile`: `^(a+)+$` vs a 32-byte line hangs >25 s (0.09 s → >25 s from N=20→30).
- **MINOR** — `{"fail": null}` silently no-ops; `test_id`-group check is lazy.
- Security core claims **hold**: audit-hook proof = 0 network / 0 subprocess / all file opens read-only; `scan-secrets` clean.

**What failed (plainly):** the tool's happy path is solid, but it fails 4/17 acceptance criteria — none covered by its 13 passing tests. Python 3.9 lower bound is **UNVERIFIED** (container has only 3.13), not passed.

**Reusable now:** dept `knowledge/verification/` — `PLAYBOOK.md` (+ round-2 lessons), `ACCEPTANCE-CHECKLIST.md` (template + pitfalls), and a **new** `signature_probe.py` harness (positive/negative/ordering probe for any `normalize()`/`signature()` pair), alongside the existing `citriage_verify.py` / `citriage_break.py`.

**Process note:** the earlier round-1 run returned CONDITIONAL PASS and missed all of the above; round 2 attacked correctness under unusual-but-valid input, worst-case performance, and the OS/permission error surface. Recorded as lessons L-0009/L-0010. Also verified: `astra.py spawn` **does** work as a delegation path for freshly-hired specialists (the `task` tool does not resolve them).

**Blockers:** none. Specialists `qa-edge-breaker`, `qa-sec-auditor`, `qa-repro-auditor` retired at end of run.
