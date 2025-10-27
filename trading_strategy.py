import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# Download stock data
def get_stock_data(ticker, period="5y"):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        if data.empty:
            print(f"No data found for ticker: {ticker}")
            return None
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# Calculate moving averages
def calculate_moving_averages(data):
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()
    return data

# Identify golden cross (buy signals)
def identify_golden_cross(data):
    data['Signal'] = 0
    data['GoldenCross'] = (data['MA50'] > data['MA200']) & (data['MA50'].shift(1) <= data['MA200'].shift(1))
    return data

# Implement trading strategy
def implement_strategy(data):
    positions = []

    # Need at least 200 days to calculate the 200-day MA
    if len(data) < 200:
        print("Not enough data for analysis (need at least 200 days)")
        return pd.DataFrame(positions)
    
    data = data.iloc[200:].copy()
    buy_dates = data[data['GoldenCross'] == True].index.tolist()

    print(f"Found {len(buy_dates)} golden cross signals")

    for buy_date in buy_dates:
        buy_price = data.loc[buy_date, 'Close']
        buy_open = data.loc[buy_date, 'Open']
        buy_high = data.loc[buy_date, 'High']
        buy_low = data.loc[buy_date, 'Low']
        
        target_price = buy_price * 1.15  # Take-profit (15%)
        stop_loss_price = buy_price * 0.90  # Stop-loss (10%)
        max_sell_date = buy_date + pd.Timedelta(days=60)
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

    return pd.DataFrame(positions)

# Analyze the results
def analyze_results(positions, ticker=""):
    if positions.empty:
        print(f"No trading signals detected for {ticker}" if ticker else "No trading signals detected")
        return positions

    total_trades = len(positions)
    win_trades = len(positions[positions['ProfitPct'] > 0])
    loss_trades = total_trades - win_trades
    win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0
    avg_profit = positions['ProfitPct'].mean()

    print(f"\n===== Trading Strategy Results for {ticker} =====")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {win_trades} ({win_rate:.2f}%)")
    print(f"Losing Trades: {loss_trades}")
    print(f"Average Profit: {avg_profit:.2f}%")

    return positions

# Main function
def main(tickers=["MSFT", "AAPL", "TSLA"]):
    all_positions = []
    
    if isinstance(tickers, str):
        tickers = [tickers]
    
    for ticker in tickers:
        print(f"\nProcessing {ticker}...")
        data = get_stock_data(ticker)
        if data is None:
            continue
            
        data = calculate_moving_averages(data)
        data = identify_golden_cross(data)
        positions = implement_strategy(data)
        
        if not positions.empty:
            positions["Ticker"] = ticker
            all_positions.append(positions)
            analyze_results(positions, ticker)
        else:
            print(f"No valid trades found for {ticker}")
    
    if all_positions:
        portfolio_positions = pd.concat(all_positions, ignore_index=True)
        print(f"\n=== Portfolio Summary ===")
        print(f"Total stocks analyzed: {len(tickers)}")
        print(f"Stocks with trades: {len(all_positions)}")
        print(f"Total trades: {len(portfolio_positions)}")
    else:
        portfolio_positions = pd.DataFrame()
        print("No trades generated for any stock")
    
    return portfolio_positions

# Only run this if the script is executed directly
if __name__ == "__main__":
    # Example usage
    positions = main(["MSFT", "AAPL", "TSLA"])
    if not positions.empty:
        print("\nDetailed Trades:")
        print(positions.to_string())