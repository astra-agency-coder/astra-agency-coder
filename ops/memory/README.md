# Company Memory

Durable, file-based memory for AI ASTRA AGENCY. Every file here is plain text,
versioned in git, and readable by every agent. No secrets ever live here.

| File | Purpose | Who writes |
|---|---|---|
| `decisions.md` | Append-only log of material decisions | CEO |
| `lessons.md` | Lessons learned from wins and failures | any agent (via manager) |
| `playbooks.md` | Reusable, tested procedures | CEO / managers |
| `tasks.jsonl` | Machine log of every delegated task | `ops/astra.py` |
| `revenue.md` | Verified revenue, pending payments, expenses | Operations |
| `risks.md` | Live risk register | Operations + CEO |
| `versions/` | Snapshots of instructions before changes | whoever edits |

## Memory rules
1. **Retrieval first.** Before starting work, read the relevant memory files.
2. **Write it down.** A lesson not recorded will be repeated.
3. **Promote repetition.** The third time a solution is reused, it becomes a playbook.
4. **Version before change.** Snapshot any instruction/agent file before editing it.
5. **Never store secrets.** Passwords, tokens, keys, seed phrases — never.
6. **Separate fact from projection.** Realised revenue is never mixed with estimates.

## Learning loop (no model-weight training is claimed)
```
observe → record → review → generalise → test → adopt → version
```
Learning here means improved instructions, playbooks, skills and memory — not
training model weights. We never claim model training that did not happen.
