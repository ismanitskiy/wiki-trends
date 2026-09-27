# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fpdf2>=2.7",
# ]
# ///
"""
generate_report.py — Executive One-Page Landscape A4 Wikipedia Trends Report.
Designed for B2C product decision-makers:
- Top bar: Brand pill, crisp title, metadata
- Hero row (left 64%): Spacious Tableau-style time series chart
- Hero row (right 36%): High-impact KPI cards with big bold numbers and trend badges
- Bottom row (3 columns):
  1. Strategic Conclusion (Product recommendation & launch priority)
  2. Market Signals & Anomalies (Seasonality, educational spikes, YoY)
  3. Boundaries of Confidence & Limitations (Direct task requirement)
"""
import argparse
import json
import os
import sys
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# ═══════════════════════════════════════════════════════════════
# Design Tokens & Palette
# ═══════════════════════════════════════════════════════════════
PAGE_BG         = (248, 250, 252)   # Soft neutral canvas (#F8FAFC, Slate 50)
CARD_BG         = (255, 255, 255)   # Pure white
CARD_BORDER     = (226, 232, 240)   # Slate 200 border (#E2E8F0)
CARD_SHADOW     = (238, 242, 246)   # Subtle drop-shadow tone

TEXT_900        = (15,  23,  42)    # Slate 900 (primary headings, big numbers)
TEXT_700        = (51,  65,  85)    # Slate 700 (body copy)
TEXT_500        = (100, 116, 139)   # Slate 500 (labels, subtitles)
TEXT_400        = (148, 163, 184)   # Slate 400 (secondary metadata)

# Accent Endpoints
INDIGO_PRIMARY  = (79,  70,  229)   # #4F46E5 (Indigo 600)
INDIGO_BG       = (238, 242, 255)   # #EEF2FF (Indigo 50)
INDIGO_BORDER   = (199, 210, 254)   # #C7D2FE (Indigo 200)

TEAL_PRIMARY    = (13,  148, 136)   # #0D9488 (Teal 600)
TEAL_BG         = (240, 253, 250)   # #F0FDFA (Teal 50)

AMBER_PRIMARY   = (217, 119, 6)     # #D97706 (Amber 600)
AMBER_BG        = (254, 243, 199)   # #FEF3C7 (Amber 100)

# Trends: Positive / Negative
GREEN_BG        = (220, 252, 231)   # #DCFCE7
GREEN_TEXT      = (22,  101, 52)    # #166534
RED_BG          = (254, 226, 226)   # #FEE2E2
RED_TEXT        = (159, 18,  57)    # #9F1239

# Dataset Accents (Royal Blue for UK, Rose/Coral for EN/Global)
DS_ACCENTS      = [
    (37,  99,  235),  # Royal Blue
    (244, 63,  94),   # Rose / Coral
    (13,  148, 136),  # Teal
    (245, 158, 11),   # Amber
]


class LandscapeReportPDF(FPDF):
    def __init__(self, font_family="DejaVu"):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.ff = font_family
        self.set_auto_page_break(auto=False)

    def draw_card(self, x, y, w, h, bg=CARD_BG, border=CARD_BORDER, r=3.5, shadow=True):
        """Draw card with soft rounded corners and subtle shadow."""
        if shadow:
            self.set_fill_color(*CARD_SHADOW)
            self.rect(x + 0.35, y + 0.65, w, h, style="F", round_corners=True, corner_radius=r)
        self.set_fill_color(*bg)
        if border:
            self.set_draw_color(*border)
            self.set_line_width(0.25)
            self.rect(x, y, w, h, style="DF", round_corners=True, corner_radius=r)
        else:
            self.rect(x, y, w, h, style="F", round_corners=True, corner_radius=r)

    def draw_pill(self, x, y, text, bg=INDIGO_BG, tc=INDIGO_PRIMARY, font_size=7.0, bold=True, h=5.0):
        """Draw rounded pill badge."""
        self.set_font(self.ff, "B" if bold else "", font_size)
        pw = self.get_string_width(text) + 6.0
        self.set_fill_color(*bg)
        self.rect(x, y, pw, h, style="F", round_corners=True, corner_radius=h / 2)
        self.set_xy(x, y + (h - 3.2) / 2)
        self.set_text_color(*tc)
        self.cell(pw, 3.2, text, align="C")
        return pw

    def draw_number_badge(self, cx, cy, radius, text, bg=INDIGO_PRIMARY, tc=(255, 255, 255)):
        """Draw small circular number badge for sections."""
        self.set_fill_color(*bg)
        self.ellipse(cx - radius, cy - radius, radius * 2, radius * 2, style="F")
        self.set_font(self.ff, "B", 7.5)
        self.set_text_color(*tc)
        self.set_xy(cx - radius, cy - 2.0)
        self.cell(radius * 2, 4.0, str(text), align="C")


