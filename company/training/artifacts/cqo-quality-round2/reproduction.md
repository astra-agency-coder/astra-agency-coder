# Independent Reproduction — `citriage` v0.1.0

**Auditor:** qa-repro-auditor (Quality dept, AI ASTRA AGENCY)
**Date:** 2026-11-13
**Pristine tree:** `/tmp/stranger` → copied to `/tmp/ra-work` (`rm -rf build/ *.egg-info`, `__pycache__`)
**Isolated venv:** `/tmp/ra-venv` (Python 3.13.15)
**Install command:** `cd /tmp/ra-work && /tmp/ra-venv/bin/pip install .`
**Result:** `Successfully installed citriage-0.1.0`
**Source was NOT modified.** All commands below were run by the auditor; output is pasted verbatim.

> Environment note: the tree requires Python 3.9+; the container provides 3.13.15,
> which satisfies `requires-python = ">=3.9"`. This was the only interpreter available.

---

## Claim 1 — ZERO third-party dependencies (stdlib only, Python 3.9+)

**Commands**
```bash
/tmp/ra-venv/bin/pip list
/tmp/ra-venv/bin/pip show citriage
grep -rhE "^\s*(import|from) " citriage/*.py | sort -u
```

**Output — `pip list` (evidence)**
```
Package  Version
-------- -------
citriage 0.1.0
pip      26.3
```
Only `citriage` (the product itself) and `pip` are present. No third-party runtime deps.

**Output — `pip show citriage`**
```
Name: citriage
Version: 0.1.0
...
Requires:
Required-by:
```
`Requires:` is empty → the installed distribution declares no dependencies.

**Output — every import statement in the package**
```
    from .parse import load_profile
    from .parse import parse_source
from . import __version__
from .cli import main
from .cluster import analyze
from .parse import FAIL, Run
from .parse import parse_source
from .report import build, render_json, render_text
from .signature import signature_for_record
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
```
Every top-level module — `argparse, dataclasses, hashlib, json, pathlib, re, sys, __future__` — is
part of the Python standard library; the rest are intra-package relative imports.

**Verdict: PASS.** Zero third-party dependencies; stdlib only. `pyproject.toml` confirms
`dependencies = []` and `requires-python = ">=3.9"`.

---

## Claim 2 — unittest suite passes and count matches CHANGELOG "13 tests"

**Command**
```bash
cd /tmp/ra-work && /tmp/ra-venv/bin/python -m unittest discover -s tests -v
```

**Output (exact count line)**
```
...
----------------------------------------------------------------------
Ran 13 tests in 0.230s

OK
```
Per-test lines (all `ok`): `test_clean_exit0`, `test_json_report_exit1`,
`test_report_failures_exit1`, `test_usage_error_exit2`,
`test_checkout_clusters_despite_different_numbers`, `test_flakiness_classification`,
`test_render_json_byte_identical`, `test_render_text_stable`, `test_generic_profile`,
`test_pytest_inline_and_summary`, `test_different_error_diff_sig`,
`test_normalize_collapses_numbers`, `test_same_shape_same_sig`.
Process exit code: `0`.

**Exact test count observed: 13.** Matches the CHANGELOG claim of "13 stdlib `unittest` tests".

**Verdict: PASS.**

---

## Claim 3 — Deterministic output (byte-identical text AND --json; across restarts and PYTHONHASHSEED)

