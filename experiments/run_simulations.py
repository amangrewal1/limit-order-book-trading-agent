import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from lob.agents.adaptive import AdaptiveAgent
from lob.agents.static_quoter import StaticQuoter
from lob.agents.taker import MarketTaker
from lob.backtest import Backtester
from lob.book import OrderBook
from lob.market import PoissonFlow


@dataclass
class RunResult:
    agent: str
    seed: int
    final_pnl: float
    max_abs_inventory: int
    inventory_drawdown: int
    fills: int


AGENT_FACTORIES: Dict[str, Callable] = {
    "taker": lambda seed: MarketTaker(seed=seed, trade_prob=0.5),
    "static": lambda seed: StaticQuoter(spread_ticks=3),
    "adaptive": lambda seed: AdaptiveAgent(),
}


def run_single(agent_name: str, seed: int, steps: int) -> RunResult:
    book = OrderBook()
    flow = PoissonFlow(seed=seed)
    agent = AGENT_FACTORIES[agent_name](seed)
    bt = Backtester(book, flow, agent)
    bt.run(steps)
    summary = bt.summary()
    return RunResult(agent=agent_name, seed=seed, **summary)


def _worker(args):
    agent_name, seed, steps = args
    return run_single(agent_name, seed, steps)


def run_experiments(n_sims: int, steps: int, workers: int = 1) -> Dict[str, List[RunResult]]:
    results: Dict[str, List[RunResult]] = {k: [] for k in AGENT_FACTORIES}
    tasks = []
    for i in range(n_sims):
        seed = 10_000 + i
        for name in AGENT_FACTORIES:
            tasks.append((name, seed, steps))

    start = time.time()
    if workers <= 1:
        for i, t in enumerate(tasks):
            r = _worker(t)
            results[r.agent].append(r)
            if (i + 1) % max(1, len(tasks) // 20) == 0:
                elapsed = time.time() - start
                print(f"  {i+1}/{len(tasks)} runs  ({elapsed:.1f}s)")
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_worker, t) for t in tasks]
            for i, fut in enumerate(as_completed(futures)):
                r = fut.result()
                results[r.agent].append(r)
                if (i + 1) % max(1, len(tasks) // 20) == 0:
                    elapsed = time.time() - start
                    print(f"  {i+1}/{len(tasks)} runs  ({elapsed:.1f}s)")
    return results


def summarize(results: Dict[str, List[RunResult]]) -> None:
    print("\n" + "=" * 70)
    print(f"{'Agent':<12}{'PnL mean':>12}{'PnL median':>14}{'PnL std':>12}{'Win %':>8}{'InvDD':>10}")
    print("-" * 70)
    stats = {}
    for name, runs in results.items():
        pnls = np.array([r.final_pnl for r in runs])
        invs = np.array([r.inventory_drawdown for r in runs])
        stats[name] = {
            "pnl_mean": pnls.mean(),
            "pnl_median": np.median(pnls),
            "pnl_std": pnls.std(),
            "win_rate": float((pnls > 0).mean()),
            "inv_dd_mean": invs.mean(),
            "inv_dd_p95": np.percentile(invs, 95),
        }
        print(f"{name:<12}{pnls.mean():>12.3f}{np.median(pnls):>14.3f}"
              f"{pnls.std():>12.3f}{(pnls > 0).mean()*100:>7.1f}%"
              f"{invs.mean():>10.2f}")
    print("=" * 70)

    if "adaptive" in stats and "static" in stats:
        adap_dd = stats["adaptive"]["inv_dd_mean"]
        static_dd = stats["static"]["inv_dd_mean"]
        if static_dd > 0:
            reduction = 1.0 - (adap_dd / static_dd)
            print(f"\nInventory drawdown reduction (adaptive vs static): {reduction:.1%}")

    if "adaptive" in stats and "taker" in stats:
        adap_pnl = stats["adaptive"]["pnl_mean"]
        taker_pnl = stats["taker"]["pnl_mean"]
        print(f"Adaptive mean PnL: {adap_pnl:.3f}  vs  Market-taker mean PnL: {taker_pnl:.3f}")
        print(f"PnL advantage:     {adap_pnl - taker_pnl:.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sims", type=int, default=10000)
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    print(f"Running {args.sims} simulations of {args.steps} steps each ({args.workers} workers)...")
    results = run_experiments(args.sims, args.steps, args.workers)
    summarize(results)


if __name__ == "__main__":
    main()
