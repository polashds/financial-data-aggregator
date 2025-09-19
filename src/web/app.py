
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import json
from pathlib import Path

from data.database import FinancialDataDB
from config import settings

app = Flask(__name__, 
            template_folder=Path(__file__).parent / "templates",
            static_folder=Path(__file__).parent / "static")

db = FinancialDataDB()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/companies')
def get_companies():
    """Get list of companies"""
    try:
        with db.conn:
            cursor = db.conn.cursor()
            cursor.execute("SELECT id, name, ticker FROM companies ORDER BY name")
            companies = [{"id": row[0], "name": row[1], "ticker": row[2]} for row in cursor.fetchall()]
        return jsonify(companies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sentiment/<int:company_id>')
def get_sentiment(company_id):
    """Get sentiment data for a company"""
    try:
        days = request.args.get('days', 30, type=int)
        
        with db.conn:
            cursor = db.conn.cursor()
            cursor.execute(
                '''SELECT analysis_date, total_articles, positive_count, negative_count, neutral_count 
                FROM sentiment_results 
                WHERE company_id = ? AND date(analysis_date) >= date('now', ?) 
                ORDER BY analysis_date DESC''',
                (company_id, f'-{days} days')
            )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "date": row[0],
                    "total_articles": row[1],
                    "positive": row[2],
                    "negative": row[3],
                    "neutral": row[4]
                })
            
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news/<int:company_id>')
def get_news(company_id):
    """Get recent news for a company"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        with db.conn:
            cursor = db.conn.cursor()
            cursor.execute(
                '''SELECT title, excerpt, published_date, source, url, sentiment_label 
                FROM news_articles 
                WHERE company_id = ? 
                ORDER BY published_date DESC 
                LIMIT ?''',
                (company_id, limit)
            )
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    "title": row[0],
                    "excerpt": row[1],
                    "date": row[2],
                    "source": row[3],
                    "url": row[4],
                    "sentiment": row[5]
                })
            
            return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/filings/<int:company_id>')
def get_filings(company_id):
    """Get SEC filings for a company"""
    try:
        with db.conn:
            cursor = db.conn.cursor()
            cursor.execute(
                '''SELECT filing_type, filing_date, file_path, content_length 
                FROM sec_filings 
                WHERE company_id = ? 
                ORDER BY filing_date DESC''',
                (company_id,)
            )
            
            filings = []
            for row in cursor.fetchall():
                filings.append({
                    "type": row[0],
                    "date": row[1],
                    "file_path": row[2],
                    "content_length": row[3]
                })
            
            return jsonify(filings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)