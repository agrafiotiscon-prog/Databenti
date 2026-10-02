# Metrics: exact definitions used in every report

Net PnL is always **after fees and modelled slippage**, in USD, for 1 contract unless stated.

| Metric | Definition |
|---|---|
| Trades | Count of round trips. **Flag if < 200.** |
| Win rate | Share of trades with net PnL > 0 |
| Avg trade | Mean net PnL per trade (USD and ticks). Also the median. |
| Profit factor | Σ winning net PnL / |Σ losing net PnL| |
| Daily PnL series | Net PnL per **trading date**, including **zero days** (days with no trades). |
| Sharpe (annualised) | mean(daily) / std(daily) × √252, computed on the daily series. Also report **Lo (2002)**-style autocorrelation-adjusted SR and the **Probabilistic SR** (PSR) vs 0. |
| Deflated Sharpe | DSR with N = **all logged trials** for the strategy family (see [methodology](../05-anti-overfitting/methodology.md)). |
| t-stat of mean trade | mean / (std/√n). **Target ≥ 3** (Harvey, Liu and Zhu multiple-testing hurdle). |
| Max drawdown | Max peak-to-trough of cumulative daily net PnL (USD), plus its duration in days. |
| Exposure | Share of RTH minutes in a position. |
| Concentration | Share of total PnL from the top 5 days and from the top 10% of days, and PnL after removing the best 5 days. **Flag if the best 5 days ≥ 50% of PnL or if removing them makes PnL ≤ 0.** |
| Breakdown | Per **year**, per **month**, per session (RTH/ETH), per weekday, per hour, per volatility tercile. |
| Cost stress | All of the above at fees ×1, ×1.5, ×2 and latency 100/250/500 ms. |
| Markouts | Mean mid-price move after our fills at +0.1/1/10/60/300 s. |
| Slippage | Distribution of arrival-vs-signal touch differences. |