**Commands**
```bash
# across three separate process restarts
for i in 1 2 3; do /tmp/ra-venv/bin/citriage report tests/fixtures > /tmp/t$i.txt 2>&1; done
md5sum /tmp/t1.txt /tmp/t2.txt /tmp/t3.txt
diff /tmp/t1.txt /tmp/t2.txt && diff /tmp/t1.txt /tmp/t3.txt

for i in 1 2 3; do /tmp/ra-venv/bin/citriage report tests/fixtures --json > /tmp/j$i.json 2>&1; done
md5sum /tmp/j1.json /tmp/j2.json /tmp/j3.json
diff /tmp/j1.json /tmp/j2.json && diff /tmp/j1.json /tmp/j3.json

# PYTHONHASHSEED sweep
for s in 0 1 42 12345 99999 random; do PYTHONHASHSEED=$s /tmp/ra-venv/bin/citriage report tests/fixtures > /tmp/hs_text_$s.txt 2>&1; done
md5sum /tmp/hs_text_*.txt
for s in 0 1 42 12345 99999 random; do PYTHONHASHSEED=$s /tmp/ra-venv/bin/citriage report tests/fixtures --json > /tmp/hs_json_$s.json 2>&1; done
md5sum /tmp/hs_json_*.json
```

**Output — text, 3 process restarts**
```
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/t1.txt
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/t2.txt
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/t3.txt
TEXT_IDENTICAL_OK
```

**Output — JSON, 3 process restarts**
```
18f55d24191b9a0399ed0942c1d66bf1  /tmp/j1.json
18f55d24191b9a0399ed0942c1d66bf1  /tmp/j2.json
18f55d24191b9a0399ed0942c1d66bf1  /tmp/j3.json
JSON_IDENTICAL_OK
```

**Output — text across PYTHONHASHSEED sweep**
```
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/hs_text_0.txt
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/hs_text_1.txt
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/hs_text_12345.txt
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/hs_text_42.txt
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/hs_text_99999.txt
19a01508a7ea8bfbe9dba40d9cb0ae2d  /tmp/hs_text_random.txt
```

**Output — JSON across PYTHONHASHSEED sweep**
```
18f55d24191b9a0399ed0942c1d66bf1  /tmp/hs_json_0.json
18f55d24191b9a0399ed0942c1d66bf1  /tmp/hs_json_1.json
18f55d24191b9a0399ed0942c1d66bf1  /tmp/hs_json_12345.json
18f55d24191b9a0399ed0942c1d66bf1  /tmp/hs_json_42.json
18f55d24191b9a0399ed0942c1d66bf1  /tmp/hs_json_99999.json
18f55d24191b9a0399ed0942c1d66bf1  /tmp/hs_json_random.json
```
Single MD5 per format across all runs and all hash seeds; `diff` reported no differences.
Text MD5 = `19a01508a7ea8bfbe9dba40d9cb0ae2d`; JSON MD5 = `18f55d24191b9a0399ed0942c1d66bf1`.

**Verdict: PASS.** Byte-identical across process restarts and across six PYTHONHASHSEED values
(including `random`), for both text and `--json`.

---

## Claim 4 — Exit codes: 0 clean, 1 failures, 2 usage/setup error

**Commands**
```bash
printf 'tests/t.py::a PASSED\ntests/t.py::b PASSED\n' > /tmp/cleanlogs/ok.log
/tmp/ra-venv/bin/citriage report /tmp/cleanlogs;                       echo "EXIT0=$?"
/tmp/ra-venv/bin/citriage report tests/fixtures >/dev/null;            echo "EXIT1=$?"
/tmp/ra-venv/bin/citriage report /no/such/path.log;                    echo "EXIT2=$?"
```

**Output**
```
citriage report
========================================
runs analysed : 1 (ok.log)
tests seen    : 2
total failures: 0

FLAKY  (0):
  (none)

ALWAYS FAILING (0):
  (none)

FAILURE CLUSTERS (0):
  (none)
EXIT0=0
EXIT1=1
citriage: error: no such file or directory: /no/such/path.log
EXIT2=2
```

**Verdict: PASS.** Clean input → `0`; failing fixtures → `1`; missing path → `2`
(with a clear error message on stderr).

---

## Claim 5 — `citriage report tests/fixtures` → exit 1, two FLAKY, one ALWAYS FAILING

