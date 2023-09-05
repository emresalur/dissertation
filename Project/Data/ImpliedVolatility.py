import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
from scipy.stats import norm

# Fetch the stock data
ticker = "AAPL"
df = yf.download('AAPL', start='2010-01-01', end='2022-12-31')

# Define a function to calculate implied volatility


def implied_volatility(price, S, K, T, r):
    d1 = (np.log(S/K) + (r + 0.5 * price**2) * T) / (price * np.sqrt(T))
    d2 = d1 - price * np.sqrt(T)
    return price * S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


# Compute implied volatility
option_price = df['Close']
S = df['Close'].iloc[-1]
K = S
T = (df.index[-1] - df.index[0]).days / 365
r = 0.02
price = np.linspace(0.1, 1, 100)
impl_vol = [implied_volatility(p, S, K, T, r) for p in price]

# Plot the results
plt.plot(price, impl_vol)
plt.xlabel('Volatility')
plt.ylabel('Option Price')
plt.title(f'Implied Volatility for {ticker} Stock')
plt.show()
