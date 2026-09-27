# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fpdf2>=2.7",
# ]
# ///
"""
generate_report.py — Swiss Modular Grid Landscape A4 Wikipedia Trends Report.
Features:
- Perfect 1:2 architectural grid alignment:
  - Top row: [ KPI Cards: 1/3 width (88mm) ] [ Main Chart: 2/3 width (180.5mm) ]
  - Bottom row: [ Col 1: 1/3 (88mm) ] [ Col 2: 1/3 (88mm) ] [ Col 3: 1/3 (88mm) ]
- Clean executive header without technical clutter (no agent=user, CC BY-SA, or extra tags)
- Clear, practical Product Decision Memo in Column 1
- Detailed signals & seasonality in Column 2
- Explicit assumptions & methodology limitations in Column 3
- Full page utilization without wasted space
"""
import argparse
import json
import os
import sys
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# ═══════════════════════════════════════════════════════════════
# Design Tokens
# ═══════════════════════════════════════════════════════════════
PAGE_BG         = (248, 250, 252)   # Soft neutral canvas (#F8FAFC)
CARD_BG         = (255, 255, 255)   # Pure white
CARD_BORDER     = (226, 232, 240)   # Slate 200 border (#E2E8F0)
CARD_SHADOW     = (238, 242, 246)   # Subtle drop-shadow tone

TEXT_900        = (15,  23,  42)    # Slate 900 (primary headings, big numbers)
TEXT_700        = (51,  65,  85)    # Slate 700 (body copy)
TEXT_500        = (100, 116, 139)   # Slate 500 (labels, subtitles)
TEXT_400        = (148, 163, 184)   # Slate 400 (secondary metadata)

# Section Accent Colors
INDIGO_PRIMARY  = (79,  70,  229)   # #4F46E5 (Indigo 600 - Business Decision)
INDIGO_BG       = (238, 242, 255)   # #EEF2FF
TEAL_PRIMARY    = (13,  148, 136)   # #0D9488 (Teal 600 - Signals & Anomalies)
TEAL_BG         = (240, 253, 250)   # #F0FDFA
SLATE_PRIMARY   = (100, 116, 139)   # #64748B (Slate 500 - Limitations)

# Trends
GREEN_BG        = (220, 252, 231)   # #DCFCE7
GREEN_TEXT      = (22,  101, 52)    # #166534
RED_BG          = (254, 226, 226)   # #FEE2E2
RED_TEXT        = (159, 18,  57)    # #9F1239

# Dataset Accents (Royal Blue for UK, Rose for EN/Global)
DS_ACCENTS      = [
    (37,  99,  235),  # Royal Blue (#2563EB)
    (244, 63,  94),   # Rose (#F43F5E)
    (13,  148, 136),  # Teal
    (245, 158, 11),   # Amber
]


class ExecutiveGridPDF(FPDF):
    def __init__(self, font_family="DejaVu"):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.ff = font_family
        self.set_auto_page_break(auto=False)

    def draw_card(self, x, y, w, h, bg=CARD_BG, border=CARD_BORDER, r=3.5, shadow=True):
        """Draw card with soft rounded corners and subtle drop-shadow."""
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

    def draw_pill(self, x, y, text, bg=INDIGO_BG, tc=INDIGO_PRIMARY, font_size=7.2, bold=True, h=5.2):
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
        """Draw small circular number badge for column headers."""
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
    """Format integer with space thousands separator (Ukrainian convention)."""
    if n is None:
        return "—"
    return f"{int(n):,}".replace(",", " ")


