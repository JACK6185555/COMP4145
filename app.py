import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from trading_strategy import get_stock_data, calculate_moving_averages, identify_golden_cross, implement_strategy, main

st.set_page_config(page_title="Golden Cross Trading Dashboard", layout="wide")

def load_custom_data(tickers):
    """Load data for custom tickers"""
    positions = main(tickers)
    return positions

def get_chart_data(ticker):
    """Get price and MA data for chart display"""
    data = get_stock_data(ticker)
    if data is not None:
        data = calculate_moving_averages(data)
        data = identify_golden_cross(data)
    return data

# Sidebar for stock selection
st.sidebar.title("Stock Selection")

# Default tickers
default_tickers = ["MSFT", "AAPL", "TSLA"]

# User input for custom tickers
st.sidebar.subheader("Custom Tickers")
user_tickers_input = st.sidebar.text_input(
    "Enter stock tickers (comma separated)",
    value=", ".join(default_tickers)
)

# Process user input
if user_tickers_input:
    user_tickers = [ticker.strip().upper() for ticker in user_tickers_input.split(",") if ticker.strip()]
else:
    user_tickers = default_tickers


# Initialize positions
positions = pd.DataFrame()

# Run analysis button
if st.sidebar.button("Start Analysis"):
    with st.spinner(f"Analyzing {len(user_tickers)} stocks: {', '.join(user_tickers)}"):
        positions = load_custom_data(user_tickers)
else:
    # Use default analysis on initial load
    try:
        positions = load_custom_data(user_tickers)
    except:
        positions = pd.DataFrame()

# Sidebar navigation
page = st.sidebar.radio("Select Page", 
                       ["Price Chart", 
                        "Trade Statistics", 
                        "Detailed Trades", 
                        "Backtesting Module"])

