# AI ASTRA AGENCY — Intensive Training Program

Purpose: raise every department to a working professional standard **before** any
commercial activity. Training is not a document; it is a **run**: an agent is
spawned with a curriculum, executes the modules with real tools, produces a
verified deliverable, and the output is stored in the department repo + memory.

## How a training run works
1. CEO picks a curriculum for a manager.
2. `python3 ops/train.py <agent> <curriculum>` spawns that manager in its own
   child conversation with the curriculum attached.
3. The manager decomposes it, may hire specialists, and executes the modules.
4. The manager writes durable artifacts to its department repo (`knowledge/`)
   and returns an evidence-backed summary.
5. CEO + Quality review; failures are recorded, not hidden.

## Curricula
| File | Department | Focus |
|---|---|---|
| `curricula/engineering.md` | Engineering | read real codebases, build to spec, review, test |
| `curricula/software-delivery.md` | Engineering/Product | end-to-end delivery of a shippable product |
| `curricula/video-production.md` | Creative | analyze real videos, script, voice, edit, render |
| `curricula/design.md` | Creative | visual systems, layout, thumbnails, brand assets |
| `curricula/marketing.md` | Marketing | positioning, content, distribution, measurement |
| `curricula/business-development.md` | Business Development | find real work, qualify, propose |
| `curricula/product.md` | Product | shape sellable products, scope, package, price |
| `curricula/research.md` | Research | market/technical intelligence with citations |
| `curricula/quality.md` | Quality | independent verification, acceptance testing |

## Rules (all curricula)
- Never fabricate a result, a source, a customer or a capability.
- Every module ends with an **artifact** and a **check**. No artifact = not done.
- Use real tools (ffmpeg, Python, git, browser). "I learned X" without an output is not training.
- Respect platform terms; never bypass CAPTCHA/2FA; never spam.
- Record what failed and why in the run report.