**Command**
```bash
cd /tmp/ra-work && /tmp/ra-venv/bin/citriage report tests/fixtures; echo "EXIT=$?"
```

**Output**
```
citriage report
========================================
runs analysed : 3 (run1.log, run2.log, run3.log)
tests seen    : 6
total failures: 6

FLAKY  (2):
  - tests/test_cart.py::test_checkout
  - tests/test_net.py::test_fetch

ALWAYS FAILING (1):
  - tests/test_db.py::test_migrate

FAILURE CLUSTERS (3):
  [1642bfb7da2ea9ee] 1 test(s), 3 run(s)
  [a140c92291bc184e] 1 test(s), 2 run(s)
  [cda824ea7741f96a] 1 test(s), 1 run(s)
EXIT=1
```

**Verdict: PASS.** Exit code `1`; exactly two tests under `FLAKY`
(`test_checkout`, `test_fetch`); exactly one under `ALWAYS FAILING` (`test_migrate`).
Matches the QUICKSTART expectation and the README "Sample output" block verbatim
(same cluster hashes `1642bfb7da2ea9ee`, `a140c92291bc184e`, `cda824ea7741f96a`).

---

## Claim 6 — `bash demo/demo.sh` exits 0 and prints "DEMO PASS"

**Command**
```bash
cd /tmp/ra-work && bash demo/demo.sh; echo "DEMO_EXIT=$?"
```

**Output**
```
== 1. Generate three runs of the same suite (one flaky, one always-broken) ==

== 2. Triage the folder ==
citriage report
========================================
runs analysed : 3 (run1.log, run2.log, run3.log)
tests seen    : 3
total failures: 5

FLAKY  (1):
  - tests/test_cart.py::test_checkout

ALWAYS FAILING (1):
  - tests/test_db.py::test_migrate

FAILURE CLUSTERS (2):
  [1642bfb7da2ea9ee] 1 test(s), 3 run(s)
  [a140c92291bc184e] 1 test(s), 2 run(s)
EXIT=1

== 3. Self-check ==
DEMO PASS: flaky + always-failing detected, deterministic, exit 1.
DEMO_EXIT=0
```

**Verdict: PASS.** Script exit code `0` and it prints `DEMO PASS: flaky + always-failing
detected, deterministic, exit 1.`

---

## Summary

| # | Claim | Verdict |
|---|-------|---------|
| 1 | Zero third-party deps (stdlib only, Py 3.9+) | **PASS** |
| 2 | unittest suite passes; 13 tests | **PASS** (Ran 13 tests, OK) |
| 3 | Deterministic text + `--json`, across restarts & PYTHONHASHSEED | **PASS** |
| 4 | Exit codes 0 / 1 / 2 | **PASS** |
| 5 | `report tests/fixtures` → exit 1, 2 FLAKY, 1 ALWAYS FAILING | **PASS** |
| 6 | `bash demo/demo.sh` → exit 0 + "DEMO PASS" | **PASS** |

**All 6 headline claims reproduce. No mismatch found between the docs and observed behaviour.**

### Notes / minor observations (not failures)
- `pyproject.toml` still carries the deprecated `License :: OSI Approved :: MIT License`
  classifier, which emits a `SetuptoolsDeprecationWarning` at build time. Cosmetic only;
  does not affect install, deps, or behaviour.
- The demo (`demo/demo.sh`) invokes `python3 -m citriage` against the *system* interpreter
  (module resolvable from the repo root via `cd "$(dirname "$0")/.."`), not the venv's
  `citriage` script. It worked here because the module is importable from the source tree;
  this is a demo-harness detail, not a claim failure.
- The environment's only interpreter is Python 3.13.15; the "3.9+" lower bound was **not**
  exercised on an actual 3.9 interpreter (unavailable in the container). The declared
  `requires-python = ">=3.9"` and stdlib-only imports are consistent with 3.9 compatibility,
  but a 3.9 run was out of scope given the container toolchain.
