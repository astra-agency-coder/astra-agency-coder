# citriage v0.1.0 — Independent Security Pass

**Auditor:** qa-sec-auditor (Quality dept.)
**Date:** 2026-11-13
**Target:** `citriage` v0.1.0 (CI log triage CLI)
**Source:** pristine tree copied from `/tmp/stranger` → `/tmp/sa-work`
**Environment:** isolated venv `/tmp/sa-venv`; entry point `/tmp/sa-venv/bin/citriage`
**Scope of claims verified (README):**
- "No network. No telemetry. No credentials."
- "Safe by default — CI logs often contain secrets; nothing ever leaves the box."

**Method note:** `strace` is unavailable, so runtime egress was proven with a
`sys.addaudithook` recorder (CPython audit events), which is the intended
replacement here. Source was **not modified** (verified below).

---

## Summary

| # | Check | Result |
|---|-------|--------|
| 1 | Static egress surface (socket/urllib/http/requests/ssl/ftplib/smtplib/urlopen) | **PASS** |
| 2 | Static exec surface (subprocess/os.system/eval/exec/pickle.loads) | **PASS** |
| 3 | Static file-WRITE surface (`open(...,'w')`, `write_text`, `.write()`) | **PASS** |
| 4 | Runtime egress proof (audit hook over real CLI runs) | **PASS** |
| 5 | Secret-like literals in tree / committed `.env`/key files | **PASS** |
| 6 | Env-var leak into report output (dummy `MY_SECRET`) | **PASS** |
| 7 | Unsafe defaults — does it execute anything from a log/profile? | **PASS** (no code exec) |
| 8 | Malicious `--profile` regex → **ReDoS / DoS** | **FAIL — MAJOR** |
| 9 | Malformed `--profile` (invalid regex / non-string) → clean error | **FAIL — MINOR** |
| 10 | File permissions of shipped tree (world-writable / setuid) | **PASS** |

**Bottom line:** The core egress/telemetry/credential claims **hold** — there is
genuinely no network, no telemetry, no subprocess/eval/exec, and no file writes
by the tool. Two real defects exist, both in the user-supplied `--profile` regex
path: a **ReDoS denial-of-service (MAJOR)** and an **unhandled-exception/exit-code
bug (MINOR)**. Neither exfiltrates data, but the ReDoS is a genuine "hang the
triage job" hole. Details below.

---

## 1. Static egress surface — PASS

**Command**
```bash
grep -rnE "socket|urllib|http|requests|ssl|ftplib|smtplib|urlopen|telnetlib|poplib|imaplib|xmlrpc" citriage/*.py
```
**Output**
```
(no matches)
```
**Verdict: PASS.** No network/egress primitives anywhere in the installed package.
Package imports are stdlib-only: `argparse, json, sys, re, hashlib, dataclasses,
pathlib`. No `os.environ`, `getenv`, `expanduser`, or `Path.home` reads either.

---

## 2. Static exec surface — PASS

**Command**
```bash
grep -rnE "subprocess|os\.system|eval\(|exec\(|pickle|marshal|__import__|importlib|compile\(|pty\.|os\.spawn|shutil|tempfile|os\.popen" citriage/*.py
```
**Output (all hits are `re.compile`, not code execution)**
```
citriage/parse.py:21:    (re.compile(r"^(?P<test_id>[\w./\\-]+::[\w.:\-\[\]]+)\s+(?P<status>PASSED|FAILED|ERROR)\b"),
citriage/parse.py:24:    (re.compile(r"^(?P<status>FAILED|ERROR)\s+(?P<test_id>[\w./\\-]+::[\w.:\-\[\]]+)(?:\s+-\s+(?P<error>.+))?$"),
citriage/parse.py:27:    (re.compile(r"^(?P<status>PASSED)\s+(?P<test_id>[\w./\\-]+::[\w.:\-\[\]]+)$"),
citriage/parse.py:32: _GENERIC_FAIL_ID = re.compile( ...
citriage/parse.py:36: _GENERIC_FAIL_STATUS = re.compile( ...
citriage/parse.py:39: _GENERIC_FAIL_DOTS = re.compile( ...
citriage/parse.py:42: _GENERIC_PASS_ID = re.compile( ...
citriage/parse.py:44: _GENERIC_PASS_STATUS = re.compile( ...
citriage/signature.py:13:    (re.compile(r"\b[0-9a-fA-F]{7,64}\b"), "<HEX>"),
citriage/signature.py:14:    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}\b"), "<UUID>"),
citriage/signature.py:15:    (re.compile(r"\b\d+\.\d+\.\d+\b"), "<VER>"),
citriage/signature.py:16:    (re.compile(r"\b\d+(?:\.\d+)?(?:ms|s|us|ns|MiB|GiB|KiB|MB|GB)\b"), "<DUR>"),
citriage/signature.py:17:    (re.compile(r"\b\d+\b"), "<N>"),
citriage/signature.py:18:    (re.compile(r"0x[0-9a-fA-F]+"), "<ADDR>"),
citriage/signature.py:19:    (re.compile(r"(/[\w.\-+]+)+"), "<PATH>"),
```
**Verdict: PASS.** Only `re.compile`. No `subprocess`, `os.system`, `eval`,
`exec`, `pickle`, `marshal`, `__import__`, `importlib`, `pty`, `shutil`,
`tempfile`. Note `demo/render_assets.py` and `tests/test_citriage.py` do use
`subprocess` — but these are **not part of the installed package**
(`citriage.egg-info/top_level.txt` = `citriage` only) and ship no console entry
point.

