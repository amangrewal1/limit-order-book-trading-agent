# Agents

| Agent | Role | Strategy |
|---|---|---|
| `MarketTaker` | baseline | Bernoulli-triggered market orders; uniform side |
| `StaticQuoter` | baseline | Two-sided quotes at mid ± spread/2 |
| `AdaptiveAgent` | main | OFI-driven; crosses on strong signal, quotes otherwise |

All share a common PnL/inventory bookkeeping base class.
