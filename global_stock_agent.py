import requests
import yfinance as yf
from textblob import TextBlob
import os
from openai import OpenAI
import logging
from typing import Dict, List, Optional, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None

# Get API keys from environment variables
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Global stock exchange suffixes for Yahoo Finance
EXCHANGE_SUFFIXES = {
    # India
    "NSE": ".NS",      # National Stock Exchange
    "BSE": ".BO",      # Bombay Stock Exchange
    
    # UK
    "LSE": ".L",       # London Stock Exchange
    
    # Europe
    "XETRA": ".DE",    # Germany (Frankfurt)
    "EURONEXT": ".PA", # France (Paris)
    "AEX": ".AS",      # Netherlands (Amsterdam)
    "SIX": ".SW",      # Switzerland (Zurich)
    "BME": ".MC",      # Spain (Madrid)
    "BIT": ".MI",      # Italy (Milan)
    
    # Asia Pacific
    "TSE": ".T",       # Japan (Tokyo)
    "HKEX": ".HK",     # Hong Kong
    "SSE": ".SS",      # China (Shanghai)
    "SZSE": ".SZ",     # China (Shenzhen)
    "KRX": ".KS",      # South Korea
    "ASX": ".AX",      # Australia
    "SGX": ".SI",      # Singapore
    "TWO": ".TWO",     # Taiwan OTC
    "TWSE": ".TW",     # Taiwan
    
    # Americas
    "TSX": ".TO",      # Canada (Toronto)
    "BMV": ".MX",      # Mexico
    "BOVESPA": ".SA",  # Brazil (Sao Paulo)
    
    # Middle East
    "TASE": ".TA",     # Israel (Tel Aviv)
    "TADAWUL": ".SAU", # Saudi Arabia
    
    # Default (US exchanges - no suffix needed)
    "NYSE": "",        # New York Stock Exchange
    "NASDAQ": "",      # NASDAQ
}

# Expanded stock symbol mappings for popular companies worldwide
COMPANY_SYMBOLS = {
    # US Tech Giants
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "netflix": "NFLX",
    
    # Indian Companies (NSE)
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "wipro": "WIPRO.NS",
    "hcl": "HCLTECH.NS",
    "tech mahindra": "TECHM.NS",
    "mahindra": "M&M.NS",
    "reliance": "RELIANCE.NS",
    "hdfc bank": "HDFCBANK.NS",
    "hdfc": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "icici": "ICICIBANK.NS",
    "bharti": "BHARTIARTL.NS",
    "airtel": "BHARTIARTL.NS",
    "itc": "ITC.NS",
    "sbi": "SBIN.NS",
    "tata motors": "TATAMOTORS.NS",
    "tata steel": "TATASTEEL.NS",
    "adani": "ADANIENT.NS",
    "bajaj": "BAJFINANCE.NS",
    "axis bank": "AXISBANK.NS",
    "maruti": "MARUTI.NS",
    "asian paints": "ASIANPAINT.NS",
    
    # UK Companies
    "bp": "BP.L",
    "shell": "SHEL.L",
    "hsbc": "HSBA.L",
    "unilever": "ULVR.L",
    "astrazeneca": "AZN.L",
    "glaxosmithkline": "GSK.L",
    "gsk": "GSK.L",
    "vodafone": "VOD.L",
    "rolls royce": "RR.L",
    
    # European Companies
    "volkswagen": "VOW.DE",
    "bmw": "BMW.DE",
    "mercedes": "MBG.DE",
    "siemens": "SIE.DE",
    "sap": "SAP.DE",
    "lvmh": "MC.PA",
    "total": "TTE.PA",
    "air liquide": "AI.PA",
    "nestle": "NESN.SW",
    "novartis": "NOVN.SW",
    "roche": "ROG.SW",
    
    # Japanese Companies
    "toyota": "7203.T",
    "sony": "6758.T",
    "nintendo": "7974.T",
    "softbank": "9984.T",
    "honda": "7267.T",
    "mitsubishi": "8058.T",
    
    # Chinese Companies
    "alibaba": "BABA",  # US-listed
    "tencent": "0700.HK",
    "baidu": "BIDU",
    "ping an": "2318.HK",
    "icbc": "1398.HK",
    
    # Other Global
    "samsung": "005930.KS",
    "shopify": "SHOP.TO",
    "petrobras": "PETR4.SA",
}


