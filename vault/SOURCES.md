---
type: sources
tags: [sources]
updated: 2026-10-02
---
# Sources (accessed 2026-10-02)

## Databento (primary documentation)
- MBO schema: https://databento.com/docs/schemas-and-data-formats/mbo
- Trades schema: https://databento.com/docs/schemas-and-data-formats/trades
- MBP-1 / MBP-10 / TBBO / BBO / OHLCV / statistics / status / definitions: https://databento.com/docs/schemas-and-data-formats
- Common fields, enums, flags, side, action, prices, timestamps: https://databento.com/docs/standards-and-conventions/common-fields-enums-types
- MBO snapshots: https://databento.com/docs/standards-and-conventions/mbo-snapshot
- Symbology (continuous c/n/v, parent, resolve): https://databento.com/docs/standards-and-conventions/symbology
- CME Globex MDP 3.0 dataset notes: https://databento.com/docs/venues-and-datasets/glbx-mdp3
- Continuous contracts example: https://databento.com/docs/examples/symbology/continuous
- Futures trading hours via status schema: https://databento.com/docs/examples/futures/trading-hours
- Limit order book construction: https://databento.com/docs/examples/order-book/limit-order-book
- Queue position of an order: https://databento.com/docs/examples/order-book/queue-position
- Execution slippage and markouts: https://databento.com/docs/examples/algo-trading/execution-slippage
- High-frequency liquidity-taking strategy: https://databento.com/docs/examples/algo-trading/high-frequency
- Matching engine latencies: https://databento.com/docs/examples/algo-trading/latency
- Timestamping guide: https://databento.com/docs/architecture/timestamping-guide
- Usage pricing and credits: https://databento.com/docs/faqs/usage-pricing-and-data-credits
- Streaming vs batch: https://databento.com/docs/faqs/streaming-vs-batch-download
- MBP-1 vs TBBO vs BBO: https://databento.com/docs/faqs/difference-between-mbp-and-tbbo
- Pricing and plans: https://databento.com/pricing
- CME matching algorithms explained: https://databento.com/blog/cme-matching-algorithms-explained

## CME, brokers, market structure
- IBKR CME exchange-fee pass-through (ES $1.385, MES $0.352): https://www.interactivebrokers.ca/en/accounts/fees/CME.php
- IBKR futures commissions ($0.85 standard, $0.25 micro, ≤1,000/mo): https://www.interactivebrokers.ca/en/pricing/commissions-futures.php
- CME fee changes effective 2026-10-01 (SER #9799, not fetched): https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2026/08/ser-9799.pdf
- CME 15:15–15:30 halt removal (2021-06-28): https://ampfutures.com/news/cme-equity-index-products-trading-halt-between-315-and-330-pm-removed
- CME MBO FAQ (iceberg OrderID behaviour): https://www.cmegroup.com/articles/faqs/market-by-order-mbo.html
- ES roll convention: https://crosstrade.io/learn/futures-trading/contract-rollover
- Margins (2026 search): https://www.tradestation.com/?p=42775 ; https://nexusfi.com/a/brokers/futures-margin-requirements

## Backtesting engines
- hftbacktest Level-3 backtesting: https://hftbacktest.readthedocs.io/en/latest/tutorials/Level-3%20Backtesting.html
- hftbacktest order fill: https://hftbacktest.readthedocs.io/en/latest/order_fill.html
- hftbacktest latency models: https://hftbacktest.readthedocs.io/en/latest/latency_models.html
- NautilusTrader Databento integration: https://nautilustrader.io/docs/latest/integrations/databento
- NautilusTrader fill models: https://nautilustrader.io/docs/nightly/concepts/backtesting/fill-models/

## Research papers
- Cont, Kukanov, Stoikov (2014), The Price Impact of Order Book Events: https://arxiv.org/abs/1011.6402
- Kolm, Turiel, Westray, Deep Order Flow Imbalance: https://papers.ssrn.com/abstract=3900141
- Cont, Cucuringu, Zhang, Cross-impact of order flow imbalance: https://arxiv.org/abs/2112.13213
- Zotikov, Antonov (2019), CME Iceberg Order Detection and Prediction: https://arxiv.org/abs/1909.09495
- Spoofing detection: https://arxiv.org/abs/2009.14818 ; https://arxiv.org/abs/2504.15908
- Barber, Lee, Liu, Odean, Do Day Traders Rationally Learn…/Day trading skill: https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf
- Chague, De-Losso, Giovannetti, Day Trading for a Living?: https://econpapers.repec.org/RePEc:fgv:eesptd:525
- Kirilenko et al. / CFTC HFT profits in E-mini (summary): https://www.bloomberg.com/news/articles/2012-12-04/high-frequency-traders-seen-profiting-at-small-firm-expense-1-
- Bailey, López de Prado (2014), The Deflated Sharpe Ratio: https://papers.ssrn.com/abstract=2460551
- Bailey, Borwein, López de Prado, Zhu, The Probability of Backtest Overfitting: https://papers.ssrn.com/abstract=2326253
- Harvey, Liu, Zhu, …and the Cross-Section of Expected Returns: https://papers.ssrn.com/abstract=2513152
- Harvey, Liu, Backtesting: https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF
- Purged cross-validation: https://en.wikipedia.org/wiki/Purged_cross-validation
