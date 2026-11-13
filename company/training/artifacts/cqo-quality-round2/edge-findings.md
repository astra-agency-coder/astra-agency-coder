# citriage v0.1.0 — Independent Edge-Case / Robustness Findings

- **Tester:** qa-edge-breaker (independent; prior reports not trusted)
- **Date:** 2026-11-13
- **Artifact under test:** `citriage` 0.1.0, pristine source copied from `/tmp/stranger` → `/tmp/eb-work`
- **Install:** `python3 -m venv /tmp/eb-venv && /tmp/eb-venv/bin/pip install .` (from tree root)
- **Binary:** `/tmp/eb-venv/bin/citriage` (Python 3.13.3, uid 10001)
- **Contract:** exit 0 = no failures · 1 = failures found · 2 = usage/setup error. Dir input reads only `*.log`/`*.txt`. Custom JSON profile needs a `fail` regex capturing group `test_id`; docs claim exit 2 if missing.
- **Source not modified.** All fixtures live under `/tmp/eb-work/edge/`.

## Result summary

- **PASS: 13** · **FAIL: 4**
- **Worst severity: HIGH** — 4 distinct unhandled-exception crashes (raw Python traceback + wrong exit code 1 instead of the contractual 2).

## Findings table

| # | case | exact command | observed exit | observed behaviour (real output) | expected per docs | verdict | severity |
|---|------|---------------|---------------|----------------------------------|-------------------|---------|----------|
| 1 | empty file | `citriage report edge/empty.log` | 0 | Clean report: `runs analysed : 1 (empty.log)` / `tests seen : 0` / `total failures: 0`, no stderr | no failures → exit 0 | PASS | — |
| 2 | whitespace-only file | `citriage report edge/ws.log` | 0 | Clean report, `tests seen : 0`, no stderr | no failures → exit 0 | PASS | — |
| 3 | empty directory | `citriage report edge/empty_dir` | 2 | `citriage: error: no .log/.txt files in edge/empty_dir` (stderr) | QUICKSTART troubleshooting: `no .log/.txt files in ...`; exit 2 | PASS | — |
| 4 | missing path | `citriage report edge/nope.log` | 2 | `citriage: error: no such file or directory: edge/nope.log` | exit 2 (setup error) | PASS | — |
| 5 | binary / random-byte file | `citriage report edge/bin.log` (2048 random bytes) | 0 | Clean report, `tests seen : 0`, no crash. (UTF-8 decode is fault-tolerant: `read_text(errors="replace")`) | should not crash | PASS | — |
| 6 | 5 MB single line | `citriage report edge/big.log` (one 5,000,000-char line) | 0 | Clean report, `tests seen : 0`, elapsed ≈ 1 s, no OOM/hang | should not hang/crash | PASS | — |
| 7 | unicode / emoji test id | `citriage report edge/uni.log` (`tests/t.py::test_emoji_😀 FAILED - boom`) | 0 | Report produced, no crash. **Note:** `tests seen : 0` — the emoji line is silently *not parsed* (pytest `test_id` char class `[\w.:\-\[\]]` excludes non-ASCII). Behaviourally safe; lossy, not a robustness bug | should not crash | PASS | — |
| 8 | CRLF line endings | `citriage report edge/crlf.log` | 1 | `tests seen : 2` / `total failures: 1` / `ALWAYS FAILING (1): - tests/t.py::test_b` — `\r` stripped, parsed correctly | correct parse | PASS | — |
| 9 | unreadable file (`chmod 000`) | `citriage report edge/unreadable.log` | **1** (traceback) | **UNHANDLED `PermissionError`** — raw traceback tail: `File ".../citriage/parse.py", line 168, in parse_source` → `p.read_text(...)` → `PermissionError: [Errno 13] Permission denied: 'edge/unreadable.log'` | setup error → **exit 2** with friendly message | **FAIL** | **HIGH** |
| 10 | unreadable dir (`chmod 000`) | `citriage report edge/unreadable_dir` | **1** (traceback) | **UNHANDLED `PermissionError`** — traceback tail: `File ".../citriage/parse.py", line 161, in parse_source` → `files = sorted(f for f in p.iterdir()...)` → `PermissionError: [Errno 13] Permission denied: 'edge/unreadable_dir'` | setup error → **exit 2** with friendly message | **FAIL** | **HIGH** |
| 11 | invalid-regex profile | `citriage report edge/ok.log --profile edge/p_invalid_regex.json` (`{"fail": "["}`) | **1** (traceback) | **UNHANDLED `re.PatternError`** — tail: `File ".../citriage/parse.py", line 104, in _parse_line` → `re.search(pat, line)` → `re.PatternError: unterminated character set at position 0`. Regex is compiled lazily per-line, so the malformed profile only explodes on first matching attempt | malformed profile/regex → exit 2 (QUICKSTART troubleshooting) | **FAIL** | **HIGH** |
| 12 | profile `fail` = non-string (`123`) | `citriage report edge/custom_match.log --profile edge/p_fail_int.json` (`{"fail": 123}`) | **1** (traceback) | **UNHANDLED `TypeError`** — tail: `File ".../citriage/parse.py", line 104, in _parse_line` → `re.search(pat, line)` → `TypeError: first argument must be string or compiled pattern` | malformed profile → exit 2 | **FAIL** | **HIGH** |
| 13 | profile `fail` = `null` | `citriage report edge/custom_match.log --profile edge/p_fail_null.json` (`{"fail": null}`) | 0 | Clean report, `tests seen : 0` (null regex skipped). Does **not** error, despite docs claiming `fail` is required and `test_id` is required. Silent no-op | docs: `fail` required → arguably should error exit 2 | PASS* (lenient) | LOW |
| 14 | profile missing `test_id` group **that DOES match a line** | `citriage report edge/custom_match.log --profile edge/p_nogroup_match.json` (`{"fail": "^[^ ]+ FAIL"}`) | 2 | `citriage: error: regex for 'fail' must capture group 'test_id'` | docs: errors exit 2 if `test_id` missing | PASS | — |
| 15 | profile missing `test_id` group, line does **NOT** match | `citriage report edge/ok.log --profile edge/p_nogroup_match.json` | 0 | Clean report, no error. Validation is lazy — only fires if the regex matches a line | docs: "errors (exit 2) if it is missing" (unconditional claim) | PASS* (deviation, benign) | LOW |
| 16 | empty stdin | `citriage report - < /dev/null` | 0 | Clean report: `runs analysed : 1 (<stdin>)` / `tests seen : 0`, no stderr | no failures → exit 0 | PASS | — |
| 17 | no args at all | `citriage` | 2 | `usage: citriage [-h] [--version] {report,parse,cluster} ...` / `citriage: error: the following arguments are required: command` | usage error → exit 2 | PASS | — |
| 18 | unknown subcommand | `citriage frobnicate edge/ok.log` | 2 | `usage: ...` / `citriage: error: argument command: invalid choice: 'frobnicate' (choose from 'report', 'parse', 'cluster')` | usage error → exit 2 | PASS | — |
| 19 | `report` with no source | `citriage report` | 2 | `usage: citriage report [-h] [--profile PROFILE] [--json] source` / `citriage: error: the following arguments are required: source` | usage error → exit 2 | PASS | — |
| 20 | directory named `*.log` | `citriage report edge/logdir.log` | 0 | Treated as directory (not a log file); `runs analysed : 1 (inner.log)`, `tests seen : 1`, exit 0. Correct: `is_dir()` checked before suffix matching | dir of logs → read `*.log`/`*.txt` inside | PASS | — |
| 21 | POSITIVE CONTROL — bundled fixtures | `citriage report tests/fixtures` | 1 | `runs analysed : 3 (run1.log, run2.log, run3.log)` / `FLAKY (2)` / `ALWAYS FAILING (1)` / 3 clusters — matches README sample | exit 1, 2 flaky, 1 always-failing | PASS | — |
| 22 | POSITIVE CONTROL — valid custom profile | `citriage report edge/custom_match.log --profile edge/p_ok.json` (`{"fail": "^(?P<test_id>[^ ]+) FAIL"}`) | 1 | `tests seen : 1` / `ALWAYS FAILING (1): - tests/t.py::a` | valid profile works | PASS | — |

