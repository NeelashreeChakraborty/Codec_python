# Codec_python
Projects for the python internship by codec technologies


# 1. Automated Web Scraper with Scheduler

A single-file Python tool that scrapes a website on a schedule, stores the
results in SQLite, and can export everything to CSV.

## Stack

| Purpose        | Tool                          |
|-----------------|--------------------------------|
| Scraping        | `requests` + `BeautifulSoup`  |
| JS-heavy pages  | `selenium` (optional, off by default) |
| Scheduling      | `schedule` (in-process, no broker needed) |
| Storage         | `sqlite3` (built into Python) |
| Export          | `csv` (built into Python)     |

**Why not Celery?** Celery needs a separate broker (Redis/RabbitMQ) running
alongside it, which is a lot of infrastructure for "run this every N
minutes." `schedule` does the same job in-process with zero extra services.
If you later need distributed workers across multiple machines, Celery is
the natural upgrade path — this script is intentionally simple.

## Setup

```bash
git clone <your-repo-url>
cd <your-repo>
pip install -r requirements.txt
```

## Configuration

Open `scraper.py` and edit the config block near the top:

```python
TARGET_URL = "https://example.com"   # site to scrape
DB_PATH = "scraper_data.db"          # SQLite file
INTERVAL_MINUTES = 60                # how often to scrape
USE_SELENIUM = False                 # True only if the page needs JS rendering
```

Then customize the `parse()` function's CSS selectors to extract the data
you actually want. By default it grabs every `<h1>`, `<h2>`, and `<a>` tag
as a placeholder example.

## Usage

Run continuously with scheduling (scrapes immediately, then every
`INTERVAL_MINUTES`):

```bash
python3 scraper.py
```

Run a single scrape and exit (useful for cron jobs or CI pipelines instead
of the built-in scheduler):

```bash
python3 scraper.py --once
```

Export everything currently in the database to CSV:

```bash
python3 scraper.py --export data.csv
```

## Data

All scraped rows are stored in `scraper_data.db` (SQLite) in a table called
`scraped_data`, with columns:

| Column       | Description                     |
|--------------|----------------------------------|
| `id`         | Auto-incrementing row ID        |
| `scraped_at` | UTC timestamp of the scrape      |
| `tag`        | HTML tag the data came from     |
| `text`       | Extracted text content          |
| `href`       | Link target, if any              |

## Notes

- If `USE_SELENIUM = True`, you'll also need `pip install selenium` and a
  matching chromedriver available on your system PATH.
- To run this on a schedule without keeping a process alive yourself (e.g.
  in production), consider using `--once` with a system cron job or a
  GitHub Actions scheduled workflow instead of the built-in loop.

## License

MIT — use freely.

# 2. 📈 Real-Time Stock Market Dashboard

A simple, single-file Streamlit app for tracking and visualizing live stock data.

**Stack:** Python · Pandas · Plotly · yfinance · Streamlit

## Features
- Live-ish price data (candlestick chart) for any ticker(s), Yahoo Finance delay applies (~15 min)
- Moving averages (20/50), RSI (14)
- Volume chart
- Key metrics: current price, change %, day high/low, volume
- Multi-ticker support (comma-separated)
- Optional auto-refresh every 60 seconds
- Raw data table (expandable)

## Setup

```bash
git clone <your-repo-url>
cd stock-dashboard
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## Usage
1. In the sidebar, enter one or more ticker symbols (e.g. `AAPL, MSFT, TSLA`).
2. Pick a history range (1d up to 5y).
3. Toggle moving averages / RSI on or off.
4. Optionally enable auto-refresh to poll for new data every 60 seconds.

## Notes
- No API key required — `yfinance` pulls public Yahoo Finance data.
- Data is cached for 60 seconds per ticker to avoid rate limiting and keep the UI snappy.
- This is "real-time-ish": Yahoo Finance data is typically delayed by about 15 minutes, which is standard for free stock data sources.

## Project structure
```
stock-dashboard/
├── app.py              # entire dashboard (single file)
├── requirements.txt    # dependencies
└── README.md
```

## Deploying
Easiest free option: [Streamlit Community Cloud](https://streamlit.io/cloud)
1. Push this repo to GitHub.
2. Go to share.streamlit.io, connect your GitHub, pick this repo, set main file to `app.py`.
3. Deploy.
