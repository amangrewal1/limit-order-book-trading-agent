#!/usr/bin/env bash
set -euo pipefail

python3 experiments/run_simulations.py --sims 10000 --steps 500 --workers 4
