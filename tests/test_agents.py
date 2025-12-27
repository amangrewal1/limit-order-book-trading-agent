import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lob.agents.adaptive import AdaptiveAgent
from lob.agents.static_quoter import StaticQuoter
from lob.agents.taker import MarketTaker
from lob.backtest import Backtester
from lob.book import OrderBook
from lob.market import PoissonFlow


def run(agent, seed=7, steps=300):
    book = OrderBook()
    flow = PoissonFlow(seed=seed)
    bt = Backtester(book, flow, agent)
    bt.run(steps)
    return bt.summary()


def test_taker_runs():
    s = run(MarketTaker(seed=1))
    assert s["fills"] >= 0


def test_static_quoter_runs():
    s = run(StaticQuoter())
    assert s["fills"] > 0


def test_adaptive_runs():
    s = run(AdaptiveAgent())
    assert s["fills"] > 0


if __name__ == "__main__":
    test_taker_runs()
    test_static_quoter_runs()
    test_adaptive_runs()
    print("all agent tests passed")
