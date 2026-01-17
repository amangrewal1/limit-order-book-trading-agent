from lob.book import OrderBook
from lob.order import Order, Side, OrderType


def test_best_bid_le_best_ask():
    book = OrderBook()
    # With no orders, no crossing
    assert book.best_bid() is None
    assert book.best_ask() is None


def test_empty_book_properties():
    book = OrderBook()
    assert book.depth(Side.BID) == 0
    assert book.depth(Side.ASK) == 0
