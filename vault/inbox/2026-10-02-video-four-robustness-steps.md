---
type: source
source: video transcript pasted by the user (author/channel not given)
received: 2026-10-02
status: processed
tags: [robustness, monte-carlo, clustering, walk-forward]
---
# Video: four robustness steps before deploying an automated strategy

## Summary (in our words)
1. **Parameter stability test** shown as a heatmap. An overfit strategy shows an isolated hot
   spot. Robust parameters show a broad, stable region.
2. **Monte Carlo on every parameter set**, not only on the chosen one. The video calls MC on a
   single set "completely wrong".
3. **Meta-analysis of all those results by cluster analysis.**
4. **In-sample / out-of-sample testing plus walk-forward validation.** The video then claims
   that if everything checks out, the strategy is ready to go live.

## Assessment
- Steps 1, 2 and 4 agree with the literature already in the vault. Step 2 adds something we did
  not have: **MC across the whole grid, with selection based on MC percentiles.**
- Step 3 matches **López de Prado & Lewis (2019)**: clustering the trials gives the *effective*
  number of independent trials for the Deflated Sharpe, and it finds plateaus or regions rather
  than single points.
- The claim that you are "good to deploy live" afterwards is **too strong**. These steps cannot
  detect lookahead bias, optimistic fills or under-stated costs, and the strategy still needs a
  holdout and paper trading.

## Where it went in the vault
- [methodology §6 heatmap, §6b Monte Carlo, §6c clusters, gates G9–G11](../05-anti-overfitting/methodology.md)
- [research loop: MC and clustering run on every trial batch](../05-anti-overfitting/research-loop.md)
- [decision D-011](../_memory/decisions.md)
