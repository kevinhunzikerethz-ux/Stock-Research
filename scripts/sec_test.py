
import requests

HEADERS = {
    "User-Agent": "StockResearchTerminal/0.1 your-real-email@example.com"
}

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"


def get_cik(ticker):
    response = requests.get(TICKERS_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    for company in response.json().values():
        if company["ticker"].upper() == ticker.upper():
            return str(company["cik_str"]).zfill(10)

    raise ValueError(f"Ticker not found in SEC mapping: {ticker}")


def get_latest_annual_fact(facts, concept):
    """Return the latest full-year observation for a financial concept."""
    if concept not in facts:
        return None

    concept_data = facts[concept]
    units = concept_data.get("units", {})

    # Prefer USD or USD/shares, depending on the concept.
    preferred_unit = "USD/shares" if concept == "EarningsPerShareDiluted" else "USD"

    if preferred_unit not in units:
        return None

    observations = []

    for item in units[preferred_unit]:
        # Annual 10-K observations typically span approximately one year.
        if item.get("form") != "10-K":
            continue

        start = item.get("start")
        end = item.get("end")

        # Flow metrics have a start and end date; balance-sheet values
        # are point-in-time observations and should not be annualized.
        if start:
            from datetime import date

            duration_days = (
                date.fromisoformat(end) - date.fromisoformat(start)
            ).days

            if not 330 <= duration_days <= 380:
                continue

        observations.append(item)

    if not observations:
        return None

    # The latest period end wins; prefer the most recently filed observation
    # when the same period has been reported more than once.
    observations.sort(
        key=lambda item: (item.get("end", ""), item.get("filed", ""))
    )

    return observations[-1]


def main():
    ticker = input("Enter a stock ticker (e.g. AAPL): ").strip().upper()

    try:
        cik = get_cik(ticker)
        url = FACTS_URL.format(cik)

        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        facts = data["facts"].get("us-gaap", {})

        concepts = {
            "Revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Operating income": "OperatingIncomeLoss",
            "Net income": "NetIncomeLoss",
            "Diluted EPS": "EarningsPerShareDiluted",
            "Operating cash flow": "NetCashProvidedByUsedInOperatingActivities",
            "Capital expenditures": "PaymentsToAcquirePropertyPlantAndEquipment",
            "Cash and equivalents": "CashAndCashEquivalentsAtCarryingValue",
            "Current long-term debt": "LongTermDebtCurrent",
            "Long-term debt": "LongTermDebtNoncurrent",
        }

        print(f"\n{data['entityName']} — latest annual observations")
        print("=" * 75)

        for label, concept in concepts.items():
            item = get_latest_annual_fact(facts, concept)

            if item is None:
                print(f"{label:25} No suitable annual observation found")
                continue

            value = item["val"]
            unit = (
                "USD/share"
                if concept == "EarningsPerShareDiluted"
                else "USD"
            )

            print(
                f"{label:25} {value:>18,.2f} {unit:10} "
                f"| Period end: {item['end']} "
                f"| Filed: {item['filed']}"
            )

        print("=" * 75)

    except (requests.RequestException, ValueError, KeyError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
