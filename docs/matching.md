# Matching Algorithm

On incoming orders:

1. If limit order, check for crossing levels on the opposite side.
2. Match at the resting order's price, FIFO within the level.
3. Remainder rests on the book at its submitted price.
4. Market orders fully execute against the best available price, walking
   the book as needed. Unfilled remainder is cancelled.
