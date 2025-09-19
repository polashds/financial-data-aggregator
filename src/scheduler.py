
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from utils.logger import logger

from sec_edgar import SECEdgarScraper
from news_scraper import NewsScraper
from sentiment_analyzer import SentimentAnalyzer

class DataAggregatorScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.sec_scraper = SECEdgarScraper()
        self.news_scraper = NewsScraper()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def schedule_daily_tasks(self):
        """Schedule daily data collection and processing tasks"""
        
        # Schedule SEC filings scraping (weekdays at 2 AM)
        self.scheduler.add_job(
            self.scrape_sec_filings,
            trigger=CronTrigger(day_of_week='mon-fri', hour=2, minute=0),
            id='sec_scraping',
            name='Scrape SEC EDGAR filings',
            replace_existing=True
        )
        
        # Schedule news scraping (every 4 hours during market hours)
        self.scheduler.add_job(
            self.scrape_news,
            trigger=CronTrigger(day_of_week='mon-fri', hour='9-17/4', minute=0),
            id='news_scraping',
            name='Scrape financial news',
            replace_existing=True
        )
        
        # Schedule sentiment analysis (after market close)
        self.scheduler.add_job(
            self.analyze_sentiment,
            trigger=CronTrigger(day_of_week='mon-fri', hour=18, minute=0),
            id='sentiment_analysis',
            name='Analyze news sentiment',
            replace_existing=True
        )
        
        # Schedule weekly report generation (Friday after market close)
        self.scheduler.add_job(
            self.generate_weekly_report,
            trigger=CronTrigger(day_of_week='fri', hour=19, minute=0),
            id='weekly_report',
            name='Generate weekly report',
            replace_existing=True
        )
        
        logger.info("Scheduled tasks initialized")
    
    def scrape_sec_filings(self):
        """Task to scrape SEC filings"""
        logger.info("Starting SEC filings scraping task")
        try:
            results = self.sec_scraper.process_all_companies(limit=5)
            logger.info(f"SEC scraping completed: {len(results)} companies processed")
        except Exception as e:
            logger.error(f"SEC scraping task failed: {str(e)}")
    
    def scrape_news(self):
        """Task to scrape news"""
        logger.info("Starting news scraping task")
        try:
            results = self.news_scraper.process_all_companies()
            total_articles = sum([len(r) for r in results.values()])
            logger.info(f"News scraping completed: {total_articles} articles collected")
        except Exception as e:
            logger.error(f"News scraping task failed: {str(e)}")
    
    def analyze_sentiment(self):
        """Task to analyze sentiment"""
        logger.info("Starting sentiment analysis task")
        try:
            results = self.sentiment_analyzer.process_all_companies()
            logger.info(f"Sentiment analysis completed: {len(results)} companies analyzed")
        except Exception as e:
            logger.error(f"Sentiment analysis task failed: {str(e)}")
    
    def generate_weekly_report(self):
        """Task to generate weekly report"""
        logger.info("Starting weekly report generation")
        try:
            # This would generate a comprehensive weekly report
            # including sentiment trends, filing changes, etc.
            report_date = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"Weekly report generated for {report_date}")
        except Exception as e:
            logger.error(f"Weekly report generation failed: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        self.schedule_daily_tasks()
        self.scheduler.start()
        logger.info("Data aggregator scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Data aggregator scheduler stopped")

# For running the scheduler directly
if __name__ == "__main__":
    scheduler = DataAggregatorScheduler()
    
    try:
        scheduler.start()
        # Keep the script running
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()