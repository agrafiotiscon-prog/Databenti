"""Order-flow features (Phase 2). Spec: vault/03-order-flow/feature-definitions.md

Conventions shared by every feature:
  * input = one CME session of one contract, records in Databento file order,
    indexed by ts_recv (UTC);
  * every output row carries `known_at` -- the earliest time the value could be
    known live; bar features are known at the bar's end (left-closed bars);
  * no output may depend on input with ts_recv >= known_at (tests enforce this).
"""