def setup_font(pdf: FPDF) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(script_dir, "..", "assets", "fonts")
    regular = os.path.join(fonts_dir, "DejaVuSans.ttf")
    bold = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")
    italic = os.path.join(fonts_dir, "DejaVuSans-Oblique.ttf")
    if os.path.exists(regular):
        try:
            pdf.add_font("DejaVu", "", regular)
            pdf.add_font("DejaVu", "B", bold if os.path.exists(bold) else regular)
            pdf.add_font("DejaVu", "I", italic if os.path.exists(italic) else regular)
            pdf.add_font("DejaVu", "BI", bold if os.path.exists(bold) else regular)
            return "DejaVu"
        except Exception as e:
            sys.stderr.write(f"Warning: font load failed: {e}\n")
    return "helvetica"


def fmt_n(n) -> str:
    """Format integer with space thousands separator (Ukrainian typography)."""
    if n is None:
        return "—"
    return f"{int(n):,}".replace(",", " ")


def main():
    parser = argparse.ArgumentParser(description="Generate Executive Landscape A4 Wikipedia Trends Report")
    parser.add_argument("--analysis", required=True, help="Path to JSON file from analyze_trends.py")
    parser.add_argument("--chart", required=True, help="Path to chart PNG file from generate_chart.py")
    parser.add_argument("--title", default="Аналіз ринкового інтересу: Wikipedia Trends", help="Report title")
    parser.add_argument("--output", default="report.pdf", help="Output PDF file path")
    args = parser.parse_args()

    # Load analysis data
    try:
        with open(args.analysis, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read {args.analysis}: {str(e)}"}), file=sys.stdout)
        sys.exit(1)

    datasets = data.get("datasets", [])
    comparison = data.get("comparison", {}) or {}
    limitations = data.get("limitations", [])

    pdf = LandscapeReportPDF()
    ff = setup_font(pdf)
    pdf.ff = ff
    pdf.add_page()

    # Canvas background (297 x 210 mm)
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, 0, 297, 210, style="F")

    # Top accent line
    pdf.set_fill_color(*INDIGO_PRIMARY)
    pdf.rect(0, 0, 297, 2.0, style="F")

    # ═══════════════════════════════════════════════════════════
    # 1. TOP HEADER (y: 7 to 24)
    # ═══════════════════════════════════════════════════════════
    # Category tag
    pdf.draw_pill(
        x=12, y=7.5,
        text="WIKIPEDIA MARKET INTELLIGENCE  •  EXECUTIVE MEMO",
        bg=INDIGO_BG, tc=INDIGO_PRIMARY,
        font_size=6.8, bold=True, h=5.0
    )

    # Main Report Title
    pdf.set_xy(12, 14.0)
    pdf.set_font(ff, "B", 15.0)
    pdf.set_text_color(*TEXT_900)
    title_text = args.title if not args.title.startswith("Звіт") else args.title
    pdf.cell(185, 7.0, title_text, align="L")

    # Right-aligned metadata
    now_str = datetime.now().strftime("%d.%m.%Y • %H:%M")
    pdf.set_font(ff, "", 7.8)
    pdf.set_text_color(*TEXT_500)
    pdf.set_xy(197, 8.5)
    pdf.cell(88, 4.0, f"Дата: {now_str}", align="R")
    pdf.set_xy(197, 13.0)
    pdf.cell(88, 4.0, "Вибірка: 24 місяці  •  agent=user", align="R")
    pdf.set_xy(197, 17.5)
    pdf.set_font(ff, "", 7.2)
    pdf.set_text_color(*TEXT_400)
    pdf.cell(88, 4.0, "Джерело: Wikimedia REST API (CC BY-SA)", align="R")

    # Header divider
    pdf.set_draw_color(*CARD_BORDER)
    pdf.set_line_width(0.3)
    pdf.line(12, 24.5, 285, 24.5)

    # ═══════════════════════════════════════════════════════════
    # 2. HERO ROW: CHART (LEFT 64%) & KPI CARDS (RIGHT 36%)
    # y = 28 to 123 (Height = 95 mm)
    # ═══════════════════════════════════════════════════════════
    hero_y = 28.0
    hero_h = 95.0
    chart_w = 175.0
    cards_x = 192.0
    cards_w = 93.0

    # ── Left: Chart Container Card ──
    pdf.draw_card(12, hero_y, chart_w, hero_h, r=3.5)

    # Header inside chart card
    pdf.set_xy(17, hero_y + 3.8)
    pdf.set_font(ff, "B", 7.8)
    pdf.set_text_color(*TEXT_500)
    pdf.cell(chart_w - 10, 4.0, "ДИНАМІКА ПОПИТУ ТА ДОВГОСТРОКОВИЙ ТРЕНД (24 МІСЯЦІ)")

    # Embed chart
    if os.path.exists(args.chart):
        try:
            pdf.image(args.chart, x=13.5, y=hero_y + 8.5, w=chart_w - 3.0, h=hero_h - 10.5)
        except Exception as e:
            sys.stderr.write(f"Chart render warning: {e}\n")

    # ── Right: KPI Cards (2 Datasets) ──
    card_gap = 4.5
    avail_h = hero_h - card_gap
    card_h = avail_h / 2.0  # ~45.25 mm each

    for i in range(2):
        cy = hero_y + i * (card_h + card_gap)
        pdf.draw_card(cards_x, cy, cards_w, card_h, r=3.5)

        if i < len(datasets):
            ds = datasets[i]
            article = ds.get("article_display", "—")
            project = ds.get("project", "")
            lang = project.split(".")[0].upper()

            accent_c = DS_ACCENTS[i % len(DS_ACCENTS)]
            # Vertical accent strip on the left edge
            pdf.set_fill_color(*accent_c)
            pdf.rect(cards_x, cy, 3.0, card_h, style="F", round_corners=True, corner_radius=1.5)

            # Language badge
            lpw = pdf.draw_pill(
                cards_x + 6, cy + 4.5,
                text=lang,
                bg=(238, 242, 255) if i == 0 else (255, 241, 242),
                tc=accent_c,
                font_size=6.8, bold=True, h=4.2
            )

            # Article Title
            pdf.set_xy(cards_x + 6 + lpw + 2.5, cy + 4.2)
            pdf.set_font(ff, "B", 9.5)
            pdf.set_text_color(*TEXT_900)
            max_c = int((cards_w - lpw - 15) / 2.2)
            art_disp = article if len(article) <= max_c else article[:max_c-1] + "…"
            pdf.cell(cards_w - lpw - 15, 4.5, art_disp)

            # Domain subtext
            pdf.set_xy(cards_x + 6, cy + 9.5)
            pdf.set_font(ff, "", 7.2)
            pdf.set_text_color(*TEXT_400)
            pdf.cell(cards_w - 12, 3.5, project)

            # Total Views (Big bold)
            total = ds.get("total_views", 0)
            avg = ds.get("avg_views", 0)
            pdf.set_xy(cards_x + 6, cy + 14.5)
            pdf.set_font(ff, "B", 19.0)
            pdf.set_text_color(*TEXT_900)
            tot_str = fmt_n(total)
            tw = pdf.get_string_width(tot_str)
            pdf.cell(tw + 1, 8.5, tot_str)

            # Baseline monthly average next to main number
            pdf.set_xy(cards_x + 6 + tw + 3.0, cy + 18.0)
            pdf.set_font(ff, "", 7.6)
            pdf.set_text_color(*TEXT_500)
            pdf.cell(40, 4.0, f"ср. {fmt_n(int(avg))} / міс")

            # Trend Badge
            trend = ds.get("trend", {})
            pct = trend.get("change_percent_total", 0.0)
            is_up = (pct > 0)
            arrow = "▲" if is_up else "▼"
            badge_lbl = f"{arrow} {pct:+.1f}%"
            badge_bg = GREEN_BG if is_up else RED_BG
            badge_tc = GREEN_TEXT if is_up else RED_TEXT

            tbw = pdf.draw_pill(cards_x + 6, cy + 25.5, badge_lbl, bg=badge_bg, tc=badge_tc, font_size=7.6, h=5.2)

            # R-squared & Confidence alongside trend badge
            r2 = trend.get("r_squared", 0.0)
            conf = str(trend.get("confidence", "—")).capitalize()
            pdf.set_xy(cards_x + 6 + tbw + 3.0, cy + 26.2)
            pdf.set_font(ff, "", 7.0)
            pdf.set_text_color(*TEXT_500)
            pdf.cell(50, 4.0, f"R² = {r2:.2f}  •  {conf} надійність")

            # Anomaly / Seasonal insight footer line
            anom = ds.get("anomalies", [])
            season = ds.get("seasonality", {})
            if anom:
                a_str = f"Виявлено сплеск: {anom[0].get('timestamp')} ({fmt_n(anom[0].get('views', 0))} переглядів)"
            elif season.get("detected"):
                pk = season.get("peak_months", [])
                a_str = f"Сезонні піки: місяці {', '.join(str(m) for m in pk[:3])}" if pk else "Сезонні коливання помірні"
            else:
                a_str = "Динаміка плавна без різких збурень"

            pdf.set_xy(cards_x + 6, cy + 34.5)
            pdf.set_font(ff, "I", 6.8)
            pdf.set_text_color(*TEXT_400)
            pdf.cell(cards_w - 12, 4.0, a_str)

    # ═══════════════════════════════════════════════════════════
    # 3. BOTTOM ROW: THREE ANALYTICAL COLUMNS
    # y = 127 to 198 (Height = 71 mm)
    # Col 1: Strategic Recommendation (Business)
    # Col 2: Market Signals & Anomalies (Data Insights)
    # Col 3: Boundaries of Confidence & Limitations (Methodology)
    # ═══════════════════════════════════════════════════════════
    bot_y = 127.0
    bot_h = 71.0
    col_w = 88.0
    col_gap = 4.5

    # ── COLUMN 1: 1. СТРАТЕГІЧНИЙ ВИСНОВОК ──
    c1_x = 12.0
    pdf.draw_card(c1_x, bot_y, col_w, bot_h, r=3.5)

    # Top accent bar (Indigo)
    pdf.set_fill_color(*INDIGO_PRIMARY)
    pdf.rect(c1_x, bot_y, col_w, 2.5, style="F", round_corners=True, corner_radius=1.5)

    # Number badge & title
    pdf.draw_number_badge(c1_x + 8.0, bot_y + 8.5, radius=3.0, text="1", bg=INDIGO_PRIMARY)
    pdf.set_xy(c1_x + 14.0, bot_y + 6.5)
    pdf.set_font(ff, "B", 9.2)
    pdf.set_text_color(*INDIGO_PRIMARY)
    pdf.cell(col_w - 18, 4.5, "СТРАТЕГІЧНИЙ ВИСНОВОК")

    # Recommendation core text
    rec_text = ""
    if isinstance(comparison, dict):
        rec_text = comparison.get("recommendation", "")
    if not rec_text and datasets:
        d0 = datasets[0]
        t = d0.get("trend", {})
        dir_uk = "зростання" if t.get("direction") == "growing" else "спад"
        rec_text = f"Тема «{d0.get('article_display')}» демонструє {dir_uk} попиту на {t.get('change_percent_total', 0):+.1f}%."

    pdf.set_xy(c1_x + 6, bot_y + 14.0)
    pdf.set_font(ff, "", 8.0)
    pdf.set_text_color(*TEXT_700)
    pdf.multi_cell(col_w - 12, 4.1, rec_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Key business bullet points
    b1_y = max(pdf.get_y() + 2.0, bot_y + 36.0)
    c1_bullets = []
    if isinstance(comparison, dict):
        fg = comparison.get("fastest_growing", {})
        la = comparison.get("largest_audience", {})
        if la:
            c1_bullets.append(f"Лідер обсягу: {la.get('project')} ({fmt_n(int(la.get('avg_monthly_views', 0)))}/міс).")
        if fg:
            c1_bullets.append(f"Відносний ріст: {fg.get('project')} демонструє стійкішу траєкторію.")
    c1_bullets.append("Таймінг запуску: активні промокампанії прив'язувати до осіннього піку попиту.")

    for b in c1_bullets[:3]:
        pdf.set_fill_color(*INDIGO_PRIMARY)
        pdf.ellipse(c1_x + 6, b1_y + 1.2, 1.6, 1.6, style="F")
        pdf.set_xy(c1_x + 10, b1_y)
        pdf.set_font(ff, "", 7.5)
        pdf.set_text_color(*TEXT_700)
        pdf.multi_cell(col_w - 15, 3.8, b, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        b1_y = pdf.get_y() + 1.2

    # ── COLUMN 2: 2. СИГНАЛИ ТА АНОМАЛІЇ РИНКУ ──
    c2_x = c1_x + col_w + col_gap
    pdf.draw_card(c2_x, bot_y, col_w, bot_h, r=3.5)

    # Top accent bar (Teal)
    pdf.set_fill_color(*TEAL_PRIMARY)
    pdf.rect(c2_x, bot_y, col_w, 2.5, style="F", round_corners=True, corner_radius=1.5)

    pdf.draw_number_badge(c2_x + 8.0, bot_y + 8.5, radius=3.0, text="2", bg=TEAL_PRIMARY)
    pdf.set_xy(c2_x + 14.0, bot_y + 6.5)
    pdf.set_font(ff, "B", 9.2)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(col_w - 18, 4.5, "СИГНАЛИ ТА АНОМАЛІЇ")

    # Collect signals from datasets
    signals = []
    for ds in datasets:
        art = ds.get("article_display", "")
        proj = ds.get("project", "").split(".")[0].upper()
        # Anomalies
        for a in ds.get("anomalies", []):
            signals.append(f"{proj} ({art}): сплеск {a.get('timestamp')} — {fmt_n(a.get('views',0))} переглядів (Z = {a.get('z_score',0):.1f}σ).")
        # Seasonality
        s = ds.get("seasonality", {})
        if s.get("detected"):
            pks = s.get("peak_months", [])
            troughs = s.get("trough_months", [])
            if pks:
                signals.append(f"{proj}: виражений пік у місяцях {', '.join(str(m) for m in pks[:3])} (навчальний курс).")
            if troughs:
                signals.append(f"{proj}: літнє просідання інтересу (місяці: {', '.join(str(m) for m in troughs[:3])}).")
        # YoY
        for ych in ds.get("yoy_changes", [])[:1]:
            signals.append(f"{proj}: річна динаміка {ych.get('period')} → {ych.get('change_percent', 0):+.1f}%.")

    if not signals:
        signals = [
            "Динаміка попиту стабільна без екстремальних збурень.",
            "Рівномірний розподіл інтересу протягом усього календарного року."
        ]

    b2_y = bot_y + 14.0
    for sig in signals[:4]:
        pdf.set_fill_color(*TEAL_PRIMARY)
        pdf.ellipse(c2_x + 6, b2_y + 1.2, 1.6, 1.6, style="F")
        pdf.set_xy(c2_x + 10, b2_y)
        pdf.set_font(ff, "", 7.5)
        pdf.set_text_color(*TEXT_700)
        pdf.multi_cell(col_w - 15, 3.8, sig, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        b2_y = pdf.get_y() + 1.2

    # ── COLUMN 3: 3. МЕЖІ ДОВІРИ ТА ПРИПУЩЕННЯ ──
    c3_x = c2_x + col_w + col_gap
    pdf.draw_card(c3_x, bot_y, col_w, bot_h, r=3.5)

    # Top accent bar (Slate)
    pdf.set_fill_color(*TEXT_500)
    pdf.rect(c3_x, bot_y, col_w, 2.5, style="F", round_corners=True, corner_radius=1.5)

    pdf.draw_number_badge(c3_x + 8.0, bot_y + 8.5, radius=3.0, text="3", bg=TEXT_500)
    pdf.set_xy(c3_x + 14.0, bot_y + 6.5)
    pdf.set_font(ff, "B", 9.2)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(col_w - 18, 4.5, "МЕЖІ ДОВІРИ ТА ОБМЕЖЕННЯ")

    if not limitations:
        limitations = [
            "Інтерес ≠ готовність платити: перегляди Вікіпедії відображають академічну цікавість, а не платоспроможний попит на курс.",
            "Фільтрація ботів: використано фільтр agent=user, проте частина автоматизованих парсерів може залишатися у вибірці.",
            "Вплив медіа-подій: новинні приводи (затемнення, запуски NASA) створюють короткі неорганічні сплески.",
            "Статистична похибка: менші мовні розділи (uk) мають вищу волатильність через менший абсолютний розмір аудиторії."
        ]

    b3_y = bot_y + 14.0
    for lim in limitations[:4]:
        pdf.set_fill_color(*TEXT_500)
        pdf.ellipse(c3_x + 6, b3_y + 1.2, 1.6, 1.6, style="F")
        pdf.set_xy(c3_x + 10, b3_y)
        pdf.set_font(ff, "", 7.3)
        pdf.set_text_color(*TEXT_700)
        pdf.multi_cell(col_w - 15, 3.6, lim, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        b3_y = pdf.get_y() + 1.0

    # ═══════════════════════════════════════════════════════════
    # 4. FOOTER
    # ═══════════════════════════════════════════════════════════
    pdf.set_xy(12, 202.0)
    pdf.set_font(ff, "", 7.2)
    pdf.set_text_color(*TEXT_400)
    pdf.cell(273, 4.0, "wiki-trends • Автономний AI-аналітик ринкового попиту (Agent Skills Specification) • 1 сторінка A4 Landscape", align="C")

    # Output file
    try:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        pdf.output(args.output)
        print(json.dumps({"status": "success", "output": args.output}), file=sys.stdout)
        sys.stderr.write(f"Report saved → {args.output}\n")
    except Exception as e:
        print(json.dumps({"error": f"Failed to save report: {str(e)}"}), file=sys.stdout)
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