---

## 3. Static file-WRITE surface — PASS

**Command**
```bash
grep -rnE "open\([^)]*['\"][wax]|write_text|write_bytes|\.write\(|Path\.mkdir|shutil\.(copy|move|rmtree)|os\.(remove|unlink|rename|mkdir)" citriage/*.py
```
**Output**
```
(no matches)
```
**Verdict: PASS.** The tool has no write path at all — it only reads input logs.

---

## 4. Runtime egress proof — PASS

`strace` is unavailable; instead a `sys.addaudithook` recorder was installed
before importing the CLI, capturing `socket.connect`, `socket.getaddrinfo`,
`socket.bind`, `socket.create_connection`, `urllib.Request`, `ftplib.connect`,
`smtplib.connect`, `ssl.wrap_socket`, `subprocess.Popen`, `os.system`,
`os.exec*`, `os.spawn*`, `os.fork`, `pty.spawn`, `ctypes.dlopen`, and every
`open` event with its mode.

**Command**
```bash
find . -name __pycache__ -type d -exec rm -rf {} + ; PYTHONDONTWRITEBYTECODE=1 \
  /tmp/sa-venv/bin/python /tmp/sa-work/audit_full.py
```
**Output (tail; full capture had 69 events, all `open` mode `'r'`)**
```
=== OPEN / NETWORK / EXEC events across report, report --json, parse, cluster ===
('open', "path='tests/fixtures/run1.log' mode='r'")
('open', "path='tests/fixtures/run2.log' mode='r'")
('open', "path='tests/fixtures/run3.log' mode='r'")
('open', "path='tests/fixtures/run1.log' mode='r'")
('open', "path='tests/fixtures/run2.log' mode='r'")
('open', "path='tests/fixtures/run3.log' mode='r'")
('open', "path='tests/fixtures/run1.log' mode='r'")
('open', "path='tests/fixtures/run1.log' mode='r'")
('open', "path='tests/fixtures/run2.log' mode='r'")
('open', "path='tests/fixtures/run3.log' mode='r'")
total events: 69
rc report=1 report-json=1 parse=0 cluster=1
```
**Analysis**
- **Zero** network events (no `socket.*`, no `urllib`, no `ssl`, no `ftplib`/`smtplib`).
- **Zero** process-execution events (no `subprocess.Popen`, no `os.system`, no `os.exec*`/`os.fork`).
- Every `open` event is **mode `'r'`** — reads of the input logs and of CPython
  stdlib/`.pyc` files only. No write-mode open fired.
- The only writes observed in the *earlier* (pre-`PYTHONDONTWRITEBYTECODE`)
  run were attributed by traceback to CPython writing `.pyc` bytecode caches,
  **not** the tool; with bytecode writing disabled the count is 0.

**Verdict: PASS — egress is disproven at runtime, not merely by grep.**

---

## 5. Secret-like literals & committed key files — PASS

**Commands & output**
```bash
grep -rniE "api[_-]?key|secret|token|password|passwd|private[_-]?key|BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}" . --include='*' -l
```
```
./demo/DEMO.md
./README.md
./citriage.egg-info/PKG-INFO
./security-pass.md          # <- this audit file (contains the words, not secrets)
```
```bash
find . \( -iname '*.env' -o -iname '.env*' -o -iname '*.pem' -o -iname '*.key' -o -iname 'id_rsa*' \) -print
grep -rnE "AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY" .
```
```
(end filename sweep)                     # no .env / *.pem / *.key / id_rsa*
(no AWS keys / private-key blocks)
```
Content matches are prose only: `README.md` / `citriage.egg-info/PKG-INFO`
("CI logs often contain secrets; nothing ever leaves the box") and `demo/DEMO.md`.
No literal credential, token, or private key anywhere.

