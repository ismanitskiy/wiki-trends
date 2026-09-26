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

class ModernReportPDF(FPDF):
    def __init__(self, title, font_family="DejaVu", orientation="L", unit="mm", format="A4"):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.report_title = title
        self.font_family_name = font_family
        self.set_auto_page_break(auto=False)

    def draw_badge(self, x, y, w, h, text, bg_color, text_color, font_size=8, bold=True):
        self.set_fill_color(*bg_color)
        self.set_draw_color(*bg_color)
        self.rect(x=x, y=y, w=w, h=h, style="DF", round_corners=True, corner_radius=2)
        
        self.set_xy(x, y + (h - 3.8) / 2)
        self.set_text_color(*text_color)
        self.set_font(self.font_family_name, "B" if bold else "", font_size)
        self.cell(w, 3.8, text, align="C")

    def footer(self):
        self.set_y(202)
        self.set_font(self.font_family_name, "", 8)
        self.set_text_color(148, 163, 184) # #94A3B8
        self.cell(0, 5, "wiki-trends • Автономний AI-аналітик ринкового попиту (Agent Skills Specification) • 1 сторінка", align="C")

def setup_pdf_font(pdf: FPDF) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_font_dir = os.path.join(script_dir, "..", "assets", "fonts")
    
    font_regular = os.path.join(assets_font_dir, "DejaVuSans.ttf")
    font_bold = os.path.join(assets_font_dir, "DejaVuSans-Bold.ttf")
    font_italic = os.path.join(assets_font_dir, "DejaVuSans-Oblique.ttf")
    
    if os.path.exists(font_regular):
        try:
            pdf.add_font("DejaVu", "", font_regular)
            pdf.add_font("DejaVu", "B", font_bold if os.path.exists(font_bold) else font_regular)
            pdf.add_font("DejaVu", "I", font_italic if os.path.exists(font_italic) else font_regular)
            pdf.add_font("DejaVu", "BI", font_bold if os.path.exists(font_bold) else font_regular)
            return "DejaVu"
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load bundled DejaVu font: {e}\n")

    return "helvetica"

def safe_str(val, font_family: str) -> str:
    s = str(val) if val is not None else ""
    if font_family == "helvetica":
        return s.encode("latin-1", "replace").decode("latin-1")
    return s

def draw_card_bullets(pdf, x, y, w, items, font_family, max_lines=4):
    pdf.set_font(font_family, "", 8.3)
    pdf.set_text_color(51, 65, 85) # Slate 700
    
    current_y = y
    for it in items[:max_lines]:
        pdf.set_xy(x, current_y)
        bullet_text = f"• {it}"
        pdf.multi_cell(w, 4.4, safe_str(bullet_text, font_family))
        current_y = pdf.get_y() + 1.2

