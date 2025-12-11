import numpy as np
from collections import deque
from typing import Optional

from .order import Order, Side, OrderType


class PoissonFlow:
    def __init__(
        self,
        fair_value: float = 100.0,
        tick_size: float = 0.01,
        lambda_limit: float = 8.0,
        lambda_market: float = 0.9,
        lambda_cancel: float = 0.35,
        vol: float = 0.00025,
        drift: float = 0.0,
        size_mean: float = 3.0,
        offset_mean: float = 5.0,
        informed_prob: float = 0.08,
        seed: Optional[int] = None,
    ):
        self.fair_value = fair_value
        self.tick = tick_size
        self.lam_l = lambda_limit
        self.lam_m = lambda_market
        self.lam_c = lambda_cancel
        self.vol = vol
        self.drift = drift
        self.size_mean = size_mean
        self.offset_mean = offset_mean
        self.informed_prob = informed_prob
        self.rng = np.random.default_rng(seed)

    def round_price(self, p: float) -> float:
        return round(p / self.tick) * self.tick

    def _update_fair_value(self, dt: float):
        shock = self.vol * np.sqrt(dt) * self.rng.normal()
        self.fair_value *= np.exp(self.drift * dt + shock)

    def _informed_bias(self, book) -> float:
        mid = book.mid()
        if mid is None:
            return 0.0
        return np.tanh((self.fair_value - mid) / (self.tick * 5))

    def step(self, book, dt: float = 1.0):
        self._update_fair_value(dt)
        events = []

        n_limit = self.rng.poisson(self.lam_l * dt)
        for _ in range(n_limit):
            side = Side.BUY if self.rng.random() < 0.5 else Side.SELL
            size = max(1, int(self.rng.exponential(self.size_mean)))
            offset_ticks = max(1, int(self.rng.exponential(self.offset_mean)))
            offset = offset_ticks * self.tick
            if side == Side.BUY:
                price = self.round_price(self.fair_value - offset)
            else:
                price = self.round_price(self.fair_value + offset)
            events.append(Order(side, OrderType.LIMIT, size, price))

        n_market = self.rng.poisson(self.lam_m * dt)
        bias = self._informed_bias(book)
        for _ in range(n_market):
            if self.rng.random() < self.informed_prob:
                side = Side.BUY if bias > 0 else Side.SELL
            else:
                p_buy = 0.5 + 0.1 * bias
                side = Side.BUY if self.rng.random() < p_buy else Side.SELL
            size = max(1, int(self.rng.exponential(self.size_mean)))
            events.append(Order(side, OrderType.MARKET, size))

        self._cancel(book, dt)
        return events

    def _cancel(self, book, dt: float):
        rate = self.lam_c * dt
        for bookside in (book.bids, book.asks):
            for p in list(bookside.keys()):
                keep = deque()
                for o in bookside[p]:
                    if o.agent_id == "noise" and self.rng.random() < rate:
                        continue
                    keep.append(o)
                if keep:
                    bookside[p] = keep
                else:
                    del bookside[p]

    def seed_book(self, book, levels: int = 5, size_per_level: int = 6):
        mid = self.fair_value
        for i in range(1, levels + 1):
            bid_p = self.round_price(mid - i * self.tick)
            ask_p = self.round_price(mid + i * self.tick)
            book.submit(Order(Side.BUY, OrderType.LIMIT, size_per_level, bid_p))
            book.submit(Order(Side.SELL, OrderType.LIMIT, size_per_level, ask_p))
