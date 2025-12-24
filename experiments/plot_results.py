import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np

from lob.agents.adaptive import AdaptiveAgent
from lob.agents.static_quoter import StaticQuoter
from lob.agents.taker import MarketTaker
from lob.backtest import Backtester
from lob.book import OrderBook
from lob.market import PoissonFlow


def run_one(agent_class, seed, steps, **kwargs):
    book = OrderBook()
    flow = PoissonFlow(seed=seed)
    kwargs.setdefault("agent_id", agent_class.__name__.lower())
    if agent_class is MarketTaker:
        kwargs.setdefault("seed", seed)
    agent = agent_class(**kwargs)
    bt = Backtester(book, flow, agent)
    bt.run(steps)
    return agent, bt


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--steps", type=int, default=2000)
    p.add_argument("--out", type=str, default="results.png")
    args = p.parse_args()

    taker, bt1 = run_one(MarketTaker, args.seed, args.steps, trade_prob=0.5)
    static, bt2 = run_one(StaticQuoter, args.seed, args.steps, spread_ticks=2)
    adaptive, bt3 = run_one(AdaptiveAgent, args.seed, args.steps)

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

    axes[0].plot(bt3.mid_history, color="gray", alpha=0.7, label="Mid price")
    axes[0].set_ylabel("Mid")
    axes[0].legend(loc="upper left")
    axes[0].set_title(f"Market Simulation (seed={args.seed}, steps={args.steps})")

    axes[1].plot(taker.pnl_history, label=f"Market Taker (final={taker.pnl_history[-1]:.2f})")
    axes[1].plot(static.pnl_history, label=f"Static Quoter (final={static.pnl_history[-1]:.2f})")
    axes[1].plot(adaptive.pnl_history, label=f"Adaptive (final={adaptive.pnl_history[-1]:.2f})")
    axes[1].axhline(0, color="black", linewidth=0.5)
    axes[1].set_ylabel("PnL")
    axes[1].legend(loc="upper left")

    axes[2].plot(taker.inventory_history, label="Market Taker", alpha=0.7)
    axes[2].plot(static.inventory_history, label="Static Quoter", alpha=0.7)
    axes[2].plot(adaptive.inventory_history, label="Adaptive", alpha=0.9)
    axes[2].axhline(0, color="black", linewidth=0.5)
    axes[2].set_ylabel("Inventory")
    axes[2].set_xlabel("Step")
    axes[2].legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(args.out, dpi=120)
    print(f"Saved {args.out}")

    for name, agent, bt in [("Taker", taker, bt1), ("Static", static, bt2), ("Adaptive", adaptive, bt3)]:
        s = bt.summary()
        print(f"{name:<10} pnl={s['final_pnl']:8.3f}  max|inv|={s['max_abs_inventory']:3d}  inv_dd={s['inventory_drawdown']:3d}  fills={s['fills']}")


if __name__ == "__main__":
    main()
