from typing import List, Dict

from .order import Side


class Backtester:
    def __init__(self, book, flow, agent, warmup_steps: int = 30):
        self.book = book
        self.flow = flow
        self.agent = agent
        self.warmup_steps = warmup_steps
        self.mid_history: List[float] = []

    def _process_fills(self, fills: List[Dict]) -> None:
        aid = self.agent.agent_id
        for f in fills:
            if f["aggressor"] == aid:
                self.agent.on_fill(f["price"], f["size"], f["aggressor_side"])
            elif f["resting_agent"] == aid:
                opp = f["aggressor_side"].opposite
                self.agent.on_fill(f["price"], f["size"], opp)

    def warmup(self) -> None:
        self.flow.seed_book(self.book)
        for _ in range(self.warmup_steps):
            events = self.flow.step(self.book)
            for e in events:
                self.book.submit(e)

    def run(self, steps: int = 2000) -> None:
        self.warmup()
        for _ in range(steps):
            events = self.flow.step(self.book)
            for e in events:
                fills = self.book.submit(e)
                self._process_fills(fills)

            orders = self.agent.act(self.book)
            for o in orders:
                fills = self.book.submit(o)
                self._process_fills(fills)

            mid = self.book.mid()
            if mid is not None:
                self.agent.record(mid)
                self.mid_history.append(mid)

    def summary(self) -> Dict:
        hist = self.agent.inventory_history
        pnl = self.agent.pnl_history
        if not pnl:
            return {"final_pnl": 0.0, "max_abs_inventory": 0, "inventory_drawdown": 0, "fills": 0}
        peak = hist[0]
        trough = hist[0]
        max_dd = 0
        for v in hist:
            if v > peak:
                peak = v
            if v < trough:
                trough = v
            max_dd = max(max_dd, peak - v, v - trough)
        return {
            "final_pnl": pnl[-1],
            "max_abs_inventory": max(abs(v) for v in hist),
            "inventory_drawdown": max_dd,
            "fills": self.agent.fill_count,
        }