def search_stock_symbol(company_name: str) -> Optional[Tuple[str, str]]:
    """
    Search for stock symbol using Yahoo Finance search.
    
    Args:
        company_name: Name of the company to search
        
    Returns:
        Tuple of (symbol, full_company_name) or None if not found
    """
    try:
        # Use yfinance Ticker with search capability
        # Try to find the company by searching
        search_url = f"https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": company_name,
            "quotesCount": 5,
            "newsCount": 0,
            "enableFuzzyQuery": False,
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        quotes = data.get("quotes", [])
        
        if not quotes:
            logger.warning(f"No symbols found for '{company_name}'")
            return None
        
        # Get the first result (most relevant)
        first_result = quotes[0]
        symbol = first_result.get("symbol")
        long_name = first_result.get("longname") or first_result.get("shortname") or company_name
        
        if symbol:
            logger.info(f"Found symbol '{symbol}' for '{company_name}' ({long_name})")
            return (symbol, long_name)
        
        return None
        
    except Exception as e:
        logger.error(f"Error searching for symbol '{company_name}': {e}")
        return None


def validate_symbol(symbol: str, company_name: str = None) -> Optional[Tuple[str, str]]:
    """
    Validate and normalize stock symbol globally.
    Supports stocks from any exchange worldwide.
    
    Args:
        symbol: Stock ticker symbol or company name
        company_name: Optional full company name
        
    Returns:
        Tuple of (normalized_symbol, company_name) or None if invalid
    """
    original_symbol = symbol
    symbol = symbol.strip()
    symbol_lower = symbol.lower()
    
    # Step 1: Check if it's in our pre-mapped company names
    if symbol_lower in COMPANY_SYMBOLS:
        mapped_symbol = COMPANY_SYMBOLS[symbol_lower]
        logger.info(f"Mapped '{symbol}' to '{mapped_symbol}'")
        return (mapped_symbol, company_name or symbol)
    
    # Step 2: Check if it already has an exchange suffix
    for exchange, suffix in EXCHANGE_SUFFIXES.items():
        if suffix and symbol.upper().endswith(suffix):
            logger.info(f"Symbol '{symbol}' already has {exchange} suffix")
            return (symbol.upper(), company_name or symbol)
    
    # Step 3: If it looks like a ticker (short, uppercase letters/numbers)
    if re.match(r'^[A-Z0-9]{1,6}$', symbol.upper()):
        # Assume US stock (no suffix needed)
        logger.info(f"Treating '{symbol}' as US ticker")
        return (symbol.upper(), company_name or symbol)
    
    # Step 4: Search for the symbol using Yahoo Finance API
    logger.info(f"Searching for '{symbol}' in Yahoo Finance...")
    result = search_stock_symbol(symbol)
    
    if result:
        return result
    
    # Step 5: Last resort - try common variations
    # Try adding .NS for potential Indian stocks
    if not any(symbol.upper().endswith(suffix) for suffix in EXCHANGE_SUFFIXES.values() if suffix):
        test_symbol = f"{symbol.upper()}.NS"
        try:
            test_stock = yf.Ticker(test_symbol)
            hist = test_stock.history(period="5d")
            if not hist.empty:
                logger.info(f"Found '{test_symbol}' on NSE")
                return (test_symbol, company_name or symbol)
        except:
            pass
    
    logger.error(f"Could not find valid symbol for '{original_symbol}'")
    return None


