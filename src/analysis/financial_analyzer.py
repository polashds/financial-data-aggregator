
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.logger import logger

class FinancialAnalyzer:
    """Advanced financial analysis tools"""
    
    def __init__(self, db):
        self.db = db
    
    def calculate_sentiment_trend(self, company_id, days=30):
        """Calculate sentiment trend for a company"""
        try:
            sentiment_data = self.db.get_latest_sentiment(company_id, days)
            
            if not sentiment_data:
                return None
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(sentiment_data, columns=[
                'date', 'total_articles', 'positive', 'negative', 'neutral'
            ])
            
            # Calculate daily sentiment score
            df['sentiment_score'] = (df['positive'] - df['negative']) / df['total_articles']
            
            # Calculate moving averages
            df['ma_7'] = df['sentiment_score'].rolling(window=7).mean()
            df['ma_30'] = df['sentiment_score'].rolling(window=min(30, len(df))).mean()
            
            # Calculate trend direction
            if len(df) >= 2:
                recent_trend = "up" if df['sentiment_score'].iloc[-1] > df['sentiment_score'].iloc[-2] else "down"
            else:
                recent_trend = "stable"
            
            return {
                'trend_direction': recent_trend,
                'current_score': df['sentiment_score'].iloc[-1] if len(df) > 0 else 0,
                'average_score': df['sentiment_score'].mean(),
                'volatility': df['sentiment_score'].std(),
                'data': df.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error calculating sentiment trend: {str(e)}")
            return None
    
    def detect_anomalies(self, company_id, window=14, threshold=2.0):
        """Detect anomalies in sentiment data"""
        try:
            sentiment_data = self.db.get_latest_sentiment(company_id, 90)  # 3 months data
            
            if not sentiment_data or len(sentiment_data) < window:
                return None
            
            df = pd.DataFrame(sentiment_data, columns=[
                'date', 'total_articles', 'positive', 'negative', 'neutral'
            ])
            
            # Calculate sentiment score
            df['sentiment_score'] = (df['positive'] - df['negative']) / df['total_articles']
            
            # Calculate rolling mean and standard deviation
            df['rolling_mean'] = df['sentiment_score'].rolling(window=window).mean()
            df['rolling_std'] = df['sentiment_score'].rolling(window=window).std()
            
            # Detect anomalies (values outside mean ± threshold * std)
            df['anomaly'] = np.where(
                abs(df['sentiment_score'] - df['rolling_mean']) > threshold * df['rolling_std'],
                1, 0
            )
            
            # Get anomaly dates and values
            anomalies = df[df['anomaly'] == 1][['date', 'sentiment_score']].to_dict('records')
            
            return {
                'anomaly_count': len(anomalies),
                'anomalies': anomalies,
                'data': df.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return None
    
    def correlate_news_filings(self, company_id, days_before=7, days_after=7):
        """Correlate news sentiment with SEC filing dates"""
        try:
            # Get filing dates
            with self.db.conn:
                cursor = self.db.conn.cursor()
                cursor.execute(
                    '''SELECT filing_date FROM sec_filings 
                    WHERE company_id = ? AND date(filing_date) >= date('now', ?) 
                    ORDER BY filing_date DESC''',
                    (company_id, f'-{days_before + days_after + 30} days')
                )
                filing_dates = [row[0] for row in cursor.fetchall()]
            
            # Get sentiment data
            sentiment_data = self.db.get_latest_sentiment(company_id, days_before + days_after + 30)
            
            if not sentiment_data or not filing_dates:
                return None
            
            df = pd.DataFrame(sentiment_data, columns=[
                'date', 'total_articles', 'positive', 'negative', 'neutral'
            ])
            df['date'] = pd.to_datetime(df['date'])
            df['sentiment_score'] = (df['positive'] - df['negative']) / df['total_articles']
            
            results = []
            
            for filing_date in filing_dates:
                filing_date = pd.to_datetime(filing_date)
                
                # Get sentiment window around filing date
                start_date = filing_date - timedelta(days=days_before)
                end_date = filing_date + timedelta(days=days_after)
                
                window_data = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                
                if len(window_data) > 0:
                    # Calculate pre and post-filing sentiment
                    pre_filing = window_data[window_data['date'] < filing_date]
                    post_filing = window_data[window_data['date'] >= filing_date]
                    
                    pre_avg = pre_filing['sentiment_score'].mean() if len(pre_filing) > 0 else 0
                    post_avg = post_filing['sentiment_score'].mean() if len(post_filing) > 0 else 0
                    
                    results.append({
                        'filing_date': filing_date.strftime('%Y-%m-%d'),
                        'pre_filing_sentiment': pre_avg,
                        'post_filing_sentiment': post_avg,
                        'sentiment_change': post_avg - pre_avg,
                        'data_points': len(window_data)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error correlating news and filings: {str(e)}")
            return None