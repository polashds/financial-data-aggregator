
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import json
from pathlib import Path
from config import settings

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

class SentimentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.processed_data_path = settings.PROCESSED_DATA_PATH
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
    
    def analyze_text(self, text):
        """Analyze sentiment of text"""
        scores = self.sia.polarity_scores(text)
        
        # Determine sentiment label
        if scores['compound'] >= settings.SENTIMENT_THRESHOLD:
            sentiment = "positive"
        elif scores['compound'] <= -settings.SENTIMENT_THRESHOLD:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            'scores': scores,
            'sentiment': sentiment
        }
    
    def analyze_news_articles(self, articles):
        """Analyze sentiment of news articles"""
        analyzed_articles = []
        
        for article in articles:
            # Combine title and excerpt for analysis
            text = f"{article['title']}. {article['excerpt']}"
            sentiment = self.analyze_text(text)
            
            analyzed_articles.append({
                **article,
                'sentiment': sentiment
            })
        
        return analyzed_articles
    
    def process_company_news(self, ticker):
        """Process news sentiment for a company"""
        input_file = settings.RAW_DATA_PATH / "news" / f"{ticker}_news.json"
        
        if not input_file.exists():
            print(f"No news data found for {ticker}")
            return None
        
        # Load news data
        with open(input_file, 'r') as f:
            news_data = json.load(f)
        
        # Analyze sentiment
        analyzed_articles = self.analyze_news_articles(news_data['articles'])
        
        # Calculate overall sentiment
        sentiment_counts = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        
        for article in analyzed_articles:
            sentiment_counts[article['sentiment']['sentiment']] += 1
        
        # Prepare results
        results = {
            'company': news_data['company'],
            'ticker': news_data['ticker'],
            'articles_count': len(analyzed_articles),
            'sentiment_distribution': sentiment_counts,
            'articles': analyzed_articles
        }
        
        # Save results
        output_file = self.processed_data_path / f"{ticker}_sentiment.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
    
    def process_all_companies(self):
        """Process sentiment for all companies"""
        results = {}
        
        # Load companies data
        with open(Path(__file__).parent.parent / "config" / "companies.json", "r") as f:
            companies = json.load(f)["companies"]
        
        for company in companies:
            print(f"Analyzing sentiment for {company['name']}...")
            result = self.process_company_news(company['ticker'])
            if result:
                results[company['ticker']] = result
        
        return results

# Example usage
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    results = analyzer.process_all_companies()
    
    for ticker, data in results.items():
        print(f"{ticker}: {data['sentiment_distribution']}")