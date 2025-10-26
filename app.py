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
page = st.sidebar.radio("Select Page", ["Price Chart", "Trade Statistics", "Detailed Trades", "Backtesting Module"])

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
    st.title("Portfolio Trade Statistics Summary")
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

    st.subheader("Portfolio Metrics")
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

    # Portfolio allocation pie chart
    st.subheader("Portfolio Allocation")
    if "Ticker" in positions.columns:
        alloc = positions.groupby("Ticker")['BuyPrice'].sum()
        fig2, ax2 = plt.subplots()
        ax2.pie(alloc, labels=alloc.index, autopct='%1.1f%%', startangle=90)
        ax2.set_title("Allocation by Buy Price")
        st.pyplot(fig2)

    # Per-stock breakdowns
    st.subheader("Per-Stock Performance")
    if "Ticker" in positions.columns:
        per_stock = positions.groupby("Ticker").agg({
            'ProfitPct': ['mean', 'count'],
            'HoldingDays': 'mean'
        })
        per_stock.columns = ['Avg Profit (%)', 'Trade Count', 'Avg Holding Days']
        st.dataframe(per_stock)


elif page == "Detailed Trades":
    st.title("Detailed Trades Record")
    st.dataframe(positions)
    st.download_button("Download Trades as CSV", positions.to_csv(index=False), "trades.csv")

# --- Backtesting Module ---
elif page == "Backtesting Module":
    st.title("Customizable Strategy Backtesting")
    st.write("Select strategy parameters and run backtests across your portfolio.")

    # User inputs for strategy parameters
    tickers = st.multiselect("Select Tickers", ["MSFT", "AAPL", "TSLA", "AMZN", "GOOG"], default=["MSFT", "AAPL", "TSLA"])
    ma_short = st.number_input("Short Moving Average Window", min_value=10, max_value=100, value=50)
    ma_long = st.number_input("Long Moving Average Window", min_value=50, max_value=300, value=200)
    holding_period = st.number_input("Max Holding Period (days)", min_value=10, max_value=120, value=60)
    stop_loss_pct = st.number_input("Stop-Loss (%)", min_value=1.0, max_value=50.0, value=10.0)
    take_profit_pct = st.number_input("Take-Profit (%)", min_value=1.0, max_value=50.0, value=15.0)

    def run_custom_strategy(tickers, ma_short, ma_long, holding_period, stop_loss_pct, take_profit_pct):
        from trading_strategy import get_stock_data
        results = []
        for ticker in tickers:
            data = get_stock_data(ticker)
            # Custom moving averages
            data['MA_short'] = data['Close'].rolling(window=int(ma_short)).mean()
            data['MA_long'] = data['Close'].rolling(window=int(ma_long)).mean()
            # Custom golden cross
            data['GoldenCross'] = (data['MA_short'] > data['MA_long']) & (data['MA_short'].shift(1) <= data['MA_long'].shift(1))
            # Custom strategy logic
            positions = []
            data = data.iloc[int(ma_long):].copy()
            buy_dates = data[data['GoldenCross'] == True].index.tolist()
            for buy_date in buy_dates:
                buy_price = data.loc[buy_date, 'Close']
                target_price = buy_price * (1 + take_profit_pct/100)
                stop_loss_price = buy_price * (1 - stop_loss_pct/100)
                max_sell_date = buy_date + pd.Timedelta(days=int(holding_period))
                sell_period = data.loc[buy_date:max_sell_date].copy()
                stop_loss_hit = sell_period[sell_period['Close'] <= stop_loss_price]
                target_reached = sell_period[sell_period['Close'] >= target_price]
                if not stop_loss_hit.empty:
                    sell_date = stop_loss_hit.index[0]
                    sell_price = stop_loss_hit.loc[sell_date, 'Close']
                    sell_reason = "Stop-loss hit"
                elif not target_reached.empty:
                    sell_date = target_reached.index[0]
                    sell_price = target_reached.loc[sell_date, 'Close']
                    sell_reason = "Target reached"
                else:
                    sell_date_candidates = sell_period.index.tolist()
                    if sell_date_candidates:
                        sell_date = sell_date_candidates[-1]
                        sell_price = data.loc[sell_date, 'Close']
                        sell_reason = "Max holding period"
                    else:
                        continue
                holding_days = (sell_date - buy_date).days
                profit_pct = (sell_price / buy_price - 1) * 100
                positions.append({
                    'Ticker': ticker,
                    'BuyDate': buy_date,
                    'BuyPrice': buy_price,
                    'SellDate': sell_date,
                    'SellPrice': sell_price,
                    'HoldingDays': holding_days,
                    'ProfitPct': profit_pct,
                    'SellReason': sell_reason
                })
            if positions:
                results.append(pd.DataFrame(positions))
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame()

    if st.button("Run Backtest"):
        backtest_results = run_custom_strategy(tickers, ma_short, ma_long, holding_period, stop_loss_pct, take_profit_pct)
        if not backtest_results.empty:
            st.success("Backtest completed!")
            st.dataframe(backtest_results)
            # Portfolio summary
            st.subheader("Backtest Portfolio Summary")
            st.metric("Total Trades", len(backtest_results))
            st.metric("Average Profit (%)", f"{backtest_results['ProfitPct'].mean():.2f}")
            st.metric("Win Rate (%)", f"{(backtest_results['ProfitPct'] > 0).mean()*100:.2f}")
            # Allocation pie chart
            alloc = backtest_results.groupby("Ticker")['BuyPrice'].sum()
            fig3, ax3 = plt.subplots()
            ax3.pie(alloc, labels=alloc.index, autopct='%1.1f%%', startangle=90)
            ax3.set_title("Allocation by Buy Price")
            st.pyplot(fig3)
        else:
            st.warning("No trades generated for selected parameters.")
