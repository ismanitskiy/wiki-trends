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

# SaaS Dashboard Palette: Royal Blue, Rose/Coral, Emerald/Teal, Amber
PALETTE = [
    "#2563EB",  # Royal Blue (Primary)
    "#F43F5E",  # Rose / Coral (Secondary)
    "#0D9488",  # Teal
    "#F59E0B",  # Amber
    "#8B5CF6",  # Violet
]

# Background color matching report cards
BG_COLOR = "#FFFFFF"

def main():
    parser = argparse.ArgumentParser(description="Generate Tableau-style Wikipedia pageviews chart")
    parser.add_argument("--input", action="append", required=True, help="Path to JSON file(s) from fetch_pageviews.py. Can be specified multiple times.")
    parser.add_argument("--title", default="", help="Chart title (optional, leave empty for seamless report embedding)")
    parser.add_argument("--output", default="chart.png", help="Output PNG file path")
    parser.add_argument("--width", type=float, default=9.2, help="Chart width in inches")
    parser.add_argument("--height", type=float, default=3.0, help="Chart height in inches")
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
        label = f"{article} ({project.split('.')[0]})"
        
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
        
    # ── Typography & RC params ──
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans'],
        'axes.edgecolor': '#D0D0D0',
        'axes.linewidth': 0.6,
        'xtick.color': '#6B7280',
        'ytick.color': '#6B7280',
        'text.color': '#374151',
        'figure.facecolor': BG_COLOR,
        'axes.facecolor': BG_COLOR,
        'axes.labelcolor': '#6B7280',
    })
    
    fig, ax = plt.subplots(figsize=(args.width, args.height), dpi=200)
    
    # ── Minimal spines: only bottom + left, very thin ──
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E5E7EB')
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_color('#E5E7EB')
    ax.spines['bottom'].set_linewidth(0.5)
    
    # ── Subtle horizontal gridlines (Tableau hallmark) ──
    ax.yaxis.grid(True, color='#F3F4F6', linewidth=0.8, linestyle='-')
    ax.xaxis.grid(False)
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
            # Semi-transparent area fill (Tableau-style subtle shading)
            ax.fill_between(parsed_dates, ds["views"], color=color, alpha=0.07)
            
            # Thin smooth line — Tableau aesthetic: no markers for clean look
            ax.plot(
                parsed_dates,
                ds["views"],
                label=ds["label"],
                color=color,
                linewidth=2.0,
                solid_capstyle='round',
                solid_joinstyle='round',
            )
            
            # Small dot markers at data points — very subtle
            ax.scatter(
                parsed_dates,
                ds["views"],
                color=color,
                s=12,
                zorder=5,
                edgecolors='white',
                linewidths=0.8,
            )
            
            # Subtle dashed linear trend
            if args.trend_line and len(ds["views"]) > 1:
                x_num = mdates.date2num(parsed_dates)
                z = np.polyfit(x_num, ds["views"], 1)
                p = np.poly1d(z)
                ax.plot(
                    parsed_dates, p(x_num),
                    linestyle='--', color=color, alpha=0.35, linewidth=1.2,
                    dash_capstyle='round'
                )
        else:
            # Fallback for non-parsed dates
            x_seq = list(range(len(ds["views"])))
            ax.fill_between(x_seq, ds["views"], color=color, alpha=0.07)
            ax.plot(
                x_seq,
                ds["views"],
                label=ds["label"],
                color=color,
                linewidth=2.0,
            )
            ax.set_xticks(x_seq)
            ax.set_xticklabels(ds["timestamps"])

    # ── X-axis formatting ──
    if datasets and parsed_dates:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    # ── Tick styling: no tick marks, just labels ──
    ax.tick_params(axis='both', which='both', length=0, labelsize=8.5, pad=6)
    
    # ── Y-axis: thousands separator ──
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    # ── Axis labels ──
    ax.set_ylabel("Перегляди / місяць", fontsize=9, labelpad=10)
    
    # ── Optional Title (left-aligned, Tableau style) ──
    if args.title:
        ax.set_title(args.title, fontsize=12, weight='bold', color='#1F2937', pad=16, loc='left')
        
    # ── Legend: clean, horizontal, bottom-anchored, frameless ──
    legend = ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.12),
        ncol=len(datasets),
        frameon=False,
        fontsize=9,
        labelcolor='#4B5563',
        handlelength=2.0,
        handletextpad=0.6,
        columnspacing=2.5,
    )
    
    # ── Add min Y padding ──
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(bottom=max(0, y_min - (y_max - y_min) * 0.05))
            
    plt.tight_layout()
    
    try:
        plt.savefig(
            args.output, dpi=200,
            facecolor=BG_COLOR, edgecolor='none',
            bbox_inches='tight', pad_inches=0.15
        )
        print(json.dumps({"status": "success", "output": args.output}), file=sys.stdout)
        sys.stderr.write(f"Chart successfully saved to {args.output}\n")
    except Exception as e:
        print(json.dumps({"error": f"Failed to save chart: {str(e)}"}), file=sys.stdout)
        sys.stderr.write(f"Error saving chart: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
