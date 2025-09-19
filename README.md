# financial-data-aggregator
Create a system to scrape financial news sites and the SEC EDGAR database for mentions of specific companies and keywords. Data is processed to perform sentiment analysis and track filing changes.




# Financial Data Aggregator

A system to scrape financial news sites and the SEC EDGAR database for mentions of specific companies and keywords. Data is processed to perform sentiment analysis and track filing changes.

## Features

- SEC EDGAR filings downloader
- Financial news scraper (Reuters, Bloomberg, Financial Times)
- Sentiment analysis using NLTK
- Configurable company list and keywords
- Data export in JSON format

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Usage

Run the complete pipeline:
```bash
python -m src.main --all
```

Run specific components:
```bash
# Only SEC filings
python -m src.main --sec

# Only news scraping
python -m src.main --news

# Only sentiment analysis
python -m src.main --sentiment
```

## Configuration

Edit `config/companies.json` to add/remove companies and keywords.

Modify `config/settings.py` to adjust scraping parameters and thresholds.

## Project Structure

```
financial_data_aggregator/
├── config/          # Configuration files
├── data/           # Data storage
├── src/            # Source code
├── tests/          # Test cases
├── requirements.txt # Dependencies
└── README.md       # Documentation
```

## Important Notes

- Respect website terms of service and robots.txt
- Add appropriate delays between requests
- SEC EDGAR has specific rate limiting requirements
- News websites may change their structure, requiring code updates
```