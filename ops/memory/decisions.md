# Decision Log

Format: `- YYYY-MM-DDTHH:MM:SSZ | <decision> | rationale: <why> | owner: <agent>`

<!-- newest at the bottom -->
- 2026-11-13T00:00:00Z | Founding structure: 7 departments (Engineering, Marketing, Business Development, Product, Operations, Quality, Research) under a CEO | rationale: covers build, distribution, sales, productisation, internal ops, independent verification and intelligence — the minimum complete set for a digital agency | owner: astra-ceo
- 2026-11-13T00:00:00Z | Agent workforce runs on two mechanisms: synchronous `task` delegation for nested work, and child conversations (`ops/astra.py spawn`) for long/parallel work | rationale: both verified working on agent server v1.62.0 | owner: astra-ceo
- 2026-11-13T00:00:00Z | Durable company state lives in git (`astra-agency` repo), not only in the ephemeral runtime | rationale: runtimes are recycled; git survives | owner: astra-ceo
- 2026-11-13T00:00:00Z | Wallet is receive-only; no agent holds keys | rationale: Owner policy; removes custody risk entirely | owner: owner