if page == "Price Chart":
    st.title("Price Chart with Golden Cross Signals")
    
    if not positions.empty:
        available_tickers = positions['Ticker'].unique()
        selected_ticker = st.selectbox("Select Ticker", available_tickers)
        
        chart_data = get_chart_data(selected_ticker)
        if chart_data is not None:
            fig, ax = plt.subplots(figsize=(14, 6))
            ax.plot(chart_data.index, chart_data['Close'], label='Close Price', color='blue', linewidth=1)
            ax.plot(chart_data.index, chart_data['MA50'], label='MA50', color='orange', linewidth=1)
            ax.plot(chart_data.index, chart_data['MA200'], label='MA200', color='green', linewidth=1)

            # Buy points (Golden Cross)
            buy_points = chart_data[chart_data['GoldenCross']]
            ax.scatter(buy_points.index, buy_points['Close'], color='green', label='Buy Signal', marker='^', s=100)

            # Filter positions for selected ticker
            ticker_positions = positions[positions['Ticker'] == selected_ticker]
            
            # Sell points (from positions)
            if not ticker_positions.empty:
                ax.scatter(ticker_positions['SellDate'], ticker_positions['SellPrice'], 
                          color='red', label='Sell Point', marker='v', s=100)

            ax.set_xlabel('Date')
            ax.set_ylabel('Price ($)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_title(f'{selected_ticker} - Price Chart')
            st.pyplot(fig)
            
            # Show signals summary
            st.subheader("Signals Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Golden Cross Signals", len(buy_points))
            with col2:
                st.metric("Completed Trades", len(ticker_positions))
            with col3:
                if len(ticker_positions) > 0:
                    win_rate = (ticker_positions['ProfitPct'] > 0).mean() * 100
                    st.metric("Win Rate", f"{win_rate:.1f}%")
        else:
            st.error(f"Cannot fetch data for {selected_ticker}")
    else:
        st.warning("No trade data available. Please run analysis first.")

elif page == "Trade Statistics":
    st.title("Portfolio Trade Statistics Summary")
    
    if positions.empty:
        st.warning("No trades data available. Please run analysis first.")
    else:
        # Overall portfolio statistics
        st.subheader("Portfolio Overview")
        
        total_trades = len(positions)
        win_trades = len(positions[positions['ProfitPct'] > 0])
        loss_trades = total_trades - win_trades
        win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0
        avg_profit = positions['ProfitPct'].mean()
        avg_holding = positions['HoldingDays'].mean()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", total_trades)
            st.metric("Average Profit", f"{avg_profit:.2f}%")
        with col2:
            st.metric("Winning Trades", win_trades)
            st.metric("Average Holding Days", f"{avg_holding:.1f}")
        with col3:
            st.metric("Losing Trades", loss_trades)
            st.metric("Win Rate", f"{win_rate:.2f}%")
        with col4:
            total_stocks = positions['Ticker'].nunique()
            st.metric("Stocks Analyzed", total_stocks)
            st.metric("Analysis Period", period)

        # Portfolio allocation pie chart
        st.subheader("Portfolio Allocation")
        col1, col2 = st.columns(2)
        
        with col1:
            alloc = positions.groupby("Ticker")['BuyPrice'].sum()
            if not alloc.empty:
                fig1, ax1 = plt.subplots()
                ax1.pie(alloc, labels=alloc.index, autopct='%1.1f%%', startangle=90)
                ax1.set_title("Allocation by Buy Price")
                st.pyplot(fig1)
        
        with col2:
            trade_count = positions['Ticker'].value_counts()
            if not trade_count.empty:
                fig2, ax2 = plt.subplots()
                ax2.bar(trade_count.index, trade_count.values)
                ax2.set_title("Trades per Stock")
                ax2.set_ylabel("Number of Trades")
                plt.xticks(rotation=45)
                st.pyplot(fig2)

        # Per-stock performance
        st.subheader("Per-Stock Performance")
        if "Ticker" in positions.columns:
            per_stock = positions.groupby("Ticker").agg({
                'ProfitPct': ['mean', 'count', 'std'],
                'HoldingDays': 'mean'
            }).round(2)
            per_stock.columns = ['Avg Profit (%)', 'Trade Count', 'Std Dev', 'Avg Holding Days']
            st.dataframe(per_stock)

elif page == "Detailed Trades":
    st.title("Detailed Trades Record")
    
    if positions.empty:
        st.warning("No trades to display. Please run analysis first.")
    else:
        st.success(f"Found {len(positions)} trades")
        
        # Filter by ticker
        if positions['Ticker'].nunique() > 1:
            selected_ticker = st.selectbox("Filter by Ticker", ["All"] + list(positions['Ticker'].unique()))
            if selected_ticker != "All":
                display_positions = positions[positions['Ticker'] == selected_ticker]
            else:
                display_positions = positions
        else:
            display_positions = positions

        # Display columns
        display_columns = [
            'Ticker', 'BuyDate', 'BuyPrice', 'BuyOpen', 'BuyHigh', 'BuyLow',
            'SellDate', 'SellPrice', 'SellOpen', 'SellHigh', 'SellLow',
            'HoldingDays', 'ProfitPct', 'SellReason'
        ]
        
        available_columns = [col for col in display_columns if col in display_positions.columns]
        st.dataframe(display_positions[available_columns])
        
        # Download button
        st.download_button(
            "Download Trades as CSV", 
            display_positions.to_csv(index=False), 
            "trades.csv", 
            "text/csv"
        )

# Backtesting Module
# Backtesting Module with complete implementation
# Backtesting Module with custom ticker input
elif page == "Backtesting Module":
    st.title("Customizable Strategy Backtesting")
    st.write("Select strategy parameters and run backtests across your portfolio.")
    
    st.info("**Note:** Maximum 5 stocks per backtest due to Yahoo Finance restrictions")

    # User input for custom tickers in backtesting
    st.subheader("Stock Selection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        backtest_tickers_input = st.text_input(
            "Enter stock tickers (comma separated, max 5)",
            value="MSFT, AAPL, TSLA",
            help="Examples: MSFT, AAPL, TSLA, GOOGL, AMZN, NVDA, META, NFLX, 0005.HK"
        )
    
    with col2:
        st.markdown("###")
        st.markdown("**Popular Tickers:**")
        st.markdown("US: MSFT, AAPL, TSLA")
        st.markdown("HK: 0005.HK, 0700.HK")

    # Process user input for backtesting
    if backtest_tickers_input:
        backtest_tickers = [ticker.strip().upper() for ticker in backtest_tickers_input.split(",") if ticker.strip()]
        # Limit to first 5 stocks
        if len(backtest_tickers) > 5:
            st.warning(f"Limited to first 5 stocks: {', '.join(backtest_tickers[:5])}")
            backtest_tickers = backtest_tickers[:5]
    else:
        backtest_tickers = ["MSFT", "AAPL", "TSLA"]

    # Display current selection
    if backtest_tickers:
        st.success(f"**Selected Stocks ({len(backtest_tickers)})**: {', '.join(backtest_tickers)}")
    
    # Strategy parameters
    st.subheader("Strategy Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ma_short = st.number_input("Short Moving Average Window", min_value=5, max_value=100, value=50, key="backtest_ma_short")
        ma_long = st.number_input("Long Moving Average Window", min_value=20, max_value=300, value=200, key="backtest_ma_long")
        holding_period = st.number_input("Max Holding Period (days)", min_value=5, max_value=180, value=60, key="backtest_holding")
    
    with col2:
        stop_loss_pct = st.number_input("Stop-Loss (%)", min_value=1.0, max_value=50.0, value=10.0, key="backtest_stop_loss")
        take_profit_pct = st.number_input("Take-Profit (%)", min_value=1.0, max_value=100.0, value=15.0, key="backtest_take_profit")
        period_backtest = st.selectbox("Data Period", ["6mo", "1y", "2y", "5y", "max"], index=3, key="backtest_period")

    # Strategy parameter presets
    st.subheader("Quick Strategy Presets")
    
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
    
    with preset_col1:
        if st.button("🏛️ Golden Cross Classic", use_container_width=True):
            st.session_state.backtest_ma_short = 50
            st.session_state.backtest_ma_long = 200
            st.session_state.backtest_holding = 60
            st.session_state.backtest_stop_loss = 10.0
            st.session_state.backtest_take_profit = 15.0
            st.rerun()
    
    with preset_col2:
        if st.button("⚡ Short-term", use_container_width=True):
            st.session_state.backtest_ma_short = 20
            st.session_state.backtest_ma_long = 50
            st.session_state.backtest_holding = 30
            st.session_state.backtest_stop_loss = 5.0
            st.session_state.backtest_take_profit = 8.0
            st.rerun()
    
    with preset_col3:
        if st.button("🛡️ Conservative", use_container_width=True):
            st.session_state.backtest_ma_short = 100
            st.session_state.backtest_ma_long = 200
            st.session_state.backtest_holding = 90
            st.session_state.backtest_stop_loss = 8.0
            st.session_state.backtest_take_profit = 12.0
            st.rerun()
    
    with preset_col4:
        if st.button("🎯 Aggressive", use_container_width=True):
            st.session_state.backtest_ma_short = 10
            st.session_state.backtest_ma_long = 30
            st.session_state.backtest_holding = 20
            st.session_state.backtest_stop_loss = 15.0
            st.session_state.backtest_take_profit = 25.0
            st.rerun()

    # Initialize session state for backtest parameters
    if 'backtest_ma_short' not in st.session_state:
        st.session_state.backtest_ma_short = 50
    if 'backtest_ma_long' not in st.session_state:
        st.session_state.backtest_ma_long = 200
    if 'backtest_holding' not in st.session_state:
        st.session_state.backtest_holding = 60
    if 'backtest_stop_loss' not in st.session_state:
        st.session_state.backtest_stop_loss = 10.0
    if 'backtest_take_profit' not in st.session_state:
        st.session_state.backtest_take_profit = 15.0

    # Complete Backtesting function
    def run_custom_strategy(tickers, ma_short, ma_long, holding_period, stop_loss_pct, take_profit_pct, period="5y"):
        results = []
        successful_tickers = []
        failed_tickers = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(tickers):
            try:
                # Update progress
                progress = (i / len(tickers))
                progress_bar.progress(progress)
                status_text.text(f"Analyzing {ticker}... ({i+1}/{len(tickers)})")
                
                # Add delay to avoid rate limiting
                import time
                time.sleep(0.5)
                
                data = get_stock_data(ticker, period)
                if data is None or data.empty:
                    failed_tickers.append(ticker)
                    continue
                
                # Custom moving averages
                data['MA_short'] = data['Close'].rolling(window=int(ma_short)).mean()
                data['MA_long'] = data['Close'].rolling(window=int(ma_long)).mean()
                
                # Custom golden cross
                data['GoldenCross'] = (data['MA_short'] > data['MA_long']) & (data['MA_short'].shift(1) <= data['MA_long'].shift(1))
                
                positions = []
                
                # Need enough data for the longer moving average
                if len(data) >= ma_long:
                    data = data.iloc[int(ma_long):].copy()
                    buy_dates = data[data['GoldenCross'] == True].index.tolist()
                    
                    for buy_date in buy_dates:
                        buy_price = data.loc[buy_date, 'Close']
                        buy_open = data.loc[buy_date, 'Open']
                        buy_high = data.loc[buy_date, 'High']
                        buy_low = data.loc[buy_date, 'Low']
                        
                        target_price = buy_price * (1 + take_profit_pct/100)
                        stop_loss_price = buy_price * (1 - stop_loss_pct/100)
                        max_sell_date = buy_date + pd.Timedelta(days=int(holding_period))
                        sell_period = data.loc[buy_date:max_sell_date].copy()
                        
                        # Check for stop-loss first
                        stop_loss_hit = sell_period[sell_period['Close'] <= stop_loss_price]
                        target_reached = sell_period[sell_period['Close'] >= target_price]

                        if not stop_loss_hit.empty:
                            sell_date = stop_loss_hit.index[0]
                            sell_price = stop_loss_hit.loc[sell_date, 'Close']
                            sell_open = data.loc[sell_date, 'Open']
                            sell_high = data.loc[sell_date, 'High']
                            sell_low = data.loc[sell_date, 'Low']
                            sell_reason = "Stop-loss hit"
                        elif not target_reached.empty:
                            sell_date = target_reached.index[0]
                            sell_price = target_reached.loc[sell_date, 'Close']
                            sell_open = data.loc[sell_date, 'Open']
                            sell_high = data.loc[sell_date, 'High']
                            sell_low = data.loc[sell_date, 'Low']
                            sell_reason = "Target reached"
                        else:
                            sell_date_candidates = sell_period.index.tolist()
                            if sell_date_candidates:
                                sell_date = sell_date_candidates[-1]
                                sell_price = data.loc[sell_date, 'Close']
                                sell_open = data.loc[sell_date, 'Open']
                                sell_high = data.loc[sell_date, 'High']
                                sell_low = data.loc[sell_date, 'Low']
                                sell_reason = "Max holding period"
                            else:
                                continue

                        holding_days = (sell_date - buy_date).days
                        profit_pct = (sell_price / buy_price - 1) * 100
                        
                        positions.append({
                            'Ticker': ticker,
                            'BuyDate': buy_date,
                            'BuyPrice': buy_price,
                            'BuyOpen': buy_open,
                            'BuyHigh': buy_high,
                            'BuyLow': buy_low,
                            'SellDate': sell_date,
                            'SellPrice': sell_price,
                            'SellOpen': sell_open,
                            'SellHigh': sell_high,
                            'SellLow': sell_low,
                            'HoldingDays': holding_days,
                            'ProfitPct': profit_pct,
                            'SellReason': sell_reason
                        })
                
                if positions:
                    results.append(pd.DataFrame(positions))
                    successful_tickers.append(ticker)
                else:
                    successful_tickers.append(ticker)  # Successfully analyzed but no trades
                    
            except Exception as e:
                failed_tickers.append(ticker)
                continue
        
        # Complete progress bar
        progress_bar.progress(1.0)
        status_text.text("Analysis complete!")
        
        # Show summary
        if failed_tickers:
            st.warning(f"Failed to analyze: {', '.join(failed_tickers)}")
        
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame()

    # Run Backtest button
    st.markdown("---")
    if st.button("🚀 Run Backtest Analysis", type="primary", use_container_width=True):
        if not backtest_tickers:
            st.error("Please enter at least one stock ticker.")
        else:
            try:
                with st.spinner("Running backtest analysis... This may take a few moments"):
                    backtest_results = run_custom_strategy(
                        backtest_tickers, ma_short, ma_long, holding_period, 
                        stop_loss_pct, take_profit_pct, period_backtest
                    )
                
                if not backtest_results.empty:
                    st.success(f"✅ Backtest completed! Found {len(backtest_results)} trades across {backtest_results['Ticker'].nunique()} stocks")
                    
                    # Display results
                    st.subheader("📊 Backtest Results")
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_trades = len(backtest_results)
                    avg_profit = backtest_results['ProfitPct'].mean()
                    win_rate = (backtest_results['ProfitPct'] > 0).mean() * 100
                    avg_holding = backtest_results['HoldingDays'].mean()
                    
                    with col1:
                        st.metric("Total Trades", total_trades)
                        st.metric("Stocks Analyzed", backtest_results['Ticker'].nunique())
                    
                    with col2:
                        st.metric("Average Profit (%)", f"{avg_profit:.2f}%")
                        st.metric("Win Rate", f"{win_rate:.2f}%")
                    
                    with col3:
                        win_trades = len(backtest_results[backtest_results['ProfitPct'] > 0])
                        loss_trades = total_trades - win_trades
                        st.metric("Winning Trades", win_trades)
                        st.metric("Losing Trades", loss_trades)
                    
                    with col4:
                        st.metric("Avg Holding Days", f"{avg_holding:.1f}")
                        st.metric("Strategy", f"MA{ma_short}/{ma_long}")
                    
                    # Detailed results table
                    st.subheader("📋 Detailed Trades")
                    st.dataframe(backtest_results)
                    
                    # Performance by stock
                    st.subheader("📈 Performance by Stock")
                    stock_performance = backtest_results.groupby('Ticker').agg({
                        'ProfitPct': ['mean', 'count', 'std'],
                        'HoldingDays': 'mean',
                        'BuyPrice': 'mean'
                    }).round(2)
                    stock_performance.columns = ['Avg Profit (%)', 'Trade Count', 'Std Dev', 'Avg Holding Days', 'Avg Buy Price']
                    st.dataframe(stock_performance)
                    
                    # Visualizations
                    col_viz1, col_viz2 = st.columns(2)
                    
                    with col_viz1:
                        # Sell reason breakdown
                        st.subheader("📊 Exit Reasons")
                        sell_reasons = backtest_results['SellReason'].value_counts()
                        fig1, ax1 = plt.subplots()
                        ax1.pie(sell_reasons.values, labels=sell_reasons.index, autopct='%1.1f%%', startangle=90)
                        ax1.set_title("Exit Reasons Distribution")
                        st.pyplot(fig1)
                    
                    with col_viz2:
                        # Profit distribution
                        st.subheader("💰 Profit Distribution")
                        fig2, ax2 = plt.subplots()
                        ax2.hist(backtest_results['ProfitPct'], bins=20, alpha=0.7, color='skyblue')
                        ax2.axvline(0, color='red', linestyle='--', label='Break-even')
                        ax2.set_xlabel('Profit (%)')
                        ax2.set_ylabel('Number of Trades')
                        ax2.legend()
                        st.pyplot(fig2)
                    
                    # Download button for backtest results
                    st.subheader("💾 Export Results")
                    csv_data = backtest_results.to_csv(index=False)
                    st.download_button(
                        "Download Backtest Results as CSV", 
                        csv_data, 
                        f"backtest_results_{ma_short}_{ma_long}.csv", 
                        "text/csv",
                        use_container_width=True
                    )
                    
                else:
                    st.warning("❌ No trades generated for the selected parameters and stocks.")
                    st.info("""
                    **💡 Suggestions to generate trades:**
                    - Try different moving average periods
                    - Adjust stop-loss and take-profit levels
                    - Select different stocks or more stocks
                    - Extend the analysis period
                    - Use shorter moving averages for more signals
                    """)
                    
            except Exception as e:
                st.error(f"❌ Backtesting failed: {str(e)}")
                st.info("""
                **🔧 Possible solutions:**
                - Reduce the number of stocks
                - Try again in a few moments (Yahoo Finance rate limits)
                - Check your internet connection
                - Verify the stock tickers are valid
                - Try with popular US stocks first
                """)

    # Example tickers for user reference
    st.markdown("---")
    st.subheader("💡 Popular Ticker Examples")
    
    example_col1, example_col2, example_col3 = st.columns(3)
    
    with example_col1:
        st.markdown("**US Stocks:**")
        st.markdown("- MSFT (Microsoft)")
        st.markdown("- AAPL (Apple)")
        st.markdown("- TSLA (Tesla)")
        st.markdown("- GOOGL (Google)")
        
    with example_col2:
        st.markdown("**More US Stocks:**")
        st.markdown("- AMZN (Amazon)")
        st.markdown("- NVDA (NVIDIA)")
        st.markdown("- META (Meta/Facebook)")
        st.markdown("- NFLX (Netflix)")
        
    with example_col3:
        st.markdown("**HK Stocks:**")
        st.markdown("- 0005.HK (HSBC)")
        st.markdown("- 0700.HK (Tencent)")
        st.markdown("- 0939.HK (CCB)")
        st.markdown("- 1299.HK (AIA)")