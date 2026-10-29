
import json
from pathlib import Path


def check_eps_restatements():
    path = Path("data/sec_raw/aapl_companyfacts.json")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    observations = data["facts"]["us-gaap"][
        "EarningsPerShareDiluted"
    ]["units"]["USD/shares"]

    target_periods = {
        "2012-09-29",
        "2013-09-28",
        "2016-09-24",
        "2018-09-29",
    }

    for end_date in sorted(target_periods):
        print(f"\nPeriod end: {end_date}")

        matches = [
            item for item in observations
            if item.get("end") == end_date
            and item.get("form") == "10-K"
            and item.get("start")
            and 350 <= (
                __import__("datetime").date.fromisoformat(item["end"])
                - __import__("datetime").date.fromisoformat(item["start"])
            ).days <= 380
        ]

        for item in sorted(matches, key=lambda x: x.get("filed", "")):
            print(
                f"Start={item['start']} | EPS={item['val']:.2f} "
                f"| Filed={item['filed']} | FY={item.get('fy')} "
                f"| Accession={item.get('accn')}"
            )


if __name__ == "__main__":
    check_eps_restatements()
