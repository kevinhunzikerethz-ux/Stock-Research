
"""Explore raw SEC Company Facts data for one company."""
import gzip
import json
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen


CIK = "0000320193"  # Apple Inc.
TICKER = "AAPL"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "sec_raw"
OUTPUT_FILE = OUTPUT_DIR / f"{TICKER.lower()}_companyfacts.json"

SEC_URL = (
    f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"
)

# SEC requires a descriptive User-Agent identifying the application
# and providing contact information.
USER_AGENT = "StockResearchTerminal research contact@example.com"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    request = Request(
        SEC_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        },
    )

    print(f"Fetching SEC Company Facts for {TICKER}...")

    with urlopen(request, timeout=30) as response:
        raw_data = response.read()
        content_encoding = response.headers.get("Content-Encoding", "")

    if content_encoding.lower() == "gzip" or raw_data.startswith(b"\x1f\x8b"):
        raw_data = gzip.decompress(raw_data)

    facts = json.loads(raw_data)

    facts = json.loads(raw_data)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(facts, file, indent=2)

    company = facts.get("entityName", "Unknown company")
    namespaces = facts.get("facts", {})

    print(f"\nCompany: {company}")
    print(f"Saved raw JSON to: {OUTPUT_FILE}")
    print(f"File size: {len(raw_data):,} bytes")

    for namespace, concepts in namespaces.items():
        print(f"\n{namespace}: {len(concepts):,} concepts")

        if namespace == "us-gaap":
            for concept_name, concept in list(concepts.items())[:15]:
                units = ", ".join(concept.get("units", {}).keys())
                print(f"  {concept_name} [{units}]")

    us_gaap = namespaces.get("us-gaap", {})
    print(f"\nTotal US-GAAP concepts: {len(us_gaap):,}")

    unit_counts = Counter()
    observation_count = 0

    for concept in us_gaap.values():
        for unit, observations in concept.get("units", {}).items():
            unit_counts[unit] += 1
            observation_count += len(observations)

    print(f"Total US-GAAP observations across concepts: {observation_count:,}")
    print("Concept counts by unit:")
    for unit, count in unit_counts.most_common():
        print(f"  {unit}: {count:,} concept-unit groups")


if __name__ == "__main__":
    main()