**Verdict: PASS.** No credentials in the tree and none required by the tool.

---

## 6. Environment-variable leak into output — PASS

**Command**
```bash
MY_SECRET='SUPERSECRETVALUE12345' /tmp/sa-venv/bin/citriage report tests/fixtures > /tmp/env-out.txt 2>&1
grep -c 'SUPERSECRETVALUE12345' /tmp/env-out.txt   # value
grep -c 'MY_SECRET' /tmp/env-out.txt               # name
```
**Output**
```
0   # secret value not present in output
0   # variable name not present in output
```
**Verdict: PASS.** The report never echoes the process environment (consistent
with the absence of any `os.environ`/`getenv` read in the source).

---

## 7. Unsafe defaults — executes anything from log or profile? — PASS

- A log line is only ever fed to `re.search` and to string normalization; there
  is no path from log content to `eval`/`exec`/`subprocess` (checks 1–3).
- A `--profile` is JSON parsed with `json.loads` and its regex strings are
  passed to `re.compile`/`re.search`. Regex is a **pattern language, not code**:
  it cannot invoke `__import__`, `os.system`, etc.

**Command (regex that *looks* like code)**
```bash
printf '{"fail": "^__import__(?P<test_id>x)$"}\n' > /tmp/pwn.json
printf 'FAILED something\n' > /tmp/t.log
/tmp/sa-venv/bin/citriage parse /tmp/t.log --profile /tmp/pwn.json
```
**Output**
```
[
  {
    "records": [],
    "run": "t.log"
  }
]
exit=0
```
**Verdict: PASS (no code execution).** The pattern is treated as an inert
literal and simply fails to match.

