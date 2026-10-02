# Costs, fees and slippage: the numbers that kill most order-flow strategies

## Fees per contract per side (retail, Interactive Brokers, read 2026-10)
| Component | ES | MES | Source |
|---|---|---|---|
| CME exchange fee (non-member) | **$1.385** | **$0.352** | IBKR CME fee pass-through table [doc] |
| NFA regulatory fee | $0.02 | $0.02 | broker fee pages [doc] |
| Broker commission (IBKR tiered, ≤1,000 contracts/mo) | $0.85 | $0.25 | IBKR futures commissions [doc] |
| **Total per side** | **$2.255** | **$0.622** | |
| **Round turn** | **$4.51** | **$1.24** | |
| Round turn in ticks | **0.36 tick** | **0.99 tick** | |

- Other brokers differ mainly in commission (and sometimes a separate clearing or platform fee).
  The exchange fee is the same for every non-member.
- **CME announced fee schedule changes effective 2026-10-01 (SER #9799).** The document could
  not be fetched here, so **verify current ES fees on your broker statement** and update
  `config/costs.yaml`.
- **Key insight:** in *tick* terms, MES fees are about **2.8× worse** than ES (1 tick vs 0.36
  tick per round turn). A small-edge order-flow strategy that works on ES may die on MES. ES
  needs about $22–24k of exchange maintenance margin per contract.

## Spread and slippage
- In RTH the ES spread is almost always **1 tick**. Displayed depth at the touch is usually far
  more than 1 lot, so a 1-lot market order *at the moment it arrives* fills at the touch.
  [inferred; to be measured from TBBO and MBP-1 per hour of day]
- The real slippage risk is **latency**: the touch moves between signal and arrival. Order-flow
  signals fire in *fast* markets, so slippage is **correlated with the signal**. A flat "+1 tick"
  can be too optimistic exactly when it matters.
  → **Measure it empirically:** for every signal, slippage = touch(signal_time + latency) −
  touch(signal_time), taken from TBBO/MBP-1. Report its distribution.
- Stop orders: when triggered they become market orders. In gaps (news, open) the fill is the
  next available price, not the stop price.
- ETH spreads and depth are worse than RTH. Report results by session.

## Break-even math (ES, 1 lot)
| Execution style | Cost vs mid per round turn |
|---|---|
| Market in, market out, no latency drift | 1 tick spread + 0.36 fees = **1.36 ticks ≈ $17** |
| Same, plus 1 tick adverse latency drift each side (conservative default) | **3.36 ticks ≈ $42** |
| Market in, passive limit out | 0.5 + 0.36 = 0.86 tick, **but** the exit fills only when traded through, and adverse selection applies |

> A strategy must earn more than about **1.4 ticks per trade, gross, on average**, before it pays
> anything else. Most published retail order-flow setups never report this number.

## Defaults (`config/costs.yaml`, Phase 3)
```yaml
ES:  {tick: 0.25, tick_value: 12.50, fee_per_side: 2.255, latency_ms: 100, extra_slippage_ticks: 0}
MES: {tick: 0.25, tick_value: 1.25,  fee_per_side: 0.622, latency_ms: 100, extra_slippage_ticks: 0}
```
Slippage comes from the latency model plus the book, **not** from a magic constant. Every report
is rerun at **1.5× and 2× fees** and **250 ms and 500 ms latency**. A strategy that only works
at 1× and 100 ms is not robust.
