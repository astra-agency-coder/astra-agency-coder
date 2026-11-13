# Training run — astra-cro — research

- manager: `astra-cro` (Chief Research Officer)
- department: Research
- date: 2026-11-13
- nature: **training only** (no customer contact / outreach / sales)
- curriculum: `company/training/curricula/research.md`
- status: **finished** (with one recorded blocker — see §5)

## Result — module table

| Module | Artifact | Check | Result |
|---|---|---|---|
| **1. Method** | `dept-research:knowledge/method/sourcing-standard.md` (v1.1) | source hierarchy T1>T2>T3; fact/inference labelling; 7-step verification; corrections log | **PASS** |
| **2. Market study** | `dept-research:knowledge/market/ai-video-generation-market.md` (v1.1) | size signals from 2 independent houses (reported as a range), primary demand telemetry, key players — each cited by URL + sha256 | **PASS** |
| **3. Technical study** | `dept-research:knowledge/technical/ai-video-pipeline-feasibility.md` (v1.1) | **re-measured** diffusion on CPU + **ran a real ffmpeg 1080p→9:16 captioned render**; raw output in `work/astra-cro/evidence/2026-11-13/benchmark/` | **PASS** |
| **4. Competitive scan** | `dept-research:knowledge/competitive/ai-video-tools-scan.md` (v1.1) | 6 vendors' live pricing pages (HTTP 200) + VEED inaccessible status; billing-unit analysis | **PASS** |
| **5. Decision brief** | `dept-research:knowledge/briefs/brief-ai-video-entry.md` (v1.1) | one page; recommendation + confidence/unknowns + cheap next step | **PASS** |
| **Verification record** | `dept-research:knowledge/verification/2026-11-13-reverification.md` | every claim re-fetched; 4 corrections logged | **PASS** |

All artifacts committed and **pushed** to `astra-agency-coder/dept-research` (commit `a6daacf`,
verified via `git ls-tree origin/main`). Evidence: `work/astra-cro/evidence/2026-11-13/` (raw
snapshots + sha256 index).

## 1. What this run actually did (and why it is more than the prior attempt)

A **prior run of this same curriculum failed** (`status: error`, 341 s) but left untracked,
unverified drafts in the dept repo working tree. Rather than trust them, this run treated them
as *unverified claims* and **re-fetched every primary source live**, then had a **second agent
re-fetch the key figures independently**. That process found **4 real errors** in the drafts:

| # | Draft claim | Corrected | How caught |
|---|---|---|---|
| 1 | GVR CAGR **20.6%** | **20.3%** | "20.6" existed only in SVG path coordinates, not report text |
| 2 | repo **`ComfyUI/ComfyUI`** | **`Comfy-Org/ComfyUI`** | the original path returns HTTP 404 |
| 3 | Dataintelo "**Europe ≈28%**" | Europe share **not stated**; "28%" = *Media & Entertainment*; APAC ≈20% (CAGR 25.1%); NA ≈42% | re-read the page text |
| 4 | "**12.2 s/image**" | **2.3 s @ 8 steps, 11.3 s @ 50 steps** | step count was unstated and dominates runtime |

This is the module that matters most: the department's **Method** standard was proven by
applying it to the department's own output and catching its mistakes.

## 2. Commands & real output (evidence, not narrative)

**GitHub repo stats (primary T1):**
```
HTTP:404 ComfyUI/ComfyUI          <-- wrong owner, caught here
HTTP:200 hpcaitech/Open-Sora      29929* 3094 forks Apache-2.0
HTTP:200 Wan-Video/Wan2.1         17427* 4055 forks Apache-2.0
HTTP:200 Tencent-Hunyuan/HunyuanVideo 12767* 1385 forks NOASSERTION
HTTP:200 guoyww/AnimateDiff       12295* 1105 forks Apache-2.0
HTTP:200 Lightricks/LTX-Video     11376* 1234 forks Apache-2.0
HTTP:200 Comfy-Org/ComfyUI        146618* 17480 forks GPL-3.0   <-- canonical path
```

**Demand telemetry (primary T1):**
```
pypistats diffusers/recent -> {"last_day":249549,"last_month":6256527,"last_week":1402679}
HN nbHits: "AI video generator"=2023  "sora video"=710  "video generation model"=392  "text-to-video"=173
```

