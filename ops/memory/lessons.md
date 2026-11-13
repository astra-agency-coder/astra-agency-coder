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
