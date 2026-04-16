"""Curated GICS sector universe — static discovery data for sector browsing.

This module maps each major GICS sector (plus an ETFs pseudo-sector) to an
ordered list of well-known, liquid symbols.  It is intentionally separate from
yf_client.py (which is a network integration layer) so that the data model
stays clean.
"""

SECTOR_UNIVERSE: dict[str, list[str]] = {
    "Technology": [
        "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AVGO", "ORCL",
        "ADBE", "CRM", "AMD", "INTC", "QCOM", "CSCO", "IBM",
    ],
    "Healthcare": [
        "UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT",
        "DHR", "BMY", "AMGN", "GILD",
    ],
    "Financials": [
        "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK",
        "SCHW", "C", "AXP", "SPGI",
    ],
    "Energy": [
        "XOM", "CVX", "COP", "SLB", "EOG", "OXY", "PSX", "MPC",
        "VLO", "PXD", "HAL", "KMI",
    ],
    "Consumer Discretionary": [
        "AMZN", "TSLA", "HD", "MCD", "NKE", "LOW",
        "SBUX", "BKNG", "TJX", "ABNB", "F", "GM",
    ],
    "Consumer Staples": [
        "WMT", "PG", "KO", "PEP", "COST", "PM", "MO",
        "CL", "MDLZ", "TGT", "KMB", "GIS",
    ],
    "Industrials": [
        "GE", "CAT", "BA", "HON", "UPS", "RTX", "LMT", "DE",
        "UNP", "ETN", "ADP", "FDX",
    ],
    "Materials": [
        "LIN", "SHW", "APD", "ECL", "FCX", "NEM", "DOW",
        "DD", "NUE", "CTVA", "PPG", "ALB",
    ],
    "Real Estate": [
        "PLD", "AMT", "EQIX", "CCI", "PSA", "WELL", "DLR",
        "O", "SPG", "AVB", "EQR", "VTR",
    ],
    "Utilities": [
        "NEE", "SO", "DUK", "SRE", "AEP", "D", "XEL", "EXC",
        "PCG", "CEG", "ED", "WEC",
    ],
    "Communication Services": [
        "META", "GOOGL", "NFLX", "DIS", "T", "VZ",
        "CMCSA", "TMUS", "CHTR", "EA", "TTWO", "WBD",
    ],
    "ETFs": [
        "SPY", "QQQ", "VTI", "VOO", "IWM", "DIA",
        "XLK", "XLF", "XLE", "XLV", "XLY", "XLI", "XLU", "XLRE",
    ],
}

# Stable display order for UI chips — matches insertion order above.
SECTOR_DISPLAY_ORDER: list[str] = list(SECTOR_UNIVERSE.keys())


def get_symbols_for_sector(sector: str, limit: int = 30) -> list[str]:
    """Return symbol list for *sector* (case-insensitive). Returns [] if unknown."""
    sector_lower = sector.strip().lower()
    for key, syms in SECTOR_UNIVERSE.items():
        if key.lower() == sector_lower:
            return syms[:limit]
    return []
