# Order Book Mechanics

The simulated LOB has standard price-time priority matching. Two order
types: limit (rests on the book) and market (crosses the spread).

Cancellations are supported but no modifications — a cancel+replace is
required for price or size changes. This matches the semantics of most
real-world matching engines.
