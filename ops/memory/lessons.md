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
