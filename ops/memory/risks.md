# Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-01 | Runtime recycled; unsaved work lost | High | Medium | All durable state in git; commit frequently | CEO | Open |
| R-02 | Secret accidentally committed | Medium | High | `ops/astra.py scan-secrets` before commit | COO | Open |
| R-03 | Fabricated result reported to Owner | Low | High | Independent Quality verification before delivery | CQO | Open |
| R-04 | LLM API key unavailable/expired | Medium | High | `ops/heal.py` probes and re-resolves config | CTO | Open |
| R-05 | Agent loop runs unbounded | Low | Medium | `max_iterations` + stuck detection + 3-attempt cap | CTO | Open |
| R-06 | Payment fraud (fake receipt) | Medium | High | On-chain verification only; never trust screenshots | COO | Open |
| R-07 | Platform terms violation during outreach | Medium | High | Compliance review before any outreach campaign | CBDO | Open |
| R-08 | Telegram command spoofing | Low | High | Owner-ID allowlist enforced in bot layer | CTO | Open |
