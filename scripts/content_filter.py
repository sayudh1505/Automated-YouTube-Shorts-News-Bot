import re
import json
import os
import sys
from pathlib import Path
import google.generativeai as genai

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import config

# Initialize Gemini if key is present
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None

# A set of blacklisted keywords for basic keyword filtering (regex-ready)
BLACKLIST_KEYWORDS = [
    r"\bkill(ed|ing|s)?\b", r"\bdeath(s)?\b", r"\bdie(d|s)?\b", r"\bmurder(ed|s)?\b", 
    r"\bsuicide(s)?\b", r"\baccident(s)?\b", r"\bcrash(ed|es)?\b", r"\btragedy\b",
    r"\bterror(ism|ist|ists)?\b", r"\bwar(s|fare)?\b", r"\bbomb(ed|ing|s)?\b", 
    r"\battack(ed|s)?\b", r"\bassault(ed|s)?\b", r"\bshoot(ing|s|er)?\b", 
    r"\bcrime(s)?\b", r"\barrest(ed|s)?\b", r"\bcourt\b", r"\blawsuit(s)?\b", 
    r"\bscandal(s)?\b", r"\bprotest(s|er|ers)?\b", r"\bstrike(s)?\b", 
    r"\bpolitic(al|s)?\b", r"\belection(s)?\b", r"\btrump\b", r"\bbiden\b", 
    r"\bpresident(ial)?\b", r"\bcongress\b", r"\bsenate\b", r"\bdemocrat(ic|s)?\b", 
    r"\brepublican(s)?\b", r"\babuse(d|s)?\b", r"\brape(d|s)?\b", r"\bsexual(ly)?\b",
    r"\bdisaster(s)?\b", r"\bearthquake(s)?\b", r"\bflood(ed|s|ing)?\b", r"\bhurricane(s)?\b",
    r"\btraged(y|ies)?\b", r"\bdead\b", r"\bcasualt(y|ies)?\b"
]

def keyword_filter(text):
    """
    Checks if text contains any blacklisted keyword.
    Returns (is_safe, matched_keyword)
    """
    for pattern in BLACKLIST_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, pattern
    return True, None

def gemini_filter(title, description):
    """
    Uses Gemini to perform advanced brand safety check.
    """
    if not model:
        print("[ContentFilter] Gemini not configured, skipping LLM safety check.")
        return True, "Skipped (Gemini API key missing)"
        
    prompt = f"""
You are a content safety auditor for a YouTube channel.
Analyze the following news article:
Title: {title}
Description: {description}

Determine if this article is safe, positive (or informative/neutral), engaging, and suitable for a general audience YouTube Short.
It must NOT contain topics related to:
- Severe violence, murder, deaths, war, or accidents
- Hard politics, election campaigns, or highly divisive partisan controversies
- Scandals, crimes, court trials, or lawsuits
- Depressing, sensitive, or offensive themes

Respond in JSON format only with the following structure:
{{
  "is_safe": true or false,
  "reason": "Brief explanation of the decision"
}}
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        result = json.loads(response.text)
        return result.get("is_safe", True), result.get("reason", "")
    except Exception as e:
        print(f"[ContentFilter] Gemini filter error: {e}. Defaulting to safe.")
        return True, "Error checking with Gemini"

def is_article_safe(article):
    """
    Performs full safety audit on an article.
    """
    title = article.get("title", "")
    desc = article.get("description", "")
    content = article.get("content", "")
    
    # 1. Check title and description against keyword blacklist
    is_safe_title, keyword = keyword_filter(title)
    if not is_safe_title:
        return False, f"Title matched blacklisted keyword: '{keyword}'"
        
    is_safe_desc, keyword = keyword_filter(desc)
    if not is_safe_desc:
        return False, f"Description matched blacklisted keyword: '{keyword}'"
        
    # 2. Check via Gemini
    is_safe_gemini, reason = gemini_filter(title, desc)
    if not is_safe_gemini:
        return False, f"Gemini rejected: {reason}"
        
    return True, f"Article passed all checks. Gemini reason: {reason}"

def filter_news_articles(articles):
    """
    Filters a list of articles and returns only the safe ones.
    """
    safe_articles = []
    for art in articles:
        is_safe, reason = is_article_safe(art)
        if is_safe:
            print(f"[ContentFilter] APPROVED: {art['title'][:50]}... ({reason})")
            safe_articles.append(art)
        else:
            print(f"[ContentFilter] REJECTED: {art['title'][:50]}... (Reason: {reason})")
    return safe_articles

if __name__ == "__main__":
    print("Testing Content Filter...")
    test_articles = [
        {
            "title": "OpenAI launches a new AI model for reasoning",
            "description": "The company introduced ChatGPT-5 which can write code and solve math logic.",
            "content": "ChatGPT-5 reasoning model is out now."
        },
        {
            "title": "Tragic car accident on Highway 101 leaves three dead",
            "description": "A head-on collision resulted in fatalities and road closure for several hours.",
            "content": "Three people died today in a car crash."
        },
        {
            "title": "New election poll shows shift in presidential race",
            "description": "Candidates debate key issues as the presidential election approaches.",
            "content": "Elections are coming up next month."
        }
    ]
    
    filtered = filter_news_articles(test_articles)
    print(f"\nFiltered down from {len(test_articles)} to {len(filtered)} articles.")