def fetch_stock_news(company_name: str) -> List[str]:
    """
    Fetch recent news articles for a company.
    
    Args:
        company_name: Name of the company
        
    Returns:
        List of news article summaries
    """
    if not NEWS_API_KEY:
        logger.error("NEWS_API_KEY not found in environment variables")
        return []
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": company_name,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        articles = response.json().get("articles", [])
        
        if not articles:
            logger.warning(f"No news articles found for {company_name}")
            return []
        
        news_list = []
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            if title and description:
                news_list.append(f"{title}. {description}")
            elif title:
                news_list.append(title)
        
        logger.info(f"Fetched {len(news_list)} news articles for {company_name}")
        return news_list
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout while fetching news for {company_name}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news for {company_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching news: {e}")
        return []


def fetch_stock_data(symbol: str) -> Optional[Dict]:
    """
    Fetch historical stock data and calculate performance metrics.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with price data or None if failed
    """
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo")
        
        if hist.empty:
            logger.error(f"No historical data found for {symbol}")
            return None
        
        if len(hist) < 2:
            logger.error(f"Insufficient data for {symbol}")
            return None
        
        start_price = hist["Close"].iloc[0]
        end_price = hist["Close"].iloc[-1]
        price_change = (end_price - start_price) / start_price * 100
        
        # Get additional info
        info = stock.info
        currency = info.get("currency", "USD")
        exchange = info.get("exchange", "Unknown")
        
        logger.info(f"Fetched stock data for {symbol}: Current={end_price:.2f} {currency}, Change={price_change:.2f}%")
        
        return {
            "current_price": round(end_price, 2),
            "6m_change_percent": round(price_change, 2),
            "currency": currency,
            "exchange": exchange
        }
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        return None


def analyze_news_sentiment(news_list: List[str]) -> float:
    """
    Analyze sentiment of news articles using TextBlob.
    
    Args:
        news_list: List of news article texts
        
    Returns:
        Average sentiment polarity score (-1 to 1)
    """
    if not news_list:
        logger.warning("No news articles to analyze sentiment")
        return 0.0
    
    try:
        polarity_scores = [
            TextBlob(article).sentiment.polarity
            for article in news_list
        ]
        avg_sentiment = sum(polarity_scores) / len(polarity_scores)
        logger.info(f"Analyzed sentiment: {avg_sentiment:.2f} from {len(news_list)} articles")
        return avg_sentiment
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return 0.0


def make_decision(sentiment_score: float, price_change: float) -> str:
    """
    Make BUY/SELL/HOLD decision based on sentiment and price performance.
    
    Args:
        sentiment_score: News sentiment score (-1 to 1)
        price_change: 6-month price change percentage
        
    Returns:
        Decision string: "BUY", "SELL", or "HOLD"
    """
    if sentiment_score > 0.1 and price_change > 5:
        decision = "BUY"
    elif sentiment_score < -0.1 and price_change < -5:
        decision = "SELL"
    else:
        decision = "HOLD"
    
    logger.info(f"Decision: {decision} (sentiment={sentiment_score:.2f}, price_change={price_change:.2f}%)")
    return decision


def explain_decision(stock: str, news: List[str], performance: Dict, decision: str) -> str:
    """
    Generate AI explanation for the investment decision.
    
    Args:
        stock: Stock symbol
        news: List of news articles
        performance: Stock performance data
        decision: Investment decision
        
    Returns:
        Explanation text
    """
    if not client:
        return "AI explanation unavailable: OpenAI client not initialized. Please set OPENAI_API_KEY."
    
    news_text = "\n".join([f"- {article[:150]}..." for article in news[:5]])
    
    prompt = f"""
You are a financial research assistant.

Stock: {stock}
6-month price change: {performance['6m_change_percent']}%
Current price: {performance['current_price']} {performance.get('currency', 'USD')}
Exchange: {performance.get('exchange', 'Unknown')}

Recent news headlines:
{news_text}

Final decision: {decision}

Explain clearly and concisely why this recommendation was made based on the data provided. Keep it under 150 words.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        explanation = response.choices[0].message.content
        logger.info("Generated AI explanation successfully")
        return explanation
        
    except Exception as e:
        logger.error(f"Error generating AI explanation: {e}")
        return f"AI explanation unavailable: {str(e)}"


def research_agent(symbol: str, company_name: str = None) -> Optional[Dict]:
    """
    Main research agent function that orchestrates the analysis.
    Works with stocks from ANY exchange worldwide.
    
    Args:
        symbol: Stock ticker symbol or company name
        company_name: Optional full company name for news search
        
    Returns:
        Dictionary with analysis results or None if failed
    """
    logger.info(f"Starting research for '{symbol}' {f'({company_name})' if company_name else ''}")
    
    # Validate and find the correct symbol
    result = validate_symbol(symbol, company_name)
    
    if not result:
        logger.error(f"Could not find valid stock symbol for '{symbol}'")
        print(f"\n❌ Could not find stock '{symbol}'")
        print("💡 Tips:")
        print("   - Try the full company name (e.g., 'Toyota' instead of 'TYO')")
        print("   - Use the exact ticker symbol (e.g., 'AAPL', 'TCS.NS')")
        print("   - For international stocks, include exchange suffix (e.g., 'BP.L' for UK)")
        return None
    
    normalized_symbol, resolved_company_name = result
    search_name = company_name or resolved_company_name
    
    # Fetch data
    news = fetch_stock_news(search_name)
    performance = fetch_stock_data(normalized_symbol)
    
    if performance is None:
        logger.error(f"Failed to fetch stock data for {normalized_symbol}")
        return None
    
    # Analyze
    sentiment = analyze_news_sentiment(news)
    decision = make_decision(sentiment, performance["6m_change_percent"])
    
    # Generate explanation
    try:
        explanation = explain_decision(normalized_symbol, news, performance, decision)
    except Exception as e:
        explanation = f"Explanation generation failed: {str(e)}"
    
    result_dict = {
        "symbol": normalized_symbol,
        "company_name": resolved_company_name,
        "decision": decision,
        "sentiment_score": round(sentiment, 2),
        "price_change_6m": performance["6m_change_percent"],
        "current_price": performance["current_price"],
        "currency": performance.get("currency", "USD"),
        "exchange": performance.get("exchange", "Unknown"),
        "explanation": explanation
    }
    
    logger.info(f"Research completed for {normalized_symbol}: {decision}")
    return result_dict


def print_report(result: Dict) -> None:
    """
    Print formatted research report.
    
    Args:
        result: Research analysis results
    """
    print("\n" + "="*70)
    print(f"📊 Stock Research Report: {result['symbol']}")
    print(f"🏢 Company: {result.get('company_name', 'N/A')}")
    print(f"🏦 Exchange: {result.get('exchange', 'Unknown')}")
    print("="*70)
    
    # Decision with emoji
    decision_emoji = {
        "BUY": "💚",
        "SELL": "❤️",
        "HOLD": "💛"
    }
    emoji = decision_emoji.get(result['decision'], "⚪")
    
    print(f"\n{emoji} {'Decision':<20}: {result['decision']}")
    print(f"{'Sentiment Score':<20}: {result['sentiment_score']}")
    print(f"{'Current Price':<20}: {result['current_price']} {result.get('currency', 'USD')}")
    print(f"{'6M Price Change':<20}: {result['price_change_6m']}%")
    
    print("\n🧠 AI Explanation:")
    print("-"*70)
    print(result["explanation"])
    print("="*70 + "\n")


if __name__ == "__main__":
    # Example usage - test stocks from around the world
    print("\n" + "="*70)
    print("🌍 GLOBAL STOCK RESEARCH AGENT")
    print("="*70)
    print("\nTesting stocks from multiple countries...\n")
    
    test_stocks = [
        ("Apple", "Apple Inc"),           # US - by name
        ("TCS", "Tata Consultancy"),      # India - by name
        ("Toyota", "Toyota Motor"),        # Japan - by name
        ("BP", "BP plc"),                 # UK - by name
        ("MSFT", None),                    # US - by ticker
    ]
    
    for symbol, company in test_stocks:
        result = research_agent(symbol, company)
        
        if result:
            print_report(result)
        else:
            print(f"\n❌ Failed to analyze '{symbol}'\n")