**Market size (secondary T2), extracted from stripped text:**
```
GVR: "AI video generator market size was $788.5 million in 2025 ... $3,441.6 million by 2033, CAGR of 20.3%"
Dataintelo: "USD 1.85 billion in 2024 ... USD 11.7 billion [by 2033] ... CAGR of 22.4%"
Dataintelo regions: NA ~42% (~USD 0.78B); APAC ~20% (~USD 0.37B, CAGR 25.1%); Media&Ent >28%
```

**Diffusion CPU benchmark (re-measured, tiny checkpoint, 4 threads):**
```
steps=8  avg_s=2.34
steps=20 avg_s=6.22
steps=50 avg_s=11.32
```

**ffmpeg assembly (re-run, real render):**
```
base_16x9.mp4      -> h264 1920x1080 30fps 5.00s
captioned_9x16.mp4 -> h264 1080x1920 30fps 5.00s   (crop+scale, subtitles, loudnorm)
loudness: Input Integrated -14.0 LUFS ; Input True Peak -9.6 dBTP
```

**Vendor pricing (all HTTP 200, browser UA):** Synthesia 1,024,888 B · HeyGen 900,098 B ·
Runway 1,274,080 B · invideo 292,902 B · Pictory 409,284 B · Descript 354,595 B · VEED 137,280 B
(VEED: 0 `$` chars in served HTML → JS-rendered, prices `[UNKNOWN]`).

## 3. Delegation (real, via the child-conversation path)

Hired 3 specialists: `res-demand-analyst`, `res-competitive-analyst`, `astra-mkt-researcher`.
Delegated the two independent verification passes via
`python3 ops/astra.py spawn astra-mkt-researcher "<brief>"` (child conversation), which
**worked**:

- **Demand verification** → `company/training/artifacts/res-demand-verification.md` — **7/7 PASS**
  (noted a real pypistats **429** on first contact, succeeded on retry within the 3-attempt bound).
- **Pricing verification** → `company/training/artifacts/res-pricing-verification.md` — **7/7 PASS**,
  confirmed VEED is inaccessible via static HTTP.

Copies stored in `dept-research:work/astra-cro/verification/`.

## 4. What is now reusable

- **A method standard that has teeth** (`knowledge/method/sourcing-standard.md` v1.1) incl. a
  corrections log and the rule "extract from stripped text, never raw markup".
- **A cited market/technical/competitive knowledge base** on AI-video services, each figure with
  URL + HTTP code + sha256, plus raw snapshots for audit.
- **A reusable verification pattern:** fetch → snapshot+hash → independent second-agent re-fetch.
- **A verified technical fact base:** this runtime can assemble/reframe/caption/normalise video
  with ffmpeg (~$0) but **cannot** do diffusion generation on CPU (measured).

## 5. FAILED / did not work (stated plainly)

1. **`task`-tool delegation to custom-hired specialists FAILS.** Calling `task` with
   `subagent_type=res-demand-analyst` (or `res-competitive-analyst`) returned
   `Unknown agent '…'. Available types: astra-cbdo, astra-ccr, … Use register_agent() to add
   custom agent types.` This is the **same blocker the Creative run recorded**. Only
   pre-registered agent types resolve through `task`.
2. **`task`-tool delegation to the pre-registered Research specialist also FAILS:**
   `astra-mkt-researcher` errors with `Tool 'web_search' not registered but was given to agent`.
   The agent definition on disk lists only `terminal,file_editor,grep,glob`, yet the runtime
   supplies an unregistered `web_search` tool → the agent cannot start via `task`.
3. **Workaround used:** the **child-conversation path** (`ops/astra.py spawn`) reads the agent's
   file definition directly and **worked**, so the verification still happened — with real
   delegation, just not through the `task` tool.
4. **VEED pricing not extractable** (JS-rendered). Not a failure of method — recorded as
   `[UNKNOWN]` rather than guessed.

**Recommendation to the CEO:** register file-based agents with the runtime (or expose a working
`register_agent`/`spawn` path and drop unregistered tools from agent defs) so departments can use
the `task` tool for delegation as documented.

## 6. Blocker summary
- Delegation via `task` tool: **BLOCKED** (custom agents unresolved; pre-registered agent has an
  unregistered tool). Worked around via `spawn`. Recorded, not silently ignored.
- No fabrication anywhere; every number above is a real observed value.
