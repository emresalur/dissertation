import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

ticker = "AAPL"
df = yf.download('AAPL', start='2010-01-01', end='2022-12-31')

df["returns"] = df["Close"].pct_change()

volatility = df["returns"].std() * np.sqrt(252)

print("Historical volatility of Apple stock: {:.2f}%".format(volatility * 100))

# Plot the historical volatility
plt.hist(df["returns"], bins=100, label="Returns")
plt.axvline(volatility, color="r", label="Volatility")
plt.legend()
plt.title("Apple Stock Historical Volatility")
plt.show()
