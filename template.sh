# # create project root
# mkdir -p financial_data_aggregator

# # go inside
# cd financial_data_aggregator

# create folders
mkdir -p config data/raw data/processed data/outputs src tests

# create Python files
touch config/__init__.py config/settings.py config/companies.json
touch src/__init__.py src/sec_edgar.py src/news_scraper.py src/sentiment_analyzer.py src/main.py
touch tests/__init__.py tests/test_sec_edgar.py tests/test_sentiment.py

# create project-level files
touch requirements.txt README.md .gitignore
