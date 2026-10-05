---
type: topic
tags: [research-ideas, R9, mechanism-first]
updated: 2026-10-04
---
# Next ideas (R9): mechanism first, testable on cached data ($0)

Written 2026-10-04 after R8 (H-024..H-028). Lessons that shape this list:
- Relative-value ranking on our thin 26-market universe failed twice (H-024, H-025; D-054).
- Most equity calendar effects are equity drift once a placebo is applied (G12; H-012, H-015..H-021, H-027).
- The ideas that survived longest have a **mechanical, non-discretionary payer** (index funds, dealers,
  hedgers forced to trade on a schedule), not a behavioural story.

So R9 prefers **forced, scheduled flows** in markets other than equities. Each needs a registry entry
before any result, a coverage check (D-042) and a placebo (G12).

## 1. H-029 Front-running the commodity index roll (Goldman / BCOM roll)
- **Mechanism:** commodity index funds (S&P GSCI, Bloomberg Commodity Index) roll their front-month
  futures into the next contract on fixed business days (GSCI: 5th-9th business day of the month).
  The roll is public and price-insensitive, so the near-far spread moves against the rollers before and during
  the roll window. **Payer:** passive index investors. [paper] Mou (2011, "Limits to arbitrage and commodity
  index investment: front-running the Goldman roll", Columbia WP): large profits 2000-2010, shrinking as
  capital entered. [paper] Bessembinder, Carrion, Tuttle & Venkataraman (2016 JFE, "Liquidity, resiliency
  and market quality around predictable trades"): roll trades have small, temporary price impact - evidence
  that the edge is now small. Prior: low-moderate; post-2010 decay is likely.
- **Test:** near/far calendar spread (short near, long far) on the GSCI-weighted energy, metals, grains and
  livestock markets in our universe, entering N business days before the roll window and exiting at its end.
  Uses `portfolio.signals.near_far_returns` (both legs priced, no outright exposure). Spread costs: 2 legs.
- **Data:** cached daily v.0/v.1 ($0). Caveat: v.0/v.1 are volume-ranked, so near/far must come from the
  expiry order (already handled). Coverage check: roll months where both legs are known.

## 2. H-030 Treasury futures around month-end (index duration extension / cash needs)
- **Mechanism:** bond index funds benchmarked to the Bloomberg US Treasury / Aggregate index must extend
  duration at month-end when the index rebalances, buying long Treasuries in the last days of the month.
  [paper] Etula, Rinne, Suominen & Vaittinen (2020 RFS, "Dash for cash: monthly market impact of
  institutional liquidity needs"): systematic month-end price pressure from institutional cash needs, in
  equities and Treasuries. [inferred] The duration-extension flow is widely known among practitioners;
  evidence in futures is mostly practitioner notes. **Payer:** index-tracking bond funds. Prior: low-moderate.
- **Test:** long ZN/ZB (and ZF/ZT as a check) over the last k trading days of each month (k fixed, small
  space), placebo vs the same holding length on random non-month-end windows. Month-end coverage must be
  checked first (H-019 lesson: holiday half-days and rank shifts dropped months).
- **Data:** cached daily rates futures ($0).

## 3. H-031 Treasury auction cycle (Lou, Yan & Zhang 2013)
- **Mechanism:** primary dealers absorb large new Treasury supply at auctions and need compensation; yields
  rise (prices fall) in the days before auctions and recover after. **Payer:** the Treasury / dealers'
  inventory cost. [paper] Lou, Yan & Zhang (2013 RFS, "Anticipated and repeated shocks in liquid markets"):
  significant pre-auction price declines and post-auction recoveries, 1980-2008.
- **Test:** short ZN (or matching tenor) from t-k to the auction day, long from auction to t+k; placebo vs
  random days. **Blocker:** needs the auction calendar (TreasuryDirect publishes historical auction dates).
  Fetch it once into `config/` (no Databento cost) if network policy allows; otherwise park it.

## 4. Engineering E-1: G12 placebo in the tick-data runner
`scripts/run_hypothesis.py` (used by H-001, H-002, H-004, H-028) has no placebo, so those reports show
"G12 not measured". Add a random-timing placebo: same number of trades per day at random decision times,
same holds, same costs. Needed before any new tick-data idea.

## 5. Engineering E-2: forward paper-tracking skeleton (needs the user's OK to run)
A daily job that recomputes the trend252 targets from the latest daily bars and logs simulated fills.
Code can be written and tested on cached data at $0; running it forward needs a few cents a day of data
(R8.9, waiting for the user).

## Not chosen (and why)
- More trend variants (speeds, filters): the trend family was selected on this data (H-022/H-023); new
  variants would be snooping. Confirmation must come from forward data.
- VIX futures volatility risk premium: CFE data is not on GLBX.MDP3 (not in our dataset).
- More equity calendar effects: repeatedly explained by drift (G12).

## R13 (written 2026-10-05, after R9-R12)
Evidence so far: the only idea confirmed on unseen instruments is the Treasury month-end long (H-030/H-032). Equity
calendar effects reduce to drift; FX month-end (H-037) did not confirm; trend is weakly positive (H-041). So R13 tests
the month-end mechanism from angles that are *new predictions*, not re-fits of H-030.

### H-042 Treasury curve flattener into month-end (mechanism test)
- **Mechanism:** index duration extension buys duration, i.e. mostly the long end [inferred from H-030: the effect
  scales with duration, ZT 4 bp → ZB 27 bp]. A duration-neutral long ZB / short ZT (or long UB / short ZF) position
  over the same 3 days should then earn without outright rate exposure. A pass would show the effect is about
  *duration demand*, not a general bond rally - and give a sleeve uncorrelated with rate direction.
- **Test:** DV01-neutral spread (contract ratio from duration proxies fixed in advance), same window as H-030; confirmation
  pair (UB/TN vs ZF) fixed in the registry; placebo = random windows. $0 (data cached).
### H-043 Mid-month coupon reinvestment in Treasury futures
- **Mechanism:** Treasury coupons and principal are paid on the 15th and the last day of the month; index funds and
  holders reinvest the cash, which is a scheduled buyer around the 15th too [inferred; practitioner lore, no
  peer-reviewed futures study found - low prior]. H-030 covers month-end; the 15th is a separate, unseen date.
- **Test:** long ZN/ZB (+ TN/UB, all already cached) from 2 trading days before to the first trading day on/after the
  15th; placebo vs random mid-month windows; coverage of 15ths that are holidays/weekends. $0.
### E-3 Monthly paper-tracking summary
- `scripts/paper_summary.py`: from `research/paper/ledger.csv`, mark P&L per sleeve with costs, the risk-balanced book
  (combine.py weights from the descriptive history), and compare with the descriptive expectation; ROUTINE step 2b
  needs it on the first firing of each month (first due 2026-11-02).
