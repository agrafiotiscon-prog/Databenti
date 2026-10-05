---
type: result
date: 2026-10-04
tags: [R9, combined-book, 100k, realism, descriptive]
---
# Trend252 + H-030 book on $100k, whole contracts, 2020-10..2025-09 (user question; descriptive)

Weights = the average effective weights of the 15%-vol risk-balanced book over these 5 years (trend 0.76x, H-030
6.49x of the $1M sleeve definitions), applied to $100k with **integer contracts** and realistic costs.

| | 5-year total | per year | vol | Sharpe | max DD |
|---|---|---|---|---|---|
| trend252 sleeve | −$4,212 | −0.8% | 1.8% | −0.45 | −4.8% |
| H-030 month-end sleeve (~1 ZT, 2 ZF, 1 ZN, 1 ZB for 3 days a month) | +$24,426 | +4.7% | 10.4% | 0.46 | −10.3% |
| **book** | **+$20,214** | **+3.9%** | 10.7% | 0.37 | −12.6% |

By year (book, $): 2020 (Oct-Dec) −2,154 · 2021 −3,170 · 2022 +6,775 · 2023 +1,395 · 2024 +5,565 · 2025 (to Sep) +11,803.

**Why so much lower than the $1M/fractional numbers (7.6%/yr over the same 5 years with fractional contracts):**
at $76k of trend capital spread over 26 markets most targets round to **zero contracts** (2023: no trend position at
all), so the diversified trend sleeve - the part that needs many small positions - cannot be run at $100k with full-size
futures. The H-030 sleeve works at $100k because it only needs a handful of Treasury contracts.
Fix to investigate: CME micro contracts (R9.8). Data ends 2025-09; this is in-sample for both sleeves.

## With CME micro contracts (R9.8, same day)
Micros (1/10 size; SIL 1/5) for equity indices, metals, CL/NG and FX, $0.62/side fees [assumption for non-MES micros];
rates/grains/livestock stay full size. Same weights, $100k, 2020-10..2025-09:

| | 5-year total | per year | Sharpe | max DD |
|---|---|---|---|---|
| trend252 (full-size) | −$3,634 | −0.7% | −0.37 | −5.3% |
| trend252 (micros) | +$4,446 | +0.9% | 0.12 | −12.6% |
| H-030 | +$24,426 | +4.7% | 0.46 | −10.3% |
| **book with micros** | **+$28,872** | **+5.6%** | 0.44 | −16.4% |

By year ($k): 2020 (Q4) +2.0 · 2021 −2.9 · 2022 +12.5 · 2023 +0.4 · 2024 +10.7 · 2025 (to Sep) +6.3.
2013-06..2025-09 with micros: 10.2%/yr, Sharpe 0.82 (in-sample; MCL/MHG/MNG launched ~2021 [assumption], MES etc.
2019, so the pre-2019 part is optimistic). Micros fix the sizing problem; the remaining gap is that trend itself
was weak in 2021-2025 (it earns in big trending years: 2014, 2020, 2022).

## Book v2 on $100k (2026-10-05, routine; descriptive, in-sample for H-030; H-044/H-045 rules fixed from papers)
Book v2 weights (D-073: H-030 4.10x, H-044 1.84x, H-045 3.58x of the $1M sleeve definitions) at $100k, 2020-10..2025-09,
**contracts rounded honestly (zero allowed)**, 1 tick + fees per side; FX on micros (M6E, MJY, M6B, M6A, MCD, MSF; $0.62/side).

| sleeve | contracts per window | 5-year total | per year | Sharpe |
|---|---|---|---|---|
| H-030 month-end (ZT rounds to 0) | 0 ZT, 1 ZF, 1 ZN, 1 ZB | +$18,995 | +3.8% | 0.41 |
| H-044 FOMC Treasuries at weight | **0 (each $46k target < 1 contract)** | $0 | 0% | – |
| H-044 as 1 ZN per FOMC window (≈ the sleeve's total size, ~$125k) | 1 ZN, 40 windows | +$5,382 | +1.1% | 0.42 |
| H-045 short USD on FOMC days (micros) | 3-6 micros per currency | +$11,345 | +2.3% | 0.51 |
| **H-030 + H-044 (1 ZN) + H-045** | | **+$35,723** | **+7.1%** | **0.63** (max DD −12.2%) |

By year ($): 2020 (Q4) +1,184 · 2021 −3,688 · 2022 +7,346 · 2023 +14,433 · 2024 +11,869 · 2025 (to Sep) +4,578.
Adding the trend sleeve on micros at the v2 weight (0.57 vs 0.76 above) would add roughly +0.7%/yr [inferred: scaled
from the micros row above; integer rounding makes this approximate] → **~7.8%/yr on $100k**, vs 5.6%/yr for book v1.
The binding constraint at $100k is contract size in Treasuries (no micro Treasury futures with the same contracts;
CME's Micro 10-Year Yield futures are a different, yield-quoted product not in our data).
