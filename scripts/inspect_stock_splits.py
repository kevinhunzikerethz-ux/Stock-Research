
import yfinance as yf


def inspect_stock_splits():
    ticker = yf.Ticker("AAPL")
    splits = ticker.splits

    print("Apple stock splits from yfinance:")
    if splits.empty:
        print("No split events returned.")
        return

    for date, ratio in splits.items():
        print(f"{date.date()} | split ratio: {ratio:g}")


if __name__ == "__main__":
    inspect_stock_splits()
