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
