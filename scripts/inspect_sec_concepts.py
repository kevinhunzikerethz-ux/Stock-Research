
"""Check quarterly and cumulative SEC observations."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "sec_raw" / "aapl_companyfacts.json"

CONCEPTS = [
    "NetCashProvidedByUsedInOperatingActivities",
    "PaymentsToAcquirePropertyPlantAndEquipment",
]

TARGET_END_DATES = {
    "2025-12-27",
    "2026-03-28",
    "2026-06-27",
}


def main() -> None:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    us_gaap = data["facts"]["us-gaap"]

    for name in CONCEPTS:
        concept = us_gaap.get(name)

        print(f"\n{'=' * 80}")
        print(name)

        if concept is None:
            print("Concept not available.")
            continue

        for unit, observations in concept.get("units", {}).items():
            matches = [
                item
                for item in observations
                if item.get("end") in TARGET_END_DATES
                and item.get("form") in {"10-Q", "10-K"}
                and item.get("filed", "").startswith("2025")
                or (
                    item.get("end") in TARGET_END_DATES
                    and item.get("form") in {"10-Q", "10-K"}
                    and item.get("filed", "").startswith("2026")
                )
            ]

            matches.sort(
                key=lambda item: (
                    item.get("end", ""),
                    item.get("start", ""),
                    item.get("filed", ""),
                )
            )

            print(f"\nUnit: {unit}")
            print(
                f"{'START':<12} {'END':<12} {'VALUE ($B)':>12} "
                f"{'FP':>4} {'FILED':<12}"
            )
            print("-" * 60)

            for item in matches:
                value_billions = item["val"] / 1_000_000_000
                print(
                    f"{item.get('start', '-'):12} "
                    f"{item.get('end', '-'):12} "
                    f"{value_billions:12.3f} "
                    f"{item.get('fp', '-'):>4} "
                    f"{item.get('filed', '-'):12}"
                )


if __name__ == "__main__":
    main()
