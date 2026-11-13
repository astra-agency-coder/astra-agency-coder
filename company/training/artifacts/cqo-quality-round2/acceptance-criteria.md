# Acceptance criteria — citriage v0.1.0 (pre-inspection)

**Verifier:** astra-cqo (Quality) · **Date:** 2026-11-13
**Deliverable under test:** `citriage` 0.1.0 — "Deterministic, offline CI log triage"
**Source of truth for claims:** README.md, QUICKSTART.md, CHANGELOG.md, docs/PROFILES.md
(Product dept training run). Every criterion below is derived from a *written claim*
in those docs, and is falsifiable with a command.

> Discipline note: these criteria were written **before** running the tool, so the
> verdict cannot be reverse-fitted to whatever the tool happens to do.

## Claims extracted from the docs

| # | Claim (quoted/paraphrased) | Doc |
|---|---|---|
| C1 | "Zero third-party dependencies — Python 3.9+ standard library only" | README |
| C2 | "Deterministic output — the same input always produces byte-identical output" | README |
| C3 | Exit codes: 0 = no failures, 1 = failures found, 2 = usage/setup error | README |
| C4 | Parses pytest verbose (`... PASSED/FAILED`) and short-summary (`FAILED ... - msg`) | README |
| C5 | A failure printed twice (verbose + summary) is counted **once** | PROFILES/CHANGELOG |
| C6 | Signature collapses cosmetic differences (numbers, hex, UUIDs, versions, durations, paths) so same root cause → same cluster | README/signature.py docstring |
| C7 | Cross-run classification: `flaky` (some pass/some fail), `failed` (all fail), `passed` | README/CHANGELOG |
| C8 | Flakiness requires ≥2 runs; absent test is NOT counted as a pass | cluster.py docstring |
| C9 | Directory input: every `*.log`/`*.txt` in the folder is one run; other suffixes ignored | README/QUICKSTART |
| C10 | stdin via `-` works | README/QUICKSTART |
| C11 | `--profile pytest\|generic\|<path.json>`; custom profile needs a `fail` regex that captures `test_id` | README/PROFILES |
| C12 | `--json` output is valid JSON with keys `flaky`, `always_failed`, `clusters`, etc. | README |
| C13 | `python3 -m citriage report tests/fixtures` → exit 1, two FLAKY, one ALWAYS FAILING | QUICKSTART |
| C14 | CHANGELOG: "13 stdlib unittest tests" pass | CHANGELOG |
| C15 | demo.sh exits 0 ("DEMO PASS") and self-checks flaky + always-failing + determinism | demo/DEMO.md |
| C16 | No network, no telemetry, no credentials; nothing leaves the box | README |
| C17 | Safe by default (CI logs often contain secrets) | README |

## Numbered, testable acceptance criteria

| AC | Criterion | Test method | Pass condition |
|----|-----------|-------------|----------------|
| AC1 | Installs and runs on the target interpreter without third-party deps | `python3 -m pip install .` in a clean venv; inspect installed deps; `python3 -m citriage --version` | install succeeds, no deps pulled, version prints `0.1.0` |
| AC2 | Full test suite passes | `python3 -m unittest discover -s tests -v` | all tests pass, 0 failures/errors; test count matches doc claim (C14) |
| AC3 | Determinism: identical input → byte-identical stdout | run `--json` twice, `diff`; run text twice, `diff`; also across process restarts | both diffs empty |
| AC4 | Exit codes 0/1/2 exactly as documented | run clean log (expect 0), failing log (expect 1), bad path (expect 2) | each code matches |
| AC5 | pytest verbose + short-summary both parsed; duplicate failure counted once | fixture run1: `test_checkout` appears twice; `total_failures` and cluster counts | parsed; deduped to 1 |
| AC6 | Signature normalization collapses numeric/hex/uuid/version/dur/path differences | unit-level: `signature()` over pairs that differ only in those tokens | equal signatures for same shape; different for different shapes |
| AC7 | Flakiness classification correct on fixtures | `report tests/fixtures` | checkout & fetch = FLAKY, migrate = failed, login/logout/add_item = passed |
| AC8 | Absent test not counted as pass | synthetic 2 runs where a test only appears once as failed | classified `failed`, not `flaky` |
| AC9 | Directory input selects only `*.log`/`*.txt`; case-insensitive | dir with `.log`, `.txt`, `.LOG`, `.json`, `.md` | only log/txt picked up as runs |
| AC10 | stdin `-` works and matches file input | `cat run1.log \| citriage report -` vs `citriage report run1.log` | same failure totals |
| AC11 | Custom JSON profile honored; missing `test_id` group → exit 2 | write profile per docs example; run; also malformed profile | example works; malformed → exit 2 with message |
| AC12 | `--json` is valid, machine-parsable JSON | `python3 -m citriage report FIX --json \| python3 -c "import json,sys;json.load(sys.stdin)"` | parses; has documented keys |
| AC13 | Bundled-fixture quickstart result matches docs exactly | `python3 -m citriage report tests/fixtures` | exit 1; 2 FLAKY; 1 ALWAYS FAILING |
| AC14 | `demo.sh` reproduces and self-checks | `bash demo/demo.sh` | exit 0, prints "DEMO PASS" |
| AC15 | Robustness — empty file, empty dir, missing file, binary, huge line, unicode, CRLF | adversarial inputs each with recorded behaviour | no traceback/crash; documented-or-reasonable exit code; never silently wrong |
| AC16 | Security — no secrets in repo, no network egress, safe defaults, file perms | `scan-secrets`; grep source for socket/urllib/requests; static read of parse/report | no secret patterns; no network imports/calls; report contains no env values |
| AC17 | No fabricated output — sample output in README matches real output | diff README sample vs real run | real output consistent with docs |

## Severity rubric (how a FAIL is graded)

- **BLOCKER** — wrong result on documented happy path, crash, non-determinism, secret leak, network egress, security hole.
- **MAJOR** — documented behaviour differs from reality, wrong exit code, incorrect classification on a real edge case.
- **MINOR** — docs/typos, cosmetic mismatch that does not change the result.

## Out of scope for this pass
- Performance at scale (>10k log lines) beyond a smoke check.
- Windows-specific path handling.
- Any feature the docs explicitly list as not-in-v0.1 (JUnit XML, LLM, UI, network).
