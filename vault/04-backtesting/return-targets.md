---
type: topic
tags: [backtesting, targets, D-048]
updated: 2026-10-03
---
# Return targets: what "15% a year" means here (D-048)

The user asked for strategies that make **about 15% a year** (session 6, after seeing H-007's
~1-2%/yr on $100k). A return figure alone is meaningless for futures, because return scales with
leverage: one ES contract on $100k is ~3x the account. So every candidate is now reported as
**annualised net return at a fixed 15% volatility target**, which equals 15% x Sharpe ratio.

| Net Sharpe | Return at 15% vol | Worst year you should expect (rough, ~2 sd) |
|---|---|---|
| 0.3 | 4.5% | −25% |
| 0.5 | 7.5% | −22% |
| 1.0 | **15%** (user target) | −15% |
| 1.5 | 22% | −8% |

How hard is Sharpe 1.0 after costs? [inferred from public indices; assumption-level precision]
- Diversified trend-following (SG Trend index) earned roughly Sharpe 0.3-0.5 over 2010-2024 after fees;
  published long-run back-tests (Hurst, Ooi & Pedersen 2017) show ~0.7-1.0 over a century, gross.
- Single-market calendar effects (H-005..H-019) are idle >90% of the time: even H-007 at Sharpe ~0.5
  per unit of time-in-market would need very high leverage during events to reach 15%/yr - not acceptable.
- Sharpe > 1.5 on daily bars after costs is a red flag for lookahead or leakage (ROUTINE.md).

Route chosen (D-048): **diversify** - many markets (26 CME futures, 7 sectors) and independent,
published premia (trend, carry), each weak alone. Portfolio Sharpe grows roughly with the square root
of the number of independent bets. First test: [H-022](../results/h022-report.md).
