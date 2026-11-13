# Playbooks

## PB-006 — Provision the seven department repositories
```bash
python3 ops/provision_repos.py --dry-run   # preview
python3 ops/provision_repos.py             # create/update all
```
Creates `dept-engineering`, `dept-marketing`, `dept-business-development`,
`dept-product`, `dept-operations`, `dept-quality`, `dept-research` — each
**private**, each with a README, a CHARTER, and `knowledge/` + `work/` folders.
Idempotent. Requires a token with repo-create + contents-write. Tested
2026-11-13: blocked by read-only token (403) — see lessons.

## PB-007 — Onboarding a new department
1. CEO decides the department is genuinely needed (record the decision).
2. `python3 ops/astra.py hire <dept>-manager --dept "<Dept>" --reports-to astra-ceo --tools terminal,file_editor,task_tracker,task_tool_set`
3. Add the department to `ops/provision_repos.py:DEPARTMENTS`.
4. Run PB-006 to create its private repository.
5. Create `company/departments/<slug>/` locally with README + CHARTER + knowledge/.
6. Update `company/ORG_DESIGN.md` and `company/roster.json`.

## PB-008 — Static website delivery (no build step)
1. Build `index.html` (semantic landmarks, single `h1`, `lang`, viewport meta),
   `styles.css` (mobile-first, fluid `max-width` container, `box-sizing:
   border-box`, `minmax(0,1fr)` grids), `main.js` (progressive enhancement only
   — content must stay visible with JS disabled).
2. Prove no external deps: `grep -E 'https?://' index.html styles.css main.js`
   must be empty.
3. Commit `verify_site.py`; run it — html5lib strict parse, local-asset
   existence, duplicate-id / in-page-anchor / heading-order checks, CSS
   fixed-px-width audit. Expect `RESULT: PASS`.
4. Serve and curl every asset -> expect `HTTP 200` for `/`, `index.html`,
   `styles.css`, `main.js`, `assets/*`.
5. `python3 ops/astra.py scan-secrets` -> `clean: true`.
6. Deploy: `mkdir -p /tmp/astra_site && cp -r <site>/* /tmp/astra_site/` then
   `nohup python3 -m http.server 12000 --directory /tmp/astra_site &`; record
   `curl -sI http://127.0.0.1:12000/`.
7. Independent QA pass; list untested dimensions (e.g. pixel rendering) in
   `VERIFY.md`. Check for upstream `brand/tokens.json` before hardcoding colours.

## PB-009 — Ship a site with a real backend (contact form → SMTP)
1. Use `server.py` (stdlib `ThreadingHTTPServer`) to serve the site **and** host
   `POST /api/contact`. Never serve the package directory raw: override
   `send_head()` to allowlist public asset suffixes and 404 dotfiles/source/dev
   files (see L-0012).
2. Validate input server-side (required fields, email regex), rate-limit per IP,
   cap the body; return `400` on bad input, `429` when throttled, `503` when
   mail is unconfigured, `502` on send failure, `200 {"ok": true}` on success.
3. Send via `smtplib.SMTP_SSL("smtp.gmail.com", 465)` with
   `ASTRA_GMAIL_ADDRESS` / `ASTRA_GMAIL_APP_PASSWORD` from the secret store.
   Never write credentials to disk or logs.
4. `serve.sh` is idempotent: stop the prior listener by an **anchored** pattern
   (`^python3 server\.py$`), start detached with `ASTRA_SITE_PORT` set **inline
   on the child**, wait for HTTP 200. Log to `/tmp/astra_site_new.log`.
5. Wire a single `astra_site` check into `ops/heal.py` (bounded to 3 attempts) —
   one port, one owning launcher.
6. Verify with `verify_site.py`: HTML/a11y/performance statics + live
   `/api/contact` (400 on bad, 200 on good) + the public URL returns 200.
7. `python3 ops/astra.py scan-secrets` → `clean: true`; then `deptrepo save`.
