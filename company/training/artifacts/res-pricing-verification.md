# Competitive Pricing — Independent Re-Verification

**Verifier:** astra-mkt-researcher (Research dept, reports to astra-cro)
**Run timestamp (UTC):** 2026-11-13T12:14Z
**Method:** live HTTP (curl 8.14.1) from this runtime, browser User-Agent
(`Mozilla/5.0 … Chrome/120.0.0.0 Safari/537.36`), `-L --compressed`; HTML → visible
text via `python3` + `re` (script/style/svg stripped). Every number below was
fetched **this run** from each vendor's own live pricing page — none copied from the claim.
**Retry policy:** max 3 attempts per endpoint. **All 7 pages returned HTTP 200 on attempt 1.**

## Fetch log (raw HTTP evidence)

| # | Vendor | URL | HTTP | Bytes | sha256 |
|---|--------|-----|------|-------|--------|
| 1 | Synthesia | https://www.synthesia.io/pricing | 200 | 1,024,888 | `1134e040…ad7c2` |
| 2 | HeyGen | https://www.heygen.com/pricing | 200 | 900,098 | `139081c0…d62b7` |
| 3 | Runway | https://runwayml.com/pricing | 200 | 1,274,080 | `7957f586…9fd94` |
| 4 | invideo | https://invideo.io/pricing/ | 200 | 292,902 | `5dd725ce…4d5dc` |
| 5 | Pictory | https://pictory.ai/pricing/ | 200 | 409,284 | `4bcf5c20…f5293` |
| 6 | Descript | https://www.descript.com/pricing | 200 | 354,454 | `13b326ee…a9d8a` |
| 7 | VEED | https://www.veed.io/pricing | 200 | 137,280 | `e25fdf58…e15094` |

Visible-text sizes after tag stripping: synthesia 29,844 B · heygen 16,830 B · runway 6,585 B ·
invideo 7,836 B · pictory 17,319 B · descript 17,574 B · veed 5,719 B.

## Verification table

All observed prices are `[FACT]` (directly present in the page text); billing-unit
interpretations are `[INFERENCE]`.

