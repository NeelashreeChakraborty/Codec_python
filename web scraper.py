
"""
Automated Web Scraper with Scheduler
=====================================
Scrapes a target page on a schedule, stores results in SQLite, and can
export everything to CSV.

Why these tools:
- requests + BeautifulSoup: scrape static/rendered HTML (swap in Selenium
  only if the target site needs JS rendering — see USE_SELENIUM below).
- schedule: lightweight in-process scheduler (Celery needs a broker like
  Redis/RabbitMQ running separately, which is overkill for a single script
  meant to "just run"). Swap in Celery later if you need distributed workers.
- sqlite3: built into Python, zero setup.

Install:
    pip install requests beautifulsoup4 schedule

Run:
    python3 scraper.py                 # runs once immediately, then every INTERVAL_MINUTES
    python3 scraper.py --export data.csv   # just export existing DB rows to CSV and exit
"""

import argparse
import csv
import sqlite3
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import schedule

# ---------------------- CONFIG ----------------------
TARGET_URL = "https://example.com"       # <-- change to the site you want to scrape
DB_PATH = "scraper_data.db"
INTERVAL_MINUTES = 60                    # how often to scrape
USE_SELENIUM = False                     # set True only if the page needs JS rendering
# ------------------------------------------------------


def get_html(url: str) -> str:
    """Fetch page HTML. Uses requests by default; falls back to Selenium if enabled."""
    if not USE_SELENIUM:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return resp.text

    # Optional Selenium path for JS-heavy pages
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(2)  # let JS render; tune as needed
        return driver.page_source
    finally:
        driver.quit()


def parse(html: str) -> list[dict]:
    """
    Extract the data you care about. Customize the selectors below for
    your target site — this default example grabs every <h1>/<h2> and
    every <a href> on the page as a placeholder.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tag in soup.select("h1, h2, a"):
        text = tag.get_text(strip=True)
        if not text:
            continue
        rows.append({
            "tag": tag.name,
            "text": text,
            "href": tag.get("href", ""),
        })
    return rows


def init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scraped_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraped_at TEXT,
            tag TEXT,
            text TEXT,
            href TEXT
        )
    """)
    conn.commit()


def save_rows(conn: sqlite3.Connection, rows: list[dict]):
    now = datetime.utcnow().isoformat()
    conn.executemany(
        "INSERT INTO scraped_data (scraped_at, tag, text, href) VALUES (?, ?, ?, ?)",
        [(now, r["tag"], r["text"], r["href"]) for r in rows],
    )
    conn.commit()


def job():
    print(f"[{datetime.now()}] Scraping {TARGET_URL} ...")
    try:
        html = get_html(TARGET_URL)
        rows = parse(html)
        conn = sqlite3.connect(DB_PATH)
        init_db(conn)
        save_rows(conn, rows)
        conn.close()
        print(f"  -> saved {len(rows)} rows to {DB_PATH}")
    except Exception as e:
        print(f"  !! scrape failed: {e}")


def export_csv(csv_path: str):
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    cur = conn.execute("SELECT id, scraped_at, tag, text, href FROM scraped_data")
    rows = cur.fetchall()
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "scraped_at", "tag", "text", "href"])
        writer.writerows(rows)
    conn.close()
    print(f"Exported {len(rows)} rows to {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", metavar="FILE", help="export DB to CSV and exit")
    parser.add_argument("--once", action="store_true", help="run one scrape and exit (no scheduling)")
    args = parser.parse_args()

    if args.export:
        export_csv(args.export)
        sys.exit(0)

    job()  # run immediately on startup

    if args.once:
        sys.exit(0)

    schedule.every(INTERVAL_MINUTES).minutes.do(job)
    print(f"Scheduler running: scraping every {INTERVAL_MINUTES} minute(s). Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(1)
