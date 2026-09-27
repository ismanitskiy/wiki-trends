# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
# ]
# ///

import argparse
import json
import sys
from datetime import datetime, timedelta
from urllib.parse import unquote

import requests


def compute_default_dates(months: int = 24) -> tuple[str, str]:
    """Compute (start, end) YYYYMMDD strings for the last N full completed calendar months."""
    today = datetime.now()
    first_of_cur = today.replace(day=1)
    end_date = first_of_cur - timedelta(days=1)

    cur_year = end_date.year
    cur_month = end_date.month
    tot_months = cur_year * 12 + cur_month - 1
    start_tot = tot_months - (months - 1)
    start_year = start_tot // 12
    start_month = (start_tot % 12) + 1
    start_date = datetime(start_year, start_month, 1)

    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")


def fetch_pageviews(project, article, start, end, granularity):
    headers = {
        "User-Agent": "WikiTrendsSkill/1.0 (wiki-trends-skill@example.com)"
    }
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/user/{article}/{granularity}/{start}00/{end}00"

    sys.stderr.write(f"Fetching data from: {url}\n")
    response = None
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"Error fetching data: {e}\n")
        if response is not None and response.text:
            sys.stderr.write(f"Response: {response.text}\n")
        sys.exit(1)

    data = response.json()
    items = data.get("items", [])

    formatted_data = []
    total_views = 0
    for item in items:
        timestamp_raw = item.get("timestamp", "")
        # API returns YYYYMMDDHH
        if granularity == "monthly" and len(timestamp_raw) >= 6:
            timestamp = f"{timestamp_raw[0:4]}-{timestamp_raw[4:6]}"
        elif granularity == "daily" and len(timestamp_raw) >= 8:
            timestamp = f"{timestamp_raw[0:4]}-{timestamp_raw[4:6]}-{timestamp_raw[6:8]}"
        else:
            timestamp = timestamp_raw

        views = item.get("views", 0)
        total_views += views
        formatted_data.append({"timestamp": timestamp, "views": views})

    article_display = unquote(article).replace("_", " ")

    return {
        "project": project,
        "article": article,
        "article_display": article_display,
        "granularity": granularity,
        "start": start,
        "end": end,
        "data": formatted_data,
        "total_views": total_views,
        "data_points": len(formatted_data)
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch Wikipedia pageview data from the Wikimedia REST API.")
    parser.add_argument("--project", required=True, help="Wikipedia project domain (e.g., en.wikipedia.org)")
    parser.add_argument("--article", required=True, help="Article title, URL-encoded (e.g., Intermittent_fasting)")
    parser.add_argument("--start", default=None, help="Start date YYYYMMDD (e.g., 20220601). If omitted, auto-computed from --months")
    parser.add_argument("--end", default=None, help="End date YYYYMMDD (e.g., 20240531). If omitted, auto-computed from --months")
    parser.add_argument("--months", type=int, default=24, help="Number of full calendar months if start/end omitted (default: 24)")
    parser.add_argument("--granularity", default="monthly", choices=["daily", "monthly"], help="daily or monthly (default: monthly)")
    parser.add_argument("--output", help="Output file path (default: stdout)")

    args = parser.parse_args()

    start = args.start
    end = args.end
    if not start or not end:
        def_start, def_end = compute_default_dates(args.months)
        start = start or def_start
        end = end or def_end

    result = fetch_pageviews(args.project, args.article, start, end, args.granularity)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json + "\n")
            sys.stderr.write(f"Data saved to {args.output}\n")
        except OSError as e:
            sys.stderr.write(f"Error writing to file: {e}\n")
            sys.exit(1)
    else:
        print(output_json)

if __name__ == "__main__":
    main()
