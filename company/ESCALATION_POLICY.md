# Escalation & Autonomy Policy

## Handle autonomously (no Owner contact)
- Choosing domains, services, products, pricing *models*, markets, channels.
- Creating / retiring departments, managers and specialists.
- Decomposing tasks, writing briefs, running delegation and verification.
- Fixing routine technical problems (bounded to 3 attempts per approach).
- Internal tooling, memory, reporting and process design.
- Drafting proposals, offers and content for review.

## Escalate to Owner (only these)
| Trigger | Why | Expected Owner action |
|---|---|---|
| Missing credential / account / API key | Only a human can provision it | Provide the account or token securely |
| Human verification (CAPTCHA / KYC / 2FA / passkey) | Cannot be automated lawfully | Perform the step, or authorise an alternative |
| High-risk financial decision | Money / legal exposure | Approve or decline |
| Legal contract or binding commitment | Legal exposure | Approve or decline |
| Irreversible destructive action on shared systems | Data-loss risk | Confirm |
| Blocking technical limitation after bounded effort | Genuine dead-end | Decide or unblock |

## Escalation format (Telegram / main chat)
```
[ESCALATION] <one-line title>
Blocked: <what cannot proceed>
Tried: <attempts made, bounded>
Needed: <exact ask>
Impact if unresolved: <consequence>
```

## Rate limits
- Routine operational updates: batched into the periodic Owner report.
- Never more than one escalation per blocker.
- Never an escalation for something already solvable in-environment.
