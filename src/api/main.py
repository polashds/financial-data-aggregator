
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import json

from data.database import FinancialDataDB
from analysis.financial_analyzer import FinancialAnalyzer

app = FastAPI(title="Financial Data Aggregator API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Database connection
db = FinancialDataDB()
analyzer = FinancialAnalyzer(db)

# Pydantic models
class Company(BaseModel):
    id: int
    name: str
    ticker: str
    
    class Config:
        orm_mode = True

class SentimentData(BaseModel):
    date: str
    total_articles: int
    positive: int
    negative: int
    neutral: int

class NewsArticle(BaseModel):
    title: str
    excerpt: str
    date: str
    source: str
    url: str
    sentiment: Optional[str]

class SECFiling(BaseModel):
    type: str
    date: str
    file_path: str
    content_length: int

class SentimentTrend(BaseModel):
    trend_direction: str
    current_score: float
    average_score: float
    volatility: float
    data: List[dict]

class CorrelationResult(BaseModel):
    filing_date: str
    pre_filing_sentiment: float
    post_filing_sentiment: float
    sentiment_change: float
    data_points: int

# Authentication (simplified - in production use proper auth)
def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In a real application, validate the token against your user database
    if credentials.credentials != "secret-token":
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return True

# Routes
@app.get("/")
async def root():
    return {"message": "Financial Data Aggregator API"}

@app.get("/companies", response_model=List[Company])
async def get_companies(auth: bool = Depends(authenticate)):
    """Get list of all companies"""
    try:
        with db.conn:
            cursor = db.conn.cursor()
            cursor.execute("SELECT id, name, ticker FROM companies ORDER BY name")
            companies = [Company(id=row[0], name=row[1], ticker=row[2]) for row in cursor.fetchall()]
        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/{company_id}/sentiment", response_model=List[SentimentData])
async def get_company_sentiment(company_id: int, days: int = 30, auth: bool = Depends(authenticate)):
    """Get sentiment data for a specific company"""
    try:
        sentiment_data = db.get_latest_sentiment(company_id, days)
        if not sentiment_data:
            raise HTTPException(status_code=404, detail="No sentiment data found")
        
        return [
            SentimentData(
                date=row[0],
                total_articles=row[1],
                positive=row[2],
                negative=row[3],
                neutral=row[4]
            ) for row in sentiment_data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/{company_id}/sentiment/trend", response_model=SentimentTrend)
async def get_sentiment_trend(company_id: int, days: int = 30, auth: bool = Depends(authenticate)):
    """Get sentiment trend analysis for a company"""
    try:
        trend = analyzer.calculate_sentiment_trend(company_id, days)
        if not trend:
            raise HTTPException(status_code=404, detail="No data available for trend analysis")
        
        return trend
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/{company_id}/news", response_model=List[NewsArticle])
async def get_company_news(company_id: int, limit: int = 10, auth: bool = Depends(authenticate)):
    """Get recent news articles for a company"""
    try:
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
            
            articles = [
                NewsArticle(
                    title=row[0],
                    excerpt=row[1],
                    date=row[2],
                    source=row[3],
                    url=row[4],
                    sentiment=row[5]
                ) for row in cursor.fetchall()
            ]
        
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/{company_id}/filings", response_model=List[SECFiling])
async def get_company_filings(company_id: int, auth: bool = Depends(authenticate)):
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
            
            filings = [
                SECFiling(
                    type=row[0],
                    date=row[1],
                    file_path=row[2],
                    content_length=row[3]
                ) for row in cursor.fetchall()
            ]
        
        return filings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/{company_id}/analysis/correlations", response_model=List[CorrelationResult])
async def get_correlations(company_id: int, days_before: int = 7, days_after: int = 7, 
                          auth: bool = Depends(authenticate)):
    """Get correlation between news sentiment and SEC filings"""
    try:
        correlations = analyzer.correlate_news_filings(company_id, days_before, days_after)
        if not correlations:
            raise HTTPException(status_code=404, detail="No correlation data available")
        
        return correlations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)