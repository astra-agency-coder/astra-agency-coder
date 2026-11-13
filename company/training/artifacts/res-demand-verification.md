# Demand-Signal Verification — AI-Video Market Study

**Verifier:** astra-mkt-researcher (Research dept, reports to astra-cro)
**Run timestamp (UTC):** 2026-11-13T12:13Z
**Method:** live HTTP (curl) from this runtime; all values fetched this run, not copied.
**Retry policy:** max 3 attempts per endpoint.

## Fetch log (raw HTTP evidence)

| # | Endpoint | HTTP code | Bytes | Note |
|---|----------|-----------|-------|------|
| 1 | `https://pypistats.org/api/packages/diffusers/recent` | 200 | 118 | Attempt 1 returned **429 RATE LIMIT EXCEEDED** (53 bytes); succeeded on retry with browser UA + backoff |
| 2 | `https://hn.algolia.com/api/v1/search?query=AI%20video%20generator&tags=story&hitsPerPage=1` | 200 | 1513 | — |
| 3 | `https://hn.algolia.com/api/v1/search?query=sora%20video&tags=story&hitsPerPage=1` | 200 | 3921 | — |
| 4 | `https://hn.algolia.com/api/v1/search?query=video%20generation%20model&tags=story&hitsPerPage=1` | 200 | 1512 | — |
| 5 | `https://hn.algolia.com/api/v1/search?query=text-to-video&tags=story&hitsPerPage=1` | 200 | 6600 | — |
| 6 | `https://www.synthesia.io/pricing` | 200 | 1,024,888 | Browser User-Agent; sha256 `1134e04004d13d896c6edda9279b9f5d5fec4fc444e9f9aef829fca9a62ad7c2` |

## Verification table

| Claim | Observed | Source URL | HTTP code | Label | Match? |
|---|---|---|---|---|---|
| diffusers `last_month` = 6,256,527 | `{"data":{"last_day":249549,"last_month":6256527,"last_week":1402679},"package":"diffusers","type":"recent_downloads"}` | https://pypistats.org/api/packages/diffusers/recent | 200 | [FACT] | yes |
| HN stories for "AI video generator" = 2023 | `nbHits: 2023` (top hit 2022-09-29 "Meta's new text-to-video AI generator is like DALL-E for video") | https://hn.algolia.com/api/v1/search?query=AI%20video%20generator&tags=story&hitsPerPage=1 | 200 | [FACT] | yes |
| HN stories for "sora video" = 710 | `nbHits: 710` (top hit 2024-02-15 "Sora: Creating video from text") | https://hn.algolia.com/api/v1/search?query=sora%20video&tags=story&hitsPerPage=1 | 200 | [FACT] | yes |
| HN stories for "video generation model" = 392 | `nbHits: 392` (top hit 2024-12-16 "Veo 2: Our video generation model") | https://hn.algolia.com/api/v1/search?query=video%20generation%20model&tags=story&hitsPerPage=1 | 200 | [FACT] | yes |
| HN stories for "text-to-video" = 173 | `nbHits: 173` (top hit 2026-01-22 "Show HN: Text-to-video model from scratch...") | https://hn.algolia.com/api/v1/search?query=text-to-video&tags=story&hitsPerPage=1 | 200 | [FACT] | yes |
| Synthesia "Trusted by 50,000+ teams" | Exact string present: `<div class="paragraph-small">Trusted by 50,000+ teams.</div>` (1 occurrence) | https://www.synthesia.io/pricing | 200 | [FACT] | yes |
| Synthesia "Join 2M+ users" | Exact string present: `Join 2M+ users today and start creating videos with AI avatars in 140+ languages.` (1 occurrence) | https://www.synthesia.io/pricing | 200 | [FACT] | yes |

## Exact quoted surrounding text (primary-source extracts)

- **pypistats / diffusers (full body):**
  `{"data":{"last_day":249549,"last_month":6256527,"last_week":1402679},"package":"diffusers","type":"recent_downloads"}`
  → `last_month = 6256527` exactly matches the claimed 6,256,527.

- **HN Algolia (raw `nbHits` fields):** `2023`, `710`, `392`, `173` for the four queries, respectively.

- **Synthesia — "50,000+ teams":**
  `…sticky-section-stars"/><div class="paragraph-small">Trusted by 50,000+ teams.</div>…`

- **Synthesia — "Join 2M+ users":**
  `…text-color-secondary">Join 2M+ users today and start creating videos with AI avatars in 140+ languages.</p>…`

- **Synthesia — related (context, NOT a study claim):**
  `Trusted by over 90% of Fortune 100 companies` — also present on the page.

## Per-claim verdict

- diffusers `last_month` — **PASS**
- HN "AI video generator" — **PASS**
- HN "sora video" — **PASS**
- HN "video generation model" — **PASS**
- HN "text-to-video" — **PASS**
- Synthesia "Trusted by 50,000+ teams" — **PASS**
- Synthesia "Join 2M+ users" — **PASS**

## Discrepancies & unknowns

**Discrepancies:** None. All seven claimed values were reproduced exactly from live primary sources this run.

**Unknowns / caveats (do not treat as verified facts):**
1. **[UNKNOWN] HN `nbHits` semantics.** Algolia's `nbHits` is a count of stories matching the query string under Algolia's relevance/tokenization; it is not a curated "market size" and changes as new stories are posted and as Algolia re-indexes. Values are a point-in-time snapshot (2026-11-13).
2. **[UNKNOWN] pypistats freshness/coverage.** `last_month` is PyPI download volume as tracked by the pypistats.org aggregator; it includes CI/mirror/bot traffic and does not equal human users. The endpoint is rate-limited (we hit a 429 on first contact), so an unauthenticated re-run may not reproduce immediately.
3. **[UNKNOWN] Synthesia self-reported marketing copy.** "Trusted by 50,000+ teams" and "Join 2M+ users" are the vendor's own promotional claims on its pricing page. We verified the *strings exist on the live page*; we did **not** independently validate the underlying numbers. Treat as vendor marketing, not audited data.
4. **[INFERENCE] Synthesia page is a JS-heavy marketing site.** The strings were found in the server-rendered HTML (verified via grep of the fetched bytes), so no headless-browser rendering was required. Content may still vary by geo/AB test.
5. **[UNKNOWN] Reproducibility window.** HTTP responses are volatile; byte sizes and hashes are recorded above for this run only and are expected to change over time.

## Reproduction commands

```bash
curl -sS -A "Mozilla/5.0 (X11; Linux x86_64) research-verification/1.0" \
  "https://pypistats.org/api/packages/diffusers/recent"
for q in "AI%20video%20generator" "sora%20video" "video%20generation%20model" "text-to-video"; do
  curl -sS "https://hn.algolia.com/api/v1/search?query=$q&tags=story&hitsPerPage=1"
done
curl -sS -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" \
  "https://www.synthesia.io/pricing"
```
