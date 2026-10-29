
import sqlite3
from pathlib import Path
import pandas as pd

# Folder containing this script and your CSV files
folder = Path(__file__).parent

# Create one SQLite database
database_path = folder / "stock_research.db"

# Find all historical price CSV files
csv_files = list(folder.glob("*_historical_prices.csv"))

if not csv_files:
    print("No historical price CSV files found.")
    raise SystemExit(1)

with sqlite3.connect(database_path) as connection:
    for csv_file in csv_files:
        # Example: AAPL_historical_prices.csv -> AAPL
        ticker = csv_file.name.replace("_historical_prices.csv", "")

        print(f"Importing {ticker}...")

        # Load CSV
        df = pd.read_csv(csv_file, index_col="Date", parse_dates=True)

        # Store dates as readable text
        df.index = pd.to_datetime(df.index, utc=True).strftime("%Y-%m-%d")

        # Put each stock into its own SQLite table
        table_name = f"prices_{ticker.lower()}"

        df.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=True,
            index_label="Date"
        )

        print(f"  Imported {len(df)} daily records.")

print(f"\nDatabase created at: {database_path}")
