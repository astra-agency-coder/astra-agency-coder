# Decision Log

Format: `- YYYY-MM-DDTHH:MM:SSZ | <decision> | rationale: <why> | owner: <agent>`

<!-- newest at the bottom -->
- 2026-11-13T00:00:00Z | Founding structure: 7 departments (Engineering, Marketing, Business Development, Product, Operations, Quality, Research) under a CEO | rationale: covers build, distribution, sales, productisation, internal ops, independent verification and intelligence — the minimum complete set for a digital agency | owner: astra-ceo
- 2026-11-13T00:00:00Z | Agent workforce runs on two mechanisms: synchronous `task` delegation for nested work, and child conversations (`ops/astra.py spawn`) for long/parallel work | rationale: both verified working on agent server v1.62.0 | owner: astra-ceo
- 2026-11-13T00:00:00Z | Durable company state lives in git (`astra-agency` repo), not only in the ephemeral runtime | rationale: runtimes are recycled; git survives | owner: astra-ceo
- 2026-11-13T00:00:00Z | Wallet is receive-only; no agent holds keys | rationale: Owner policy; removes custody risk entirely | owner: owner

## D-0009 — Receive-only wallet address registered
**Date:** 2026-11-13
**Decision:** Use the Owner's USDT/TRC20 address `TFBEwXbB4iTyaPC2mtwu5yXSeDjEegJmE6`
(public, from the Owner's `mony` repository) as the company's receive-only wallet.
**Rationale:** The address is valid TRON format and was accepted by TronGrid. It has no
on-chain account yet, which is expected for a fresh receive-only wallet.
**Boundary:** No agent holds a private key or seed phrase; no outbound transfer is
possible. Verification is on-chain only — screenshots and chat links are never proof.

## D-0010 — Per-manager scoped GitHub access via deploy keys
**Date:** 2026-11-13
**Decision:** Give each department manager its own ed25519 keypair, registered as a
write-enabled deploy key on exactly one repository (its department repo). Managers act
through `ops/deptrepo.py`. The company-wide write token stays with the CEO/control plane
only.
**Rationale:** A GitHub deploy key is bound to one repository by the platform, so
least-privilege isolation is enforced by GitHub, not merely by convention. Verified:
each of the 7 managers reaches its own repo and is denied every other repo (test T11).
**Alternatives considered:** (a) one shared PAT for all managers — rejected: no
per-manager isolation; (b) a GitHub App installation token — needs Owner-side App
installation; (c) machine-user accounts per manager — rejected: prohibited (no fake
identities).
**Boundary:** No manager holds the company token, wallet keys, or any secret beyond its
own deploy key. Keys are stored 0600 outside the repo and in the runtime secret store.
