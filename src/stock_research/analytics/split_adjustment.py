
from datetime import date
from math import prod


def adjust_eps_for_stock_splits(
    reported_eps: float,
    period_end: date,
    split_events: list[tuple[date, float]],
) -> float:
    """Adjust original reported EPS for stock splits after its fiscal period."""
    adjustment_factor = prod(
        ratio
        for split_date, ratio in split_events
        if split_date > period_end
    )
    return reported_eps / adjustment_factor
