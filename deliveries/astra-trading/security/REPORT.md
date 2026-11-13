# Astra Trading — Security Red-Team Report v1

Author: `astra-ciso` (Security department). Target: our own product and
infrastructure. Every finding below has a reproduction, not an opinion.

## Scope and method

| Area | How it was tested | Tool |
|---|---|---|
| Supabase RLS / grants | live HTTP against the real project, as anon and as two authenticated users | `rls_test.py` |
| Engine robustness | hostile inputs: empty, NaN, ±Inf, single candle, duplicated timestamps, absurd prices, non-dict payloads | `fuzz_test.py` |
| Repo secret hygiene | pattern scan over the whole tree and git history | `secret_scan.sh` |
| Agent API contract | specified checks + the plan to implement them | this document |

## Findings

### 1. CRITICAL — privilege escalation via `profiles.role` (FIXED)

**What:** the `profiles_self_update` policy allowed a user to `UPDATE` their own
row with no column restriction. Setting `role = 'admin'` made `public.is_staff()`
return true, which unlocked every other user's data (profiles, subscriptions,
payments, and the unpublished setup feed).

**Reproduction (before the fix):**
```
PATCH /rest/v1/profiles?id=eq.<own-uid>   {"role": "admin"}   -> 200
GET   /rest/v1/profiles?select=id,email                       -> 3 rows (all users)
```

**Fix:** `db/002_security_fixes.sql`
* a `BEFORE UPDATE` trigger (`prevent_privilege_escalation`) rejects any change to
  `role`, `disabled` or `id` unless the actor is already staff (RLS cannot
  restrict individual columns, a trigger can);
* the update policy re-asserts a `WITH CHECK` that pins `role` to its current
  value and forbids `disabled = true` for non-staff.

**Verified:** `rls_test.py` check 13 now returns
`user cannot self-escalate role via profiles UPDATE -> PASS`.

### 2. HIGH — shadow-mode setups leaked to subscribers (FIXED)

**What:** the `setups` read policy gated on subscription state but ignored the
`published` flag, so unproven (shadow-mode) AI setups were visible to any active
subscriber. That contradicts the core promise: users only ever see setups that
have earned publication.

**Reproduction (before the fix):** an active subscriber received both the
`published_fixture` **and** the `shadow_fixture` rows.

**Fix:** require `published = true` for non-staff, and make `setup_events`
inherit the parent setup's visibility exactly.

**Verified:** subscriber now sees published rows only; staff still see all.

### 3. MEDIUM — payments table accepted user-supplied state (FIXED)

**What:** no insert/update policy constrained a user's own payment rows, so a
client could attempt to write a `confirmed` payment.

**Fix:** users may insert only their own row with `status = 'pending'`;
`UPDATE` is staff-only. Confirmation happens server-side after on-chain
verification, never from the client.

### 4. MEDIUM — engine crashed on hostile input (FIXED)

**What:** the engine raised on malformed data. Fuzzing produced **16 crashes**:
`IndexError` on empty candle lists, `ValueError: cannot convert float NaN to
integer`, `OverflowError` on infinity, and `AttributeError`/`TypeError` in
`market._parse` for non-dict payloads.

**Why it matters:** a single bad bar from the feed would take down the whole
analysis path, and an attacker controlling the upstream response could do it
deliberately.

**Fix:** `analysis._clean()` drops any candle that is not finite, positive and
ordered; every public function handles the empty case; `market._parse` validates
the payload shape and every bar. **Verified:** fuzz crashes **16 → 0**,
safety violations 0, and the 27 unit tests still pass.

### 5. LOW — heavy scraped research pages were committed

**What:** 12 MB of raw competitor HTML was committed, including third-party
Google API keys and JWTs that are not ours.

**Fix:** raw scrapes are now gitignored and untracked; only derived notes stay.
Verified: no tracked file matches any real key pattern.

## Controls verified as ENFORCED (25 of 27 checks)

* anon cannot read `profiles`, `subscriptions`, `setups`, `setup_events`,
  `payments`, `alerts`, `agent_keys`, `audit_log` (all 0 rows);
* anon cannot INSERT into `setups`, `profiles`, `alerts` (RLS 42501);
* an authenticated user cannot read `agent_keys` or `audit_log`;
* writes to `setups` need the service role;
* the geometry CHECK constraint rejects a long with the stop above entry and a
  short with the stop below entry, and accepts the valid control;
* an expired-trial user cannot read setups;
* `track_record` exposes no PII columns;
* **agent API:** unauthenticated calls are rejected with 401 *before* the body is
  parsed (so schema details never leak), the open-setup cap holds at 3, replays
  return the original id, and R:R < 1.0 is refused.

## Agent API ingestion — required checks (contract)

The endpoint `POST /api/v1/setups` must enforce, in this order:

1. **Auth first** — resolve `X-Agent-Key` (SHA-256 of the key against
   `agent_keys`, `revoked_at IS NULL`) before reading the body. Implemented.
2. **Rate limit** per agent (30/min) and per IP. Implemented.
3. **Idempotency** — `idempotency_key` required, unique in the store; a replay
   returns the original id with 200, never a second row. Implemented.
4. **Validation** — direction, timeframe, positive prices, geometry, R:R ≥ 1.0.
   Implemented.
5. **Shadow by default** — new rows are `published = false` until the evaluator
   has scored them. Implemented.
6. **Concurrency cap** — refuse when ≥ 3 setups are open. Implemented.
7. **Immutable audit** — every transition is appended to `setup_events`; the
   table has no update/delete policy. Implemented.
8. **Still to add:** per-key scopes enforcement (the `scopes` column is stored
   but not yet consulted) and replay-window expiry on `idempotency_key`.

## Open items (honest)

| # | Item | Severity | Status |
|---|---|---|---|
| 1 | `scopes` column not yet enforced per endpoint | MEDIUM | OPEN |
| 2 | No WAF / bot protection in front of the public API | MEDIUM | OPEN — needs hosting decision |
| 3 | JWT verification is delegated to Supabase; no independent check in our code | LOW | ACCEPTED |
| 4 | Pen-test of the Android apps | HIGH | BLOCKED — apps not built yet |

## Reproduce everything

```bash
python3 rls_test.py        # live RLS + constraint checks against Supabase
python3 fuzz_test.py       # hostile-input robustness
./secret_scan.sh           # repo secret hygiene
```
