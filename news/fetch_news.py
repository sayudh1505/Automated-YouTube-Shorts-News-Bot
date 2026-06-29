import urllib.request
import json
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
import sys
from pathlib import Path

# Add project root to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import config

def fetch_news_api(query=None, country="us", category="technology"):
    """
    Fetches news headlines from NewsAPI.
    """
    api_key = config.NEWS_API_KEY
    if not api_key:
        print("[NewsAPI] No API key found. Falling back to RSS.")
        return None
    
    try:
        if query:
            url = f"https://newsapi.org/v2/everything?q={quote_plus(query)}&sortBy=popularity&pageSize=10&apiKey={api_key}"
        else:
            url = f"https://newsapi.org/v2/top-headlines?country={country}&category={category}&pageSize=10&apiKey={api_key}"
        
        print(f"[NewsAPI] Fetching from: {url}")
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if data.get("status") != "ok":
            print(f"[NewsAPI] API Error: {data.get('message')}")
            return None
            
        articles = []
        for item in data.get("articles", []):
            # Skip articles with removed content or missing crucial info
            if "[Removed]" in item.get("title", "") or not item.get("title") or not item.get("description"):
                continue
            articles.append({
                "title": item.get("title"),
                "description": item.get("description"),
                "content": item.get("content") or item.get("description"),
                "source": item.get("source", {}).get("name", "Unknown"),
                "url": item.get("url")
            })
        return articles
    except Exception as e:
        print(f"[NewsAPI] Failed to fetch news: {e}")
        return None

def fetch_news_rss(query=None):
    """
    Fetches news from Google News RSS (completely free, no API key required).
    """
    try:
        if query:
            url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        else:
            url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
            
        print(f"[RSS] Fetching from Google News RSS: {url}")
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        articles = []
        for item in root.findall(".//item")[:10]:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            
            # Google RSS descriptions are often HTML links to source articles. 
            # We'll use the title as description/content for the RSS fallback.
            desc = title
            source_el = item.find("source")
            source = source_el.text if source_el is not None else "Google News"
            
            # Clean up title: Google News RSS titles end with " - Source Name"
            clean_title = title
            if " - " in title:
                clean_title = " - ".join(title.split(" - ")[:-1])
                
            articles.append({
                "title": clean_title,
                "description": desc,
                "content": desc,
                "source": source,
                "url": link,
                "pubDate": pub_date
            })
        return articles
    except Exception as e:
        print(f"[RSS] Failed to fetch news from RSS: {e}")
        return []

def get_trending_news(query=None, count=5):
    """
    Orchestrated news fetcher with NewsAPI and RSS fallback.
    """
    # 1. Try NewsAPI
    articles = fetch_news_api(query=query)
    
    # 2. Fall back to RSS if NewsAPI failed or was not configured
    if not articles:
        articles = fetch_news_rss(query=query)
        
    return articles[:count]

if __name__ == "__main__":
    print("Testing News Fetcher...")
    news = get_trending_news(query="AI technology", count=3)
    for idx, art in enumerate(news, 1):
        print(f"\nArticle {idx}:")
        print(f"Title: {art['title']}")
        print(f"Source: {art['source']}")
        print(f"URL: {art['url']}")
        print(f"Snippet: {art['description'][:100]}...")
