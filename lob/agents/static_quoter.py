from typing import List

from ..order import Order, Side, OrderType
from .base import BaseAgent


class StaticQuoter(BaseAgent):
    def __init__(
        self,
        agent_id: str = "static",
        spread_ticks: int = 2,
        tick_size: float = 0.01,
        size: int = 1,
        max_inventory: int = 50,
    ):
        super().__init__(agent_id)
        self.spread_ticks = spread_ticks
        self.tick = tick_size
        self.size = size
        self.max_inventory = max_inventory

    def act(self, book) -> List[Order]:
        mid = book.mid()
        if mid is None:
            return []
        book.cancel_agent(self.agent_id)

        half = (self.spread_ticks * self.tick) / 2.0
        bid_price = round((mid - half) / self.tick) * self.tick
        ask_price = round((mid + half) / self.tick) * self.tick

        orders: List[Order] = []
        if self.inventory < self.max_inventory:
            orders.append(Order(Side.BUY, OrderType.LIMIT, self.size, bid_price, agent_id=self.agent_id))
        if self.inventory > -self.max_inventory:
            orders.append(Order(Side.SELL, OrderType.LIMIT, self.size, ask_price, agent_id=self.agent_id))
        return orders