| Vendor | Claimed price | Observed price(s) | Billing unit | Source URL | HTTP | Match? |
|---|---|---|---|---|---|---|
| **Synthesia** | Starter $14/mo ($168/yr billed yearly; $19/mo monthly) | `Starter $14 /mo $168 /yr, billed yearly`; monthly view `Starter $9 /mo first month then $19 /mo billed monthly` | per user / month; annual billed yearly `[INFERENCE]` | https://www.synthesia.io/pricing | 200 | ✅ **PASS** |
| **Synthesia** | Pro $59/mo ($708/yr) | `Pro $59 /mo $708 /yr, billed yearly` | per user / month; annual billed yearly | https://www.synthesia.io/pricing | 200 | ✅ **PASS** |
| **HeyGen** | Creator $29/mo | `Creator $29 / mo` | per user / month | https://www.heygen.com/pricing | 200 | ✅ **PASS** |
| **HeyGen** | Pro $49/mo | `Pro Most Popular $49 / mo` | per user / month | https://www.heygen.com/pricing | 200 | ✅ **PASS** |
| **HeyGen** | Business $149/mo + $20/seat/mo | `Business $149 / mo … Add team members for $20/seat/month`; FAQ: `Business plan costs $149/month plus $20/seat/month` | per user / month + per seat / month | https://www.heygen.com/pricing | 200 | ✅ **PASS** |
| **Runway** | Standard $12/mo | `Standard Billed annually. Save $36/year … $15 $12 /month` | per user / month (annual-billed) `[INFERENCE]` | https://runwayml.com/pricing | 200 | ✅ **PASS** |
| **Runway** | Pro $28/mo | `Pro Billed annually. Save $84/year … $35 $28 /month` | per user / month (annual-billed) | https://runwayml.com/pricing | 200 | ✅ **PASS** |
| **Runway** | Max $76/mo | `Max … Billed annually. Save $228/year … $95 $76 /month` | per user / month (annual-billed) | https://runwayml.com/pricing | 200 | ✅ **PASS** |
| **Runway** | 625 credits/mo | `$12 /month 625 credits /mo`; `625 credits monthly = 52s of Gen-4.5, 104s of Gen-4 Turbo` | credits / month (Standard) | https://runwayml.com/pricing | 200 | ✅ **PASS** |
| **Runway** | credits meter Gen-4.5 / Gen-4 Turbo | `Gen-4.5 60 credits/5s`; `Gen-4 Turbo` present; `Gen-4.5 … Gen-4.5 Nano Banana Pro and more` | credits per generation | https://runwayml.com/pricing | 200 | ✅ **PASS** |
| **invideo** | Starter $20/seat/mo monthly ($10/seat annual) | `$20 $10 per seat/mo, billed annually`; comparison: `Starter $20 a seat`; annual view `Annual Starter $10 per seat/mo, billed annually` | per seat / month | https://invideo.io/pricing/ | 200 | ✅ **PASS** |
| **Pictory** | Starter $25/mo annual ($29 monthly) | `Starter $25 Was $29  $29 per month, billed annually  per month, billed monthly`; comparison: `Starter $25 /month … billed annually` | per user / month | https://pictory.ai/pricing/ | 200 | ✅ **PASS** |
| **Descript** | Hobbyist $16/mo | visible: `Hobbyist $ 16 $ 24 per person / month`; data: `"name":"Hobbyist","annualAmount":16,"monthlyAmount":24` | per person / month (annual) `[INFERENCE]` | https://www.descript.com/pricing | 200 | ✅ **PASS** |
| **Descript** | Creator $24/mo | visible: `Creator $ 24 $ 35 per person / month`; data: `"name":"Creator","annualAmount":24,"monthlyAmount":35` | per person / month (annual) | https://www.descript.com/pricing | 200 | ✅ **PASS** |
| **Descript** | Business $50/mo | visible: `Business $ 50 $ 65 per person / month`; data: `"name":"Business","annualAmount":50,"monthlyAmount":65` | per person / month (annual) | https://www.descript.com/pricing | 200 | ✅ **PASS** |
| **VEED** | claim: prices could NOT be extracted (JS-rendered) | **No numeric price present in served HTML.** 0 `$` characters in the 137,280 B document; no `[$€£]`+digit pattern; `__NEXT_DATA__` JSON (47,880 B) contains only i18n placeholders (`"annualPricingSubText":"Billed {annualPrice} yearly, per user"`, `"saveBadge":"Save {discountAmount}%"`). Re-fetch (attempt 2, independent) identical: 200, 137,270 B, 0 `$`. | **inaccessible without JS** — `[FACT]` that served HTML has no prices; `[UNKNOWN]` the actual price values | https://www.veed.io/pricing | 200 | ✅ **PASS** (claim confirmed) |

**Result: 7/7 vendors PASS.** Every checkable claimed number reproduced exactly, and
the VEED "not extractable" claim is confirmed with evidence.

## Exact quoted surrounding text (primary-source extracts)

