# Problem brief — CI Log Triage (working title: `citriage`)

*Product department training run — software-delivery curriculum, Module 1.*
**Author:** astra-cpo · **Date:** 2026-11-13 · **Status:** draft for scope gate

## One-line problem
Teams spend **engineer-hours per week** reading raw CI logs to answer one
question — *"is this failure mine, or is it infrastructure/flaky noise?"* —
and there is no cheap, offline, deterministic tool that answers it.

## User
- **Primary:** an engineer on a small (2–20 dev) team who owns CI and is the de
  facto build-breaker. They have a full-time job; CI triage is overhead.
- **Secondary:** a staff/platform engineer who wants a *repeatable* signal to
  decide whether to retry, revert, or file a real bug.
- **Not the user:** large orgs with a dedicated observability budget and a
  vendor already in place (they will not switch to a CLI).

## Problem, with evidence (signals, not opinions)
| Signal | Source (real) |
|---|---|
| "End-to-end tests that don't flake" pitched as a company-scale problem | Launch HN: DeploySentinel (YC S22), 56 pts — https://news.ycombinator.com/item?id=32319404 |
| "Playwright users — wants design partner to shape an AI tool that tames flaky tests" | Show HN — https://news.ycombinator.com/item?id=44749059 |
| Flaky-test detection is a named feature in a 380★ CI reporter | ctrf-io/github-test-reporter — https://github.com/ctrf-io/github-test-reporter |
| Multiple small OSS attempts, none dominant (8,7,7★) | WithSecureOpenSource/flaky-tests-detection; buildpulse/buildpulse-action; test-flare/pytest-flakefighters |
| CI-log/failure analyzers exist but are tiny (1–6★) — an unfilled commodity niche | https://api.github.com/search/repositories?q=ci+log+analyzer+failure |

**Read of the evidence:** the *high end* (paid SaaS, ML flaky detection) is
crowded (DeploySentinel, BuildPulse, Trunk). The *low end* — a deterministic,
offline, dependency-light CLI that a single engineer runs locally over a log or
a folder of logs — is served only by tiny abandoned projects. That is the gap.

## Why now
- CI is near-universal; logs are text and stream-able, so a local parser needs
  no integration, no credentials, no data egress.
- Teams increasingly resist piping CI logs (which may contain secrets) to a
  third-party SaaS — an **offline** tool is a compliance-friendly default.
- "AI flaky detection" is expensive and non-deterministic; a **deterministic
  first pass** (clustering + repeat-run comparison) is cheaper and auditable,
  and can feed an LLM later only when needed.

## Success metric
- **North star:** median time-to-triage a failing build drops from minutes of
  log-scrolling to **< 30 seconds**: run `citriage`, read the top cluster.
- **Leading indicators (measurable in-product):**
  1. On a folder of N runs of the same suite, the tool correctly flags a test
     that passes *some* runs and fails *others* as **flaky** (fixture-verified).
  2. Identical root causes collapse into **one cluster**, with a stable
     signature hash across runs.
  3. Output is **deterministic**: same input → byte-identical report.
- **Non-metric:** revenue. This is a training artifact, not a live offer.

## Acceptance for this brief (Module 1 gate)
- [x] Named user, problem, why-now, success metric.
- [x] Every market claim carries a real URL.
- [x] Scope decision deferred to Module 2 (`scope.md`).
