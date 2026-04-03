"""
Streamlit dashboard for the Financial Market Simulation.
Run with: streamlit run Dashboard.py
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from FinancialModel import FinancialModel, STRATEGIES

st.set_page_config(page_title="Financial Market Simulation", layout="wide")

# ── Sidebar Controls ──
st.sidebar.title("Simulation Controls")

n_agents = st.sidebar.slider("Number of Agents", 2, 30, 14)
strategy_mode = st.sidebar.selectbox("Strategy Mode",
    ["Equal Distribution", "Random Mix"] + STRATEGIES)
initial_wealth = st.sidebar.slider("Initial Wealth", 1, 50, 10)
asset_config = st.sidebar.selectbox("Asset Configuration", [
    "Gold:10,Silver:5",
    "Gold:10,Silver:5,Oil:20",
    "Gold:10,Silver:5,Oil:20,Bitcoin:100",
    "Stock_A:50,Stock_B:30,Stock_C:10",
])
event_mode = st.sidebar.selectbox("Market Event",
    ["None", "Market Crash", "Bull Run", "High Volatility"])
grid_size = st.sidebar.slider("Grid Size", 5, 30, 10)
n_steps = st.sidebar.slider("Steps to Run", 50, 1000, 300, step=50)
candle_period = st.sidebar.slider("Candlestick Period (steps)", 3, 20, 5)

run = st.sidebar.button("Run Simulation", type="primary")

st.title("Financial Market Simulation")

if not run:
    st.info("Configure parameters in the sidebar and click **Run Simulation**.")
    st.stop()

# ── Run Simulation ──
progress = st.progress(0, text="Running simulation...")

model = FinancialModel(
    number_of_agents=n_agents, width=grid_size, height=grid_size,
    strategy_mode=strategy_mode, initial_wealth=initial_wealth,
    asset_config=asset_config, event_mode=event_mode
)

# Collect step-by-step data
step_data = []
agent_snapshots = []

for i in range(n_steps):
    model.step()

    # Close candles at custom period
    if i > 0 and i % candle_period == 0:
        for name in model.market.get_asset_names():
            model.market.close_candle(name)

    # Collect per-step metrics
    row = {"step": i + 1}
    for name in model.market.get_asset_names():
        row[f"{name}_price"] = model.market.get_price(name)
        row[f"{name}_vol"] = model.market.get_volatility(name)
    row["gini"] = model.compute_gini()
    row["total_wealth"] = model.compute_total_wealth()
    row["wealthiest"] = model.get_wealthiest_agent()
    row["total_trades"] = model.compute_total_trades()
    row["total_interactions"] = model.compute_total_interactions()
    row["wealthy_count"] = model.current_wealthy_agents()
    row["broke_count"] = model.current_non_wealthy_agents()
    for s in STRATEGIES:
        row[s] = sum(1 for a in model.schedule.agents if a.strategy_name == s)
    step_data.append(row)

    if (i + 1) % max(1, n_steps // 20) == 0:
        progress.progress((i + 1) / n_steps, text=f"Step {i+1}/{n_steps}")

progress.empty()

df = pd.DataFrame(step_data)

# Final agent data
for a in model.schedule.agents:
    agent_snapshots.append({
        "ID": a.unique_id,
        "Strategy": a.strategy_name,
        "Wealth": round(a.wealth, 2),
        "Net Worth": round(a.net_worth, 2),
        "Assets": len(a.assets),
        "Trades": a.trades_completed,
        "Fees Paid": round(a.fees_paid, 2),
        "P&L": round(a.wealth - a.initial_wealth, 2),
        "Mood": getattr(a, 'mood', 'N/A'),
    })
agent_df = pd.DataFrame(agent_snapshots).sort_values("Net Worth", ascending=False)

# ── Layout ──
st.success(f"Simulation complete: {n_steps} steps, {n_agents} agents")

# Top row: key metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Wealthiest Agent", f"#{agent_df.iloc[0]['ID']:.0f}",
            f"{agent_df.iloc[0]['Net Worth']:.1f} net worth")
col2.metric("Gini Coefficient", f"{df['gini'].iloc[-1]:.3f}",
            f"{df['gini'].iloc[-1] - df['gini'].iloc[0]:+.3f}")
col3.metric("Total Trades", f"{int(df['total_trades'].iloc[-1])}")
col4.metric("Wealthy / Broke",
            f"{int(df['wealthy_count'].iloc[-1])} / {int(df['broke_count'].iloc[-1])}")
col5.metric("Fees Collected", f"{model.market.total_fees_collected:.1f}")

st.divider()

# ── Candlestick Charts ──
st.subheader("Market Prices")

asset_names = model.market.get_asset_names()
tabs = st.tabs(asset_names + ["Overlay"])

for idx, name in enumerate(asset_names):
    with tabs[idx]:
        ohlc = model.market.get_ohlc(name)
        if len(ohlc) > 1:
            ohlc_df = pd.DataFrame(ohlc)
            ohlc_df["step"] = range(len(ohlc_df))

            fig = go.Figure(data=[go.Candlestick(
                x=ohlc_df["step"],
                open=ohlc_df["open"], high=ohlc_df["high"],
                low=ohlc_df["low"], close=ohlc_df["close"],
                increasing_line_color="#2ecc71", decreasing_line_color="#e74c3c",
            )])
            fig.update_layout(
                title=f"{name} — Candlestick Chart",
                xaxis_title="Candle Period",
                yaxis_title="Price",
                height=400,
                xaxis_rangeslider_visible=False,
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

# Overlay tab: all prices on one line chart
with tabs[-1]:
    price_cols = [c for c in df.columns if c.endswith("_price")]
    fig = go.Figure()
    colors = ["#f1c40f", "#95a5a6", "#2c3e50", "#e74c3c", "#1abc9c", "#8e44ad", "#d35400"]
    for i, col in enumerate(price_cols):
        name = col.replace("_price", "")
        fig.add_trace(go.Scatter(
            x=df["step"], y=df[col], mode="lines",
            name=name, line=dict(color=colors[i % len(colors)], width=2)
        ))
    fig.update_layout(title="All Asset Prices", height=400,
                      xaxis_title="Step", yaxis_title="Price",
                      template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Agent Leaderboard ──
st.subheader("Agent Leaderboard")

STRATEGY_COLORS = {
    "Asset Trading": "#2ecc71", "Wealth Trading": "#3498db",
    "Mean Reversion": "#e67e22", "Momentum": "#9b59b6",
    "Copycat": "#e74c3c", "Risk Averse": "#1abc9c", "Adaptive": "#f39c12",
}

fig_lb = go.Figure(data=[go.Bar(
    x=[f"#{r['ID']:.0f} ({r['Strategy'][:2]})" for _, r in agent_df.iterrows()],
    y=agent_df["Net Worth"],
    marker_color=[STRATEGY_COLORS.get(r["Strategy"], "gray") for _, r in agent_df.iterrows()],
    text=[f"P&L: {r['P&L']:+.1f}" for _, r in agent_df.iterrows()],
    textposition="outside",
)])
fig_lb.update_layout(title="Agent Net Worth (ranked)", height=400,
                     xaxis_title="Agent", yaxis_title="Net Worth",
                     template="plotly_dark")
st.plotly_chart(fig_lb, use_container_width=True)

st.dataframe(agent_df.reset_index(drop=True), use_container_width=True, height=300)

st.divider()

# ── Strategy Performance & Distribution ──
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Strategy Performance")
    strat_perf = agent_df.groupby("Strategy").agg(
        avg_net_worth=("Net Worth", "mean"),
        avg_pnl=("P&L", "mean"),
        total_trades=("Trades", "sum"),
        avg_fees=("Fees Paid", "mean"),
    ).sort_values("avg_net_worth", ascending=False)

    fig_sp = go.Figure(data=[go.Bar(
        x=strat_perf.index,
        y=strat_perf["avg_net_worth"],
        marker_color=[STRATEGY_COLORS.get(s, "gray") for s in strat_perf.index],
        text=[f"P&L: {v:+.1f}" for v in strat_perf["avg_pnl"]],
        textposition="outside",
    )])
    fig_sp.update_layout(title="Average Net Worth by Strategy", height=350,
                         yaxis_title="Avg Net Worth", template="plotly_dark")
    st.plotly_chart(fig_sp, use_container_width=True)

with col_right:
    st.subheader("Wealth Distribution")
    fig_pie = px.pie(agent_df, values="Net Worth", names="Strategy",
                     color="Strategy",
                     color_discrete_map=STRATEGY_COLORS)
    fig_pie.update_layout(title="Wealth Share by Strategy", height=350,
                          template="plotly_dark")
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── Time Series Charts ──
st.subheader("Simulation Metrics Over Time")

col_a, col_b = st.columns(2)

with col_a:
    fig_gini = px.line(df, x="step", y="gini", title="Gini Coefficient (Inequality)")
    fig_gini.update_layout(height=300, template="plotly_dark")
    st.plotly_chart(fig_gini, use_container_width=True)

with col_b:
    fig_w = px.line(df, x="step", y="wealthiest", title="Wealthiest Agent's Wealth")
    fig_w.update_layout(height=300, template="plotly_dark")
    st.plotly_chart(fig_w, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    fig_tw = px.line(df, x="step", y="total_wealth", title="Total System Wealth")
    fig_tw.update_layout(height=300, template="plotly_dark")
    st.plotly_chart(fig_tw, use_container_width=True)

with col_d:
    fig_tr = px.line(df, x="step", y="total_trades", title="Cumulative Trades")
    fig_tr.update_layout(height=300, template="plotly_dark")
    st.plotly_chart(fig_tr, use_container_width=True)

# Strategy distribution over time
strat_cols = [s for s in STRATEGIES if s in df.columns]
if strat_cols:
    fig_sd = go.Figure()
    for s in strat_cols:
        fig_sd.add_trace(go.Scatter(
            x=df["step"], y=df[s], mode="lines", name=s,
            line=dict(color=STRATEGY_COLORS.get(s, "gray"), width=2),
            stackgroup="one"
        ))
    fig_sd.update_layout(title="Strategy Distribution Over Time", height=350,
                         xaxis_title="Step", yaxis_title="Agent Count",
                         template="plotly_dark")
    st.plotly_chart(fig_sd, use_container_width=True)

# Volatility
vol_cols = [c for c in df.columns if c.endswith("_vol")]
if vol_cols:
    fig_vol = go.Figure()
    for i, col in enumerate(vol_cols):
        name = col.replace("_vol", "")
        fig_vol.add_trace(go.Scatter(
            x=df["step"], y=df[col], mode="lines", name=name,
            line=dict(color=colors[i % len(colors)], width=2)
        ))
    fig_vol.update_layout(title="Asset Volatility Over Time", height=300,
                          xaxis_title="Step", yaxis_title="Volatility (σ)",
                          template="plotly_dark")
    st.plotly_chart(fig_vol, use_container_width=True)