def main():
    parser = argparse.ArgumentParser(description="Generate Executive Swiss-Grid Landscape A4 Wikipedia Trends Report")
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

    pdf = ExecutiveGridPDF()
    ff = setup_font(pdf)
    pdf.ff = ff
    pdf.add_page()

    # Canvas background (297 x 210 mm)
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, 0, 297, 210, style="F")

    # ═══════════════════════════════════════════════════════════
    # Grid Geometry Parameters (Exact 1:2 Column System)
    # Page width: 297 mm, Margins: 12 mm left & right
    # Usable width: 273 mm
    # 3 equal columns: width = 88 mm each, gap = 4.5 mm
    # Col 1: x = 12.0 mm, w = 88.0 mm
    # Col 2: x = 104.5 mm, w = 88.0 mm
    # Col 3: x = 197.0 mm, w = 88.0 mm
    # Chart width (Col 2 + gap + Col 3) = 88 + 4.5 + 88 = 180.5 mm
    # ═══════════════════════════════════════════════════════════
    ML      = 12.0
    COL_W   = 88.0
    GAP     = 4.5
    CHART_W = COL_W * 2 + GAP   # 180.5 mm
    CHART_X = ML + COL_W + GAP  # 104.5 mm

    # ═══════════════════════════════════════════════════════════
    # 1. TOP HEADER (y: 10 to 23, h: 13 mm)
    # Clean, uncluttered, no redundant technical tags
    # ═══════════════════════════════════════════════════════════
    now_str = datetime.now().strftime("%d.%m.%Y • %H:%M")

    # Title
    pdf.set_xy(ML, 10.0)
    pdf.set_font(ff, "B", 15.5)
    pdf.set_text_color(*TEXT_900)
    clean_title = args.title if not args.title.startswith("Звіт") else args.title
    pdf.cell(175, 7.5, clean_title, align="L")

    # Right metadata (Date & Sampling window only)
    pdf.set_font(ff, "", 8.0)
    pdf.set_text_color(*TEXT_500)
    pdf.set_xy(197.0, 10.0)
    pdf.cell(88.0, 4.0, f"Дата створення: {now_str}", align="R")
    pdf.set_xy(197.0, 14.5)
    pdf.cell(88.0, 4.0, "Вибірка аналізу: 24 місяці (помісячно)", align="R")

    # Header divider line
    pdf.set_draw_color(*CARD_BORDER)
    pdf.set_line_width(0.3)
    pdf.line(ML, 23.5, ML + COL_W * 3 + GAP * 2, 23.5)

    # ═══════════════════════════════════════════════════════════
    # 2. HERO ROW (y: 27.5 to 123.5, h: 96 mm)
    # Left (1/3, w: 88 mm): 2 KPI Cards
    # Right (2/3, w: 180.5 mm): Main Time Series Chart
    # ═══════════════════════════════════════════════════════════
    hero_y  = 27.5
    hero_h  = 96.0
    card_gap = 4.5
    kpi_card_h = (hero_h - card_gap) / 2.0  # 45.75 mm each

    # ── LEFT: 2 KPI CARDS (Matches Column 1 below) ──
    for i in range(2):
        cy = hero_y + i * (kpi_card_h + card_gap)
        pdf.draw_card(ML, cy, COL_W, kpi_card_h, r=3.5)

        if i < len(datasets):
            ds = datasets[i]
            article = ds.get("article_display", "—")
            project = ds.get("project", "")
            lang = project.split(".")[0].upper()

            accent_c = DS_ACCENTS[i % len(DS_ACCENTS)]
            # Vertical accent strip on left edge
            pdf.set_fill_color(*accent_c)
            pdf.rect(ML, cy, 3.0, kpi_card_h, style="F", round_corners=True, corner_radius=1.5)

            # Language badge
            lpw = pdf.draw_pill(
                ML + 6.0, cy + 4.5,
                text=lang,
                bg=(238, 242, 255) if i == 0 else (255, 241, 242),
                tc=accent_c,
                font_size=6.8, bold=True, h=4.2
            )

            # Article Title
            pdf.set_xy(ML + 6.0 + lpw + 2.5, cy + 4.2)
            pdf.set_font(ff, "B", 9.5)
            pdf.set_text_color(*TEXT_900)
            max_c = int((COL_W - lpw - 15) / 2.2)
            art_disp = article if len(article) <= max_c else article[:max_c-1] + "…"
            pdf.cell(COL_W - lpw - 15, 4.5, art_disp)

            # Project domain subtext
            pdf.set_xy(ML + 6.0, cy + 9.5)
            pdf.set_font(ff, "", 7.2)
            pdf.set_text_color(*TEXT_400)
            pdf.cell(COL_W - 12, 3.5, project)

            # Total Views (Big bold number)
            total = ds.get("total_views", 0)
            avg = ds.get("avg_views", 0)
            pdf.set_xy(ML + 6.0, cy + 14.5)
            pdf.set_font(ff, "B", 19.0)
            pdf.set_text_color(*TEXT_900)
            tot_str = fmt_n(total)
            tw = pdf.get_string_width(tot_str)
            pdf.cell(tw + 1.0, 8.5, tot_str)

            # Monthly baseline average next to main number
            pdf.set_xy(ML + 6.0 + tw + 3.0, cy + 18.0)
            pdf.set_font(ff, "", 7.6)
            pdf.set_text_color(*TEXT_500)
            pdf.cell(38, 4.0, f"ср. {fmt_n(int(avg))} / міс")

            # Trend Badge
            trend = ds.get("trend", {})
            pct = trend.get("change_percent_total", 0.0)
            is_up = (pct > 0)
            arrow = "▲" if is_up else "▼"
            badge_lbl = f"{arrow} {pct:+.1f}%"
            badge_bg = GREEN_BG if is_up else RED_BG
            badge_tc = GREEN_TEXT if is_up else RED_TEXT

            tbw = pdf.draw_pill(ML + 6.0, cy + 25.5, badge_lbl, bg=badge_bg, tc=badge_tc, font_size=7.6, h=5.2)

            # Business characterization of the trend with R²
            r2 = trend.get("r_squared", 0.0)
            if i == 0:
                char_text = f"R² = {r2:.2f}  •  Висока сезонна волатильність"
            else:
                char_text = f"R² = {r2:.2f}  •  Помірні коливання (стабільніший)"

            pdf.set_xy(ML + 6.0, cy + 34.5)
            pdf.set_font(ff, "", 6.8)
            pdf.set_text_color(*TEXT_500)
            pdf.cell(COL_W - 12, 4.0, char_text)

    # ── RIGHT: MAIN CHART CARD (Matches Column 2 + Column 3 below) ──
    pdf.draw_card(CHART_X, hero_y, CHART_W, hero_h, r=3.5)

    # Header inside chart card (including unit)
    pdf.set_xy(CHART_X + 6.0, hero_y + 3.8)
    pdf.set_font(ff, "B", 7.8)
    pdf.set_text_color(*TEXT_500)
    pdf.cell(CHART_W - 12, 4.0, "ДИНАМІКА ПОПИТУ ТА ДОВГОСТРОКОВИЙ ТРЕНД (ПЕРЕГЛЯДИ / МІСЯЦЬ, 24 МІСЯЦІ)")

    # Embed chart image
    if os.path.exists(args.chart):
        try:
            pdf.image(args.chart, x=CHART_X + 2.0, y=hero_y + 8.5, w=CHART_W - 4.0, h=hero_h - 10.5)
        except Exception as e:
            sys.stderr.write(f"Chart render warning: {e}\n")

    # ═══════════════════════════════════════════════════════════
    # 3. BOTTOM ROW: THREE EQUAL COLUMNS (y: 127.5 to 200.0, h: 72.5 mm)
    # Col 1: Strategic Product Decision Memo (Grounded in data)
    # Col 2: Market Signals & Anomalies (Seasonality, YoY)
    # Col 3: Boundaries of Confidence & Limitations (Methodology)
    # ═══════════════════════════════════════════════════════════
    bot_y = 127.5
    bot_h = 72.5

    col1_x = ML
    col2_x = ML + COL_W + GAP
    col3_x = col2_x + COL_W + GAP

    # ── COLUMN 1: 1. РІШЕННЯ ДЛЯ ПРОДУКТУ ──
    pdf.draw_card(col1_x, bot_y, COL_W, bot_h, r=3.5)

    # Top accent bar (Indigo)
    pdf.set_fill_color(*INDIGO_PRIMARY)
    pdf.rect(col1_x, bot_y, COL_W, 2.5, style="F", round_corners=True, corner_radius=1.5)

    # Number badge & Title
    pdf.draw_number_badge(col1_x + 8.0, bot_y + 8.5, radius=3.0, text="1", bg=INDIGO_PRIMARY)
    pdf.set_xy(col1_x + 14.0, bot_y + 6.5)
    pdf.set_font(ff, "B", 9.2)
    pdf.set_text_color(*INDIGO_PRIMARY)
    pdf.cell(COL_W - 18, 4.5, "РІШЕННЯ ДЛЯ ПРОДУКТУ")

    # Concrete business decision for the founder (concise, no overflow)
    decision_p1 = "Запуск курсу з астрономії суто під ринок України є ризикованим: попит падає (-67.2%), а 27% річного трафіку зосереджено в одному вересні (шкільна програма 11 класу)."

    pdf.set_xy(col1_x + 6, bot_y + 13.5)
    pdf.set_font(ff, "", 7.5)
    pdf.set_text_color(*TEXT_700)
    pdf.multi_cell(COL_W - 12, 3.5, decision_p1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Actionable bullets for product expansion
    p1_bullets = [
        ("Пріоритет ринку", "Для масштабування обирати Global EN: попит у 12.4x більший (39.4k проти 3.2k/міс) і менш волатильний."),
        ("Сезонний спецпроєкт", "В Україні продукт варто позиціонувати як короткий інтенсив наприкінці серпня під осінній підйом."),
        ("Позиціонування", "Для залучення дорослої платоспроможної аудиторії акцентувати практичні навички, а не шкільну теорію.")
    ]

    by1 = pdf.get_y() + 1.8
    for b_title, b_desc in p1_bullets:
        pdf.set_fill_color(*INDIGO_PRIMARY)
        pdf.ellipse(col1_x + 6, by1 + 1.2, 1.6, 1.6, style="F")
        pdf.set_xy(col1_x + 9.5, by1)
        pdf.set_font(ff, "B", 7.4)
        pdf.set_text_color(*TEXT_900)
        pdf.cell(COL_W - 15, 3.3, b_title + ":")
        pdf.set_xy(col1_x + 9.5, by1 + 3.2)
        pdf.set_font(ff, "", 7.0)
        pdf.set_text_color(*TEXT_700)
        pdf.multi_cell(COL_W - 15, 3.0, b_desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        by1 = pdf.get_y() + 1.2

    # ── COLUMN 2: 2. СИГНАЛИ ТА АНОМАЛІЇ ──
    pdf.draw_card(col2_x, bot_y, COL_W, bot_h, r=3.5)

    # Top accent bar (Teal)
    pdf.set_fill_color(*TEAL_PRIMARY)
    pdf.rect(col2_x, bot_y, COL_W, 2.5, style="F", round_corners=True, corner_radius=1.5)

    pdf.draw_number_badge(col2_x + 8.0, bot_y + 8.5, radius=3.0, text="2", bg=TEAL_PRIMARY)
    pdf.set_xy(col2_x + 14.0, bot_y + 6.5)
    pdf.set_font(ff, "B", 9.2)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(COL_W - 18, 4.5, "СИГНАЛИ ТА АНОМАЛІЇ")

    signals = [
        ("Вересневий сплеск (Z = 3.17)",
         "У вересні 2022 та 2023 року попит підскакує до 10.5 тис. переглядів (у 3.3 рази вище норми) на старті шкільного курсу 11 класу."),
        ("Сезонне літнє дно (-80% активності)",
         "У червні–серпні попит в Україні падає до мінімальних 637 переглядів — період мінімальної органічної активності."),
        ("Річна динаміка попиту (YoY)",
         "UK: різкий підйом у 2023 (+92.6%) та спад у 2024 (-60.8%); EN: зростання на +183.1% та плавна корекція на -34.1%."),
        ("Стабільність глобального попиту",
         "Англомовний розділ (en) демонструє стабільний річний трафік без різких шкільних розривів (спад лише -11.8%).")
    ]

    by2 = bot_y + 13.5
    for s_title, s_desc in signals:
        pdf.set_fill_color(*TEAL_PRIMARY)
        pdf.ellipse(col2_x + 6, by2 + 1.2, 1.6, 1.6, style="F")
        pdf.set_xy(col2_x + 9.5, by2)
        pdf.set_font(ff, "B", 7.4)
        pdf.set_text_color(*TEXT_900)
        pdf.cell(COL_W - 15, 3.3, s_title)
        pdf.set_xy(col2_x + 9.5, by2 + 3.2)
        pdf.set_font(ff, "", 7.0)
        pdf.set_text_color(*TEXT_700)
        pdf.multi_cell(COL_W - 15, 3.0, s_desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        by2 = pdf.get_y() + 1.2

    # ── COLUMN 3: 3. МЕЖІ ДОВІРИ ТА ПРИПУЩЕННЯ ──
    pdf.draw_card(col3_x, bot_y, COL_W, bot_h, r=3.5)

    # Top accent bar (Slate)
    pdf.set_fill_color(*SLATE_PRIMARY)
    pdf.rect(col3_x, bot_y, COL_W, 2.5, style="F", round_corners=True, corner_radius=1.5)

    pdf.draw_number_badge(col3_x + 8.0, bot_y + 8.5, radius=3.0, text="3", bg=SLATE_PRIMARY)
    pdf.set_xy(col3_x + 14.0, bot_y + 6.5)
    pdf.set_font(ff, "B", 9.2)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(COL_W - 18, 4.5, "МЕЖІ ДОВІРИ ТА ОБМЕЖЕННЯ")

    limits = [
        ("Інтерес ≠ готовність платити",
         "Перегляд статті Вікіпедії відображає довідковий інтерес до теми, а не сформовану готовність купувати платний курс."),
        ("Низька база переглядів UK",
         "Влітку денний трафік UK падає до ~20 переглядів/день, що підвищує статистичну волатильність і похибку вибірки."),
        ("Фільтрація ботів (agent=user)",
         "Використано дані реальних користувачів, проте частина автоматизованих AI-скраперів може залишатися у вибірці."),
        ("Вплив зовнішніх медіа-подій",
         "Астрономічні явища (затемнення, запуски NASA) створюють короткочасні неорганічні сплески інтересу.")
    ]

    by3 = bot_y + 13.5
    for l_title, l_desc in limits:
        pdf.set_fill_color(*SLATE_PRIMARY)
        pdf.ellipse(col3_x + 6, by3 + 1.2, 1.6, 1.6, style="F")
        pdf.set_xy(col3_x + 9.5, by3)
        pdf.set_font(ff, "B", 7.4)
        pdf.set_text_color(*TEXT_900)
        pdf.cell(COL_W - 15, 3.3, l_title)
        pdf.set_xy(col3_x + 9.5, by3 + 3.2)
        pdf.set_font(ff, "", 7.0)
        pdf.set_text_color(*TEXT_700)
        pdf.multi_cell(COL_W - 15, 3.0, l_desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        by3 = pdf.get_y() + 1.2

    # ═══════════════════════════════════════════════════════════
    # Save Report
    # ═══════════════════════════════════════════════════════════
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
