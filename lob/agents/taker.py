from typing import List, Optional

import numpy as np

from ..order import Order, Side, OrderType
from .base import BaseAgent


class MarketTaker(BaseAgent):
    def __init__(
        self,
        agent_id: str = "taker",
        size: int = 1,
        trade_prob: float = 0.4,
        max_inventory: int = 50,
        seed: Optional[int] = None,
    ):
        super().__init__(agent_id)
        self.size = size
        self.trade_prob = trade_prob
        self.max_inventory = max_inventory
        self.rng = np.random.default_rng(seed)

    def act(self, book) -> List[Order]:
        if book.mid() is None:
            return []
        if self.rng.random() > self.trade_prob:
            return []
        side = Side.BUY if self.rng.random() < 0.5 else Side.SELL
        if side == Side.BUY and self.inventory >= self.max_inventory:
            return []
        if side == Side.SELL and self.inventory <= -self.max_inventory:
            return []
        return [Order(side, OrderType.MARKET, self.size, agent_id=self.agent_id)]
