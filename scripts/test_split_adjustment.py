
from datetime import date

from stock_research.analytics.split_adjustment import (
    adjust_eps_for_stock_splits,
)


def main():
    apple_splits = [
        (date(2014, 6, 9), 7.0),
        (date(2020, 8, 31), 4.0),
    ]

    examples = [
        (date(2012, 9, 29), 44.15),
        (date(2018, 9, 29), 11.91),
        (date(2025, 9, 27), 7.46),
    ]

    for period_end, reported_eps in examples:
        adjusted_eps = adjust_eps_for_stock_splits(
            reported_eps,
            period_end,
            apple_splits,
        )
        print(
            f"{period_end} | "
            f"Reported EPS: ${reported_eps:.2f} | "
            f"Adjusted EPS: ${adjusted_eps:.2f}"
        )


if __name__ == "__main__":
    main()
