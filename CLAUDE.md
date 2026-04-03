# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KCL final year project (6CCS3PRJ): Agent-based modelling of financial markets using Python's Mesa framework. Agents with different trading strategies interact on a grid, trading assets and wealth. The simulation runs as a web app via Mesa's ModularServer.

## Setup and Run

```bash
# Requires Mesa 1.2.1 specifically (not 2.x or 3.x — API breaking changes)
pip install "mesa==1.2.1" numpy matplotlib pandas yfinance scikit-learn networkx

# Launch the simulation (starts web server at http://127.0.0.1:8523/)
cd Project
python Visualisation.py
```

The data analysis scripts in `Project/Data/` are standalone and require `yfinance`, `sklearn`, `pandas`, `numpy`, `matplotlib`:
```bash
python Project/Data/Data.py  # or any script in Data/
```

## Architecture

All simulation code lives in `Project/`. The core classes:

**Market** (`Market.py`) — Centralized price store with a simple order book. Holds canonical prices, price history, supply/demand per asset type. Agents read prices from the market (not from their own asset instances). Supports `submit_order()` / `clear_orders()` for price discovery, and `update_price()` for direct changes (events, fluctuations).

**MarketEvent** (`MarketEvent.py`) — Represents market-wide events (crashes, booms, volatility spikes). Each event has a type, magnitude, duration, and optional target assets. Activated at simulation start via UI dropdown. Applied per-tick in `FinancialModel.step()`.

**Asset** (`Asset.py`) — Lightweight holding record: just `name` and `quantity`. Price is always looked up via `model.market.get_price(asset.name)`.

**FinancialAgent** (`FinancialAgent.py`) — Extends `mesa.Agent`. Each agent has wealth, an individual strategy, mood, and a list of Assets. On each step: `move()` to a neighboring cell, then `trade()` with a cellmate. Trading strategy dispatched by string:
- `"Asset Trading"` — buy a random asset from another agent at market price
- `"Wealth Trading"` — transfer a random amount of wealth
- `"Mean Reversion"` — buy when market price deviates from historical mean beyond threshold
- `"Momentum"` — buy on uptrend, sell on downtrend (uses market price history)

**FinancialModel** (`FinancialModel.py`) — Extends `mesa.Model`. Creates `MultiGrid`, `RandomActivation` scheduler, `Market`, and 9 `DataCollector` instances. Key parameters:
- `strategy_mode`: single strategy for all agents, or "Random Mix" / "Equal Distribution" for per-agent strategies
- `asset_config`: configurable asset types and initial prices (e.g. "Gold:10,Silver:5,Oil:20")
- `event_mode`: optional market event at start ("Market Crash", "Bull Run", "High Volatility")
- Price fluctuations happen once per model step (weighted by strategy distribution), not per-agent

**Visualisation** (`Visualisation.py`) — Entry point. Configures `ModularServer` with grid, pie chart, market price chart, strategy distribution chart, and standard metric charts. Agent portrayal: color-coded by strategy, red=broke, gold=wealthiest (after step 10), radius scales with wealth. Text shows `id:strategy_abbrev`.

## Key Design Notes

- Agents can have different strategies in the same simulation via "Random Mix" or "Equal Distribution" modes
- The Market is the single source of truth for prices — agents never store prices locally
- Price fluctuations are applied once per model step, weighted by the proportion of Mean Reversion vs Momentum agents
- Market events are applied after order clearing in each step, gradually affecting prices over their duration
- `Project/Testing/` contains early Mesa tutorial experiments (not automated tests)
- `Project/Data/` contains standalone financial analysis scripts (RSI, MACD, etc.) using yfinance — not integrated into the simulation
