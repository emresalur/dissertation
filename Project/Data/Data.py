import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Define the ticker symbol and start and end dates
ticker = "AAPL"
start_date = "2010-01-01"
end_date = "2022-12-31"

# Download the data
data = yf.download(ticker, start_date, end_date)

# Calculate daily returns
returns = data["Adj Close"].pct_change()

# Plot the histogram of daily returns
plt.subplot(2, 1, 1)
plt.hist(returns, bins=50, edgecolor="black")
plt.xlabel(xlabel="Daily returns")
plt.ylabel(ylabel="Frequency")
plt.title("Histogram of Daily Returns for " + ticker)

# Calculate the mean and standard deviation of daily returns
mean_returns = np.mean(returns)
std_returns = np.std(returns)

# Print the mean and standard deviation of daily returns
print("Mean of daily returns: " + str(mean_returns))
print("Standard deviation of daily returns: " + str(std_returns))

# Add the moving average to the data
data["50-day MA"] = data["Adj Close"].rolling(window=50).mean()
data["200-day MA"] = data["Adj Close"].rolling(window=200).mean()

# Plot the stock price and moving averages
plt.subplot(2, 1, 2)
plt.plot(data["Adj Close"], label="Stock Price")
plt.plot(data["50-day MA"], label="50-day MA")
plt.plot(data["200-day MA"], label="200-day MA")
plt.xlabel(xlabel="Date")
plt.ylabel(ylabel="Price")
plt.title("Stock Price and Moving Averages for " + ticker)
plt.legend()

# Add space between the subplots
plt.subplots_adjust(hspace=0.6)

# Show the plot
plt.show()

# Create a new dataframe with the returns
returns = pd.DataFrame(data["Adj Close"].pct_change().dropna())
returns["Intercept"] = 1

# Fit a linear regression model
model = LinearRegression()
model.fit(returns[["Intercept", "Adj Close"]], returns["Adj Close"])

# Print the intercept and coefficient of the regression line
print("Intercept: " + str(model.intercept_))
print("Coefficient: " + str(model.coef_[1]))
