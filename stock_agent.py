import requests
import yfinance as yf
from textblob import TextBlob
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))

NEWS_API_KEY = "77fdc1d9ac0b437da964b2932bccf33f"

def fetch_stock_news(company_name):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": company_name,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": 5
    }
    response = requests.get(url, params=params)
    articles = response.json().get("articles", [])
    
    return [a["title"] + ". " + a["description"] for a in articles]

def fetch_stock_data(symbol):
    stock = yf.Ticker(symbol)
    hist = stock.history(period="6mo")

    start_price = hist["Close"].iloc[0]
    end_price = hist["Close"].iloc[-1]

    price_change = (end_price - start_price) / start_price * 100

    return {
        "current_price": round(end_price, 2),
        "6m_change_percent": round(price_change, 2)
    }

def analyze_news_sentiment(news_list):
    if not news_list:
        return 0

    polarity_scores = [
        TextBlob(article).sentiment.polarity
        for article in news_list
    ]

    return sum(polarity_scores) / len(polarity_scores)

def make_decision(sentiment_score, price_change):
    if sentiment_score > 0.1 and price_change > 5:
        return "BUY"
    elif sentiment_score < -0.1 and price_change < -5:
        return "SELL"
    else:
        return "HOLD"

def explain_decision(stock, news, performance, decision):
    prompt = f"""
You are a financial research assistant.

Stock: {stock}
6-month price change: {performance['6m_change_percent']}%
News headlines:
{news}

Final decision: {decision}

Explain clearly why this recommendation was made.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


def research_agent(symbol, company_name):
    news = fetch_stock_news(company_name)
    performance = fetch_stock_data(symbol)
    sentiment = analyze_news_sentiment(news)

    decision = make_decision(sentiment, performance["6m_change_percent"])

    try:
        explanation = explain_decision(symbol, news, performance, decision)
    except Exception as e:
        explanation = f"LLM explanation unavailable: {str(e)}"

    return {
        "symbol": symbol,
        "decision": decision,
        "sentiment_score": round(sentiment, 2),
        "price_change_6m": performance["6m_change_percent"],
        "explanation": explanation
    }

if __name__ == "__main__":
    result = research_agent("AAPL", "Apple Inc")
    print("\n" + "="*50)
    print(f"📊 Stock Research Report: {result['symbol']}")
    print("="*50)
    
    print(f"Decision           : {result['decision']}")
    print(f"Sentiment Score    : {result['sentiment_score']}")
    print(f"6M Price Change    : {result['price_change_6m']}%")
    
    print("\n🧠 Explanation:")
    print("-"*50)
    print(result["explanation"])
    print("="*50)
    
