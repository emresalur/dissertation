import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import ta

# Download the stock price data of AAPL
df = yf.download("AAPL", start="2010-01-01", end="2022-12-31")

# Create a new column with the date as index
df["Date"] = df.index

# Reshape the data into a long format
df = df.melt(id_vars='Date', value_vars=['Close'])

# Fit a linear regression model
model = sm.OLS(df['value'], sm.add_constant(df['Date']).astype(int))
results = model.fit()

# Plot the stock price and trend line
plt.subplot(2, 1, 1)
plt.plot(df['Date'], df['value'], label='Stock Price')
plt.plot(df['Date'], results.fittedvalues, label='Trend Line', linestyle='--')
plt.legend()

# Show the plot
plt.show()
