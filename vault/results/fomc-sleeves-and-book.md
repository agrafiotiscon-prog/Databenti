---
type: result
date: 2026-10-05
tags: [R15, H-044, H-045, fomc, combined-book, descriptive]
---
# FOMC sleeves (H-044 rates, H-045 FX) and the combined book

## The two tests (pre-registered, fixed rules from published papers, one evaluation each, 2010-06..2025-09)
| | H-044 [report](h044-report.md) | H-045 [report](h045-report.md) |
|---|---|---|
| Source | Hillenbrand (2025 RFS): the 1989-2017 decline in long yields happened in 3-day FOMC windows [paper] | Mueller, Tahbaz-Salehi & Vedolin (2017 JF): short-USD earns on FOMC days [paper] |
| Rule | long ZT/ZF/ZN/ZB/TN/UB, close F-2 → close F+1 | long 6E/6J/6B/6A/6C/6S/6N/6M (= short USD), close F-1 → close F |
| Windows | 687 market-windows (122 meetings) | 976 (122 meetings) |
| Net (base / stress) | +$256k / +$207k on 6 x $250k | +$111k / +$88k on 8 x $125k |
| Per-window t / drift-neutral t | 3.63 / 4.62 | 3.44 / 4.08 |
| Placebo p (1,000 random windows) | 0.002 | 0.000 |
| Without month-end overlap (H-030) | t 2.28 (37% of windows overlap) | t 4.38 |
| Years > 0 | 11/16 | 12/16 |
| Paper sample vs post-sample | ≤2017: t 1.63, 14 bp; **>2017: t 3.60, 23 bp** | **≤2014: t −0.95, −4.7 bp**; >2014: t 5.09, 16 bp |
| Verdict | **CONFIRMS** (D-071) | **CONFIRMS**, with a caveat (D-072) |

## Skeptic's checks (after the fact; reported, not used to decide)
- **Tails:** removing the 5 best and the 5 worst meetings keeps +$221k (H-044) and +$98k (H-045). Removing only the top 10
  wipes both out - event P&L is fat-tailed (the median meeting is positive: $2.8k / $1.5k; hit rate 60% / 53%).
- **Timing:** the FOMC calendar is published a year ahead; entries are at closes before the 14:00 ET statement. No lookahead found.
- **Duration pattern (H-044):** ZT 3 bp → ZF 9 → ZN 15 → TN 23 → ZB 29 → UB 35 bp per window, the same monotone pattern as
  H-030 - consistent with a rate-expectations / term-premium mechanism, not noise.
- **H-045 caveat:** the effect was negative in 2010-2014, which overlaps the paper's own sample (it ends ~2013). The paper's
  effect may sit pre-2010, and the post-2015 profit (hiking/easing cycles) could be a different regime. Weaker than H-044.
- **Correlations (daily P&L):** H-044 vs H-045 0.29, vs H-030 0.12 / 0.02, vs trend ~0. Both FOMC sleeves are bets on
  "dovish relative to expectations" and will lose together on hawkish surprises (2022-09, 2024-12).

## Combined book - DESCRIPTIVE (hindsight weights; costs included; causal ERC weights, 2.5x leverage cap)
| Book | ann. return | vol | Sharpe | max DD | last 5 y return / Sharpe |
|---|---|---|---|---|---|
| trend252 + H-030 (current paper book) | 5.8% | 6.6% | 0.88 | −10% | 3.2% / 0.54 |
| **+ H-044 + H-045** | 8.6% | 8.9% | **0.96** | −10% | 6.6% / 0.74 |
| all five (+ H-035 watch sleeve, not confirmed) | 11.6% | 10.3% | 1.13 | −10% | 7.8% / 0.78 |
| H-030 + H-044 + H-045 (no trend) | 6.2% | 7.7% | 0.81 | −11% | 5.6% / 0.67 |

Scaled to the 15% vol target (D-048), Sharpe 0.96 ≈ **14%/yr** (last 5 y: ~11%/yr). Hindsight upper bound: the weights
and trend252 were chosen on this data; H-044/H-045 were not (rules fixed from the papers). By year (+H-044+H-045, %):
2011 33.9, 2012 −2.0, 2013 2.8, 2014 4.3, 2015 7.9, 2016 5.1, 2017 7.5, 2018 5.5, 2019 14.2, 2020 21.2, 2021 −4.8, 2022 12.8,
2023 11.5, 2024 12.5, 2025 (to Sep) −1.5.
Sleeve multipliers (last 5 y mean, ~9% vol): trend 0.34, H-030 2.43, H-044 1.09, H-045 2.12 → **book v2** in
`scripts/paper_summary.py`, scaled to 15% vol (D-073).

## Forward tracking
`scripts/paper_track.py` now logs sleeves `h044` (ZT/ZF/ZN/ZB) and `h045` (6 majors); TN/UB/6N/6M are not in the live
universe. FOMC calendar extended to 2027 (`config/fomc_dates.csv`). First forward windows: FOMC 2026-10-28
(H-044 enters at the close of 10-26) and 2026-12-09.
