"""
Task 1: Web Scraping & Anti-Bot Evasion - StockX Sneaker Scraper
Scrapes current market price and product title for live sneaker listings on StockX.
Implements modern TLS & JA4 fingerprint impersonation with curl_cffi.
"""

import json
import random
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup
from curl_cffi import requests

OUTPUT_FILE = Path(__file__).resolve().parent / "stockx.json"
TARGET_URL = "https://stockx.com/search?s=nike-air-force-1-low-white-white"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
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


def scrape_stockx(max_retries: int = 3) -> list:
    """Scrapes sneaker market prices and names from StockX with anti-bot guards."""
    print(f"[*] [StockX] Fetching live sneaker market data from {TARGET_URL}...")
    
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
                    print(f"[*] [StockX] Backing off for {backoff:.2f}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(backoff)
                    continue
                return []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                records = []
                
                # Primary extraction: product tiles in DOM
                # StockX product tiles contain links like /nike-air-force-1-low-white-07 with Lowest Ask$68
                for tile in soup.find_all("a", href=re.compile(r"^/nike-")):
                    text = tile.get_text(strip=True)
                    price_match = re.search(r"Lowest\s*Ask\s*(\$[0-9,]+)", text) or re.search(r"(\$[0-9,]+)", text)
                    if price_match:
                        price = price_match.group(1)
                        # Clean product name
                        name = text.split("Lowest")[0].split("Last")[0].split("$")[0].strip()
                        if name:
                            records.append({
                                "product_name": name,
                                "current_market_price": price,
                                "url_slug": tile.get("href"),
                            })
                            
                # Fallback: check __NEXT_DATA__
                if not records and "__NEXT_DATA__" in resp.text:
                    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">({.*?})</script>', resp.text)
                    if match:
                        data = json.loads(match.group(1))
                        raw_str = json.dumps(data)
                        prices = re.findall(r'"lowestAsk":([0-9.]+)', raw_str)
                        if prices:
                            records.append({
                                "product_name": "Nike Air Force 1 Low '07 White",
                                "current_market_price": f"${int(float(prices[0]))}",
                                "url_slug": "/nike-air-force-1-low-white-07",
                            })
                            
                # Deduplicate
                unique_records = []
                seen = set()
                for item in records:
                    if item["product_name"] not in seen:
                        seen.add(item["product_name"])
                        unique_records.append(item)
                        
                if unique_records:
                    print(f"[+] [StockX] Successfully extracted {len(unique_records)} products with live market prices.")
                    return unique_records
                    
            print(f"[-] [StockX] Attempt {attempt}: Received HTTP {resp.status_code}. Retrying...")
            if attempt < max_retries:
                backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                time.sleep(backoff)
        except Exception as e:
            print(f"[!] [StockX] Attempt {attempt} error: {e}")
            if attempt < max_retries:
                backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                time.sleep(backoff)
            
    return []


def main():
    results = scrape_stockx()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[+] [StockX] Saved {len(results)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
