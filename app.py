import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from trading_strategy import main, analyze_results

st.set_page_config(page_title="Golden Cross Trading Dashboard", layout="wide")

positions = main()

def load_data():
    # Re-run backend to get all data
    data = positions.copy()
    return data

def get_chart_data():
    # Get price and MA data from backend
    data = main.__globals__['get_stock_data']("MSFT")
    data = main.__globals__['calculate_moving_averages'](data)
    data = main.__globals__['identify_golden_cross'](data)
    return data

# Sidebar navigation
page = st.sidebar.radio("Select Page", ["Price Chart", "Trade Statistics", "Detailed Trades"])

if page == "Price Chart":
    st.title("Price Chart with Golden Cross Signals")
    chart_data = get_chart_data()
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(chart_data.index, chart_data['Close'], label='Close Price', color='blue')
    ax.plot(chart_data.index, chart_data['MA50'], label='MA50', color='orange')
    ax.plot(chart_data.index, chart_data['MA200'], label='MA200', color='green')

    # Buy points (Golden Cross)
    buy_points = chart_data[chart_data['GoldenCross']]
    ax.scatter(buy_points.index, buy_points['Close'], color='red', label='Buy Point', marker='o', s=60)

    # Sell points (from positions)
    sell_points = positions.copy()
    ax.scatter(sell_points['SellDate'], sell_points['SellPrice'], color='purple', label='Sell Point', marker='o', s=60)

    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.legend()
    st.pyplot(fig)

elif page == "Trade Statistics":
    st.title("Trade Statistics Summary")
    stats = analyze_results(positions)
    total_trades = len(positions)
    win_trades = len(positions[positions['ProfitPct'] > 0])
    loss_trades = total_trades - win_trades
    win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0
    avg_profit = positions['ProfitPct'].mean()
    avg_win = positions[positions['ProfitPct'] > 0]['ProfitPct'].mean() if win_trades > 0 else 0
    avg_loss = positions[positions['ProfitPct'] <= 0]['ProfitPct'].mean() if loss_trades > 0 else 0
    avg_holding = positions['HoldingDays'].mean()
    target_reached = len(positions[positions['SellReason'] == 'Target reached'])
    max_period = len(positions[positions['SellReason'] == 'Max holding period'])

    st.metric("Total Trades", total_trades)
    st.metric("Winning Trades", win_trades)
    st.metric("Losing Trades", loss_trades)
    st.metric("Win Rate (%)", f"{win_rate:.2f}")
    st.metric("Average Profit (%)", f"{avg_profit:.2f}")
    st.metric("Average Win (%)", f"{avg_win:.2f}")
    st.metric("Average Loss (%)", f"{avg_loss:.2f}")
    st.metric("Average Holding Days", f"{avg_holding:.2f}")
    st.metric("Target Reached Trades", target_reached)
    st.metric("Max Holding Period Trades", max_period)

elif page == "Detailed Trades":
    st.title("Detailed Trades Record")
    st.dataframe(positions)
    st.download_button("Download Trades as CSV", positions.to_csv(index=False), "trades.csv")
