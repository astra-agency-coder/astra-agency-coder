#!/usr/bin/env python3
"""Astra Trading — Supabase Row-Level-Security red-team harness.

Proves, with reproductions, whether the RLS controls on the Astra Trading
Supabase project actually hold when attacked:

  * as an ANONYMOUS client (anon key), and
  * as a FAKE AUTHENTICATED user (a real JWT for a freshly created throwaway
    account) trying to reach another user's rows.

It never prints or writes a secret value: keys are resolved at runtime through
ops/secrets.py and only ever held in memory. Fixtures are created with the
service key and deleted at the end (best effort).

Usage:
    python3 rls_test.py            # run all checks, print a table
    python3 rls_test.py --json     # also write rls_results.json next to this file
"""
from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import secrets as S  # noqa: E402

PROJECT_REF = "unrmzqnvfgaqrwyeqddn"

RESULTS: list[dict] = []


# --------------------------------------------------------------------------- #
# tiny REST client
# --------------------------------------------------------------------------- #
def _req(url: str, method: str, headers: dict, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, _maybe_json(raw)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, _maybe_json(raw)
    except Exception as e:  # noqa: BLE001
        return "ERR", str(e)


def _maybe_json(raw: bytes):
    try:
        return json.loads(raw.decode())
    except Exception:  # noqa: BLE001
        return raw.decode(errors="ignore")[:400]


class Client:
    """A REST client bound to one credential (anon, a user JWT, or service)."""

    def __init__(self, base: str, key: str | None, bearer: str | None, label: str):
        self.base = base.rstrip("/")
        self.key = key
        self.bearer = bearer
        self.label = label

    def _h(self, extra: dict | None = None) -> dict:
        h = {"Content-Type": "application/json"}
        if self.key:
            h["apikey"] = self.key
        if self.bearer:
            h["Authorization"] = "Bearer " + self.bearer
        if extra:
            h.update(extra)
        return h

    def rest(self, path: str, method="GET", body=None, extra=None):
        return _req(f"{self.base}/rest/v1/{path}", method, self._h(extra), body)

    def auth(self, path: str, method="GET", body=None, extra=None):
        return _req(f"{self.base}/auth/v1/{path}", method, self._h(extra), body)


# --------------------------------------------------------------------------- #
# assertions
# --------------------------------------------------------------------------- #
def record(name: str, control: str, expected: str, ok: bool, evidence: str):
    RESULTS.append({"check": name, "control": control, "expected": expected,
                    "result": "PASS" if ok else "FAIL",
                    "verdict": "ENFORCED" if ok else "MISSING", "evidence": evidence})
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}")
    if not ok:
        print(f"         expected {expected}")
        print(f"         evidence {evidence}")