`PASS*` = functionally safe / no crash, but the behaviour deviates from a literal reading of the docs (flagged LOW, not counted as a hard FAIL).

## Crash reproductions (minimal, all → wrong exit 1 + raw traceback)

1. **Unreadable file** — `touch f.log; chmod 000 f.log; citriage report f.log`
   → `PermissionError: [Errno 13] Permission denied: 'f.log'` (exit 1, expected 2)
2. **Unreadable dir** — `mkdir d; chmod 000 d; citriage report d`
   → `PermissionError: [Errno 13] Permission denied: 'd'` (exit 1, expected 2)
3. **Invalid regex in profile** — `echo '{"fail":"["}' > p.json; echo 'x FAIL' > l.log; citriage report l.log --profile p.json`
   → `re.PatternError: unterminated character set at position 0` (exit 1, expected 2)
4. **Non-string `fail`** — `echo '{"fail":123}' > p.json; echo 'x FAIL' > l.log; citriage report l.log --profile p.json`
   → `TypeError: first argument must be string or compiled pattern` (exit 1, expected 2)

## Root-cause note (for the fix owner, not fixed here)

`cli.main()` only catches `(FileNotFoundError, ValueError)` (cli.py:68). All four crashes raise
exception types outside that tuple: `PermissionError`, `re.PatternError`, `TypeError`.
Additionally, profile regexes are never compiled/validated at load time (`load_profile`), so a
malformed or non-string pattern surfaces only mid-parse, per line.
