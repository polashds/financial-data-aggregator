
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import settings
from utils.logger import logger

class FinancialDataDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or (Path(__file__).parent.parent.parent / "data" / "financial_data.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Companies table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS companies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        ticker TEXT UNIQUE NOT NULL,
                        cik TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # SEC Filings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sec_filings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_id INTEGER,
                        filing_type TEXT NOT NULL,
                        filing_date TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        content_length INTEGER,
                        sections TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (company_id) REFERENCES companies (id)
                    )
                ''')
                
                # News articles table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS news_articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_id INTEGER,
                        title TEXT NOT NULL,
                        excerpt TEXT,
                        content TEXT,
                        published_date TEXT,
                        source TEXT NOT NULL,
                        url TEXT NOT NULL,
                        sentiment_score REAL,
                        sentiment_label TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (company_id) REFERENCES companies (id)
                    )
                ''')
                
                # Sentiment results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sentiment_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_id INTEGER,
                        analysis_date TEXT NOT NULL,
                        total_articles INTEGER,
                        positive_count INTEGER,
                        negative_count INTEGER,
                        neutral_count INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (company_id) REFERENCES companies (id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def add_company(self, name, ticker, cik):
        """Add a company to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO companies (name, ticker, cik) VALUES (?, ?, ?)",
                    (name, ticker, cik)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add company {name}: {str(e)}")
            return None
    
    def add_sec_filing(self, company_id, filing_type, filing_date, file_path, content_length, sections):
        """Add SEC filing to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO sec_filings 
                    (company_id, filing_type, filing_date, file_path, content_length, sections) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                    (company_id, filing_type, filing_date, str(file_path), content_length, json.dumps(sections))
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add SEC filing: {str(e)}")
            return None
    
    def add_news_article(self, company_id, title, excerpt, content, published_date, source, url, 
                         sentiment_score=None, sentiment_label=None):
        """Add news article to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO news_articles 
                    (company_id, title, excerpt, content, published_date, source, url, sentiment_score, sentiment_label) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (company_id, title, excerpt, content, published_date, source, url, sentiment_score, sentiment_label)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add news article: {str(e)}")
            return None
    
    def add_sentiment_result(self, company_id, analysis_date, total_articles, 
                            positive_count, negative_count, neutral_count):
        """Add sentiment analysis results to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO sentiment_results 
                    (company_id, analysis_date, total_articles, positive_count, negative_count, neutral_count) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                    (company_id, analysis_date, total_articles, positive_count, negative_count, neutral_count)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add sentiment result: {str(e)}")
            return None
    
    def get_company_id(self, ticker):
        """Get company ID by ticker symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM companies WHERE ticker = ?",
                    (ticker,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get company ID for {ticker}: {str(e)}")
            return None
    
    def get_latest_sentiment(self, company_id, days=30):
        """Get sentiment results for a company for the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''SELECT analysis_date, total_articles, positive_count, negative_count, neutral_count 
                    FROM sentiment_results 
                    WHERE company_id = ? AND date(analysis_date) >= date('now', ?) 
                    ORDER BY analysis_date DESC''',
                    (company_id, f'-{days} days')
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to get sentiment results: {str(e)}")
            return []