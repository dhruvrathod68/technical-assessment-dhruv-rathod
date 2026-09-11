"""
Task 1: Web Scraping & Anti-Bot Evasion - Indeed Job Scraper
Scrapes job title and company name from Indeed search results.
Implements Chrome TLS impersonation via curl_cffi and DOM/regex extraction.
"""

import json
import random
import time
from pathlib import Path
from bs4 import BeautifulSoup
from curl_cffi import requests

OUTPUT_FILE = Path(__file__).resolve().parent / "indeed.json"
TARGET_URL = "https://in.indeed.com/jobs?q=python+developer&l=Mumbai"

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


def scrape_indeed(max_retries: int = 3) -> list:
    """Scrapes job titles and company names from Indeed with anti-bot guards."""
    print(f"[*] [Indeed] Fetching jobs from {TARGET_URL}...")
    
    # Operational politeness: random jitter
    time.sleep(random.uniform(1.5, 2.5))
    
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
                    print(f"[*] [Indeed] Backing off for {backoff:.2f}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(backoff)
                    continue
                return []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                jobs = []
                
                # Primary extraction: css selectors
                for a in soup.select("a.jcs-JobTitle, a[data-jk]"):
                    title = a.get_text(strip=True)
                    if not title or len(title) > 120:
                        continue
                    card = a.find_parent("div", class_=lambda c: c and "job_seen_beacon" in c) or a.find_parent("li")
                    company = "Unknown"
                    if card:
                        comp_elem = card.select_one("[data-testid='company-name'], span.companyName")
                        if comp_elem:
                            company = comp_elem.get_text(strip=True)
                    jobs.append({"job_title": title, "company_name": company})
                
                # Deduplicate
                unique_jobs = []
                seen = set()
                for j in jobs:
                    key = (j["job_title"], j["company_name"])
                    if key not in seen:
                        seen.add(key)
                        unique_jobs.append(j)
                
                if unique_jobs:
                    print(f"[+] [Indeed] Successfully extracted {len(unique_jobs)} jobs.")
                    return unique_jobs
                    
            print(f"[-] [Indeed] Attempt {attempt}: Received HTTP {resp.status_code}. Retrying...")
            if attempt < max_retries:
                backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                time.sleep(backoff)
        except Exception as e:
            print(f"[!] [Indeed] Attempt {attempt} error: {e}")
            if attempt < max_retries:
                backoff = (2.0 ** attempt) + random.uniform(2.0, 4.0)
                time.sleep(backoff)
            
    return []


def main():
    results = scrape_indeed()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[+] [Indeed] Saved {len(results)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
