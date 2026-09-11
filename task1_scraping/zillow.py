"""
Meridian Grid Security - Task 1: Zillow Real Estate Scraper
Scrapes listing price and address from active Zillow properties.
Inspects the initial server-rendered HTML for embedded __NEXT_DATA__ JSON state.
"""

import json
import random
import re
import time
from pathlib import Path
from curl_cffi import requests

OUTPUT_FILE = Path(__file__).resolve().parent / "zillow.json"
TARGET_URL = "https://www.zillow.com/austin-tx/"


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


def scrape_zillow(max_retries: int = 3) -> list:
    """Scrapes property listings (price + address) from Zillow with anti-bot guards."""
    print(f"[*] [Zillow] Fetching real estate listings from {TARGET_URL}...")
    
    # Operational politeness: random jitter
    time.sleep(random.uniform(1.5, 2.5))
    
    for attempt in range(1, max_retries + 1):
        try:
            # Let curl_cffi synthesize authentic Chrome TLS & header frames
            resp = requests.get(
                TARGET_URL,
                impersonate="chrome",
                timeout=20,
            )
            
            # Anti-bot diagnostic check
            if is_anti_bot_challenge(resp):
                print(f"[!] Anti-bot challenge detected (IP reputation trigger). Falling back to session retry... (Status: {resp.status_code})")
                if attempt < max_retries:
                    backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                    print(f"[*] [Zillow] Backing off for {backoff:.2f}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(backoff)
                    continue
                return []

            if resp.status_code == 200:
                # Primary method: __NEXT_DATA__ state extraction
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">({.*?})</script>', resp.text)
                listings = []
                
                if match:
                    data = json.loads(match.group(1))
                    
                    def find_listings(obj):
                        if isinstance(obj, dict):
                            # Identify property entries with formatted price and address
                            if "price" in obj and ("address" in obj or "streetAddress" in obj):
                                addr = obj.get("address") or obj.get("streetAddress")
                                price = obj.get("price")
                                if addr and price:
                                    # Normalize formatted price string
                                    price_str = str(price)
                                    if not price_str.startswith("$"):
                                        try:
                                            price_num = int(float(price_str))
                                            price_str = f"${price_num:,}"
                                        except ValueError:
                                            pass
                                    listings.append({"price": price_str, "address": str(addr)})
                            for v in obj.values():
                                find_listings(v)
                        elif isinstance(obj, list):
                            for item in obj:
                                find_listings(item)
                                
                    find_listings(data)
                
                # Deduplicate
                unique_listings = []
                seen = set()
                for item in listings:
                    key = (item["price"], item["address"])
                    if key not in seen and len(item["address"]) > 5:
                        seen.add(key)
                        unique_listings.append(item)
                        
                if unique_listings:
                    print(f"[+] [Zillow] Successfully extracted {len(unique_listings)} listings from __NEXT_DATA__.")
                    return unique_listings
                    
            print(f"[-] [Zillow] Attempt {attempt}: Received HTTP {resp.status_code}. Retrying...")
            if attempt < max_retries:
                backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                time.sleep(backoff)
        except Exception as e:
            print(f"[!] [Zillow] Attempt {attempt} error: {e}")
            if attempt < max_retries:
                backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                time.sleep(backoff)
            
    return []


def main():
    results = scrape_zillow()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[+] [Zillow] Saved {len(results)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
