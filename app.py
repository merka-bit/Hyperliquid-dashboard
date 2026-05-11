import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from pathlib import Path


st.set_page_config(
    page_title="Hyperliquid Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("csv")
DEFAULT_CSV = DATA_DIR / "trade_history.csv"
STARTING_CAPITAL = 2000.0


@st.cache_data
def load_data(file_source):
    df = pd.read_csv(file_source)

    if "time" in df.columns:
        df["time"] = pd.to_datetime(
            df["time"],
            format="%d.%m.%Y - %H:%M:%S",
            errors="coerce",
        )

    for col in ["closedPnl", "fee", "ntl"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def format_percent(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def format_currency(value):
    if pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"


st.sidebar.title("Hyperliquid Dashboard")
st.sidebar.caption(f"Default source: {DEFAULT_CSV}")

uploaded_file = st.sidebar.file_uploader("Upload Hyperliquid CSV", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    data_source = uploaded_file.name
elif DEFAULT_CSV.exists() and DEFAULT_CSV.stat().st_size > 0:
    df = load_data(DEFAULT_CSV)
    data_source = str(DEFAULT_CSV)
else:
    st.info(
        "Add a non-empty CSV file to the 'csv' folder or upload one in the sidebar to begin."
    )
    st.stop()

required_columns = {"coin", "closedPnl", "time"}
missing_columns = sorted(required_columns - set(df.columns))
if missing_columns:
    st.error(f"Missing required columns: {', '.join(missing_columns)}")
    st.stop()

df = df.dropna(subset=["time"]).copy()
df["date"] = df["time"].dt.date
df["trade_return_pct"] = np.where(
    df["ntl"].abs() > 0,
    df["closedPnl"] / df["ntl"].abs() * 100,
    np.nan,
)

st.sidebar.subheader("Filters")
min_date = df["date"].min()
max_date = df["date"].max()
st.sidebar.caption("You can also change the period on the main page.")
default_start_date = min_date
default_end_date = max_date

st.title("Hyperliquid Performance Dashboard")
st.caption(f"Data source: {data_source}")

filter_col1, filter_col2 = st.columns(2)
start_date = filter_col1.date_input(
    "Start Date",
    value=default_start_date,
    min_value=min_date,
    max_value=max_date,
)
end_date = filter_col2.date_input(
    "End Date",
    value=default_end_date,
    min_value=min_date,
    max_value=max_date,
)

if start_date > end_date:
    st.error("Start Date must be earlier than End Date.")
    st.stop()

filtered_df = df[
    df["date"].between(start_date, end_date)
].copy()
filtered_df = filtered_df.sort_values("time")

if filtered_df.empty:
    st.warning("No trades match the selected filters.")
    st.stop()

filtered_df["cum_pnl"] = filtered_df["closedPnl"].cumsum()
filtered_df["cum_return_pct"] = filtered_df["cum_pnl"] / STARTING_CAPITAL * 100

wins = filtered_df[filtered_df["closedPnl"] > 0]
losses = filtered_df[filtered_df["closedPnl"] < 0]

winrate = (
    len(wins) / (len(wins) + len(losses)) * 100 if (len(wins) + len(losses)) > 0 else 0
)
total_return_pct = (
    filtered_df["closedPnl"].sum() / STARTING_CAPITAL * 100
    if STARTING_CAPITAL > 0
    else np.nan
)
max_drawdown_pct = (
    (filtered_df["cum_pnl"] - filtered_df["cum_pnl"].cummax()).min() / STARTING_CAPITAL
    * 100
    if STARTING_CAPITAL > 0
    else np.nan
)
avg_trade_pct = filtered_df["trade_return_pct"].mean()
avg_trade_profit_pct = (
    filtered_df["closedPnl"].mean() / STARTING_CAPITAL * 100
    if STARTING_CAPITAL > 0
    else np.nan
)

st.caption(f"Period: {start_date} to {end_date}")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Return", format_percent(total_return_pct))
col2.metric("Winrate", format_percent(winrate))
col3.metric("Avg Trade", format_percent(avg_trade_pct))
col4.metric("Max Drawdown", format_percent(max_drawdown_pct))
col5.metric("Avg Trade Profit", format_percent(avg_trade_profit_pct))

st.divider()

st.subheader("Equity Curve")
fig_equity = px.line(
    filtered_df,
    x="time",
    y="cum_return_pct",
    template="plotly_dark",
    labels={"cum_return_pct": "Cumulative Return (%)", "time": "Time"},
)
st.plotly_chart(fig_equity, use_container_width=True)

st.subheader("Daily PnL")
pnl_daily = filtered_df.groupby("date", as_index=False)["closedPnl"].sum()
fig_daily = px.bar(pnl_daily, x="date", y="closedPnl", template="plotly_dark")
st.plotly_chart(fig_daily, use_container_width=True)

if "dir" in filtered_df.columns:
    st.subheader("Long vs Short")
    direction_stats = filtered_df.groupby("dir", as_index=False)["closedPnl"].sum()
    fig_dir = px.pie(
        direction_stats, names="dir", values="closedPnl", template="plotly_dark"
    )
    st.plotly_chart(fig_dir, use_container_width=True)

st.subheader("Top Coins by PnL")
coin_stats = (
    filtered_df.groupby("coin")["closedPnl"].sum().sort_values(ascending=False).reset_index()
)
fig_coin = px.bar(coin_stats, x="coin", y="closedPnl", template="plotly_dark")
st.plotly_chart(fig_coin, use_container_width=True)

st.subheader("Trade Distribution")
fig_hist = px.histogram(filtered_df, x="closedPnl", nbins=50, template="plotly_dark")
st.plotly_chart(fig_hist, use_container_width=True)

st.subheader("Trading Heatmap")
filtered_df["weekday"] = filtered_df["time"].dt.day_name()
filtered_df["hour"] = filtered_df["time"].dt.hour
heatmap = filtered_df.pivot_table(
    index="weekday",
    columns="hour",
    values="closedPnl",
    aggfunc="sum",
)
weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
heatmap = heatmap.reindex(weekday_order)
fig_heat = px.imshow(heatmap, aspect="auto", template="plotly_dark")
st.plotly_chart(fig_heat, use_container_width=True)

with st.expander("Raw Data"):
    st.dataframe(filtered_df, use_container_width=True)

csv_export = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Filtered CSV",
    data=csv_export,
    file_name="filtered_trades.csv",
    mime="text/csv",
)
