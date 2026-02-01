"""
API Routes for Stock Analysis
All endpoints for analyzing stocks, getting charts, news, etc.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add parent directory to path to import free_stock_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from free_stock_agent import (
    research_agent,
    fetch_stock_news,
    fetch_stock_data,
    analyze_news_sentiment,
    validate_symbol
)
import yfinance as yf

# Create router
router = APIRouter()


# Pydantic models for request/response validation
class StockAnalysisResponse(BaseModel):
    """Response model for stock analysis"""
    symbol: str
    company_name: str
    decision: str
    sentiment_score: float
    price_change_6m: float
    current_price: float
    currency: str
    exchange: str
    explanation: str


class CompareRequest(BaseModel):
    """Request model for comparing stocks"""
    stocks: List[str]


class ChartDataPoint(BaseModel):
    """Single data point in chart"""
    date: str
    price: float


class NewsItem(BaseModel):
    """News article item"""
    headline: str
    sentiment: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/analyze/{stock_name}", response_model=StockAnalysisResponse)
async def analyze_stock(stock_name: str):
    """
    Analyze a single stock and return BUY/SELL/HOLD recommendation.
    
    - **stock_name**: Company name or ticker symbol (e.g., "Apple", "TCS", "AAPL")
    
    Returns complete analysis including decision, metrics, and explanation.
    """
    try:
        # Call your existing research agent
        result = research_agent(stock_name)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Stock '{stock_name}' not found. Please check the name and try again."
            )
        
        return StockAnalysisResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing stock: {str(e)}"
        )


@router.post("/compare")
async def compare_stocks(request: CompareRequest):
    """
    Compare multiple stocks side-by-side.
    
    - **stocks**: List of stock names/symbols to compare (2-4 stocks)
    
    Returns analysis for each stock plus comparison summary.
    """
    try:
        if len(request.stocks) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least 2 stocks to compare"
            )
        
        if len(request.stocks) > 4:
            raise HTTPException(
                status_code=400,
                detail="Maximum 4 stocks can be compared at once"
            )
        
        results = []
        for stock in request.stocks:
            result = research_agent(stock)
            if result:
                results.append(result)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="Could not find any of the specified stocks"
            )
        
        # Find best performer
        best_stock = max(results, key=lambda x: x['price_change_6m'])
        
        return {
            "comparison": results,
            "best_performer": {
                "symbol": best_stock['symbol'],
                "change": best_stock['price_change_6m'],
                "decision": best_stock['decision']
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing stocks: {str(e)}"
        )


@router.get("/trending")
async def get_trending_stocks():
    """
    Get list of trending stocks with BUY signals.
    
    Returns stocks that are currently showing positive momentum.
    """
    try:
        # Popular stocks to check
        popular_stocks = [
            ("AAPL", "Apple"),
            ("MSFT", "Microsoft"),
            ("GOOGL", "Google"),
            ("TCS.NS", "TCS"),
            ("INFY.NS", "Infosys"),
            ("RELIANCE.NS", "Reliance"),
            ("TSLA", "Tesla"),
        ]
        
        trending = []
        
        for symbol, name in popular_stocks:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="6mo")
                
                if not hist.empty and len(hist) >= 2:
                    start_price = hist["Close"].iloc[0]
                    end_price = hist["Close"].iloc[-1]
                    price_change = (end_price - start_price) / start_price * 100
                    
                    # Only include stocks with positive momentum
                    if price_change > 8:  # +8% in 6 months
                        trending.append({
                            "symbol": symbol,
                            "name": name,
                            "change": round(price_change, 2),
                            "current_price": round(end_price, 2)
                        })
            except:
                continue
        
        # Sort by performance and return top 6
        trending.sort(key=lambda x: x['change'], reverse=True)
        
        return {
            "trending_stocks": trending[:6],
            "count": len(trending[:6])
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching trending stocks: {str(e)}"
        )


@router.get("/metrics/{symbol}")
async def get_stock_metrics(symbol: str):
    """
    Get detailed metrics for a stock.
    
    - **symbol**: Stock ticker symbol (e.g., "AAPL", "TCS.NS")
    
    Returns comprehensive metrics including price, volume, ratios, etc.
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1d")
        
        if hist.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol '{symbol}'"
            )
        
        current_price = hist["Close"].iloc[-1]
        open_price = hist["Open"].iloc[-1]
        day_change = current_price - open_price
        day_change_pct = (day_change / open_price) * 100
        
        metrics = {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "day_change": round(day_change, 2),
            "day_change_pct": round(day_change_pct, 2),
            "open_price": round(open_price, 2),
            "high_52w": info.get("fiftyTwoWeekHigh", None),
            "low_52w": info.get("fiftyTwoWeekLow", None),
            "market_cap": info.get("marketCap", None),
            "volume": info.get("volume", None),
            "avg_volume": info.get("averageVolume", None),
            "pe_ratio": info.get("trailingPE", None),
            "dividend_yield": info.get("dividendYield", None),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", "Unknown")
        }
        
        return metrics
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching metrics: {str(e)}"
        )


@router.get("/chart/{symbol}/{period}")
async def get_chart_data(
    symbol: str,
    period: str
):
    """
    Get historical price data for charting.
    
    - **symbol**: Stock ticker symbol
    - **period**: Time period (1mo, 3mo, 6mo, 1y, 5y)
    
    Returns array of date/price pairs for charting.
    """
    # Validate period
    valid_periods = ["1mo", "3mo", "6mo", "1y", "5y"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}"
        )
    
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        
        if hist.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No chart data found for '{symbol}'"
            )
        
        # Format data for Chart.js
        chart_data = []
        for date, row in hist.iterrows():
            chart_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(row["Close"], 2)
            })
        
        return {
            "symbol": symbol,
            "period": period,
            "data": chart_data,
            "count": len(chart_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching chart data: {str(e)}"
        )


@router.get("/news/{company_name}")
async def get_news(company_name: str):
    """
    Get recent news headlines for a company.
    
    - **company_name**: Company name (e.g., "Apple", "TCS")
    
    Returns recent news articles with sentiment.
    """
    try:
        # Fetch news using your existing function
        news_articles = fetch_stock_news(company_name)
        
        if not news_articles:
            return {
                "company": company_name,
                "news": [],
                "count": 0,
                "message": "No recent news available"
            }
        
        # Analyze sentiment for each article
        sentiment_score = analyze_news_sentiment(news_articles)
        
        # Format news with sentiment indicators
        formatted_news = []
        for article in news_articles[:5]:  # Top 5 articles
            formatted_news.append({
                "headline": article[:200] + "..." if len(article) > 200 else article,
                "sentiment": "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral"
            })
        
        return {
            "company": company_name,
            "news": formatted_news,
            "count": len(formatted_news),
            "overall_sentiment": round(sentiment_score, 2)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching news: {str(e)}"
        )


@router.get("/search/{query}")
async def search_stock(query: str):
    """
    Search for a stock symbol by company name.
    
    - **query**: Company name to search for
    
    Returns possible stock matches.
    """
    try:
        result = validate_symbol(query)
        
        if not result:
            return {
                "query": query,
                "found": False,
                "message": "Stock not found. Try full company name or exact ticker symbol."
            }
        
        symbol, company_name = result
        
        return {
            "query": query,
            "found": True,
            "symbol": symbol,
            "company_name": company_name
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching stock: {str(e)}"
        )
