from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional
import itertools


class Side(IntEnum):
    BUY = 1
    SELL = -1

    @property
    def opposite(self) -> "Side":
        return Side.SELL if self is Side.BUY else Side.BUY


class OrderType(IntEnum):
    LIMIT = 1
    MARKET = 2


_id_gen = itertools.count(1)


@dataclass
class Order:
    side: Side
    type: OrderType
    size: int
    price: Optional[float] = None
    agent_id: str = "noise"
    id: int = field(default_factory=lambda: next(_id_gen))
    timestamp: int = 0

    def __post_init__(self):
        if self.type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit order requires a price")
        if self.size <= 0:
            raise ValueError("Order size must be positive")
