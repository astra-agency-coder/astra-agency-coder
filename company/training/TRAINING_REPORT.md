# AI ASTRA AGENCY — INTENSIVE TRAINING REPORT

**Run by:** CEO (`astra-ceo`) · **Date:** 2026-11-13 · **Nature:** internal training only
No customer contact, no outreach, no sales, no external commitments.

## What was asked
Owner ordered intensive training for the engineering, software, video-design,
marketing and research teams: video teams to study real videos online and learn
scripting/voice/editing; engineering to read real projects and learn how software
is built precisely; marketing to find real places where work can be obtained plus
deep research on **buildable, sellable software projects**.

## CEO decision taken as part of this task
Video + design had **no department**. The CEO created a new **Creative** department
(manager `astra-ccr`, Chief Creative Officer) with its own private repo
`dept-creative` and its own scoped deploy key — same least-privilege model as the
rest. Roster is now **9 agents** (CEO + 8 managers).

## How training was executed
`ops/train.py` spawns the manager in its own conversation with a curriculum
attached. A module counts **only** when it produced a **real artifact** and its
**check passed**. All artifacts were pushed to each department's scoped repo.

## Results by department (evidence = files in the department repo)

| Dept | Manager | Curriculum | Artifacts produced | Result |
|---|---|---|---|---|
| Creative | astra-ccr | video-production | 5 cited ad deconstructions, script template, **real MP4** (H.264 1920×1080, 44s), audio mastered ≈ −14.4 LUFS, SRT/VTT subs, thumbnails (16:9 + 9:16), full publish pack, reusable render pipeline | **PASS** |
| Creative | astra-ccr | design | design tokens, 3 layouts, 2 thumbnails, SVG brand kit, token sheet PNG, independent design audit | **PASS** |
| Engineering | astra-cto | engineering | code-reading notes (click, django, tabulate), a reproduced build with real output, and a **real tested CLI tool** (`ndfilter` + pytest), a review with findings, packaged delivery | **PASS** |
| Product | astra-cpo | software-delivery | a real product (`citriage`), README/QUICKSTART/CHANGELOG/LICENSE, pricing sheet, sale-readiness checklist, **2-min demo video** | **PASS** |
| Marketing | astra-cmo | marketing | positioning, message house, 3 real content assets (checked 9/9), distribution plan, honest metrics (N/A over invention), **15+ work channels with measured HTTP + terms notes** | **PASS** |
| Business Dev | astra-cbdo | business-development | sourcing map with **live URL + HTTP + terms excerpts**, qualification rubric, price floor, pipeline, **ranked sellable-product candidates** | **PASS** |
| Research | astra-cro | research | method standard, AI-video market study, technical feasibility, competitive scan, decision brief, **raw evidence archive** (GitHub API JSON, pricing HTML, telemetry) | **PASS** |
| Quality | astra-cqo | quality | frozen acceptance criteria (17), reproduction of 6 claims, edge-case + security passes, verdict + reusable harness (`signature_probe.py`) | **PASS** (found 4 real defects in the Product tool) |

## The two adult answers the Owner asked for

### Where real, payable work can be found (Business Development)
A **live-verified** sourcing map. Best fit first:
1. **Superteam Earn** (https://earn.superteam.fun) — public API; listings carry an
   explicit `agentAccess` field (`AGENT_ALLOWED`/`HUMAN_ONLY`) and **pay in USDC**
   on-chain. Best-fit channel: crypto payout + agent-explicit rules.
2. **Gitcoin** — on-chain grants/funding (entity-friendly; builder participation only).
3. **Dework / DAO boards** — token/stablecoin payouts, per-DAO rules.
4. **Audit contests** (Sherlock/Cantina) — USDC, but human-warden gate today.
- **BLOCKED (not bypassed):** Upwork, Fiverr, Layer3 (bot walls/403) — recorded
  with the blocking clause, never circumvented. Product-marketplaces for
  sell-once revenue: Gumroad, Lemon Squeezy, Envato/CodeCanyon, Figma/Notion.

### Sellable software products we could build and offer (ranked)
1. **Crypto-checkout SaaS starter kit** ($249–$399) — our tested receive-only
   wallet module is a real differentiator vs fiat-first competitors.
2. **Automation workflow packs** ($29–$99) — we run real multi-agent flows; ship
   the flow plus a video walkthrough.
3. **"Brief → polished ad" short-video pack** ($149–$399) — pipeline already proven.
4. USDT invoice/payment-link micro-SaaS ($9/mo or $79) — reuses the wallet module.
5. Niche Notion/Figma bundles ($19–$49) · 6. Web3 audit-contest kit ($29–$79).

## Honest failures and blockers (not hidden)
1. **Delegation limit (real):** custom specialists created with `astra.py hire` are
   **not resolvable** by the `task` tool — only preset managers load. Managers did
   the work themselves. **Owner/CEO item:** register file-based specialists with the
   runtime, or add a working spawn path.
2. **Run status can be misleading:** several runs returned `status=error` with an
   empty final message yet had **pushed real commits**. Training quality was judged
   by **artifacts**, not the status string. Design + Research needed one retry.
3. **Voiceover is a placeholder:** the video pipeline uses robotic `espeak-ng`.
   A human/neural voice must be added **before any commercial sale**. Flagged, not
   hidden.
4. **YouTube media download = HTTP 403:** video study used metadata + auto-captions
   (shot lists marked "inferred"). The protection was **not** bypassed.
5. **Quality round 1 missed defects round 2 caught** (L-0010): the Product tool `citriage` failed 4/17 acceptance criteria on adversarial input, so it is **NOT sale-ready** until fixed. The QA system worked as designed — it caught this before a customer did.

## Verdict
- **PASS:** video-production, design, engineering, software-delivery, marketing,
  business-development, research (7 curricula, all with real artifacts).
- **FAIL:** none that produced no artifact after retry.
- **NOT CONFIGURED:** none.
- **NEEDS OWNER ACTION:** voiceover vendor (later, before selling video); nothing
  blocking training.

## Next step
Training of all requested departments is complete and evidence-backed. The company
remains **inside the foundation boundary**: no client contact, no offer, no sale.
Awaiting the Owner's next instruction.
