# Order-Flow Imbalance Signal

OFI is computed as the signed sum of aggressor trade volume over a rolling
window, normalized by the rolling volatility of that flow. Combined with
top-of-book volume imbalance for a shorter-horizon stabilizer.

Thresholds:
- `take_threshold` — above this, cross the spread
- Quote widening scales with `|signal|` on the pressured side
