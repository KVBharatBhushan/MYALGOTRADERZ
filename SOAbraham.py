# SOAbraham.py

import pandas as pd
import numpy as np
import talib
import yfinance as yf  # For downloading historical stock data

def download_data(symbol, start_date, end_date):
    data = yf.download(symbol, start=start_date, end=end_date)
    return data

def calculate_indicators(data):
    # Super Trend
    data['atr'] = talib.ATR(data['High'], data['Low'], data['Close'], timeperiod=14)
    data['st_upper'] = data['High'] - 1.5 * data['atr']
    data['st_lower'] = data['Low'] + 1.5 * data['atr']
    data['super_trend'] = np.where(data['Close'] > data['st_upper'], data['st_upper'], 
                                   np.where(data['Close'] < data['st_lower'], data['st_lower'], data['super_trend'].shift(1)))

    # MACD
    data['macd'], data['signal'], _ = talib.MACD(data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)

    # VOWP
    data['vowp'] = data['Volume'] / talib.SMA(data['Volume'], timeperiod=20)

    # EMA 20 & 50
    data['ema20'] = talib.EMA(data['Close'], timeperiod=20)
    data['ema50'] = talib.EMA(data['Close'], timeperiod=50)

    return data

def generate_signals(data):
    data['buy_signal'] = np.where((data['Close'] > data['super_trend']) & 
                                  (data['Close'] > data['ema20']) & 
                                  (data['ema20'] > data['ema50']) &
                                  (data['macd'] > data['signal']) &
                                  (data['vowp'] < data['super_trend']), 1, 0)

    data['sell_signal'] = np.where(data['Close'] < data['super_trend'], 1, 0)

    return data

def backtest(data, risk_reward_ratio=2):
    positions = []
    position = 0
    entry_price = 0

    for i in range(len(data)):
        if data['buy_signal'][i] == 1:
            entry_price = data['Close'][i]
            stop_loss = entry_price - data['atr'][i]
            take_profit = entry_price + risk_reward_ratio * data['atr'][i]
            position = 1
        elif data['sell_signal'][i] == 1 and position == 1:
            position = 0
        elif position == 1 and (data['Close'][i] < stop_loss or data['Close'][i] > take_profit):
            position = 0

        positions.append(position)

    data['position'] = positions
    return data

if __name__ == '__main__':
    # Set the parameters
    symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
    start_date = '2023-01-01'
    end_date = '2023-11-01'

    for symbol in symbols:
        # Download historical data
        historical_data = download_data(symbol, start_date, end_date)

        # Calculate technical indicators
        data_with_indicators = calculate_indicators(historical_data)

        # Generate buy/sell signals
        signals_data = generate_signals(data_with_indicators)

        # Backtest the strategy
        backtested_data = backtest(signals_data)

        # Save the backtested data to a CSV file
        output_file = f'{symbol}_options_trading_results.csv'
        backtested_data.to_csv(output_file)

        print(f"Results for {symbol} saved to {output_file}")
