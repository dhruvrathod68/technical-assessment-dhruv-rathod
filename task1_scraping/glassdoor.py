"""
Task 1: Web Scraping & Anti-Bot Evasion - Glassdoor Review Scraper
Scrapes review titles and star ratings from Glassdoor.
Implements TLS impersonation via curl_cffi with Google Referer headers.
"""

import json
import random
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup
from curl_cffi import requests

OUTPUT_FILE = Path(__file__).resolve().parent / "glassdoor.json"
TARGET_URL = "https://www.glassdoor.com/Reviews/Google-Reviews-E9079.htm"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "referer": "https://www.google.com/",
}


CHALLENGE_SIGNATURES = [
    "cf-chl-bypass",
    "just a moment...",
    "datadome",
    "px-captcha",
    "challenge-running",
    "turnstile",
    "attention required",
]


def is_anti_bot_challenge(resp) -> bool:
    """Checks response status and text for anti-bot challenge markers."""
    if resp.status_code == 403:
        return True
    text_lower = resp.text.lower()
    return any(sig in text_lower for sig in CHALLENGE_SIGNATURES)


def scrape_glassdoor(max_retries: int = 3) -> list:
    """Scrapes review titles and star ratings from Glassdoor with anti-bot guards."""
    print(f"[*] [Glassdoor] Fetching company reviews from {TARGET_URL}...")
    
    # Operational politeness: random jitter
    time.sleep(random.uniform(1.5, 3.0))
    
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(
                TARGET_URL,
                headers=HEADERS,
                impersonate="chrome124",
                timeout=20,
            )
            
            # Anti-bot diagnostic check
            if is_anti_bot_challenge(resp):
                print(f"[!] Anti-bot challenge detected (IP reputation trigger). Falling back to session retry... (Status: {resp.status_code})")
                if attempt < max_retries:
                    backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                    print(f"[*] [Glassdoor] Backing off for {backoff:.2f}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(backoff)
                    continue
                return []

            if resp.status_code == 200 and len(resp.text) > 50000:
                soup = BeautifulSoup(resp.text, "html.parser")
                reviews = []
                
                # Filter out standard non-review navigation headings
                ignored_headings = {
                    "glassdoor", "employers", "information", "work with us",
                    "bowls", "followed companies", "reviews by job title",
                    "google reviews faqs", "jobs at google"
                }
                
                # Primary extraction: Review cards containing h3
                for h3 in soup.find_all("h3"):
                    title = h3.get_text(strip=True)
                    if not title or title.lower() in ignored_headings or len(title) > 100:
                        continue
                        
                    parent = h3.find_parent("div")
                    rating = "5.0"
                    if parent:
                        for span in parent.find_all(["span", "div"]):
                            t = span.get_text(strip=True)
                            if re.match(r"^[1-5](\.[0-9])?$", t):
                                rating = t
                                break
                    reviews.append({"review_title": title, "star_rating": rating})
                
                # Deduplicate
                unique_reviews = []
                seen = set()
                for r in reviews:
                    if r["review_title"] not in seen:
                        seen.add(r["review_title"])
                        unique_reviews.append(r)
                        
                if unique_reviews:
                    print(f"[+] [Glassdoor] Successfully extracted {len(unique_reviews)} reviews.")
                    return unique_reviews
                    
            print(f"[-] [Glassdoor] Attempt {attempt}: Received HTTP {resp.status_code}. Retrying...")
            if attempt < max_retries:
                backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                time.sleep(backoff)
        except Exception as e:
            print(f"[!] [Glassdoor] Attempt {attempt} error: {e}")
            if attempt < max_retries:
                backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                time.sleep(backoff)
            
    return []


def main():
    results = scrape_glassdoor()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[+] [Glassdoor] Saved {len(results)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
