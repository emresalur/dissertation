import yfinance as yf
import ta
import matplotlib.pyplot as plt

# Download the stock price data of Apple Inc. (AAPL) from Yahoo Finance
df = yf.download('AAPL', start='2010-01-01', end='2022-12-31')

# Calculate the Relative Strength Index (RSI)
df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()

# Plot the stock price and RSI
plt.plot(df.index, df['Close'], label='Stock Price')
plt.plot(df.index, df['rsi'], label='Relative Strength Index (RSI)')
plt.legend()
plt.show()
