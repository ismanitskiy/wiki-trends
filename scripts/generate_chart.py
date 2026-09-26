# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "matplotlib",
#     "numpy",
# ]
# ///
import argparse
import json
import sys
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Generate Wikipedia pageviews chart")
    parser.add_argument("--input", action="append", required=True, help="Path to JSON file(s) from fetch_pageviews.py. Can be specified multiple times.")
    parser.add_argument("--title", default="Wikipedia Page Views Comparison", help="Chart title")
    parser.add_argument("--output", default="chart.png", help="Output PNG file path")
    parser.add_argument("--width", type=float, default=12, help="Chart width in inches")
    parser.add_argument("--height", type=float, default=6, help="Chart height in inches")
    parser.add_argument("--trend-line", action="store_true", help="Add linear trend lines")
    
    args = parser.parse_args()
    
    plt.figure(figsize=(args.width, args.height), dpi=150)
    
    colors = plt.cm.tab10.colors
    
    all_dates_set = set()
    
    datasets = []
    
    for i, input_file in enumerate(args.input):
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(json.dumps({"error": f"Failed to read {input_file}: {str(e)}"}), file=sys.stdout)
            print(f"Error reading {input_file}: {e}", file=sys.stderr)
            sys.exit(1)
            
        project = data.get("project", "unknown")
        article = data.get("article_display", data.get("article", "Unknown"))
        label = f"{article} ({project})"
        
        points = data.get("data", [])
        if not points:
            continue
            
        points.sort(key=lambda x: x.get("timestamp", ""))
        
        timestamps = [p.get("timestamp") for p in points]
        views = [p.get("views", 0) for p in points]
        
        datasets.append({
            "label": label,
            "timestamps": timestamps,
            "views": views,
            "color": colors[i % len(colors)]
        })
        all_dates_set.update(timestamps)
    
    if not datasets:
        print(json.dumps({"error": "No data found in input files."}), file=sys.stdout)
        sys.exit(1)
        
    for ds in datasets:
        parsed_dates = []
        for ts in ds["timestamps"]:
            try:
                if len(ts) == 7: # YYYY-MM
                    parsed_dates.append(datetime.strptime(ts, "%Y-%m"))
                elif len(ts) == 10:
                    parsed_dates.append(datetime.strptime(ts, "%Y-%m-%d"))
                elif len(ts) == 8:
                    parsed_dates.append(datetime.strptime(ts, "%Y%m%d"))
                else:
                    parsed_dates.append(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
            except ValueError:
                pass
        
        if not parsed_dates or len(parsed_dates) != len(ds["views"]):
            # Fallback if dates can't be parsed properly
            plt.plot(ds["timestamps"], ds["views"], label=ds["label"], color=ds["color"], linewidth=2)
            if args.trend_line and len(ds["views"]) > 1:
                x_num = np.arange(len(ds["views"]))
                z = np.polyfit(x_num, ds["views"], 1)
                p = np.poly1d(z)
                plt.plot(ds["timestamps"], p(x_num), linestyle='--', color=ds["color"], alpha=0.5)
        else:
            plt.plot(parsed_dates, ds["views"], label=ds["label"], color=ds["color"], linewidth=2)
            if args.trend_line and len(parsed_dates) > 1:
                x_num = matplotlib.dates.date2num(parsed_dates)
                z = np.polyfit(x_num, ds["views"], 1)
                p = np.poly1d(z)
                plt.plot(parsed_dates, p(x_num), linestyle='--', color=ds["color"], alpha=0.5)

    plt.title(args.title)
    plt.xlabel("Date")
    plt.ylabel("Views")
    
    plt.gca().yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    
    try:
        plt.savefig(args.output, dpi=150, facecolor='white')
        print(json.dumps({"status": "success", "output": args.output}), file=sys.stdout)
        print(f"Chart successfully saved to {args.output}", file=sys.stderr)
    except Exception as e:
        print(json.dumps({"error": f"Failed to save chart: {str(e)}"}), file=sys.stdout)
        print(f"Error saving chart: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
