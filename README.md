# Agent-Based Financial Market Simulation

KCL final year project (6CCS3PRJ): An agent-based model of financial markets built with Python's Mesa framework. Agents with different trading strategies interact on a spatial grid, trading assets and wealth while responding to market events.

## Features

- **7 trading strategies**: Asset Trading, Wealth Trading, Mean Reversion, Momentum, Copycat, Risk Averse, and Adaptive (Q-learning)
- **Configurable assets**: Define custom asset types and initial prices (e.g. Gold, Silver, Oil, Bitcoin)
- **Market events**: Simulate crashes, bull runs, and volatility spikes
- **Centralized market**: Order book with supply/demand-driven price discovery and transaction costs
- **Live visualization**: Grid view, market price charts, strategy distribution, Gini coefficient, and more
- **Streamlit dashboard**: Alternative interactive dashboard for running and analyzing simulations

## Setup

```bash
# Requires Mesa 1.2.1 specifically (not 2.x or 3.x -- API breaking changes)
pip install "mesa==1.2.1" numpy matplotlib pandas

# Optional: for the Streamlit dashboard
pip install streamlit plotly

# Optional: for standalone data analysis scripts
pip install yfinance scikit-learn networkx
```

## Running

```bash
# Mesa web visualization (starts at http://127.0.0.1:8523/)
cd Project
python Visualisation.py

# Streamlit dashboard
cd Project
streamlit run Dashboard.py
```

## Project Structure

```
Project/
  strategies.py        # Strategy pattern: ABC + 7 concrete trading strategies
  FinancialAgent.py    # Mesa Agent with movement, trade execution helpers
  FinancialModel.py    # Mesa Model: grid, scheduler, data collectors
  Market.py            # Centralized order book and price management
  MarketEvent.py       # Market-wide events (crash, boom, volatility)
  Asset.py             # Lightweight asset holding record
  Visualisation.py     # Mesa ModularServer entry point
  Dashboard.py         # Streamlit dashboard alternative
  Data/                # Standalone financial analysis scripts (yfinance)
  Testing/             # Early Mesa tutorial experiments
```

## Architecture

The simulation uses the **Strategy pattern** to separate trading logic from agent mechanics:

- `TradingStrategy` (ABC) defines the `execute(agent, other)` interface
- Each strategy (e.g. `MomentumStrategy`, `AdaptiveStrategy`) owns its own state and decision logic
- `FinancialAgent` delegates to its strategy object and provides shared `execute_buy()`/`execute_sell()` helpers
- `Market` is the single source of truth for all asset prices
- Strategy metadata (`STRATEGY_NAMES`, `STRATEGY_COLORS`, `STRATEGY_ABBREV`) lives in `strategies.py` and is imported by all other modules

## Adding a New Strategy

1. Subclass `TradingStrategy` in `strategies.py` and implement `execute(self, agent, other)`
2. Add entries to `STRATEGY_NAMES`, `STRATEGY_COLORS`, `STRATEGY_ABBREV`
3. Add the strategy to the `create_strategy()` factory function
4. Add it to the strategy choices in `Visualisation.py` and `Dashboard.py`
