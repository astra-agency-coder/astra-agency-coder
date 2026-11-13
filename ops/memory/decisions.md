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

## D-0011 — Multi-network receive-only wallet registry
**Date:** 2026-11-13
**Decision:** Accept incoming payments on five networks via a public registry at
`company/finance/wallets.json`: USDT-TRC20 (primary), USDT-BEP20, Ethereum (ERC20),
Solana, Bitcoin (native segwit). Public addresses are stored in the registry; they are
not secrets.
**Rationale:** The Owner supplied the addresses; collecting on more networks removes a
friction point with clients and lowers fees (TRC20 remains cheapest/primary).
**Boundaries unchanged:** receive-only. The company never holds private keys or seed
phrases, never signs, never transfers, never spends. Payment proof is on-chain only —
`verify_payment(txid, amount, network)` reads the chain; screenshots/links are not proof.
**Verification:** every address validated live on its chain (test T13).

## D-0012 — Gmail via Google app password in the secret store
**Date:** 2026-11-13
**Decision:** Connect the company mailbox `addh22010@gmail.com` through two OpenHands
secrets: `ASTRA_GMAIL_ADDRESS` and `ASTRA_GMAIL_APP_PASSWORD` (a 16-char Google app
password). The module resolves them from the secret store or the environment.
**Rationale:** App password works with IMAP/SMTP without a full OAuth client and keeps
the real account password out of everything. Only the Owner can create it (needs the
Google account login + 2FA), which is the one human step.
**Boundary:** the password is never written to a file, never committed, never printed.

---

## D-0012 — Creative department created (video + design)
**Date:** 2026-11-13 · **By:** CEO (astra-ceo) · **Status:** adopted
The Owner requested intensive training for a **video-production and design**
capability. No existing department owned visual/video work, so the CEO created a
new **Creative** department (manager `astra-ccr`, Chief Creative Officer) rather
than overloading Marketing. It has its own private repo `dept-creative` and its
own scoped deploy key, like every other department.
**Rationale:** departments own one domain; creative production is its own domain
with its own tools (ffmpeg, Pillow, browser) and its own quality bar.
**Result:** 9 agents total (CEO + 8 managers); access isolation re-verified
(8/8 managers isolated to their own repo).

## D-0013 — Training is a run, not a document
**Date:** 2026-11-13 · **By:** CEO · **Status:** adopted
Added `ops/train.py` + `company/training/curricula/*.md`. A training module counts
only when it produces a **real artifact** with a **check** that passed. The
manager is spawned in its own conversation, does the work with real tools, writes
durable knowledge to its scoped repo, and returns an evidence-backed report.
**Rationale:** the Owner explicitly rejected file-only "training"; skills must be
demonstrated with outputs (video files, code, cited research).
**Bound:** retries ≤ 3; failures are recorded, not hidden.

## D-0014 — Telegram bot token stored; Owner id pending
**Date:** 2026-11-13 · **By:** CEO · **Status:** adopted
The Owner provided the company bot token (`Usytvqozbwoz_bot`). It is stored in the
secret store as `ASTRA_TELEGRAM_BOT_TOKEN` and never written to a file. The
module now resolves it from the secret store. `ASTRA_OWNER_TELEGRAM_ID` is still
unset: the bot only accepts commands from the allowlisted Owner id, so we wait for
the Owner's `/start` to capture the chat id before enabling send.
**Boundary:** the bot must never accept commands from any other user; never send
passwords/keys.

---

## D-0015 — Telegram channel live; Owner allowlisted
**Date:** 2026-11-13 · **By:** CEO · **Status:** adopted
The Owner sent `/start`; the CEO captured the private chat id and stored it as
`ASTRA_OWNER_TELEGRAM_ID` in the secret store (never in a file). The channel is
now **live**: `send()` refuses when no Owner id is set and refuses text that looks
like a secret; `handle_update()` rejects any non-Owner sender.
**Verification:** new test **T14** — owner accepted, stranger rejected, missing id
rejected, non-Owner update dropped, secret-looking send refused (6/6 PASS).
**Boundary:** bot commands are accepted from the Owner id only; no passwords/keys
are ever sent over the channel.

