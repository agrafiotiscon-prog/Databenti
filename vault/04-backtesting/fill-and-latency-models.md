---
type: topic
tags: [backtesting]
updated: 2026-10-02
---
# Fill and latency models

## Timeline of one order
```
event ts_recv ──(feed + decision latency)──▶ decision ──(order latency)──▶ arrival at CME ──▶ fill/queue
```
All fill logic is evaluated against the market **at arrival**, never at the decision or signal
time.

## Market orders (tier A: TBBO / MBP-1)
- Buy fills at the **ask at arrival**. Sell fills at the **bid at arrival**.
- If the order size exceeds the touch size, walk the book. With MBP-10, use the deeper levels.
  With L1 only, assume the next level is one tick worse for the excess. That is a conservative
  approximation, and our 1-lot default rarely needs it.
- Optional `extra_slippage_ticks` (default 0, because latency drift already captures most of it),
  stress-tested at +1.
- Stops become market orders when the **trade price** touches the stop at or after arrival, and
  then fill as above.

## Limit orders
| Mode | Rule | Data | Bias |
|---|---|---|---|
| `optimistic` (forbidden in reports) | Fill when the price touches the limit | any | badly optimistic |
| `trade_through` (**default for tier A**) | Fill only when a trade prints **strictly through** the limit (a buy fills only after a trade < limit) | trades | pessimistic for the fill *rate*, still subject to adverse selection |
| `queue_l1` | Our queue-ahead = displayed size at our price at arrival (from TBBO/MBP-1). It decreases with traded volume at that price and with cancels in front via `p_k(x)` (k ≈ −0.9). Fill when queue-ahead ≤ 0 and a trade prints at our price | TBBO/MBP-1/MBP-10 | moderate |
| `l3_fifo` (**tier B reference**) | Exact FIFO queue from MBO: we join behind every order present at arrival, and orders ahead leave by fill or cancel | MBO | most realistic, though our own order cannot impact the market |

**Calibration:** on the MBO window, run the same strategy under `trade_through`, `queue_l1` and
`l3_fifo`. Report the fill-rate and PnL differences. If tier-A results depend on fills that
`l3_fifo` would not give, the tier-A result is not trusted.

## Adverse selection (passive fills)
Databento's markout study (NVDA, MBP-1) found **passive fills are positive at first, because
they earn the spread, but turn negative after about 1 s**, due to adverse selection. [doc]
→ For every strategy, report **markout curves** of our own fills at +100 ms, 1 s, 10 s, 60 s and
5 min. Limit-entry strategies whose fills systematically get run over are not robust.

## Latency defaults [assumption]
| Component | Default | Stress |
|---|---|---|
| Feed (Databento live, internet) | 1 ms | 5 ms |
| Decision/compute | 5 ms | 50 ms |
| Order entry to CME (retail broker API) | 100 ms | 250 ms, 500 ms |
| Cancel/modify | same as entry | same |

A cancel only takes effect at arrival. **The order can fill while the cancel is in flight.** This
case must be simulated.

## Things no replay backtester can do (state in every report)
- **No market impact.** Our order does not change the replayed book. This is fine for 1–2 lots
  of ES in RTH, but not for size. [doc: hftbacktest]
- No reaction of other participants to our orders.
- Queue position for our own order is modelled, not observed.
- Exchange-side events (e.g. self-match prevention, price bands) are only approximated.

## Implementation status (session 6, routine R3.1)
- `backtest/engine.py`: L1 replay in file order, strategy callback gets one record at a time,
  orders arrive at `t + latency`, **market orders** fill at the worse of the last book before
  arrival and the first book at/after it (TBBO shows the book only just before each trade),
  1-contract position limit, conservative flatten at the end. `backtest/costs.py` reads
  `config/costs.toml`. Limit/stop orders, `trade_through`/`queue_l1`: R3.2.
- Null baseline on 2024-03-05 RTH (buy every 10 min, exit after 5 min): 39 trades, −2.95 ticks
  gross per trade (≈ −1.5 drift on a falling day, −1 spread, rest latency/conservatism), fees
  $4.51 per round trip exactly. Logged in `research/trials.jsonl` (family `engine-sanity`).
- R3.2: limit (marketable → taker at the worse book within the limit; resting → `trade_through`
  or `queue_l1`), stop (trade at/through → market at the worse of trigger and next book), cancel
  (effective strictly after its arrival; a same-instant trade fills first). `optimistic` is
  refused. Real-data check (join the bid every 10 min, 2024-03-05 RTH): fills 35/39
  `trade_through`, 36/39 `queue_l1`; −2.3 ticks/trade gross vs −2.95 for market entries
  (spread saved, adverse selection on a falling day).
