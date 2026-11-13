# Module 3 — "Break it" (adversarial edge cases) — citriage v0.1.0

**Verifier:** astra-cqo · **Date:** 2026-11-13
Independently re-run by specialist `qa-edge-breaker` (child conversation, own
venv) — full 22-row table in `specialists/edge-findings.md`. Both passes agree.

## Contract under test
Exit **0** = no failures · **1** = failures found · **2** = usage/setup error.
Directory input reads only `*.log`/`*.txt`. A custom JSON profile needs a `fail`
regex that captures group `test_id`; PROFILES.md says citriage "errors (exit 2)
if it is missing".

## Results table (own run; 21 cases)

| # | Case | Command | Exit | Observed | Verdict |
|---|------|---------|------|----------|---------|
| E1 | empty file | `report empty.log` | 0 | clean report, 0 tests | PASS |
| E2 | whitespace-only file | `report blank.log` | 0 | clean report | PASS |
| E3 | empty directory | `report emptydir` | 2 | `no .log/.txt files in ...` | PASS |
| E4 | missing path | `report does-not-exist.log` | 2 | friendly error | PASS |
| E5 | empty stdin | `report -` </dev/null | 0 | clean report | PASS |
| E6 | binary/random bytes | `report blob.log` | 0 | no crash (`errors="replace"`) | PASS |
| E7 | 5 MB single line | `report huge.log` | 0 | ~1 s, no hang | PASS |
| E8 | unicode test id | `report uni.log` | 1 | parsed `test_éè`; emoji id silently dropped | PASS (lossy) |
| E9 | CRLF | `report crlf.log` | 1 | parsed correctly | PASS |
| E10 | **unreadable file (chmod 000)** | `report noperm.log` | **1** | **raw traceback: PermissionError** | **FAIL** |
| E11 | directory named `*.log` | `report weird.log/` | 2 | treated as dir; `no .log/.txt files` | PASS |
| E12 | 2000 failures | `report many.log` | 1 | fast, no crash | PASS |
| E13 | same test FAILED then PASSED | `report dup.log` | 0 | last-write-wins masks failure | see note |
| E14 | `--json` clean | `report ok.log --json` | 0 | valid JSON | PASS |
| E15 | no-args / bad subcmd | `citriage` / `frobnicate` | 2 | argparse usage error | PASS |
| E16 | symlink to log | `report link.log` | 0 | works | PASS |
| E17 | **unreadable dir (chmod 000)** | `report nodir` | **1** | **raw traceback: PermissionError** | **FAIL** |
| E18 | **invalid regex profile** | `--profile {"fail":"("}` | **1** | **raw traceback: re.PatternError** | **FAIL** |
| E19 | **profile `fail`=number** | `--profile {"fail":123}` | **1** | **raw traceback: TypeError** | **FAIL** |
| E20 | profile `fail`=null | `--profile {"fail":null}` | 0 | silent no-op (docs: `fail` required) | LOW deviation |
| E21 | path is a FIFO | `report pipe.log` | 2 | `no such file or directory` | PASS |

Specialist's independent run adds: unreadable file/dir, invalid regex, non-string
`fail` → all four reproduce; plus "missing `test_id` group that *matches* a line"
→ exit 2 (PASS), and "missing `test_id` group that does *not* match" → exit 0
(lazy validation, LOW deviation).

## Findings (with exact reproduction)

### F1 — BLOCKER/MAJOR: four unhandled exceptions → raw traceback + wrong exit code
`cli.main()` catches only `(FileNotFoundError, ValueError)`. `PermissionError`,
`re.PatternError`, and `TypeError` escape, printing a Python traceback and exiting
**1** (which the README defines as "failures found" — a *false* signal).
```
$ touch f.log && chmod 000 f.log && citriage report f.log
PermissionError: [Errno 13] Permission denied: 'f.log'      # exit 1, expected 2
$ mkdir d && chmod 000 d && citriage report d
PermissionError: [Errno 13] Permission denied: 'd'          # exit 1, expected 2
$ echo '{"fail":"["}' > p.json && echo 'x FAIL' > l.log && citriage report l.log --profile p.json
re.PatternError: unterminated character set at position 0   # exit 1, expected 2
$ echo '{"fail":123}' > p.json && citriage report l.log --profile p.json
TypeError: first argument must be string or compiled pattern # exit 1, expected 2
```
Root cause: `parse.py` reads files without guarding OS errors; profile regexes are
compiled lazily per line (`parse.py:104`) and never validated at load time.

### F2 — MAJOR (correctness): UUID normalization is broken
`signature.py` lists the hex rule **before** the UUID rule, and `\b[0-9a-fA-F]{7,64}\b`
matches each 12-hex-digit UUID segment, so UUIDs are only *partially* normalized:
```
$ python3 -c "from citriage.signature import normalize; print(normalize('job 123e4567-e89b-12d3-a456-426614174000 crashed'))"
job <HEX>-e89b-12d3-a456-<HEX> crashed
```
Two UUIDs that differ only in their hex runs can yield **different** signatures →
the same root cause splits into multiple clusters. Contradicts the module docstring
("UUIDs … normalized to placeholders").

### F3 — MAJOR (correctness): pytest *inline* failures drop the error message
The inline pattern `(?P<test_id>...)\s+(?P<status>PASSED|FAILED|ERROR)\b` has no
error group, so `FAILED - AssertionError: boom` yields `error_line = None`. With a
log containing only inline lines, two *different* errors for the same test collapse
into one cluster, and clusters carry no `e.g.` example (README's sample shows none):
```
$ citriage report inlineonly/            # r1 "ConnectionError: refused", r2 "AssertionError: boom"
FAILURE CLUSTERS (1):  [3592545cbf4dec88] 1 test(s), 2 run(s)
```
Normalization itself works (verified separately: "got 2" vs "got 5" collapse to one
cluster), but it is bypassed when the error text is never captured.

### F4 — MAJOR (availability/security): ReDoS via `--profile` (see Module 4)

### F5 — LOW: lazy profile validation
`{"fail": null}` silently no-ops (exit 0) though docs call `fail` required; and the
`test_id`-group check fires only when the regex actually matches a line, not
unconditionally as PROFILES.md implies.

## Module 3 verdict: **FAIL**
The happy path is solid, but four crashes (wrong exit code + traceback) plus three
correctness defects (UUID normalization, inline-error loss, ReDoS) mean the
deliverable does **not** meet the robustness bar for a tool that parses untrusted
CI logs. None of these are covered by the shipped 13-test suite.