def main():
    parser = argparse.ArgumentParser(description="Generate minimalist executive Wikipedia Trends PDF Report")
    parser.add_argument("--analysis", required=True, help="Path to JSON file from analyze_trends.py")
    parser.add_argument("--chart", required=True, help="Path to chart PNG file from generate_chart.py")
    parser.add_argument("--title", default="Аналіз ринкового інтересу: Wikipedia Trends", help="Report title")
    parser.add_argument("--output", default="report.pdf", help="Output PDF file path")
    
    args = parser.parse_args()
    
    try:
        with open(args.analysis, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read {args.analysis}: {str(e)}"}), file=sys.stdout)
        print(f"Error reading {args.analysis}: {e}", file=sys.stderr)
        sys.exit(1)
        
    pdf = ModernReportPDF(title=args.title)
    font_fam = setup_pdf_font(pdf)
    pdf.font_family_name = font_fam
    pdf.add_page()
    
    # ----------------------------------------------------
    # 1. TOP HEADER (Sleek category tag, bold title, date badge)
    # ----------------------------------------------------
    # Overtitle pill badge
    pdf.draw_badge(
        x=12, y=9, w=68, h=5.5,
        text="WIKIPEDIA MARKET INTELLIGENCE",
        bg_color=(238, 242, 255), text_color=(79, 70, 229), # Indigo tint
        font_size=7, bold=True
    )
    
    # Main Report Title
    pdf.set_xy(12, 16)
    pdf.set_text_color(15, 23, 42) # Slate 900
    pdf.set_font(font_fam, "B", 16)
    pdf.cell(180, 8, safe_str(args.title, font_fam), align="L")
    
    # Right-aligned metadata
    pdf.set_xy(195, 12)
    pdf.set_text_color(100, 116, 139) # Slate 500
    pdf.set_font(font_fam, "", 8.5)
    now_str = datetime.now().strftime("%d.%m.%Y • %H:%M")
    pdf.cell(90, 5, f"Дата: {now_str}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(195)
    pdf.cell(90, 5, "Вибірка: Останні 2 роки • agent=user", align="R")
    
    # Header divider line
    pdf.set_draw_color(226, 232, 240) # Slate 200
    pdf.line(12, 26, 285, 26)
    
    # ----------------------------------------------------
    # 2. HERO SECTION: CHART (LEFT) & KPI CARDS (RIGHT)
    # ----------------------------------------------------
    hero_y = 29
    hero_h = 96
    chart_w = 175
    
    # Left container card for chart
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(x=12, y=hero_y, w=chart_w, h=hero_h, style="DF", round_corners=True, corner_radius=3)
    
    if os.path.exists(args.chart):
        try:
            pdf.image(args.chart, x=13, y=hero_y + 1, w=chart_w - 2, h=hero_h - 2)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load chart image {args.chart}: {e}\n")
            
    # Right side: KPI Cards for datasets
    cards_x = 192
    cards_w = 93
    datasets = data.get("datasets", [])
    num_ds = max(1, len(datasets))
    
    card_gap = 4
    avail_h = hero_h - (card_gap * (num_ds - 1))
    card_h = avail_h / num_ds
    
    for i, ds in enumerate(datasets[:3]):
        cy = hero_y + i * (card_h + card_gap)
        
        # Card background
        pdf.set_fill_color(248, 250, 252) # Slate 50
        pdf.set_draw_color(226, 232, 240) # Slate 200
        pdf.rect(x=cards_x, y=cy, w=cards_w, h=card_h, style="DF", round_corners=True, corner_radius=3)
        
        article = ds.get("article_display", "Тема")
        proj = ds.get("project", "")
        
        # Color accent dot (Indigo for 1st, Teal for 2nd, Orange for 3rd)
        dot_colors = [(79, 70, 229), (13, 148, 136), (249, 115, 22)]
        dot_c = dot_colors[i % len(dot_colors)]
        pdf.set_fill_color(*dot_c)
        pdf.ellipse(x=cards_x + 6, y=cy + 6, w=2.6, h=2.6, style="F")
        
        # Main title
        pdf.set_xy(cards_x + 11, cy + 4.5)
        pdf.set_font(font_fam, "B", 10.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(cards_w - 18, 5, safe_str(article, font_fam))
        
        # Project subtitle
        pdf.set_xy(cards_x + 11, cy + 9.5)
        pdf.set_font(font_fam, "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(cards_w - 18, 4, safe_str(proj, font_fam))
        
        # Metric: Total views
        total_views = ds.get("total_views", 0)
        avg_views = ds.get("avg_views", 0)
        
        pdf.set_xy(cards_x + 6, cy + 15.5)
        pdf.set_font(font_fam, "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(cards_w - 12, 4, "Загальні перегляди:")
        
        pdf.set_xy(cards_x + 6, cy + 19.5)
        pdf.set_font(font_fam, "B", 16)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(48, 7, f"{total_views:,}")
        
        # Trend badge
        trend = ds.get("trend", {})
        pct = trend.get("change_percent_total", 0.0)
        
        is_positive = (pct > 0)
        badge_bg = (220, 252, 231) if is_positive else (255, 228, 230) # Green 100 / Rose 100
        badge_tc = (22, 101, 52) if is_positive else (159, 18, 57)    # Green 800 / Rose 800
        arrow = "▲" if is_positive else "▼"
        badge_text = f"{arrow} {pct:+.1f}%"
        
        pdf.draw_badge(
            x=cards_x + 52, y=cy + 20, w=35, h=6,
            text=badge_text,
            bg_color=badge_bg, text_color=badge_tc,
            font_size=8.5, bold=True
        )
        
        # Average & Confidence line
        pdf.set_xy(cards_x + 6, cy + 28)
        pdf.set_font(font_fam, "", 8)
        pdf.set_text_color(100, 116, 139)
        
        raw_conf = str(trend.get("confidence", "середня")).capitalize()
        pdf.cell(cards_w - 12, 4, f"В середньому: {avg_views:,.0f}/міс  •  Надійність: {raw_conf}")
        
        # Anomalies / Seasonality snippet if card height allows
        if card_h > 38:
            anom = ds.get("anomalies", [])
            snip = f"Аномалії: виявлено {len(anom)} сплесків" if anom else "Без різких аномалій"
            pdf.set_xy(cards_x + 6, cy + 33)
            pdf.set_font(font_fam, "I", 7.5)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(cards_w - 12, 4, snip)

    # ----------------------------------------------------
    # 3. BOTTOM SECTION: 3 MODERN ANALYSIS CARDS
    # ----------------------------------------------------
    bot_y = 129
    bot_h = 67
    col_w = 89
    
    # CARD 1: СТРАТЕГІЧНИЙ ВИСНОВОК (Highlighted Indigo tint)
    pdf.set_fill_color(245, 243, 255) # Indigo 50
    pdf.set_draw_color(199, 210, 254) # Indigo 200
    pdf.rect(x=12, y=bot_y, w=col_w, h=bot_h, style="DF", round_corners=True, corner_radius=3)
    
    pdf.set_xy(16, bot_y + 4.5)
    pdf.set_font(font_fam, "B", 10)
    pdf.set_text_color(67, 56, 202) # Indigo 700
    pdf.cell(col_w - 8, 5, "СТРАТЕГІЧНИЙ ВИСНОВОК")
    
    comparison = data.get("comparison", {})
    rec_text = ""
    if isinstance(comparison, dict):
        rec_text = comparison.get("recommendation", "")
    
    if not rec_text and datasets:
        d0 = datasets[0]
        t = d0.get("trend", {})
        dir_uk = "зростання" if t.get("direction") == "growing" else "спад"
        rec_text = f"Тема '{d0.get('article_display')}' демонструє {dir_uk} інтересу на {t.get('change_percent_total', 0):+.1f}%. Рівень довіри до тренду оцінено як {t.get('confidence')}."
        
    pdf.set_xy(16, bot_y + 11.5)
    pdf.set_font(font_fam, "", 8.4)
    pdf.set_text_color(30, 41, 59) # Slate 800
    pdf.multi_cell(col_w - 8, 4.4, safe_str(rec_text, font_fam))
    
    if isinstance(comparison, dict) and comparison.get("fastest_growing"):
        fg = comparison.get("fastest_growing", {})
        la = comparison.get("largest_audience", {})
        
        pdf.set_xy(16, bot_y + 45)
        pdf.set_font(font_fam, "B", 8)
        pdf.set_text_color(79, 70, 229)
        pdf.cell(col_w - 8, 4.5, f"Лідер росту: {fg.get('project')}")
        
        pdf.set_xy(16, bot_y + 50)
        pdf.cell(col_w - 8, 4.5, f"Найбільша база: {la.get('project')}")

    # CARD 2: КЛЮЧОВІ СИГНАЛИ ТА СЕЗОННІСТЬ
    col2_x = 12 + col_w + 3
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(x=col2_x, y=bot_y, w=col_w, h=bot_h, style="DF", round_corners=True, corner_radius=3)
    
    pdf.set_xy(col2_x + 5, bot_y + 4.5)
    pdf.set_font(font_fam, "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(col_w - 8, 5, "СИГНАЛИ ПОПИТУ ТА СЕЗОННІСТЬ")
    
    signals = []
    for ds in datasets:
        art = ds.get("article_display")
        season = ds.get("seasonality", {})
        if isinstance(season, dict) and season.get("detected"):
            peaks = season.get("peak_months", [])
            signals.append(f"{art}: виявлено сезонність (пікові місяці: {peaks}).")
        anom = ds.get("anomalies", [])
        if anom:
            dates = [a.get("timestamp") for a in anom[:2]]
            signals.append(f"{art}: сплеск(и) переглядів у {', '.join(dates)}.")
        t_expl = ds.get("trend", {}).get("confidence_explanation")
        if t_expl:
            signals.append(f"{art}: {t_expl}")
            
    if not signals:
        signals.append("Динаміка переглядів є плавною без екстремальних піків.")
        
    draw_card_bullets(pdf, col2_x + 5, bot_y + 11.5, col_w - 10, signals, font_fam, max_lines=4)

    # CARD 3: МЕТОДОЛОГІЯ ТА ПРОДУКТОВІ РИЗИКИ
    col3_x = col2_x + col_w + 3
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(x=col3_x, y=bot_y, w=col_w, h=bot_h, style="DF", round_corners=True, corner_radius=3)
    
    pdf.set_xy(col3_x + 5, bot_y + 4.5)
    pdf.set_font(font_fam, "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(col_w - 8, 5, "ПРОДУКТОВІ ЗАСТЕРЕЖЕННЯ")
    
    limitations = data.get("limitations", [])
    if not limitations:
        limitations = [
            "Перегляди сторінок відображають інтерес до читання, а не готовність платити.",
            "Зовнішні інфоприводи можуть створювати тимчасовий неорганічний попит.",
            "Менші мовні розділи Вікіпедії мають більшу статистичну похибку."
        ]
        
    draw_card_bullets(pdf, col3_x + 5, bot_y + 11.5, col_w - 10, limitations, font_fam, max_lines=4)

    # ----------------------------------------------------
    # SAVE AND OUTPUT
    # ----------------------------------------------------
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
