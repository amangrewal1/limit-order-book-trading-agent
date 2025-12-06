from collections import deque
from typing import List, Dict, Optional

from sortedcontainers import SortedDict

from .order import Order, Side, OrderType


class OrderBook:
    def __init__(self, tick_size: float = 0.01):
        self.tick_size = tick_size
        self.bids: SortedDict = SortedDict()
        self.asks: SortedDict = SortedDict()
        self.trades: List[tuple] = []
        self.time: int = 0

    def best_bid(self) -> Optional[float]:
        return self.bids.keys()[-1] if self.bids else None

    def best_ask(self) -> Optional[float]:
        return self.asks.keys()[0] if self.asks else None

    def mid(self) -> Optional[float]:
        b, a = self.best_bid(), self.best_ask()
        if b is None or a is None:
            return None
        return (b + a) / 2.0

    def spread(self) -> Optional[float]:
        b, a = self.best_bid(), self.best_ask()
        if b is None or a is None:
            return None
        return a - b

    def _side_volume(self, levels: int, side: Side) -> int:
        book = self.bids if side == Side.BUY else self.asks
        if not book:
            return 0
        keys = list(book.keys())
        chosen = keys[-levels:] if side == Side.BUY else keys[:levels]
        total = 0
        for p in chosen:
            for o in book[p]:
                total += o.size
        return total

    def bid_volume(self, levels: int = 1) -> int:
        return self._side_volume(levels, Side.BUY)

    def ask_volume(self, levels: int = 1) -> int:
        return self._side_volume(levels, Side.SELL)

    def imbalance(self, levels: int = 3) -> float:
        bv = self.bid_volume(levels)
        av = self.ask_volume(levels)
        total = bv + av
        return (bv - av) / total if total > 0 else 0.0

    def submit(self, order: Order) -> List[Dict]:
        self.time += 1
        order.timestamp = self.time
        fills = self._cross(order)
        if order.type == OrderType.LIMIT and order.size > 0:
            self._rest(order)
        return fills

    def _cross(self, taker: Order) -> List[Dict]:
        fills: List[Dict] = []
        if taker.side == Side.BUY:
            book = self.asks
            def acceptable(p):
                return taker.type == OrderType.MARKET or p <= taker.price
            def best_price():
                return book.keys()[0]
        else:
            book = self.bids
            def acceptable(p):
                return taker.type == OrderType.MARKET or p >= taker.price
            def best_price():
                return book.keys()[-1]

        while taker.size > 0 and book:
            p = best_price()
            if not acceptable(p):
                break
            queue = book[p]
            while queue and taker.size > 0:
                resting = queue[0]
                qty = min(taker.size, resting.size)
                fills.append({
                    "price": p,
                    "size": qty,
                    "aggressor": taker.agent_id,
                    "resting_agent": resting.agent_id,
                    "aggressor_side": taker.side,
                })
                self.trades.append((self.time, p, qty, taker.side))
                taker.size -= qty
                resting.size -= qty
                if resting.size == 0:
                    queue.popleft()
            if not queue:
                del book[p]
        return fills

    def _rest(self, order: Order) -> None:
        book = self.bids if order.side == Side.BUY else self.asks
        if order.price not in book:
            book[order.price] = deque()
        book[order.price].append(order)

    def cancel_agent(self, agent_id: str) -> None:
        for book in (self.bids, self.asks):
            for p in list(book.keys()):
                remaining = deque(o for o in book[p] if o.agent_id != agent_id)
                if remaining:
                    book[p] = remaining
                else:
                    del book[p]

    def snapshot(self, depth: int = 5) -> Dict:
        bids = []
        for p in list(self.bids.keys())[-depth:][::-1]:
            bids.append((p, sum(o.size for o in self.bids[p])))
        asks = []
        for p in list(self.asks.keys())[:depth]:
            asks.append((p, sum(o.size for o in self.asks[p])))
        return {"bids": bids, "asks": asks, "mid": self.mid(), "spread": self.spread()}
