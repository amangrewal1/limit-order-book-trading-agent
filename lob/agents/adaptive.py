from collections import deque
from typing import List

import numpy as np

from ..order import Order, Side, OrderType
from .base import BaseAgent


class AdaptiveAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str = "adaptive",
        base_spread_ticks: int = 3,
        tick_size: float = 0.01,
        size: int = 1,
        max_inventory: int = 50,
        ofi_window: int = 25,
        widen_coef: float = 2.5,
        take_threshold: float = 1.8,
        skew_coef: float = 1.5,
        imbalance_weight: float = 1.0,
    ):
        super().__init__(agent_id)
        self.base_spread_ticks = base_spread_ticks
        self.tick = tick_size
        self.size = size
        self.max_inventory = max_inventory
        self.ofi_window = ofi_window
        self.widen_coef = widen_coef
        self.take_threshold = take_threshold
        self.skew_coef = skew_coef
        self.imbalance_weight = imbalance_weight

        self.trade_flow = deque(maxlen=ofi_window)
        self.last_trade_count = 0

    def _update_flow(self, book) -> float:
        new_trades = book.trades[self.last_trade_count:]
        self.last_trade_count = len(book.trades)
        for _, _, size, side in new_trades:
            self.trade_flow.append(size * int(side))
        if len(self.trade_flow) < 5:
            return 0.0
        arr = np.fromiter(self.trade_flow, dtype=float)
        mean = arr.mean()
        std = arr.std() + 1e-6
        return float(mean / std)

    def _signal(self, book) -> float:
        ofi = self._update_flow(book)
        imb = book.imbalance(levels=3)
        return ofi + self.imbalance_weight * imb

    def act(self, book) -> List[Order]:
        mid = book.mid()
        if mid is None:
            return []

        book.cancel_agent(self.agent_id)
        signal = self._signal(book)

        if abs(signal) > self.take_threshold:
            if signal > 0 and self.inventory < int(self.max_inventory * 0.6):
                return [Order(Side.BUY, OrderType.MARKET, self.size, agent_id=self.agent_id)]
            if signal < 0 and self.inventory > -int(self.max_inventory * 0.6):
                return [Order(Side.SELL, OrderType.MARKET, self.size, agent_id=self.agent_id)]

        half_base = (self.base_spread_ticks * self.tick) / 2.0
        widen = self.widen_coef * abs(signal) * self.tick

        bid_widen = widen if signal < 0 else 0.0
        ask_widen = widen if signal > 0 else 0.0

        inv_ratio = self.inventory / self.max_inventory
        skew = inv_ratio * self.skew_coef * self.tick

        bid_price = round((mid - half_base - bid_widen - skew) / self.tick) * self.tick
        ask_price = round((mid + half_base + ask_widen - skew) / self.tick) * self.tick

        orders: List[Order] = []
        if self.inventory < self.max_inventory:
            orders.append(Order(Side.BUY, OrderType.LIMIT, self.size, bid_price, agent_id=self.agent_id))
        if self.inventory > -self.max_inventory:
            orders.append(Order(Side.SELL, OrderType.LIMIT, self.size, ask_price, agent_id=self.agent_id))
        return orders
