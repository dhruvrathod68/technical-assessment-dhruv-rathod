"""
Task 1: Master Web Scraping & Anti-Bot Pipeline Runner
Executes all five scrapers sequentially, verifies that the resulting JSON files
exist and contain non-empty structured data, and outputs a formatted terminal summary table.
"""

import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

# Import individual scrapers
from task1_scraping.indeed import scrape_indeed, OUTPUT_FILE as INDEED_JSON
from task1_scraping.glassdoor import scrape_glassdoor, OUTPUT_FILE as GLASSDOOR_JSON
from task1_scraping.zillow import scrape_zillow, OUTPUT_FILE as ZILLOW_JSON
from task1_scraping.g2 import scrape_g2, OUTPUT_FILE as G2_JSON
from task1_scraping.stockx import scrape_stockx, OUTPUT_FILE as STOCKX_JSON

SCRAPERS = [
    {
        "name": "Indeed",
        "func": scrape_indeed,
        "json_path": INDEED_JSON,
        "fields": ["job_title", "company_name"],
        "target_url": "https://in.indeed.com/jobs?q=python+developer&l=Mumbai"
    },
    {
        "name": "Glassdoor",
        "func": scrape_glassdoor,
        "json_path": GLASSDOOR_JSON,
        "fields": ["review_title", "star_rating"],
        "target_url": "https://www.glassdoor.com/Reviews/Google-Reviews-E9079.htm"
    },
    {
        "name": "Zillow",
        "func": scrape_zillow,
        "json_path": ZILLOW_JSON,
        "fields": ["price", "address"],
        "target_url": "https://www.zillow.com/austin-tx/"
    },
    {
        "name": "G2",
        "func": scrape_g2,
        "json_path": G2_JSON,
        "fields": ["product_name", "star_rating"],
        "target_url": "https://www.g2.com/categories/endpoint-detection-response-edr"
    },
    {
        "name": "StockX",
        "func": scrape_stockx,
        "json_path": STOCKX_JSON,
        "fields": ["product_name", "current_market_price"],
        "target_url": "https://stockx.com/search?s=nike-air-force-1-low-white-white"
    },
]


def run_pipeline():
    print("=" * 75)
    print("  TASK 1: ANTI-BOT WEB SCRAPING PIPELINE ORCHESTRATOR")
    print("=" * 75)
    print(f"[*] Starting execution of {len(SCRAPERS)} scrapers...\n")

    summary_results = []
    all_passed = True

    for item in SCRAPERS:
        name = item["name"]
        func = item["func"]
        json_path = item["json_path"]
        target = item["target_url"]

        print(f"\n>>> Running Scraper: {name} <<<")
        start_time = time.time()
        try:
            records = func()
            duration = time.time() - start_time
            
            # Save to JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
                
            # Validation
            if not json_path.exists():
                status = "FAIL (No File)"
                count = 0
                sample = "N/A"
                all_passed = False
            elif not records or len(records) == 0:
                status = "FAIL (Empty Data)"
                count = 0
                sample = "N/A"
                all_passed = False
            else:
                status = "PASS"
                count = len(records)
                first = records[0]
                sample_parts = [f"{k}: {first.get(k)}" for k in item["fields"] if k in first]
                sample = ", ".join(sample_parts)[:40] + ("..." if len(", ".join(sample_parts)) > 40 else "")

        except Exception as exc:
            duration = time.time() - start_time
            status = f"ERROR ({type(exc).__name__})"
            count = 0
            sample = str(exc)[:35]
            all_passed = False

        summary_results.append({
            "name": name,
            "status": status,
            "count": count,
            "duration": f"{duration:.2f}s",
            "json_file": json_path.name,
            "sample": sample
        })

    # Print Formatted Table
    print("\n\n" + "=" * 95)
    print("                          SCRAPING PIPELINE EXECUTION SUMMARY")
    print("=" * 95)
    header = f"{'Target Site':<12} | {'Status':<7} | {'Records':<8} | {'Time':<7} | {'Output File':<16} | {'Sample Record'}"
    print(header)
    print("-" * 95)
    
    for row in summary_results:
        print(f"{row['name']:<12} | {row['status']:<7} | {row['count']:<8} | {row['duration']:<7} | {row['json_file']:<16} | {row['sample']}")
        
    print("=" * 95)

    # Post-Execution Disk Artifact Integrity Verification
    print("\n[*] Running Post-Execution Disk Artifact Verification Guard...")
    verification_errors = []
    for item in SCRAPERS:
        path = item["json_path"]
        if not path.exists():
            verification_errors.append(f"Missing file on disk: {path.name}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                disk_data = json.load(f)
            if not isinstance(disk_data, list):
                verification_errors.append(f"{path.name} root element is not a JSON array (got {type(disk_data).__name__})")
            elif len(disk_data) == 0:
                verification_errors.append(f"{path.name} is empty (0 records)")
            else:
                print(f"  [OK] Verified {path.name:<16}: Valid JSON array with {len(disk_data)} records.")
        except Exception as err:
            verification_errors.append(f"JSON decode error in {path.name}: {err}")

    if verification_errors or not all_passed:
        print("\n" + "!" * 80)
        print("  CRITICAL: PIPELINE VERIFICATION FAILED")
        for err in verification_errors:
            print(f"  - {err}")
        print("!" * 80 + "\n")
        raise RuntimeError(f"Pipeline verification failure: {len(verification_errors)} issue(s) detected.")

    print("\n[+] SUCCESS: All 5 scrapers executed successfully with valid non-empty JSON outputs.\n")
    return 0


if __name__ == "__main__":
    exit_code = run_pipeline()
    sys.exit(exit_code)
