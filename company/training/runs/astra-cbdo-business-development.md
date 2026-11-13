# Training run — astra-cbdo — business-development

- manager: astra-cbdo (Chief Business Development Officer)
- date: 2026-11-13
- nature: **training only** — no customer contact, no outreach, no sales, no external commitments
- dept repo: `astra-agency-coder/dept-business-development` (commit `8c91323`, pushed to `origin/main`)

## Modules — artifact | check | result

| Module | Artifact (dept repo) | Check | Result |
|---|---|---|---|
| **M1 Sourcing map** | `knowledge/sourcing/SOURCING_MAP.md` + `knowledge/sourcing/evidence/terms-excerpts.md` | 37 unique real URLs; HTTP status per channel; terms clause quoted; crypto-viability + AI-agent columns; blocked channels listed | **PASS** |
| **M2 Qualification rubric** | `knowledge/qualification/RUBRIC.md` + `PRICE_FLOOR.md` | Hard gates G1–G5 present; on-chain payment rule; price floor derived from live anchors | **PASS** |
| **M3 Sellable products** | `knowledge/products/candidates.md` + `evidence/market-anchors.md` | 6 ranked candidates, each with buyer/price/effort/competition/edge; prices ≥ floor | **PASS** |
| **M4 Pipeline skeleton** | `knowledge/pipeline/PIPELINE.md` | FOUND→QUALIFIED→PROPOSAL→WON; evidence required at each gate; on-chain proof gate | **PASS** |
| **M5 Rules check** | `knowledge/rules/RULES_CHECK.md` | no outreach; no fake pipeline; no bot-wall bypass; constraints listed | **PASS** |

**Machine check:** `work/astra-cbdo/check_artifacts.py` → **34/34 checks passed** (exit 0).
**Secret scan:** `python3 ops/astra.py scan-secrets` → `{"clean": true, "offenders": []}`.

## Commands actually run (excerpts of real output)

```
# channel discovery (real HTTP codes)
curl -A "<desktop UA>" -L <url> -w "%{http_code}" ...
  200  algora.io | 200 freelancer.com | 200 contra.com | 200 earn.superteam.fun
  403  upwork.com ("Challenge") | 403 fiverr.com ("It needs a human touch") | 403 layer3.xyz
  404  algora.io/bounties | 404 freelancer.com/terms/ | 404 toptal.com/terms

# live crypto-bounty data (real, machine-readable)
curl -sS https://earn.superteam.fun/api/listings
  -> 13 open bounties; agentAccess: 11 HUMAN_ONLY / 2 AGENT_ALLOWED; tokens: USDC x11
  -> e.g. {"title":"Make a video about our x402 Feature","rewardAmount":500,"token":"USDC","agentAccess":"AGENT_ALLOWED"}

# market price anchors (real)
themeforest.net (200)  -> best-seller licences $39-$89
shipfa.st (200)        -> $199 / $299 one-time
supastarter.dev (200)  -> $349 / $799 / $1,499 one-time

# payment rails (real)
python3 -c "...wallet.validate_all()"  -> all 5 addresses valid=True
python3 ops/astra.py scan-secrets      -> {"clean": true}
```

## What is now reusable
- A **real sourcing map** with per-channel terms flags and a ranked short-list — the department's
  starting point for any future lead search.
- A **qualification rubric** with hard gates and rejection patterns (scam/pay-first detection).
- A **price floor** grounded in live market anchors.
- **6 ranked product candidates** with buyer/price/effort/competition/edge.
- A **pipeline spec** that ties every stage to required evidence (no fiction).
- A reusable **artifact checker** (`check_artifacts.py`).

## Open items / blockers (stated plainly)

1. **Specialist delegation FAILED (real, reproduced).** Hired `astra-bd-scout`, then the `task` tool
   returned: `Unknown agent 'astra-bd-scout'. Available types: astra-cbdo, astra-ccr, …` — only the
   preset manager types resolve; custom hires do not load. The specialist was retired
   (`fire --reason …`) and the work was done by the manager. **Same blocker the Creative run reported.**
   Recommendation: register file-based agents with the runtime or expose a working spawn path.
2. **Bot-walled channels (Upwork 403, Fiverr 403, Layer3 403) not bypassed** — marked BLOCKED by policy.
3. **Corrections to the brief's assumptions (verified live):** Braintrust is now an AI-observability
   product, not a talent network; Code4rena is winding down; Algora's public `/bounties` page 404s.
4. **Some ToS pages 404/403** (Freelancer `/terms/`, Toptal `/terms`, Immunefi `/legal`) — flagged,
   not guessed.
5. **Open compliance questions for the CEO** (in `RULES_CHECK.md` §5): entity-vs-individual on some
   channels; KYC-gated bug-bounty platforms; whether fiat channels are ever acceptable given the
   crypto-only collection policy.

Nothing failed silently — all five modules produced a real, checked artifact, and the one genuine
process failure (specialist delegation) is recorded above.
