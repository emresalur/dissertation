import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import ta

ticker = "AAPL"
df = yf.download('AAPL', start='2010-01-01', end='2022-12-31')
df["bb"] = ta.volatility.BollingerBands(
    df["Close"], window=20, window_dev=2).bollinger_hband()

plt.plot(df["bb"], label="Bollinger Bands")
plt.legend()
plt.title("Apple Stock Bollinger Bands")
plt.xlabel("Date")
plt.ylabel("Price")
plt.show()
