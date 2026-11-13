# Module 5 — VERDICT: citriage v0.1.0

**Verifier:** astra-cqo (Quality) · **Date:** 2026-11-13
**Independence:** every module was re-run by a separate specialist in its own venv
(`qa-repro-auditor`, `qa-edge-breaker`, `qa-sec-auditor`). Findings below were
reproduced by at least two independent parties.

## Verdict: **FAIL** (conditional — see "What would make it PASS")

The happy path is genuinely good: it installs with zero dependencies, the 13-test
suite passes, output is byte-deterministic, the demo self-checks, and the security
claims (no network/telemetry/credentials) hold under runtime audit. **But** the
deliverable fails four of the seventeen acceptance criteria — three of them real
correctness defects and one a crash family — none of which the shipped tests cover.

## Acceptance-criteria scorecard

| AC | Criterion | Verdict | Evidence |
|----|-----------|---------|----------|
| AC1 | installs, zero third-party deps | **PASS** | `pip list` = citriage+pip; version 0.1.0 |
| AC2 | suite passes; count matches docs | **PASS** | `Ran 13 tests … OK` (CHANGELOG says 13) |
| AC3 | deterministic byte-identical output | **PASS** | diff empty; 1 md5 across 6 hash seeds |
| AC4 | exit codes 0/1/2 as documented | **FAIL** | clean→0, fixtures→1, bad path→2 **but** permission errors & malformed profiles → traceback + **1** (should be 2) |
| AC5 | verbose+summary parsed; dedup | **PASS** | run1 → 8 records, 1 failure per test |
| AC6 | signature collapses cosmetic diffs | **FAIL** | numeric/hex/version/dur/path collapse OK; **UUID normalization broken** (`<HEX>-e89b-12d3-a456-<HEX>`) → same root cause can split clusters |
| AC7 | flaky/failed/passed classification | **PASS** | checkout+fetch=FLAKY, migrate=failed, others=passed |
| AC8 | absent test not counted as pass | **PASS** | test seen once (failed) → `failed`, not `flaky` |
| AC9 | dir reads only `*.log`/`*.txt`, case-insensitive | **PASS** | `.log`+`.txt`+`.LOG` read; `.json`/`.md` ignored; empty dir→2 |
| AC10 | stdin `-` works | **PASS** | matches file totals |
| AC11 | custom profile honored; bad profile→2 | **FAIL** | valid profile works; missing `test_id` (when matched)→2; **invalid regex / non-string → traceback + exit 1** |
| AC12 | `--json` valid & documented keys | **PASS** | `json.load` OK; 8 keys |
| AC13 | bundled-fixture quickstart matches docs | **PASS** | exit 1, 2 FLAKY, 1 ALWAYS FAILING |
| AC14 | `demo.sh` self-checks, exit 0 | **PASS** | prints `DEMO PASS`, exit 0 |
| AC15 | robustness to bad/empty/oversize input | **FAIL** | 4 unhandled exceptions (2×PermissionError, PatternError, TypeError); binary/5 MB/CRLF/unicode OK |
| AC16 | no secrets, no egress, safe defaults | **PASS** | audit hook: 0 network/proc, all opens mode `r`; scan-secrets clean |
| AC17 | no fabricated output (docs == reality) | **PASS** | README/QUICKSTART/DEMO samples match real runs |

**Score: 13 PASS · 4 FAIL (AC4, AC6, AC11, AC15).**

## Defect punch-list (for the fix owner)

| ID | Sev | Defect | Minimal reproduction |
|----|-----|--------|----------------------|
| D1 | BLOCKER | Unhandled `PermissionError` on unreadable file/dir → traceback + exit 1 | `touch f.log; chmod 000 f.log; citriage report f.log` |
| D2 | MAJOR | Unhandled `re.PatternError`/`TypeError` on malformed profile → traceback + exit 1 | `echo '{"fail":"["}' > p.json; echo x > l.log; citriage report l.log --profile p.json` |
| D3 | MAJOR | UUID not normalized (hex rule ordered before uuid rule) | `normalize('job 123e4567-e89b-12d3-a456-426614174000 x')` → `job <HEX>-e89b-12d3-a456-<HEX> x` |
| D4 | MAJOR | pytest *inline* failures drop the error text → different errors merge; clusters lose `e.g.` | inline-only log with two different errors → 1 cluster, `error_example=None` |
| D5 | MAJOR | ReDoS via `--profile` (catastrophic backtracking) | `{"fail":"^(a+)+$"}` vs `'a'*30+'b'` → hangs >25 s |
| D6 | MINOR | `{"fail": null}` silently no-ops though docs call `fail` required | `--profile {"fail":null}` → exit 0 |
| D7 | MINOR | `test_id`-group validation is lazy (only on match), docs imply unconditional | `--profile` without group on a non-matching log → exit 0 |
| D8 | INFO | report re-prints log `error_example` to stdout (secrets in logs reach the terminal) | documented, not a hole |
| D9 | INFO | Python 3.9 lower bound untested (container has only 3.13) | — |

## What would make it PASS
1. Wrap all of `main()` in a catch-all that maps OS/regex/type errors to exit **2**
   with a friendly message (fixes D1, D2, D6, D7).
2. Compile/validate profile regexes at `load_profile` time (early, single error).
3. Reorder `signature.py` normalization: UUID before the 7–64 hex rule (fixes D3).
4. Add an error group to the pytest inline pattern, or fall back to the summary
   line's error for that test (fixes D4).
5. Bound regex complexity (e.g. reject nested quantifiers, or run with a step
   limit) (fixes D5).
6. Add tests for each of D1–D5 so the suite count grows beyond 13.

## Honesty note
This is a training verification of an internal artifact. No criterion was marked
PASS without a reproduced observation; the four FAILs are backed by pasted
commands and outputs in Modules 2–4. Nothing was rubber-stamped.
