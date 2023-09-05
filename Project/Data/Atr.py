import yfinance as yf
import ta
import pandas as pd
import matplotlib.pyplot as plt

ticker = "AAPL"
df = yf.download(ticker, start="2010-01-01", end="2022-12-31")
df["atr"] = ta.volatility.AverageTrueRange(
    df["High"], df["Low"], df["Close"], window=14).average_true_range()

print(df)

plt.plot(df["atr"], label="ATR")
plt.legend()
plt.title("Apple Stock ATR")
plt.xlabel("Date")
plt.ylabel("Price")
plt.show()
