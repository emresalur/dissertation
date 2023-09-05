import yfinance as yf
import ta
import matplotlib.pyplot as plt

# Download the stock price data of Apple Inc. (AAPL) from Yahoo Finance
df = yf.download('AAPL', start='2010-01-01', end='2022-12-31')

# Calculate the Moving Average Convergence Divergence (MACD)
df['macd'] = ta.trend.MACD(df['Close']).macd()
df['macd_signal'] = ta.trend.MACD(df['Close']).macd_signal()

# Plot the stock price and MACD
plt.plot(df.index, df['macd'], label='MACD')
plt.plot(df.index, df['macd_signal'], label='MACD Signal Line')
plt.legend()
plt.show()
