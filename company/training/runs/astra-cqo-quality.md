# Training run — astra-cqo — quality

- conversation (round 1, errored): c416d58b-4cd9-42e7-b878-b48dcb4496a7
- status (round 1): error
- elapsed_s (round 1): 508.3

## Result (round 1 — errored, partial)

Round 1 left a CONDITIONAL PASS for `citriage` v0.1.0 (3 profile-error crashes)
in the department repo. It did **not** complete the curriculum.

---

# Training run — astra-cqo — quality (round 2)

- **Curriculum:** `company/training/curricula/quality.md`
- **Manager:** `astra-cqo` (Chief Quality Officer)
- **Date:** 2026-11-13
- **Subject under verification:** `citriage` v0.1.0 — deterministic offline CI-log
  triage CLI (Product dept, software-delivery training run).
- **Status:** COMPLETE — verdict **FAIL (conditional)**, 13 PASS / 4 FAIL.
- Round 2 is **additive**: it found defects round 1 missed (UUID normalization,
  inline-error loss, ReDoS, `chmod 000` crash family).

## Specialists used (hired + retired this run)
| Name | Purpose | Result |
|---|---|---|
| `qa-repro-auditor` | independent reproduction of 6 headline claims | 6/6 PASS |
| `qa-edge-breaker` | adversarial robustness (22 cases) | 13 PASS / 4 FAIL |
| `qa-sec-auditor` | security pass (10 checks) | 8 PASS / 2 FAIL |
All three fired at end of run (reason: training run complete). Two were newly
hired (`qa-edge-breaker`, `qa-sec-auditor`); one pre-existed (`qa-repro-auditor`).

## Modules

| # | Module | Artifact | Check |
|---|--------|----------|-------|
| 1 | Acceptance discipline | `acceptance-criteria.md` (17 ACs frozen pre-inspection) | **PASS** |
| 2 | Reproduce | `reproduction.md` | **PASS** (6/6 claims) |
| 3 | Break it | `edge-case-report.md` (+ `edge-findings.md`) | **FAIL** (4 crashes + 3 correctness) |
| 4 | Security pass | `security-pass.md` | **PASS on core claims, FAIL on robustness** |
| 5 | Verdict | `verdict.md` | **FAIL** (AC4, AC6, AC11, AC15) |

Artifacts also in `company/training/artifacts/cqo-quality-round2/` and in the
department repo (`dept-quality`, commit `df0d3d7`).

## Commands run (representative; real output captured in the artifacts)
```bash
# Module 2 — reproduce
python3 -m venv .venv && .venv/bin/pip install .
.venv/bin/pip list --format=freeze                  # -> citriage==0.1.0, pip==26.3
.venv/bin/python -m unittest discover -s tests -v   # -> Ran 13 tests ... OK
.venv/bin/citriage report tests/fixtures            # -> exit 1, 2 FLAKY, 1 ALWAYS FAILING
.venv/bin/citriage report tests/fixtures --json | md5sum   # identical x5 runs, x6 hash seeds
bash demo/demo.sh                                   # -> DEMO PASS ... exit 1.  (exit 0)

# Module 3 — break it
touch f.log; chmod 000 f.log; citriage report f.log # PermissionError traceback, exit 1 (want 2)
mkdir d; chmod 000 d; citriage report d             # PermissionError traceback, exit 1 (want 2)
echo '{"fail":"["}' > p.json; echo x > l.log; citriage report l.log --profile p.json  # re.PatternError, exit 1
echo '{"fail":123}'  > p.json; citriage report l.log --profile p.json                 # TypeError, exit 1
python3 -c "from citriage.signature import normalize; print(normalize('job 123e4567-e89b-12d3-a456-426614174000 x'))"
    # -> 'job <HEX>-e89b-12d3-a456-<HEX> x'   <-- UUID NOT normalized (hex rule pre-empts it)

# Module 4 — security
python3 probe_egress.py                             # sys.addaudithook -> 0 network, 0 proc, 0 write-opens
python3 redos_timing.py                             # {"fail":"^(a+)+$"}: N=20 0.09s ... N=30 TIMEOUT>25s
python3 ops/astra.py scan-secrets                   # -> {"clean": true, "offenders": []}
```

## Key findings (all reproduced by >=2 independent parties)
1. **BLOCKER — unhandled `PermissionError`** on `chmod 000` file *and* directory:
   raw traceback, exit **1** instead of the documented **2**.
2. **MAJOR — malformed `--profile`**: invalid regex → `re.PatternError`;
   non-string `fail` → `TypeError`; both traceback + exit 1.
3. **MAJOR — UUID normalization broken**: `signature.py` orders the 7–64 hex rule
   before the UUID rule, so UUIDs are only partially normalized; the same root
   cause can split into different clusters. (Round 1 missed this.)
4. **MAJOR — pytest inline failures drop the error text** (`error_line=None`):
   different errors for the same test merge into one cluster; clusters lose the
   `e.g.` example. (Round 1 missed this.)
5. **MAJOR — ReDoS via `--profile`**: `^(a+)+$` vs a 32-byte line hangs >25 s.
   (Round 1 missed this.)
6. **MINOR** — `{"fail": null}` silently no-ops; `test_id`-group validation is lazy.

## What FAILED (stated plainly)
- Module 3 (**Break it**) FAILED: 4 unhandled-exception crashes on ordinary bad
  input (unreadable file/dir, malformed profile) → raw traceback + wrong exit code.
- Module 4 (**Security pass**) core claims PASS, but FAILED on robustness (ReDoS).
- Module 5 (**Verdict**) is **FAIL** — AC4 (exit codes), AC6 (normalization),
  AC11 (malformed profile), AC15 (robustness) are not met.
- **Not verified:** Python 3.9 lower bound (container has only 3.13) → UNVERIFIED,
  not PASS.

## Reusable output (durable)
- `dept-quality/knowledge/verification/PLAYBOOK.md` (+ round-2 additions)
- `dept-quality/knowledge/verification/ACCEPTANCE-CHECKLIST.md` (template + pitfalls)
- `dept-quality/knowledge/verification/signature_probe.py` (**new** harness —
  positive/negative/ordering probe for any `normalize()`/`signature()` pair)
- pre-existing `citriage_verify.py`, `citriage_break.py` (repointable)

## Blockers
None. All modules completed; the FAIL is a finding about the subject, not a
blocker to this run.

## Retire
`qa-edge-breaker`, `qa-sec-auditor`, `qa-repro-auditor` fired at end of run.

