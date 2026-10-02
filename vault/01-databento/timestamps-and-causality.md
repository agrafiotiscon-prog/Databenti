# Timestamps, causality and latency

## What each timestamp is [doc]
- `ts_event`: when CME's matching engine received the event (tag 60). Taken from the exchange
  clock. **It can be non-monotonic.**
- Sending time = `ts_recv - ts_in_delta` (tag 52): when CME sent the packet.
- `ts_recv`: when Databento's capture server in Aurora received it. Hardware timestamps,
  4–10 ns precision, under 1 µs accuracy vs UTC. **Monotonic per symbol.**
  - Exceptions: records flagged `F_BAD_TS_RECV` (snapshots, legacy data).
- `ts_out` (live only): when the record left Databento's gateway.

## The causality rule
> A strategy may react to a record **no earlier than `ts_recv + feed_latency + decision_latency`**.
> Its order reaches the matching engine at **`decision_time + order_latency`**.
> Fills are evaluated against the market **at the arrival time**, not at decision time.

- `ts_recv` is a **best case**. It is the time a co-located box in Aurora saw the data.
  A retail bot sees it later.
- Databento quotes its live feed latency up to the application as **p90 about 590 µs over the
  internet, about 42 µs on a cross-connect**. [doc] Add your own network and processing time.
- Retail order latency (bot → broker → CME): tens to hundreds of milliseconds, and it varies by
  broker API and route. **[assumption]** default 100 ms decision-to-exchange, stress-tested at
  250 ms and 500 ms. hftbacktest's docs suggest measuring real order latency by sending
  non-marketable orders.
- Bar features: a bar's values are known only **at the bar's close (`ts_recv` ≥ bar end)**.
  The earliest action is the bar close plus latency. *Signal on the bar's close and fill at
  that same bar's close* is the textbook lookahead bug.

## Practical checks (each becomes a test)
1. Every feature row carries `known_at` = the `ts_recv` of the last input record. The
   backtester asserts `order_time ≥ known_at + latency`.
2. Perturbation test: shuffle or alter data **after** time *t* and assert that features at *t*
   do not change.
3. Truncation test: features computed on data truncated at *t* equal the full-data features
   at *t*.
4. Never use `ts_event` to decide "known at". Never resample with right-labelled or centred
   windows. Pandas `resample` defaults (`label`/`closed`) must be set explicitly.