---

## D-0016 — Telegram file delivery (video + brand) to the Owner
**Date:** 2026-11-13 · **By:** CEO · **Status:** adopted
The Owner asked for the Reels video and the visual identity on Telegram. Added
`send_document` / `send_video` / `send_photo` to the Telegram integration
(multipart upload), all Owner-only and all refusing secret-looking captions or
missing files. Sent: reel MP4, thumbnail, brand sheet, three logo SVGs, and two
ZIP packs (brand kit, reel pack).
**Verification:** T14 extended to 8 checks (adds missing-file guard and
caption-secret guard); full suite **13/13 PASS**.

---

## D-0017 — Company website (cinematic) + real email bridge
**Date:** 2026-11-13 · **By:** CEO · **Status:** adopted
Owner asked for a striking company site wired to the company mailbox. Built
`deliveries/astra-site/` — an "OBSIDIAN" dark cinematic one-page site (self-hosted
fonts, constellation canvas, scroll reveals, count-up, custom cursor) with a real
contact endpoint (`POST /api/contact`) that emails `ASTRA_GMAIL_ADDRESS` over
Gmail SMTP. No secrets are written to disk or served.
**Verification:** public URL 200; the contact endpoint returns `{"ok": true}` and
the message really arrives in the mailbox. Engineering delegated to add a verify
script, `serve.sh`/`healthcheck.sh`, a bounded `ops/heal.py` check and an a11y pass.

---

## D-0018 — Company repo default branch corrected to `main`
**Date:** 2026-11-13 · **By:** CEO · **Status:** adopted
The company GitHub repo (`astra-agency-coder/ai-astra-agency`) had `master` as its
default branch, and that `master` is a **divergent history** left by an earlier
session (`master` HEAD `1fe2b7c`; `foundation-v2` branch). All of the current
work lives on `main` (`6a02129`). A fresh visitor to the repo therefore saw the
wrong, stale tree. Fixed by setting the default branch to `main`.
**Nothing was deleted** — `master`, `foundation-v2` and `foundation-2026-11-13`
are left untouched for audit. PR #1 (foundation-v2 → master) is left open but
superseded; it should be closed or re-targeted deliberately, not silently.
**Verification:** `GET /repos/.../ai-astra-agency` → `default_branch = main`.

## D-0010 — Company site is a Next.js 16 build on :12000
**Date:** 2026-11-13
**Decision:** Replace the static `deliveries/astra-site` with
`deliveries/astra-site-v2` (Next.js 16, App Router, 3 locales) as the canonical
public site. `ops/heal.py` and `up.sh` now target it; the old static site stays
in the tree as a rollback path.
**Rationale:** The static page could not carry live engine data, real RTL or a
locale-aware build, and its figures were hand-typed. The new site reads
`src/data/facts.json`, which `tools/gen_facts.py` generates by running the
suites, so no figure on the page can drift from the truth.
**Verified:** 3 locales return 200, audit 9/9 clean, heal reports the site OK,
public URL serves the new build.
**Owner:** astra-ceo

## D-0011 — Treat a credential's blind spot as a finding, not a fact (2026-11-13)
The read-only integration token could not see private repos, so its 403 was
recorded as "repos do not exist". They existed all along (10 private dept repos
with content, accepting pushes). Rule: before recording absence, confirm the
credential can see that class of resource at all.

## D-0012 — Secrets live in the runtime store, never in chat or repo files
Owner-supplied tokens are written only to the OpenHands runtime secret store
(`ops/secrets.py`), read into memory, and masked in every report. Files in the
repo reference secret *names*, never values. Tokens pasted into chat are flagged
to the Owner for rotation.
