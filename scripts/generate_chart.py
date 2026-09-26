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
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np

# Premium minimalist palette (Indigo, Emerald/Teal, Coral/Orange, Purple, Cyan)
PALETTE = [
    "#4F46E5",  # Modern Indigo
    "#0D9488",  # Deep Teal
    "#F97316",  # Warm Coral/Orange
    "#8B5CF6",  # Violet
    "#0284C7",  # Sky Blue
]

def main():
    parser = argparse.ArgumentParser(description="Generate minimalist modern Wikipedia pageviews chart")
    parser.add_argument("--input", action="append", required=True, help="Path to JSON file(s) from fetch_pageviews.py. Can be specified multiple times.")
    parser.add_argument("--title", default="", help="Chart title (optional, leave empty for seamless report embedding)")
    parser.add_argument("--output", default="chart.png", help="Output PNG file path")
    parser.add_argument("--width", type=float, default=11.5, help="Chart width in inches")
    parser.add_argument("--height", type=float, default=5.2, help="Chart height in inches")
    parser.add_argument("--trend-line", action="store_true", help="Add subtle linear trend lines")
    
    args = parser.parse_args()
    
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
        label = f"{article} • {project}"
        
        points = data.get("data", [])
        if not points:
            continue
            
        points.sort(key=lambda x: x.get("timestamp", ""))
        
        timestamps = [p.get("timestamp") for p in points]
        views = [p.get("views", 0) for p in points]
        
        color = PALETTE[i % len(PALETTE)]
        datasets.append({
            "label": label,
            "timestamps": timestamps,
            "views": views,
            "color": color
        })
    
    if not datasets:
        print(json.dumps({"error": "No data found in input files."}), file=sys.stdout)
        sys.exit(1)
        
    # Styling figure
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    plt.rcParams['axes.edgecolor'] = '#CBD5E1'
    fig, ax = plt.subplots(figsize=(args.width, args.height), dpi=180, facecolor='#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    
    # Remove top, right, left spines for ultra-clean minimalist look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.spines['bottom'].set_linewidth(1.2)
    
    # Subtle horizontal grid only
    ax.grid(axis='y', color='#F1F5F9', linestyle='-', linewidth=1.2)
    ax.grid(axis='x', visible=False)
    ax.set_axisbelow(True)
    
    for ds in datasets:
        parsed_dates = []
        for ts in ds["timestamps"]:
            try:
                if len(ts) == 7:
                    parsed_dates.append(datetime.strptime(ts, "%Y-%m"))
                elif len(ts) == 10:
                    parsed_dates.append(datetime.strptime(ts, "%Y-%m-%d"))
                elif len(ts) == 8:
                    parsed_dates.append(datetime.strptime(ts, "%Y%m%d"))
                else:
                    parsed_dates.append(datetime.strptime(ts[:10], "%Y-%m-%d"))
            except ValueError:
                pass
                
        color = ds["color"]
        
        if len(parsed_dates) == len(ds["views"]) and parsed_dates:
            # Subtle gradient area fill under the line
            ax.fill_between(parsed_dates, ds["views"], color=color, alpha=0.08)
            
            # Crisp main curve
            ax.plot(
                parsed_dates,
                ds["views"],
                label=ds["label"],
                color=color,
                linewidth=2.4,
                marker='o',
                markersize=4.5,
                markerfacecolor='#FFFFFF',
                markeredgecolor=color,
                markeredgewidth=1.8,
                solid_capstyle='round'
            )
            
            # Subtle dashed linear trend
            if args.trend_line and len(ds["views"]) > 1:
                x_num = mdates.date2num(parsed_dates)
                z = np.polyfit(x_num, ds["views"], 1)
                p = np.poly1d(z)
                ax.plot(parsed_dates, p(x_num), linestyle=':', color=color, alpha=0.5, linewidth=1.6)
        else:
            # Fallback for non-parsed dates
            x_seq = list(range(len(ds["views"])))
            ax.fill_between(x_seq, ds["views"], color=color, alpha=0.08)
            ax.plot(
                x_seq,
                ds["views"],
                label=ds["label"],
                color=color,
                linewidth=2.4,
                marker='o',
                markersize=4.5,
                markerfacecolor='#FFFFFF',
                markeredgecolor=color,
                markeredgewidth=1.8
            )
            ax.set_xticks(x_seq)
            ax.set_xticklabels(ds["timestamps"])

    # X-axis formatting: Clean date locator
    if datasets and parsed_dates:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    # Ticks styling
    ax.tick_params(axis='both', which='both', length=0, labelsize=9, colors='#64748B', pad=8)
    
    # Y-axis thousands separator
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    # Axis labels: minimal, muted
    ax.set_ylabel("Перегляди за місяць", fontsize=9, color='#94A3B8', labelpad=10, weight='medium')
    
    # Optional Title
    if args.title:
        ax.set_title(args.title, fontsize=12, color='#1E293B', weight='bold', pad=18, loc='left')
        
    # Legend: Minimalist, horizontal, borderless at top
    legend = ax.legend(
        loc='upper left',
        bbox_to_anchor=(0.0, 1.12),
        ncol=len(datasets),
        frameon=False,
        fontsize=9.5,
        labelcolor='#334155',
        handlelength=1.4,
        handletextpad=0.5,
        columnspacing=1.8
    )
    if legend:
        for text in legend.get_texts():
            text.set_weight('medium')
            
    plt.tight_layout()
    
    try:
        plt.savefig(args.output, dpi=180, facecolor='#FFFFFF', edgecolor='none', bbox_inches='tight')
        print(json.dumps({"status": "success", "output": args.output}), file=sys.stdout)
        sys.stderr.write(f"Chart successfully saved to {args.output}\n")
    except Exception as e:
        print(json.dumps({"error": f"Failed to save chart: {str(e)}"}), file=sys.stdout)
        sys.stderr.write(f"Error saving chart: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
