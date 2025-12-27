import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lob.book import OrderBook
from lob.order import Order, Side, OrderType


def test_limit_rest_and_best():
    b = OrderBook()
    b.submit(Order(Side.BUY, OrderType.LIMIT, 5, 99.50))
    b.submit(Order(Side.BUY, OrderType.LIMIT, 3, 99.40))
    b.submit(Order(Side.SELL, OrderType.LIMIT, 4, 100.20))
    assert b.best_bid() == 99.50
    assert b.best_ask() == 100.20
    assert abs(b.spread() - 0.70) < 1e-9


def test_market_order_matches_price_time_priority():
    b = OrderBook()
    b.submit(Order(Side.SELL, OrderType.LIMIT, 2, 100.00, agent_id="A"))
    b.submit(Order(Side.SELL, OrderType.LIMIT, 3, 100.00, agent_id="B"))
    b.submit(Order(Side.SELL, OrderType.LIMIT, 2, 100.10, agent_id="C"))

    fills = b.submit(Order(Side.BUY, OrderType.MARKET, 4))
    assert len(fills) == 2
    assert fills[0]["resting_agent"] == "A" and fills[0]["size"] == 2
    assert fills[1]["resting_agent"] == "B" and fills[1]["size"] == 2
    assert b.best_ask() == 100.00


def test_limit_order_crosses():
    b = OrderBook()
    b.submit(Order(Side.SELL, OrderType.LIMIT, 5, 100.00))
    fills = b.submit(Order(Side.BUY, OrderType.LIMIT, 3, 100.50))
    assert len(fills) == 1
    assert fills[0]["price"] == 100.00
    assert fills[0]["size"] == 3


def test_cancel_agent():
    b = OrderBook()
    b.submit(Order(Side.BUY, OrderType.LIMIT, 5, 99.50, agent_id="me"))
    b.submit(Order(Side.BUY, OrderType.LIMIT, 3, 99.50, agent_id="other"))
    b.cancel_agent("me")
    assert sum(o.size for o in b.bids[99.50]) == 3


if __name__ == "__main__":
    test_limit_rest_and_best()
    test_market_order_matches_price_time_priority()
    test_limit_order_crosses()
    test_cancel_agent()
    print("all book tests passed")
