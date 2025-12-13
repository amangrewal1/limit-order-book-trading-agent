from abc import ABC, abstractmethod
from typing import List

from ..order import Order, Side


class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.inventory = 0
        self.cash = 0.0
        self.pnl_history: List[float] = []
        self.inventory_history: List[int] = []
        self.fill_count = 0

    @abstractmethod
    def act(self, book) -> List[Order]:
        ...

    def on_fill(self, price: float, size: int, side: Side) -> None:
        if side == Side.BUY:
            self.inventory += size
            self.cash -= price * size
        else:
            self.inventory -= size
            self.cash += price * size
        self.fill_count += 1

    def mtm(self, mid: float) -> float:
        return self.cash + self.inventory * mid

    def record(self, mid: float) -> None:
        self.pnl_history.append(self.mtm(mid))
        self.inventory_history.append(self.inventory)
