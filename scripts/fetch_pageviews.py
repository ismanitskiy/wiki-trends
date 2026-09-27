# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
# ]
# ///

import argparse
import json
import sys
from urllib.parse import unquote

import requests


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
    parser.add_argument("--start", required=True, help="Start date YYYYMMDD (e.g., 20220101)")
    parser.add_argument("--end", required=True, help="End date YYYYMMDD (e.g., 20240901)")
    parser.add_argument("--granularity", default="monthly", choices=["daily", "monthly"], help="daily or monthly (default: monthly)")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    result = fetch_pageviews(args.project, args.article, args.start, args.end, args.granularity)
    
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
