import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.sec_edgar import SECEdgarScraper
from src.news_scraper import NewsScraper
from src.sentiment_analyzer import SentimentAnalyzer

def main():
    parser = argparse.ArgumentParser(description="Financial Data Aggregator")
    parser.add_argument("--sec", action="store_true", help="Scrape SEC filings")
    parser.add_argument("--news", action="store_true", help="Scrape news")
    parser.add_argument("--sentiment", action="store_true", help="Analyze sentiment")
    parser.add_argument("--all", action="store_true", help="Run all processes")
    
    args = parser.parse_args()
    
    # If no specific arguments provided, show help
    if not any([args.sec, args.news, args.sentiment, args.all]):
        parser.print_help()
        return
    
    # Run all if --all flag is provided
    if args.all:
        args.sec = True
        args.news = True
        args.sentiment = True
    
    results = {}
    
    # SEC Edgar scraping
    if args.sec:
        print("=" * 50)
        print("Scraping SEC Edgar filings...")
        print("=" * 50)
        sec_scraper = SECEdgarScraper()
        sec_results = sec_scraper.process_all_companies(limit=2)
        results['sec'] = sec_results
    
    # News scraping
    if args.news:
        print("=" * 50)
        print("Scraping news...")
        print("=" * 50)
        news_scraper = NewsScraper()
        news_results = news_scraper.process_all_companies()
        results['news'] = {
            ticker: {"articles_count": data["articles_count"]} 
            for ticker, data in news_results.items()
        }
    
    # Sentiment analysis
    if args.sentiment:
        print("=" * 50)
        print("Analyzing sentiment...")
        print("=" * 50)
        sentiment_analyzer = SentimentAnalyzer()
        sentiment_results = sentiment_analyzer.process_all_companies()
        results['sentiment'] = {
            ticker: data["sentiment_distribution"] 
            for ticker, data in sentiment_results.items()
        }
    
    # Generate summary report
    generate_report(results)
    
    print("=" * 50)
    print("Process completed!")
    print("=" * 50)

def generate_report(results):
    """Generate a summary report of the processed data"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {}
    }
    
    if 'sec' in results:
        report['summary']['sec_filings'] = {
            "total_companies": len(results['sec']),
            "successful_downloads": sum(1 for r in results['sec'].values() if r['status'] == 'success')
        }
    
    if 'news' in results:
        total_articles = sum(data['articles_count'] for data in results['news'].values())
        report['summary']['news'] = {
            "total_companies": len(results['news']),
            "total_articles": total_articles
        }
    
    if 'sentiment' in results:
        positive = sum(data['positive'] for data in results['sentiment'].values())
        negative = sum(data['negative'] for data in results['sentiment'].values())
        neutral = sum(data['neutral'] for data in results['sentiment'].values())
        total = positive + negative + neutral
        
        report['summary']['sentiment'] = {
            "total_articles": total,
            "positive_articles": positive,
            "negative_articles": negative,
            "neutral_articles": neutral,
            "positive_percentage": round(positive / total * 100, 2) if total > 0 else 0,
            "negative_percentage": round(negative / total * 100, 2) if total > 0 else 0
        }
    
    # Save report
    from config import settings
    report_file = settings.OUTPUTS_PATH / "summary_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to {report_file}")
    
    # Print summary
    print("\nSummary:")
    print(f"Timestamp: {report['timestamp']}")
    
    if 'sec_filings' in report['summary']:
        sec = report['summary']['sec_filings']
        print(f"SEC Filings: {sec['successful_downloads']}/{sec['total_companies']} companies successful")
    
    if 'news' in report['summary']:
        news = report['summary']['news']
        print(f"News: {news['total_articles']} articles from {news['total_companies']} companies")
    
    if 'sentiment' in report['summary']:
        sent = report['summary']['sentiment']
        print(f"Sentiment: {sent['positive_articles']} positive ({sent['positive_percentage']}%), "
              f"{sent['negative_articles']} negative ({sent['negative_percentage']}%), "
              f"{sent['neutral_articles']} neutral")

if __name__ == "__main__":
    main()