- **Synthesia — annual card:** `…Starter 3 months free $19 $14 per month $168 billed yearly 15,000 credits / year…` and `…Pro Most popular 4 months free $89 $59 per month $708 billed yearly 72,000 credits / year…`; comparison table `…Starter $14 /mo $168 /yr, billed yearly… Pro $59 /mo $708 /yr, billed yearly…`; monthly view `…Starter $9 /mo first month then $19 /mo billed monthly…`.
- **HeyGen:** `…Monthly Yearly 2 months free Creator $29 / mo…`, `…Pro Most Popular $49 / mo…`, `…Business $149 / mo Secure, scalable video creation for teams and businesses… Add team members for $20/seat/month…`; FAQ: `…the Creator plan costs $29/month (or $24/month if you pay annually)… Pro starts at $49/month… Business plan costs $149/month plus $20/seat/month.`
- **Runway:** `…Standard Billed annually. Save $36/year. … $15 $12 /month 625 credits /mo 625 credits monthly = 52s of Gen-4.5, 104s of Gen-4 Turbo…`; `…Pro … $35 $28 /month 2250 credits /mo…`; `…Max … Save $228/year … $95 $76 /month 9500 credits /mo…`; monthly comparison row `…Standard $15/month … Pro $28/month … Max $76/month…` (annual column `$12/$28/$76`).
- **invideo:** `…Starter 50% off … $20 $10 per seat/mo, billed annually … Save $120 per seat compared to monthly…`; `…Annual Starter $10 per seat/mo, billed annually…`; `…including Starter at $20 a seat.`
- **Pictory:** `…Starter $25 Was $29 $29 per month, billed annually per month, billed monthly Buy now…`; `…Professional Black Friday Offer $29.50 Was $59 $59 per month, billed annually…`; `…Teams $119 Was $199 $199 per month, billed annually…`.
- **Descript:** `…Hobbyist $ 16 $ 24 per person / month… Creator $ 24 $ 35 per person / month… Business $ 50 $ 65 per person / month…`; embedded data `{"_id":"plan-hobbyist","annualAmount":16,…,"monthlyAmount":24,"name":"Hobbyist"}` (Creator 24/35, Business 50/65).
- **VEED:** visible text contains plan names and FAQs but **no prices**; served HTML has zero `$`; `__NEXT_DATA__` has only i18n templates. Prices are injected client-side after hydration.

## Discrepancies & unknowns

1. **Billing-unit ambiguity (not a price mismatch, but a labeling risk).** Runway, Descript,
   invideo and Pictory list **monthly** (non-annual) prices that are **higher** than the
   claimed/observed annual-billed figures:
   - Runway monthly $15 / $35 / $95 vs annual-billed $12 / $28 / $76. `[FACT]`
   - Descript monthly $24 / $35 / $65 vs annual $16 / $24 / $50. `[FACT]`
   - invideo monthly $20/seat vs annual $10/seat. `[FACT]`
   - Pictory Starter monthly $29 vs annual $25. `[FACT]`
   The scan's numbers are the **annual-billed** figures; the artifact should always state
   the billing unit to avoid mis-citing a monthly price. `[INFERENCE]`
2. **Active promotions on the run date (2026-11-13).** Pictory shows a "Black Friday Offer"
   banner (Professional $29.50 promo vs $59 list; Starter "Was $29" → $25); invideo shows a
   "50% off" / "50% discount" annual banner; Synthesia shows a first-month promo ($9 Starter /
   $49 Pro). Promo prices are time-limited and may differ on a future run. `[FACT]`
3. **HeyGen annual:** Creator annual is **$24/mo** (`$29/month (or $24/month if you pay annually)`).
   The claim did not specify annual, so no mismatch — but note it. Also the `~~$29/mo~~ Free`
   text near "Professional Voice Clone" is an **add-on** promo, not a plan price. `[FACT]`
4. **VEED — inaccessible without JavaScript.** The claimed "prices could NOT be extracted"
   is **CONFIRMED**: HTTP 200 but zero currency figures in the served HTML/`__NEXT_DATA__`,
   reproduced across two independent fetches. Actual VEED plan prices remain `[UNKNOWN]`
   from static HTTP; a headless-JS fetch would be required (out of scope for this curl method).
5. **Currency/region.** Synthesia, VEED and others state prices are shown in local currency
   (USD fallback). All figures above are the **USD** default observed from this runtime's
   geolocation; other regions may see different amounts. `[UNKNOWN]`
6. **No fabricated values:** every observed figure is quoted from the fetched page text; no
   price was inferred where the page did not state one (VEED left `[UNKNOWN]`).
