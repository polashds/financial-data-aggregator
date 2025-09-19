
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SEC EDGAR settings
SEC_EDGAR_BASE_URL = "https://www.sec.gov/edgar/searchedgar/companysearch.html"
SEC_RATE_LIMIT_DELAY = 0.1  # seconds between requests

# News sources
NEWS_SOURCES = {
    "reuters": "https://www.reuters.com/finance",
    "bloomberg": "https://www.bloomberg.com/markets",
    "financial_times": "https://www.ft.com/?edition=international"
}

# Sentiment analysis
SENTIMENT_THRESHOLD = 0.2  # Above this is positive, below negative is negative

# Data storage
RAW_DATA_PATH = BASE_DIR / "data" / "raw"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed"
OUTPUTS_PATH = BASE_DIR / "data" / "outputs"

