# Integrations — Status & Requirements

Everything here is prepared to plug in the moment the Owner provides the
resource. Nothing claims to be connected until a live test passes.

Status legend: `CONNECTED` (live-tested) · `PREPARED` (code ready, needs
credential) · `NEEDS OWNER ACTION` (waiting on the Owner).

| Integration | Status | Code | Needs from Owner |
|---|---|---|---|
| Gmail | NEEDS OWNER ACTION | `ops/integrations/gmail.py` | company Gmail address + OAuth client / app password, delivered as a runtime secret |
| GitHub | PREPARED | `ops/integrations/github.py` | confirm the company account is `astra-agency-coder` and that the token may create private repos |
| Telegram | PREPARED | `ops/integrations/telegram.py` | bot token + Owner's numeric Telegram user ID, delivered as runtime secrets |
| Wallet (USDT/TRC20) | PREPARED | `ops/integrations/wallet.py` | receive-only wallet address (public; never a key) |
| Scheduling | PREPARED | `ops/scheduler.py` | confirm which OpenHands Cloud automation schedule to enable |

## How to deliver a secret safely (never paste into chat or files)
Secrets belong in the OpenHands Cloud secret store or as environment variables
injected into the runtime. They are read here only by name:

| Env var name | Purpose |
|---|---|
| `ASTRA_GMAIL_ADDRESS` | company Gmail address |
| `ASTRA_GMAIL_APP_PASSWORD` | Gmail app password (or OAuth token) |
| `ASTRA_TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `ASTRA_OWNER_TELEGRAM_ID` | Owner's numeric Telegram user ID (allowlist) |
| `ASTRA_WALLET_USDT_TRC20` | public receive-only TRON address |

`ops/astra.py scan-secrets` fails the build if any of these values leak into a
tracked file.

<a id="integration-gmail"></a>
## Gmail
- Purpose: read business mail, classify, draft replies, follow up, read OTP.
- Method: IMAP/SMTP with an app password, or the Gmail API with OAuth.
- Rules: never store the password in a file; never bypass 2FA/CAPTCHA; send only
  legitimate business mail; no bulk unsolicited email.

<a id="integration-github"></a>
## GitHub
- Purpose: repositories, code, issues, releases, org structure.
- Account: `astra-agency-coder` (verified reachable with the runtime token).
- Rule: no secrets in repos; use repository secrets.

<a id="integration-telegram"></a>
## Telegram
- Purpose: primary CEO↔Owner channel.
- Rule: **only** the Owner's numeric user ID may issue commands. Any other
  sender is rejected and logged.

<a id="integration-wallet"></a>
## Wallet (USDT / TRC20)
- Purpose: receive payment. **Receive-only.**
- Rule: no private key, no seed phrase, no outbound transfer, ever.
- Verification: on-chain only (TronGrid), never a screenshot or a chat link.
