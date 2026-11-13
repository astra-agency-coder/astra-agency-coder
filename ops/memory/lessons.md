# Lessons Learned

Format: `### <date> — <title>` then What happened / What we learned / What we change.

### 2026-11-13 — Runtime state is ephemeral
**What happened:** The agent server runs in a container with a 1200s idle timeout;
`/workspace/project` is the durable mount but conversation state can be recycled.
**What we learned:** Anything not committed to git can vanish.
**What we change:** All durable memory, roster, reports and code live in git.

### 2026-11-13 — Child conversations need an explicit LLM config
**What happened:** Creating a child conversation with only `agent_profile_id`
failed: the referenced LLM profile `default` was not resolvable.
**What we learned:** Passing the working `llm` object (copied from a live
conversation's encrypted state) with `secrets_encrypted: true` succeeds.
**What we change:** `ops/astra.py` always sources the LLM config this way.

### 2026-11-13 — Nested delegation works
**What happened:** A child conversation with `task_tool_set` delegated to a
file-based sub-agent, which ran a real tool and returned output.
**What we learned:** Managers can create and run specialists the same way the
CEO does; the org design is technically real, not aspirational.
**What we change:** Managers are instructed to hire and delegate, not solo-work.

### 2026-11-13 — The runtime GitHub token is read-only
**What happened:** Attempting to create department repositories returned
`403 Resource not accessible by integration` on `POST /user/repos`, and
`git push` to an existing repo returned `403`. Reading (`GET /user`,
`GET /user/repos`) works and authenticates as `astra-agency-coder`.
**What we learned:** The runtime uses a GitHub **App installation** token with
read-only permissions, not a classic PAT with `repo` scope. The
`X-OAuth-Scopes` header is empty, which is the signature of an installation token.
**What we change:** Repository creation and push are classified
**NEEDS OWNER ACTION**. `ops/provision_repos.py` is ready and idempotent; it will
create all seven private department repositories in one command once the token
gains `Administration: write` + `Contents: write`. Until then, department homes
are kept locally under `company/departments/`.

### 2026-11-13 (update) — GitHub write access restored via the secret store
**What happened:** The Owner provided a write-capable fine-grained PAT. It was
registered in the OpenHands runtime secret store as `GITHUB_TOKEN_WRITE` and resolved
through `ops/secrets.py`. All seven private department repositories were then created
and populated, and the foundation was pushed to `ai-astra-agency` on a branch.
**What we learned:** The runtime read-only `GITHUB_TOKEN` and the Owner's write PAT are
different credentials; the secret store survives only within the sandbox, so durable
credential handling must also consider a 0600 file outside the repo (prior attempt used
`~/.astra/secrets.env`).
**Mistake to avoid:** A push URL of the form `https://x-access-token:<token>@host`
writes the token into `.git/config`. Always push via `ops/gitpush.sh`, which passes an
ephemeral credential helper instead.

### 2026-11-13 — Custom-hired specialists are NOT resolvable by the `task` tool
**What happened:** In training runs, a manager hired a specialist
(`python3 ops/astra.py hire astra-mktg-copywriter --dept Marketing …`), which correctly
wrote `.agents/agents/astra-<name>.md`, but delegating via the **`task` tool** with
`subagent_type=astra-mktg-copywriter` returned:
`Unknown agent 'astra-mktg-copywriter'. Available types: astra-cbdo, astra-ccr, … .
Use register_agent() to add custom agent types.`
The Creative training run (astra-ccr) hit the identical error.
**What we learned:** The `task` tool resolves only **pre-registered** agent types
(the 9 managers + a few test agents). File-based agent definitions on disk are not
auto-registered with the runtime, so hired specialists cannot be delegated to yet.
**What we change:** Until a registration path exists, managers should (a) record the
blocker plainly, (b) do the work directly, and (c) retire the specialist with a reason.
Proposed fix: wire `ops/astra.py hire` to call the runtime's `register_agent()` so the
hire→delegate flow actually works. Every manager should report this if they hit it.

### 2026-11-13 (update) — The `task` tool is blocked two ways; `spawn` is the working path
**What happened:** The Research training run (astra-cro) confirmed the above and found a
**second, independent** failure: delegating via the `task` tool to the one
*pre-registered* Research specialist, `astra-mkt-researcher`, also fails — the runtime
errors with `Tool 'web_search' not registered but was given to agent astra-mkt-researcher`,
even though the agent's file lists only `terminal,file_editor,grep,glob`.
**What we learned:** Two separate blockers stop `task`-tool delegation: (1) custom-hired
agents are unresolved ("Unknown agent … Use register_agent()"), and (2) at least one
pre-registered agent is given an **unregistered tool** (`web_search`), which aborts the run.
Separately, the **child-conversation path** (`python3 ops/astra.py spawn <agent> "<brief>"`)
reads the agent's `.md` definition directly and **works** — it ran both independent
verification tasks successfully (7/7 demand claims, 7/7 pricing pages).
**What we change:** When `task`-tool delegation fails, use `ops/astra.py spawn <agent>
"<brief>"` — real delegation still happens, just through the other supported path. Report
which path was used. Proposed fixes for Engineering: (a) call `register_agent()` on hire,
and (b) stop attaching `web_search` to agents whose definitions do not declare it.

## L-0007 — Spawned runs can report status=error yet still have done the work
**Date:** 2026-11-13 · **Context:** intensive training runs via `ops/train.py`.
Several runs returned `execution_status=error` with an empty final response, but
the department had **already pushed real commits** to its scoped repo (verified via
the GitHub tree). The empty result is the runtime dropping the final message
(session/context limit), not the work failing.
**Action:** always verify a run by its **artifacts** (repo commits / files), not by
the status string alone. Retry once with a higher `--max-iter` when no commits
appear; the second attempt succeeded for design and research.
**Takeaway:** judge training by evidence, never by the status label.

## L-0008 — Custom-hired sub-agents are not resolvable by the `task` tool
**Date:** 2026-11-13 · **Context:** managers tried to delegate to specialists they
created with `astra.py hire`; the `task` tool returned `Unknown agent`.
Only the preset manager types are registered with the runtime. So a manager can
currently delegate only to the other department managers, not to its own fresh
specialists. Managers worked around it by doing the work themselves.
**Open item for CEO:** register file-based specialist agents with the runtime (or
expose a working spawn path) so departments can truly delegate. Tracked as a RISK.

## L-0009 — `astra.py spawn` IS a working delegation path for fresh specialists
**Date:** 2026-11-13 · **Context:** Quality round-2 training run.
L-0008 noted the `task` tool cannot resolve `astra.py hire`-created specialists
(only preset manager types are registered). **Verified workaround:** `python3
ops/astra.py spawn <agent> "<brief>"` DOES run a hired specialist in its own child
conversation and returns its result. Round 2 used it to run `qa-edge-breaker`
(status `finished`, elapsed 157.6 s) which produced a real 22-row findings file.
**Action:** managers should delegate to their own specialists via `astra.py spawn`
(background it and poll the log for long tasks). The `task` tool remains usable
only for the preset agent types.

## L-0010 — Re-verification must attack what round 1 did NOT
**Date:** 2026-11-13 · **Context:** Quality round-2 verification of `citriage` v0.1.0.
Round 1 returned CONDITIONAL PASS and found only 3 profile-error crashes. Round 2,
attacking different surfaces, found a **signature-normalization bug** (UUIDs not
collapsed — a broad hex rule pre-empted the specific UUID rule), a **ReDoS** via
`--profile`, an **inline-error-drop** that silently merged different root causes,
and a `chmod 000` **PermissionError** crash family. None were covered by the
subject's 13 passing tests.
**Takeaway:** a verifier that only replays the producer's own examples passes a
defective tool. Always add (a) correctness probes with unusual-but-valid input,
(b) worst-case performance, (c) the OS/permission error surface. See the Quality
department playbook `knowledge/verification/PLAYBOOK.md` and the new
`signature_probe.py` harness.

## L-0009 — Delegation works via `astra.py spawn`, not the `task` tool
**Date:** 2026-11-13 · **Context:** Quality training round 2. The `task` tool
returns `Unknown agent` for freshly-hired specialists, but `python3 ops/astra.py
spawn <specialist> "<brief>"` **does** run them. The Quality manager used this to
run `qa-edge-breaker`, `qa-sec-auditor`, `qa-repro-auditor` successfully.
**Resolution:** supersedes the blanket statement in L-0008. Departments *can*
delegate to their own specialists — via `spawn`, not `task`.

## L-0010 — One verification round is not enough
**Date:** 2026-11-13 · **Context:** Quality's round 1 gave the Product tool a
conditional PASS and missed 4 real defects (permission-crash, UUID normalisation
bug, dropped error text, ReDoS). Round 2 — attacking correctness under
unusual-but-valid input, worst-case performance and the OS error surface — found
all of them.
**Rule adopted:** a single "reproduce + check" pass is insufficient. Add a second
adversarial round before a commercial PASS.

## L-0011 — Static deliverables: verify with code, ship zero-dependency
**Date:** 2026-11-13 · **Context:** Engineering delivered the company intro
website (`deliveries/astra-launch/website/`). **Findings:** (a) a static site
with no build step, no CDN and no external fonts renders offline and cannot
break from a third-party outage — the fastest reliable client artefact;
(b) committing the verification as a script (`verify_site.py`: html5lib strict
parse + asset-existence + duplicate-id/anchor/heading checks + CSS fixed-width
audit) makes the PASS reproducible instead of a one-off claim; (c) the test
tool (`html5lib`) was not preinstalled and there is **no headless browser**, so
pixel-level responsive rendering cannot be tested here — state that as a
limitation, never imply it was tested. **Rule adopted:** every deliverable
ships with a re-runnable verify script, and untested dimensions are listed
explicitly in `VERIFY.md`.

## L-0012 — Serving a repo directory leaks internals; one port, one owner
**Date:** 2026-11-13 · **Context:** Engineering hardened the company site
(`deliveries/astra-site/`). **Findings:** (a) the stdlib `server.py` served the
package directory itself, so `/server.py` and `/verify_site.py` returned HTTP
**200 on the public URL** — a real leak; fixed by overriding `send_head()` to
allowlist public asset suffixes and 404 dotfiles/source/dev files. Never point
`SimpleHTTPRequestHandler` at a repo. (b) Two heal checks (`intro_site` and the
new company site) both claimed `:12000`; leaving both lets the older launcher
win the port and regress the public site — `ops/heal.py` now has a single
`astra_site` check. (c) `pgrep -f 'server\.py'` matches any process whose args
merely mention the string (e.g. an agent prompt); anchor the pattern
(`^python3 server\.py$`). (d) `nohup python3 server.py` inherits the parent
shell env — if `ASTRA_SITE_PORT` is unset it binds the wrong port; set it inline
on the child. **Rule adopted:** a web-reachable path must be allowlisted, never
"everything minus a denylist", and a port has exactly one owning launcher.

## 2026-11-13 — RLS cannot restrict columns; a trigger can
A `profiles_self_update` policy let users set their own `role = 'admin'`.
Postgres RLS decides *rows*, not *columns*, so the fix is a `BEFORE UPDATE`
trigger that rejects changes to `role`/`disabled`/`id` for non-staff, plus a
`WITH CHECK` that pins `role` to its current value. Always test privilege
escalation explicitly: it is the finding that turns a leak into a breach.

## 2026-11-13 — Fuzz the engine, not just the happy path
16 crashes came from empty lists, NaN, ±Inf and non-dict payloads. One bad bar
from the feed took down the whole analysis path. Normalise at the boundary
(`_clean`, `_parse`) and make every public function tolerate empty input.

## 2026-11-13 — Keep the site on 12000, the product on 12001
`ops/heal.py` and `astra-site/healthcheck.sh` both assume `ASTRA_SITE_PORT=12000`.
Moving the company site silently breaks self-healing. Product services get 12001.

### 2026-11-13 — A page must not claim what a suite cannot prove
**What happened:** The site showed "API contract 23/23". Re-running the suite
gave 9/22: Supabase credentials were cleared when the runtime recycled, so the
key store was unavailable. The old figure was remembered, not measured.
**What we learned:** Any number that reaches the Owner or the public must be
produced by a run, not by memory. A remembered score is a false claim.
**What we change:** `tools/gen_facts.py` executes the suites and writes
`src/data/facts.json`; the site reads only that file, and a suite that cannot
run renders as "needs credentials" with the last measured score.

### 2026-11-13 — `curl` without `-f` treats a 404 as success
**What happened:** `serve.sh` reported "already up on :12000" while the old
static site was serving a 404 on `/en`. The health check passed on a broken
deployment.
**What we learned:** `curl -s -o /dev/null` exits 0 on HTTP errors. A readiness
probe must assert a 2xx, not merely a connection.
**What we change:** Launchers and probes use `curl -fsS` so only a 2xx counts.

### 2026-11-13 — A backtest below 30 trades proves nothing
**What happened:** The new backtester returned 2 closed trades on the free
feed, which the raw numbers would render as "100% win rate".
**What we learned:** The data source caps history at 101 bars per timeframe, so
edge cannot be established from it. Publishing the ratio would be dishonest.
**What we change:** `sample_adequate` is false below 30 closed trades and the
result carries a note explaining why; a real sample needs a longer-history feed.

### 2026-11-13 — A visual addition can silently desync a chart's axes
**What happened:** A volume strip was added beneath the candles and the chart
kept looking correct, but the price gridlines were still spaced over the full
box while the candles were remapped over a shorter `innerH`. Three of the five
price labels no longer pointed at the price they claimed. The Creative manager
found it by measuring geometry, not by looking at a screenshot.
**What we learned:** Any change to a chart's inner drawing area must be applied
to every scale that uses it. A plausible-looking render is not evidence.
**What we change:** Gridlines and candles share one `innerH`. When a plot area
changes, re-derive every mapping from it and re-measure.

### 2026-11-13 — A CSS comment claiming a property is not a test
**What happened:** `globals.css` said "reveal on scroll (visible without JS)",
but every `.reveal` started at `opacity: 0`, so with JavaScript disabled the
whole page was blank (23 of 23 blocks hidden).
**What we learned:** Comments describe intent; only a run with JS off shows
whether content is actually reachable.
**What we change:** Content is visible by default; `RevealObserver` adds `.js`
to `<html>` and only then does `.reveal` start hidden. Verified with JS off.

### 2026-11-13 — Fallback fonts quietly replace the brand face
**What happened:** IBM Plex Sans Arabic was loaded and applied to `body`, but
`.display` and `.eyebrow` named only the Latin faces. On `/ar` the headline
rendered in DejaVu Sans — a font from nowhere in the design system — while
`/en` and `/tr` rendered Fraunces. It looked like a different product.
**What we learned:** A loaded font is not an applied font. Every display class
needs an explicit stack for each script.
**What we change:** `[dir="rtl"] .display` and `[dir="rtl"] .eyebrow` name
`var(--font-ar)` first, and drop the Latin negative tracking.
