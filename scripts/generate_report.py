# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fpdf2>=2.7",
# ]
# ///
import argparse
import json
import os
import sys
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

class ReportPDF(FPDF):
    def __init__(self, title, font_family="DejaVu", orientation="L", unit="mm", format="A4"):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.report_title = title
        self.font_family_name = font_family

    def header(self):
        self.set_font(self.font_family_name, "B", 16)
        self.cell(0, 10, self.report_title, align="L")
        self.set_font(self.font_family_name, "", 10)
        self.cell(0, 10, datetime.now().strftime("%Y-%m-%d %H:%M"), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)
        self.line(10, self.get_y(), 287, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font(self.font_family_name, "", 8)
        self.line(10, self.get_y() - 2, 287, self.get_y() - 2)
        self.cell(0, 8, "Створено за допомогою wiki-trends Agent Skill", align="C")

def setup_pdf_font(pdf: FPDF) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_font_dir = os.path.join(script_dir, "..", "assets", "fonts")
    
    font_regular = os.path.join(assets_font_dir, "DejaVuSans.ttf")
    font_bold = os.path.join(assets_font_dir, "DejaVuSans-Bold.ttf")
    
    if os.path.exists(font_regular):
        try:
            pdf.add_font("DejaVu", "", font_regular)
            if os.path.exists(font_bold):
                pdf.add_font("DejaVu", "B", font_bold)
            else:
                pdf.add_font("DejaVu", "B", font_regular)
            return "DejaVu"
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load bundled DejaVu font: {e}\n")

    # Fallback to helvetica
    return "helvetica"

def safe_str(val, font_family: str) -> str:
    s = str(val) if val is not None else ""
    if font_family == "helvetica":
        return s.encode("latin-1", "replace").decode("latin-1")
    return s

def main():
    parser = argparse.ArgumentParser(description="Generate Wikipedia Trends PDF Report")
    parser.add_argument("--analysis", required=True, help="Path to JSON file from analyze_trends.py")
    parser.add_argument("--chart", required=True, help="Path to chart PNG file from generate_chart.py")
    parser.add_argument("--title", default="Wikipedia Trends Report", help="Report title")
    parser.add_argument("--output", default="report.pdf", help="Output PDF file path")
    
    args = parser.parse_args()
    
    try:
        with open(args.analysis, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read {args.analysis}: {str(e)}"}), file=sys.stdout)
        print(f"Error reading {args.analysis}: {e}", file=sys.stderr)
        sys.exit(1)
        
    pdf = ReportPDF(title=args.title)
    font_fam = setup_pdf_font(pdf)
    pdf.font_family_name = font_fam
    pdf.add_page()
    
    # Layout: Chart on left, Summary on right
    chart_w = 165
    chart_y = pdf.get_y()
    if os.path.exists(args.chart):
        try:
            pdf.image(args.chart, x=10, y=chart_y, w=chart_w)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load chart image {args.chart}: {e}\n")
    
    # Summary on the right
    summary_x = 10 + chart_w + 6
    pdf.set_xy(summary_x, chart_y)
    pdf.set_font(font_fam, "B", 12)
    pdf.cell(0, 8, safe_str("Підсумкові показники", font_fam), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    datasets = data.get("datasets", [])
    if datasets:
        for ds in datasets:
            article = ds.get("article_display", "Unknown")
            proj = ds.get("project", "")
            trend = ds.get("trend", {})
            
            pdf.set_font(font_fam, "B", 10)
            pdf.set_x(summary_x)
            pdf.cell(0, 6, safe_str(f"{article} ({proj})", font_fam), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.set_font(font_fam, "", 9)
            
            total_views = ds.get("total_views", 0)
            pdf.set_x(summary_x + 3)
            pdf.cell(34, 5, safe_str("Всього переглядів:", font_fam))
            pdf.set_font(font_fam, "B", 9)
            pdf.cell(0, 5, f"{total_views:,}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font(font_fam, "", 9)
            
            raw_dir = trend.get("direction", "unknown").lower()
            dir_map = {"growing": "Зростає", "declining": "Спадає", "stable": "Стабільний", "зростаючий": "Зростає", "спадний": "Спадає"}
            direction = dir_map.get(raw_dir, raw_dir.capitalize())
            
            pct = trend.get("change_percent_total", 0.0)
            if pct is None:
                pct = 0.0
            pdf.set_x(summary_x + 3)
            pdf.cell(34, 5, safe_str("Тренд:", font_fam))
            pdf.cell(0, 5, safe_str(f"{direction} ({pct:+.1f}%)", font_fam), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            raw_conf = str(trend.get("confidence", "unknown")).lower()
            conf_map = {"high": "Висока", "medium": "Середня", "low": "Низька", "висока": "Висока", "середня": "Середня", "низька": "Низька"}
            conf = conf_map.get(raw_conf, raw_conf.capitalize())
            
            pdf.set_x(summary_x + 3)
            pdf.cell(34, 5, safe_str("Надійність:", font_fam))
            pdf.cell(0, 5, safe_str(conf, font_fam), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.ln(3)
            
    # Position below the chart
    pdf.set_xy(10, chart_y + 92)
    pdf.set_font(font_fam, "B", 11)
    pdf.cell(0, 7, safe_str("Ключові знахідки та рекомендації", font_fam), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font(font_fam, "", 9)
    
    findings = []
    comparison = data.get("comparison", {})
    if isinstance(comparison, dict) and comparison:
        rec = comparison.get("recommendation")
        if rec:
            findings.append(f"Стратегічна рекомендація: {rec}")
        fastest = comparison.get("fastest_growing")
        if fastest:
            findings.append(f"Найшвидше відносне зростання: {fastest.get('project')} (коефіцієнт: {fastest.get('normalized_growth_rate')})")
        largest = comparison.get("largest_audience")
        if largest:
            findings.append(f"Найбільша аудиторія: {largest.get('project')} (~{largest.get('avg_monthly_views', 0):,.0f} переглядів/міс)")
    elif isinstance(comparison, str) and comparison:
        findings.append(f"Порівняння: {comparison}")
    
    for ds in datasets:
        article = ds.get("article_display", "Unknown")
        anomalies = ds.get("anomalies", [])
        if anomalies:
            spike_dates = [a.get("timestamp") for a in anomalies]
            findings.append(f"{article}: виявлено {len(anomalies)} аномальний сплеск(и) ({', '.join(spike_dates)}).")
        seasonality = ds.get("seasonality", {})
        if isinstance(seasonality, dict) and seasonality.get("detected"):
            peaks = seasonality.get("peak_months", [])
            findings.append(f"{article} (сезонність): пік переглядів у місяцях {peaks} ({seasonality.get('explanation', '')}).")
        trend = ds.get("trend", {})
        conf_exp = trend.get("confidence_explanation")
        if conf_exp:
            findings.append(f"{article} (надійність): {conf_exp}")
            
    if not findings:
        findings.append("Немає специфічних знахідок для відображення.")
        
    for finding in findings[:4]:
        bullet = "•" if font_fam != "helvetica" else "-"
        pdf.multi_cell(0, 5, safe_str(f"{bullet} {finding}", font_fam), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
    pdf.ln(2)
    
    limitations = data.get("limitations", [])
    if limitations:
        pdf.set_font(font_fam, "B", 10)
        pdf.cell(0, 6, safe_str("Методологія та обмеження", font_fam), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font(font_fam, "", 8)
        for lim in limitations[:3]:
            bullet = "•" if font_fam != "helvetica" else "-"
            pdf.multi_cell(0, 4.5, safe_str(f"{bullet} {lim}", font_fam), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
    try:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        pdf.output(args.output)
        print(json.dumps({"status": "success", "output": args.output}), file=sys.stdout)
        sys.stderr.write(f"Report successfully saved to {args.output}\n")
    except Exception as e:
        print(json.dumps({"error": f"Failed to save report: {str(e)}"}), file=sys.stdout)
        sys.stderr.write(f"Error saving report: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
