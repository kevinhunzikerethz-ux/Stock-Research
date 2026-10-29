import yfinance as yf

ticker = "IREN"

stock = yf.Ticker(ticker)

# Retrieve the maximum available daily history
prices = stock.history(
    period="max",
    interval="1d",
    auto_adjust=False,
    actions=True,
)

if prices.empty:
    raise RuntimeError("No historical data returned.")

prices.index.name = "Date"
prices.to_csv(f"{ticker}_historical_prices.csv")

print(prices.head())
print(prices.tail())
print(f"Downloaded {len(prices)} daily observations.")
print(f"Earliest date: {prices.index.min()}")
