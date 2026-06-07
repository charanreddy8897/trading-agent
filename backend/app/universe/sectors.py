SECTORS: dict[str, list[str]] = {
    "AI_SOFTWARE": [
        "NVDA", "MSFT", "GOOG", "META", "AMZN", "PLTR", "AI",
        "SNOW", "CRM", "NOW", "PATH", "DDOG", "SMCI",
    ],
    "SEMICONDUCTORS": [
        "NVDA", "AMD", "INTC", "AVGO", "QCOM", "MU", "MRVL",
        "ARM", "TSM", "ASML", "LRCX", "AMAT", "ON", "ACMR",
        "TER", "KLAC",
    ],
    "MEMORY": [
        "MU", "WDC", "STX", "NXPI",
    ],
    "SPACE_DEFENSE": [
        "RKLB", "LMT", "BA", "NOC", "ASTS", "LUNR", "RDW",
        "SPIR", "RTX", "GD",
    ],
    "PHYSICAL_AI_ROBOTICS": [
        "ISRG", "TER", "TSLA", "ABBNY", "FANUY", "RCAT", "GH",
    ],
}

# Sectors whose combined exposure is capped together
CORRELATED_GROUPS: list[list[str]] = [
    ["AI_SOFTWARE", "SEMICONDUCTORS", "MEMORY"],
]

ALL_TICKERS: list[str] = list(set(
    t for tickers in SECTORS.values() for t in tickers
))

TICKER_SECTOR: dict[str, str] = {
    ticker: sector
    for sector, tickers in SECTORS.items()
    for ticker in tickers
}

BENCHMARKS: list[str] = ["SPY", "QQQ", "SMH"]