def count_rows(res) -> int | None:
    status, body = res
    if status == 200 and isinstance(body, list):
        return len(body)
    return None


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    url = S.resolve("ASTRA_SUPABASE_URL")
    anon = S.resolve("ASTRA_SUPABASE_ANON_KEY")
    svc = S.resolve("ASTRA_SUPABASE_SECRET_KEY")
    if not (url and anon and svc):
        print("missing Supabase credentials in the runtime secret store", file=sys.stderr)
        return 2
    url = url.rstrip("/")
    anon_c = Client(url, anon, anon, "anon")
    svc_c = Client(url, svc, svc, "service")

    # sanity: the service key must actually bypass RLS, else the harness is blind
    st, _ = svc_c.rest("profiles?select=id&limit=1")
    if st != 200:
        print(f"service key cannot read (http={st}); aborting", file=sys.stderr)
        return 2

    created_users: list[str] = []
    created_setups: list[str] = []
    tag = uuid.uuid4().hex[:8]

    def make_user(role_note: str, sub_status: str | None) -> tuple[str, Client] | None:
        email = f"rt-{tag}-{uuid.uuid4().hex[:6]}@astra-redteam.test"
        pw = "AstraRt-" + uuid.uuid4().hex[:14] + "!7"
        st, body = svc_c.auth("admin/users", "POST",
                              {"email": email, "password": pw, "email_confirm": True})
        if st not in (200, 201):
            print(f"could not create {role_note} user: {st} {body}", file=sys.stderr)
            return None
        uid = body["id"]
        created_users.append(uid)
        st, body = svc_c.auth("token?grant_type=password", "POST",
                              {"email": email, "password": pw})
        if st != 200:
            print(f"could not sign in {role_note}: {st} {body}", file=sys.stderr)
            return None
        jwt = body["access_token"]
        if sub_status is not None:
            svc_c.rest("subscriptions?user_id=eq." + uid, "PATCH", {"status": sub_status},
                       {"Prefer": "return=minimal"})
        return uid, Client(url, anon, jwt, role_note)

    print("== setting up fixtures ==")
    # purge any fixtures left by a previous interrupted run
    for path in ("setups?idempotency_key=like.rt-*", "setups?idempotency_key=like.dbg-*",
                 "setups?idempotency_key=like.f-*", "setups?idempotency_key=like.good-*",
                 "payments?tx_hash=like.RT-TX-*", "agent_keys?name=like.rt-key-*"):
        svc_c.rest(path, "DELETE", None, {"Prefer": "return=minimal"})

    u1 = make_user("victim-active", "active")
    u2 = make_user("attacker-active", "active")
    u3 = make_user("nosub-expired", "expired")
    if not (u1 and u2 and u3):
        return 2
    (u1_id, u1_c), (u2_id, u2_c), (u3_id, u3_c) = u1, u2, u3

    # private rows for the victim, written with the service key (bypasses RLS)
    svc_c.rest("profiles?id=eq." + u1_id, "PATCH",
               {"email": f"victim-{tag}@private.test", "full_name": "Victim Real Name"})
    svc_c.rest("subscriptions?user_id=eq." + u1_id, "PATCH", {"plan": "pro", "provider_ref": "SECRET-PROVIDER-REF"})
    st, p = svc_c.rest("payments", "POST", {
        "user_id": u1_id, "provider": "usdt_trc20", "network": "TRON",
        "tx_hash": "RT-TX-" + tag, "to_address": "TFBEwXbB4iTyaPC2mtwu5yXSeDjEegJmE6",
        "amount": 19, "currency": "USDT", "status": "confirmed"})
    svc_c.rest("alerts", "POST", {"user_id": u1_id, "channel": "telegram",
                                  "address": "@victim_private_handle"})
    # a published setup + an UNPUBLISHED (shadow) setup
    st, created = svc_c.rest("setups", "POST", {
        "direction": "long", "entry": 2000, "stop_loss": 1990, "tp1": 2010, "tp2": 2020,
        "tp3": 2030, "risk_reward": 2.0, "confidence": 0.7, "published": True,
        "status": "tp1_hit", "outcome_r": 1.0, "idempotency_key": f"rt-pub-{tag}"},
        {"Prefer": "return=representation"})
    if isinstance(created, list) and created:
        created_setups.append(created[0]["id"])
        svc_c.rest("setup_events", "POST", {"setup_id": created[0]["id"], "to_status": "tp1_hit",
                                            "price": 2010, "reason": "rt fixture"})
    else:
        print(f"  ! published fixture not created: http={st} {str(created)[:160]}")
    st, created = svc_c.rest("setups", "POST", {
        "direction": "short", "entry": 2000, "stop_loss": 2010, "tp1": 1990, "tp2": 1980,
        "tp3": 1970, "risk_reward": 2.0, "confidence": 0.6, "published": False,
        "status": "proposed", "idempotency_key": f"rt-shadow-{tag}"},
        {"Prefer": "return=representation"})
    if isinstance(created, list) and created:
        created_setups.append(created[0]["id"])
    else:
        print(f"  ! shadow fixture not created: http={st} {str(created)[:160]}")
    # an agent key (hash only) and an audit row
    svc_c.rest("agent_keys", "POST", {"name": "rt-key-" + tag,
                                      "key_hash": uuid.uuid4().hex + uuid.uuid4().hex})
    svc_c.rest("audit_log", "POST", {"actor": "rt", "action": "redteam-fixture",
                                     "target": u1_id, "meta": {"note": "rt"}})

    # ------------------------------------------------------------------ #
    print("\n== 1. ANON client: cross-user read ==")
    for table in ("profiles", "subscriptions", "setups", "setup_events", "payments", "alerts"):
        res = anon_c.rest(f"{table}?select=*&limit=5")
        n = count_rows(res)
        # setups are readable by *authenticated subscribers*, never by anon.
        ok = (n == 0)
        record(f"anon cannot read {table}", "RLS: anon has no SELECT grant/policy",
               "0 rows", ok, f"http={res[0]} rows={n} body={str(res[1])[:120]}")

    print("\n== 2. ANON client: cannot read agent_keys / audit_log AT ALL ==")
    for table in ("agent_keys", "audit_log"):
        res = anon_c.rest(f"{table}?select=*&limit=5")
        n = count_rows(res)
        ok = (n == 0)
        record(f"anon cannot read {table}", "RLS: no anon policy on secrets/audit",
               "0 rows", ok, f"http={res[0]} rows={n}")

    print("\n== 3. ANON client: cannot WRITE setups ==")
    res = anon_c.rest("setups", "POST", {
        "direction": "long", "entry": 2000, "stop_loss": 1990, "idempotency_key": "anon-" + tag},
        {"Prefer": "return=minimal"})
    ok = res[0] not in (200, 201, 204)
    record("anon cannot INSERT setups", "RLS: setups has SELECT policy only",
           "write denied (401/403)", ok, f"http={res[0]} body={str(res[1])[:160]}")

    print("\n== 4. ANON client: cannot WRITE other tables ==")
    for table, row in (("profiles", {"id": u1_id, "role": "admin"}),
                       ("alerts", {"user_id": u1_id, "channel": "email"}),
                       ("agent_keys", {"name": "anon", "key_hash": uuid.uuid4().hex})):
        res = anon_c.rest(table, "POST", row, {"Prefer": "return=minimal"})
        ok = res[0] not in (200, 201, 204)
        record(f"anon cannot INSERT {table}", "RLS deny-by-default",
               "write denied", ok, f"http={res[0]} body={str(res[1])[:120]}")

    # ------------------------------------------------------------------ #
    print("\n== 5. AUTHENTICATED user U2: cannot read U1's private rows ==")
    for table, col in (("profiles", "id"), ("subscriptions", "user_id"),
                       ("payments", "user_id"), ("alerts", "user_id")):
        res = u2_c.rest(f"{table}?select=*&limit=10")
        body = res[1]
        rows = body if isinstance(body, list) else []
        foreign = [r for r in rows if str(r.get(col)) == u1_id]
        own = [r for r in rows if str(r.get(col)) == u2_id]
        ok = (len(foreign) == 0)
        record(f"U2 cannot read U1's {table} rows", "RLS: user_id = auth.uid()",
               "no rows owned by U1", ok,
               f"http={res[0]} returned={len(rows)} foreign(U1)={len(foreign)} own(U2)={len(own)}")

    print("\n== 6. AUTHENTICATED user U2: cannot UPDATE U1's profile ==")
    res = u2_c.rest("profiles?id=eq." + u1_id, "PATCH", {"full_name": "PWNED"},
                    {"Prefer": "return=representation"})
    body = res[1]
    changed = isinstance(body, list) and len(body) > 0
    ok = not changed
    record("U2 cannot UPDATE U1 profile", "RLS: profiles_self_update using id=auth.uid()",
           "0 rows modified", ok, f"http={res[0]} modified={len(body) if isinstance(body, list) else body}")

    print("\n== 7. AUTHENTICATED user: cannot read agent_keys / audit_log ==")
    for table in ("agent_keys", "audit_log"):
        res = u2_c.rest(f"{table}?select=*&limit=5")
        n = count_rows(res)
        ok = (n == 0)
        record(f"U2 cannot read {table}", "RLS: no authenticated policy",
               "0 rows", ok, f"http={res[0]} rows={n}")

    print("\n== 8. AUTHENTICATED user: cannot WRITE setups ==")
    res = u2_c.rest("setups", "POST", {
        "direction": "long", "entry": 2000, "stop_loss": 1990, "idempotency_key": "u2-" + tag},
        {"Prefer": "return=minimal"})
    ok = res[0] not in (200, 201, 204)
    record("U2 cannot INSERT setups (write needs service role)",
           "RLS: setups has SELECT policy only", "write denied", ok,
           f"http={res[0]} body={str(res[1])[:160]}")

    # ------------------------------------------------------------------ #
    print("\n== 9. setups visibility gate (subscription) ==")
    res = u2_c.rest("setups?select=id,status,published&limit=50")
    body = res[1] if isinstance(res[1], list) else []
    pub_seen = any(r.get("id") == created_setups[0] for r in body) if created_setups else None
    shadow_seen = any(r.get("id") == created_setups[1] for r in body) if len(created_setups) > 1 else None
    # Active subscriber: may read setups (policy grants any authenticated
    # subscriber). Shadow/unpublished setups are NOT filtered by the policy —
    # this is recorded as an observation, not necessarily a failure.
    print(f"  [info] active subscriber sees {len(body)} setups; published_fixture={pub_seen} "
          f"shadow_fixture={shadow_seen}")
    if shadow_seen:
        record("setups policy hides unpublished (shadow) setups",
               "RLS: setups_read has no `published` predicate",
               "unpublished setups hidden from users", False,
               "unpublished fixture WAS returned to an active subscriber — shadow-mode setups leak")

    print("\n== 10. EXPIRED subscriber cannot read setups ==")
    res = u3_c.rest("setups?select=id&limit=50")
    n = count_rows(res)
    ok = (n == 0)
    record("expired-trial user cannot read setups",
           "RLS: setups_read requires active/trialing subscription", "0 rows", ok,
           f"http={res[0]} rows={n}")

    # ------------------------------------------------------------------ #
    print("\n== 11. setups CHECK constraint (geometry) ==")
    bad_long = {"direction": "long", "entry": 2000, "stop_loss": 2010,  # stop ABOVE entry
                "idempotency_key": "bad-long-" + tag}
    res = svc_c.rest("setups", "POST", bad_long, {"Prefer": "return=minimal"})
    ok = res[0] not in (200, 201, 204) and "check" in str(res[1]).lower()
    record("CHECK rejects long with stop ABOVE entry", "setups geometry CHECK",
           "rejected by check constraint", ok, f"http={res[0]} body={str(res[1])[:200]}")

    bad_short = {"direction": "short", "entry": 2000, "stop_loss": 1990,  # stop BELOW entry
                 "idempotency_key": "bad-short-" + tag}
    res = svc_c.rest("setups", "POST", bad_short, {"Prefer": "return=minimal"})
    ok = res[0] not in (200, 201, 204) and "check" in str(res[1]).lower()
    record("CHECK rejects short with stop BELOW entry", "setups geometry CHECK",
           "rejected by check constraint", ok, f"http={res[0]} body={str(res[1])[:200]}")

    good = {"direction": "long", "entry": 2000, "stop_loss": 1990, "tp1": 2010,
            "idempotency_key": "good-" + tag}
    res = svc_c.rest("setups", "POST", good, {"Prefer": "return=minimal"})
    ok = res[0] in (200, 201, 204)
    if ok:
        st, rows = svc_c.rest(f"setups?idempotency_key=eq.good-{tag}&select=id")
        if isinstance(rows, list) and rows:
            created_setups.append(rows[0]["id"])
    record("CHECK accepts a valid long setup (control)", "setups geometry CHECK",
           "accepted", ok, f"http={res[0]} body={str(res[1])[:160]}")

    # ------------------------------------------------------------------ #
    print("\n== 12. track_record view exposes NO personal data ==")
    res = anon_c.rest("track_record?select=*")
    body = res[1]
    cols = set(body[0].keys()) if isinstance(body, list) and body else set()
    pii = {"email", "full_name", "user_id", "id", "address", "tx_hash", "to_address", "provider_ref"}
    leak = cols & pii
    ok = not leak
    record("track_record exposes no PII columns", "public view column allow-list",
           "aggregate counters only", ok, f"http={res[0]} columns={sorted(cols)} leak={sorted(leak)}")

    # ------------------------------------------------------------------ #
    print("\n== 13. privilege escalation: user sets own role to admin ==")
    res = u2_c.rest("profiles?id=eq." + u2_id, "PATCH", {"role": "admin"},
                    {"Prefer": "return=representation"})
    body = res[1]
    escalated = isinstance(body, list) and any(str(r.get("role")) == "admin" for r in body)
    if escalated:
        # prove the impact: is_staff() now returns true → full cross-user read
        after = u2_c.rest("profiles?select=id&limit=200")
        n = count_rows(after)
        record("user cannot self-escalate role via profiles UPDATE",
               "RLS: profiles_self_update has no column allow-list",
               "role stays 'user'", False,
               f"role update ACCEPTED (http={res[0]}); user can now read {n} profiles "
               f"incl. other users — staff bypass via public.is_staff()")
    else:
        record("user cannot self-escalate role via profiles UPDATE",
               "RLS: profiles_self_update restricted", "role stays 'user'", True,
               f"http={res[0]} modified={len(body) if isinstance(body, list) else body}")

    # ------------------------------------------------------------------ #
    print("\n== cleanup ==")
    for sid in created_setups:
        svc_c.rest("setups?id=eq." + sid, "DELETE", None, {"Prefer": "return=minimal"})
    svc_c.rest("payments?tx_hash=eq.RT-TX-" + tag, "DELETE", None, {"Prefer": "return=minimal"})
    svc_c.rest("agent_keys?name=eq.rt-key-" + tag, "DELETE", None, {"Prefer": "return=minimal"})
    svc_c.rest("audit_log?action=eq.redteam-fixture", "DELETE", None, {"Prefer": "return=minimal"})
    for uid in created_users:
        st, _ = svc_c.auth("admin/users/" + uid, "DELETE")
        print(f"  deleted user {uid[:8]}… http={st}")

    # ------------------------------------------------------------------ #
    passed = sum(1 for r in RESULTS if r["result"] == "PASS")
    failed = len(RESULTS) - passed
    print(f"\nRESULT {passed}/{len(RESULTS)} checks passed; {failed} finding(s)")
    for r in RESULTS:
        if r["result"] == "FAIL":
            print(f"  FINDING [{r['verdict']}]: {r['check']} — {r['evidence']}")

    if "--json" in sys.argv:
        out = HERE / "rls_results.json"
        out.write_text(json.dumps({"project": PROJECT_REF, "results": RESULTS}, indent=2))
        print(f"wrote {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