> **Informational (not a hole):** the report's `FAILURE CLUSTERS` section renders
> `error_example`, i.e. a substring of the input log. This is by design (it is
> the tool's whole purpose) and is printed to **local stdout only** — nothing
> leaves the box. Verified: a log line `FAILED ... token=ghp_realtoken999 leaked`
> is echoed as `e.g. AssertionError: token=ghp_realtoken999 leaked`. Operators
> who paste `citriage` output into a public issue tracker should be aware the
> output can contain the same secrets the log contained. Not a defect against the
> README claim.

---

## 8. Malicious `--profile` regex → ReDoS / DoS — **FAIL (MAJOR)**

**Root cause:** `citriage/parse.py:104` calls `re.search(pat, line)` where `pat`
comes verbatim from the user-supplied JSON profile, applied to every line of
every log. A catastrophic-backtracking pattern (e.g. `^(a+)+$`) against a long
non-matching line causes **exponential** CPU time. Python's `re` engine has no
timeout, so the process hangs.

**Minimal reproduction**
```bash
printf '{"fail": "^(a+)+$"}\n' > /tmp/redos-profile.json
python3 -c "open('/tmp/redos.log','w').write('a'*30+'b\n')"   # 30 a's + b (no match)
time timeout 5 /tmp/sa-venv/bin/citriage parse /tmp/redos.log --profile /tmp/redos-profile.json
```
**Output**
```
exit=124 (124 = timeout killed at 5s)
wall= 5.00492 s
```

**Scaling (each `+2` chars ≈ 4× time — confirms exponential, not linear)**
```
n= 18 a's :    0.062s  rc=0
n= 20 a's :    0.094s  rc=0
n= 22 a's :    0.214s  rc=0
n= 24 a's :    0.679s  rc=0
n= 26 a's :    2.640s  rc=0
n= 28 a's :   10.80s   rc=0
n= 30 a's :   41.93s   rc=0
n= 40 a's : >10.000s   KILLED by timeout (rc=124)
```
A 42-byte input line is enough to burn ~40 s; ~50 bytes exceeds practical timeouts.
An attacker who can influence the profile (or a shared profile file) can hang
the triage job — a classic algorithmic-complexity DoS.

**Why it matters even though there is no network:** the tool is meant to run in
CI over untrusted logs. If a profile is fetched/shared (docs encourage custom
profiles) or if an operator pastes a "clever" regex, a single crafted line stalls
the build. It is not remote code execution and does not exfiltrate data, so it is
**not** a BLOCKER — but it is a genuine availability hole.

**Severity: MAJOR** (denial of service; requires the ability to set/choose the
profile, which the docs explicitly invite).

**Suggested remediation (for the owning team, not applied here):**
- Bound input line length before matching, and/or cap per-line regex work.
- Reject/whitelist profile patterns, or run matching under a wall-clock budget.
- Prefer a non-backtracking engine or `re` patterns known to be linear.

---

## 9. Malformed `--profile` → unhandled exception / wrong exit code — **FAIL (MINOR)**

**Root cause:** profile regex strings are compiled lazily inside `re.search`
during parsing, so a bad pattern surfaces as an uncaught traceback instead of a
clean usage error. README contract: exit **2** = usage/setup error; exit **1** =
failures found.

**Command 9a — invalid regex**
```bash
printf '{"fail": "^(unclosed"}\n' > /tmp/bad-profile.json
/tmp/sa-venv/bin/citriage parse tests/fixtures/run1.log --profile /tmp/bad-profile.json ; echo "exit=$?"
```
**Output (abridged)**
```
Traceback (most recent call last):
  ...
  File "/tmp/sa-venv/lib/python3.13/site-packages/citriage/parse.py", line 104, in _parse_line
    m = re.search(pat, line)
re.PatternError: missing ), unterminated subpattern at position 1
exit=1
```
→ Uncaught traceback, and exit **1** (README says 1 means "failures found"), i.e.
a bad profile is misreported as a test failure.

**Command 9b — non-string regex value**
```bash
printf '{"fail": 12345}\n' > /tmp/intprof.json
/tmp/sa-venv/bin/citriage parse /tmp/t.log --profile /tmp/intprof.json ; echo "exit=$?"
```
**Output (abridged)**
```
  File ".../parse.py", line 104, in _parse_line
    m = re.search(pat, line)
TypeError: first argument must be string or compiled pattern
exit=1
```
→ Same class of bug (uncaught `TypeError`, wrong exit code).

**Contrast — a *missing* `test_id` group is handled cleanly:**
```
citriage: error: regex for 'fail' must capture group 'test_id'
exit=2
```
So the validation path exists but does not cover "pattern won't compile" or
"value isn't a string".

**Severity: MINOR** — robustness/contract issue, no data exposure, no crash of
anything but the intended process. Recommend compiling/validating profile
patterns in `load_profile` and emitting the exit-2 usage error.

---

## 10. File permissions of the shipped tree — PASS

**Commands**
```bash
find . -type f -perm -o+w -not -path "*/.git/*" -printf "%M %p\n"   # world-writable
find . -type f -perm -g+w -not -path "*/.git/*" -printf "%M %p\n"   # group-writable
find . \( -perm -u+s -o -perm -g+s \) -printf "%M %p\n"             # setuid/setgid
```
**Output**
```
=== world-writable files (mode o+w) in shipped tree ===
--- end ---
=== group-writable ===
--- end ---
=== setuid/setgid ===
--- end ---
```
**Verdict: PASS.** No world-writable, group-writable, or setuid/setgid files.

---

## Integrity: source not modified

**Command**
```bash
diff -r /tmp/stranger/citriage citriage --exclude=__pycache__   # → identical
diff -r /tmp/stranger/tests     tests   --exclude=__pycache__   # → identical
```
**Output**
```
citriage/ IDENTICAL to pristine
tests/ IDENTICAL
```
The installed package in `/tmp/sa-venv/lib/python3.13/site-packages/citriage/`
was also diffed against the source tree: **IDENTICAL**. All audit scripts and
inputs live under `/tmp` (`audit_full.py`, `edge_tests.sh`, `redos-profile.json`,
etc.); **no repository file was changed.**

---

## Findings recap

| Severity | Finding | Repro |
|----------|---------|-------|
| **MAJOR** | ReDoS: user `--profile` regex is applied to log lines with no bound; `^(a+)+$` on 30 `a`'s ≈ 42 s, exponential scaling. | §8 |
| **MINOR** | Malformed profile (uncompilable regex, or non-string value) raises an uncaught traceback and exits **1** instead of the documented usage error **2**. | §9 |
| Info | Report echoes `error_example` (a slice of the log) to local stdout by design; can reprint secrets the log contained. Not an off-box leak. | §7 |

**README claims assessment:**
- "No network. No telemetry. No credentials." → **HOLDS** (static + runtime proven).
- "Safe by default — … nothing ever leaves the box." → **HOLDS for egress**;
  caveat: the shipped tool is **not** resilient to a malicious `--profile`
  regex (DoS), and its own output can re-print log secrets to the terminal.
