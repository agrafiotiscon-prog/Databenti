# What the evidence says about order flow (read this before getting excited)

## 1. Order flow explains price changes *contemporaneously*
**Cont, Kukanov and Stoikov (2014)**, *The Price Impact of Order Book Events*, J. Fin.
Econometrics. Over short intervals, price changes are mainly driven by **order flow imbalance
(OFI)** at the best bid and ask. The relation is linear, with slope inversely proportional to
depth, and robust across stocks and time scales. [paper]
→ This is *explanation*, not *prediction*. Knowing OFI over the same 10 s as the price change
does not let you trade it.

## 2. Predictive power exists, but at very short horizons
- **Kolm, Turiel and Westray (2021/2023)**, *Deep Order Flow Imbalance*. They studied 115
  Nasdaq stocks with neural networks. Models fed with **order flow** (stationary inputs) beat
  models fed raw book states. Forecast accuracy **peaks at about two price changes ahead and
  then decays**. [paper]
- Multi-level OFI (deeper levels, combined via PCA) improves both in-sample and out-of-sample
  fit (Cont, Cucuringu and Zhang, *Cross-impact of order flow imbalance*). [paper]
→ The exploitable horizon is **seconds**. That is the domain of co-located firms with
microsecond latency. **At 100 ms+ retail latency, much of that edge is gone before our order
arrives.** Our latency stress tests exist to show exactly this.

## 3. Who makes money in ES
- CFTC-linked studies of E-mini S&P 500 audit-trail data (Kirilenko et al.; Baron, Brogaard,
  Hagströmer and Kirilenko): **aggressive HFTs earned the most**, and per contract they earned
  more from trading against **small traders** than against institutions (reported at about $3.49
  vs $1.92 per contract). [paper and press summaries]
- Retail day-trader outcomes:
  - **Taiwan** (Barber, Lee, Liu, Odean): more than 80% lose, and **under 1% are predictably
    profitable**. [paper]
  - **Brazil mini-index futures** (Chague, De-Losso, Giovannetti): among people who day traded
    at least 300 days, **97% lost money**, only 0.4% earned more than a bank teller, and there
    was **no evidence of learning**. Mini-index futures are a close analogue of ES/MES.
    [paper]
→ The **prior** probability that a retail-latency, rule-based order-flow strategy is profitable
after costs is **low**. The system should be built to deliver a cheap, trustworthy "no" and to
recognise a rare "yes".

## 4. Hidden liquidity
Zotikov and Antonov (2019), *CME Iceberg Order Detection and Prediction*: native icebergs are
about 4% of ES volume, with a median total size of 6 lots. Total size is predictable using
Kaplan–Meier survival estimates (they report about 90% accuracy for native icebergs on their
metric). [paper] → Iceberg detection is feasible from Databento MBO. Whether it *predicts price*
is an open question for us to test.

## 5. Spoofing
Detection research (e.g. arXiv 2009.14818, 2504.15908) treats spoofing as large orders away from
the touch, cancelled before execution. One recent study flags a large share of big orders as
*potentially* spoof-capable. [paper] → "Spoof-like" is a noisy label. Using it as a predictive
feature needs proper testing, like any other hypothesis.

## 6. Practitioner concepts with no rigorous public evidence
Footprint "absorption", stacked imbalances, POC and value-area "magnets", delta divergence.
They may encode real mechanisms (inventory pressure, liquidity provision at levels, VWAP as an
institutional execution benchmark), but **nothing peer-reviewed shows they survive costs**.
Treat each one as a **hypothesis** with a stated mechanism, and test it exactly like any other.

## 7. What this suggests for hypothesis selection
- Prefer horizons of **minutes, not seconds**, where 100 ms latency is a smaller share of the
  move and the cost of about 1.4 ticks is small relative to the target.
- Prefer **event-conditioned** setups: rare, high-information moments such as liquidity events at
  key levels or failed auctions. Avoid continuously-on signals that trade hundreds of times a day.
- Use order flow as a **filter or confirmation** on a structural setup, not as standalone
  sub-second alpha.
- Pre-register every hypothesis (mechanism, direction, horizon) **before** looking at results.
