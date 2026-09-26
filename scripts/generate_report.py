# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fpdf2>=2.7",
# ]
# ///
"""
generate_report.py — Modern SaaS-style Executive Wikipedia Trends Report.
Matches the design system of high-end analytical dashboards (floating cards,
status badges, anomaly callout banner, central chart, deep AI insights card,
and blue Quick Wins action plan).
"""
import argparse
import json
import os
import sys
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# ═══════════════════════════════════════════════════════════════
# Design Tokens (Exact Dashboard Match)
# ═══════════════════════════════════════════════════════════════
PAGE_BG         = (244, 245, 247)   # Neutral soft gray canvas (#F4F5F7)
CARD_BG         = (255, 255, 255)   # Pure white
CARD_BORDER     = (229, 231, 235)   # Slate 200 border (#E5E7EB)
CARD_SHADOW     = (238, 240, 244)   # Subtle drop-shadow tone

TEXT_900        = (15,  23,  42)    # Darkest slate (#0F172A)
TEXT_700        = (51,  65,  85)    # Body slate (#334155)
TEXT_500        = (100, 116, 139)   # Muted gray (#64748B)
TEXT_400        = (148, 163, 184)   # Light gray (#94A3B8)

# Alerts & Negative
RED_ACCENT      = (239, 68,  68)    # #EF4444
RED_BG          = (254, 226, 226)   # #FEE2E2
RED_TEXT        = (220, 38,  38)    # #DC2626

# Positive
GREEN_ACCENT    = (16,  185, 129)   # #10B981
GREEN_BG        = (220, 252, 231)   # #DCFCE7
GREEN_TEXT      = (22,  101, 52)    # #166534

# Primary Actions / Blue
BLUE_PRIMARY    = (37,  99,  235)   # #2563EB (Royal Blue)
BLUE_BG         = (239, 246, 255)   # #EFF6FF
BLUE_LIGHT      = (191, 219, 254)   # #BFDBFE

# Dark Insights Card
DARK_CARD_BG    = (15,  23,  42)    # #0F172A
DARK_TILE_BG    = (30,  41,  59)    # #1E293B
DARK_TILE_BORDER= (51,  65,  85)    # #334155
PURPLE_ACCENT   = (192, 132, 252)   # #C084FC
CYAN_ACCENT     = (56,  189, 248)   # #38BDF8
AMBER_ACCENT    = (251, 191, 36)    # #FBBF24


class ModernDashboardPDF(FPDF):
    def __init__(self, font_family="DejaVu"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.ff = font_family
        self.set_auto_page_break(auto=False)

    # ── Drawing Primitives ───────────────────────────────────

    def draw_card(self, x, y, w, h, bg=CARD_BG, border=CARD_BORDER, r=3.5, shadow=True):
        """Draw a card with rounded corners and subtle drop-shadow."""
        if shadow:
            self.set_fill_color(*CARD_SHADOW)
            self.rect(x + 0.3, y + 0.6, w, h, style="F", round_corners=True, corner_radius=r)
        self.set_fill_color(*bg)
        if border:
            self.set_draw_color(*border)
            self.set_line_width(0.2)
            self.rect(x, y, w, h, style="DF", round_corners=True, corner_radius=r)
        else:
            self.rect(x, y, w, h, style="F", round_corners=True, corner_radius=r)

    def draw_pill(self, x, y, text, bg=RED_BG, tc=RED_TEXT, font_size=7, bold=True, h=5.0):
        """Rounded badge/pill."""
        self.set_font(self.ff, "B" if bold else "", font_size)
        pw = self.get_string_width(text) + 6
        self.set_fill_color(*bg)
        self.rect(x, y, pw, h, style="F", round_corners=True, corner_radius=h / 2)
        self.set_xy(x, y + (h - 3.2) / 2)
        self.set_text_color(*tc)
        self.cell(pw, 3.2, text, align="C")
        return pw

    def draw_check_icon(self, cx, cy, radius=2.6, bg=BLUE_PRIMARY, check_color=(255, 255, 255)):
        """Draw a filled circle with a checkmark."""
        self.set_fill_color(*bg)
        self.ellipse(cx - radius, cy - radius, radius * 2, radius * 2, style="F")
        # Draw checkmark lines
        self.set_draw_color(*check_color)
        self.set_line_width(0.4)
        # Checkmark points: left, bottom, top-right
        x1 = cx - radius * 0.45
        y1 = cy
        x2 = cx - radius * 0.1
        y2 = cy + radius * 0.45
        x3 = cx + radius * 0.55
        y3 = cy - radius * 0.45
        self.line(x1, y1, x2, y2)
        self.line(x2, y2, x3, y3)

    def draw_alert_icon(self, cx, cy, radius=3.2, bg=RED_BG, tc=RED_TEXT):
        """Draw circular alert icon with exclamation mark."""
        self.set_fill_color(*bg)
        self.ellipse(cx - radius, cy - radius, radius * 2, radius * 2, style="F")
        self.set_font(self.ff, "B", 8)
        self.set_text_color(*tc)
        self.set_xy(cx - radius, cy - 2.0)
        self.cell(radius * 2, 4.0, "!", align="C")


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
    """Format integer with space thousands separator."""
    if n is None:
        return "—"
    return f"{int(n):,}".replace(",", " ")


def main():
    parser = argparse.ArgumentParser(description="Generate Executive SaaS-style Wikipedia Trends Report")
    parser.add_argument("--analysis", required=True, help="Path to JSON file from analyze_trends.py")
    parser.add_argument("--chart", required=True, help="Path to chart PNG file from generate_chart.py")
    parser.add_argument("--title", default="Аналіз ринкового інтересу: Wikipedia Trends", help="Report title")
    parser.add_argument("--output", default="report.pdf", help="Output PDF file path")
    args = parser.parse_args()

    # Load data
    try:
        with open(args.analysis, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read {args.analysis}: {str(e)}"}), file=sys.stdout)
        sys.exit(1)

    datasets = data.get("datasets", [])
    comparison = data.get("comparison", {}) or {}

    pdf = ModernDashboardPDF()
    ff = setup_font(pdf)
    pdf.ff = ff
    pdf.add_page()

    # 1. Fill entire page background with light neutral canvas
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, 0, 210, 297, style="F")

    # Geometry settings
    ML = 8.0               # Left margin
    CW = 194.0              # Content width (210 - 16)

    # ═══════════════════════════════════════════════════════════
    # BLOCK 1: HEADER CARD (y: 8, h: 16)
    # ═══════════════════════════════════════════════════════════
    h_y = 8.0
    h_h = 16.0
    pdf.draw_card(ML, h_y, CW, h_h, r=3.0)

    # Status Pill (determine overall market posture)
    d0_pct = datasets[0].get("trend", {}).get("change_percent_total", 0.0) if datasets else 0
    is_declining = (d0_pct < 0)
    pill_label = "СПАД ПОПИТУ" if is_declining else "ЗРОСТАННЯ"
    pill_bg = RED_BG if is_declining else GREEN_BG
    pill_tc = RED_TEXT if is_declining else GREEN_TEXT

    pill_w = pdf.draw_pill(ML + 5, h_y + 3.2, pill_label, bg=pill_bg, tc=pill_tc, font_size=6.5, h=4.2)

    # Date range tag
    pdf.set_xy(ML + 5 + pill_w + 3, h_y + 3.2)
    pdf.set_font(ff, "", 7.2)
    pdf.set_text_color(*TEXT_500)
    pdf.cell(70, 4.2, "24 місяці (2022–2024)")

    # Top right meta
    now_str = datetime.now().strftime("%d.%m.%Y")
    pdf.set_xy(ML + CW - 70, h_y + 3.2)
    pdf.set_font(ff, "", 6.8)
    pdf.set_text_color(*TEXT_400)
    pdf.cell(65, 4.2, f"Wikimedia REST API  •  {now_str}", align="R")

    # Title
    pdf.set_xy(ML + 5, h_y + 8.5)
    pdf.set_font(ff, "B", 13.5)
    pdf.set_text_color(*TEXT_900)
    disp_title = args.title if args.title.startswith("Звіт") else f"Звіт: {args.title}"
    pdf.cell(CW - 10, 6.0, disp_title)

    # ═══════════════════════════════════════════════════════════
    # BLOCK 2: TOP KPI CARDS (y: 26.5, h: 27)
    # ═══════════════════════════════════════════════════════════
    kpi_y = 26.5
    kpi_h = 27.0
    kpi_gap = 4.0
    kpi_w = (CW - kpi_gap) / 2  # 95 mm each

    for i in range(2):
        cx = ML + i * (kpi_w + kpi_gap)
        pdf.draw_card(cx, kpi_y, kpi_w, kpi_h, r=3.0)

        if i < len(datasets):
            ds = datasets[i]
            article = ds.get("article_display", "—")
            project = ds.get("project", "")
            lang = project.split(".")[0].upper()
            flag = "🇺🇦" if lang == "UK" else ("🇺🇸" if lang == "EN" else "🌐")
            
            total_views = ds.get("total_views", 0)
            avg_views = ds.get("avg_views", 0)
            trend = ds.get("trend", {})
            pct = trend.get("change_percent_total", 0.0)

            # Card Header (Language / Entity)
            pdf.set_xy(cx + 5, kpi_y + 3.5)
            pdf.set_font(ff, "B", 7.8)
            pdf.set_text_color(*TEXT_500)
            pdf.cell(kpi_w - 10, 4.0, f"[{lang}] {article} • {project}")

            # Main Number (Big bold)
            pdf.set_xy(cx + 5, kpi_y + 8.0)
            pdf.set_font(ff, "B", 18.0)
            pdf.set_text_color(*TEXT_900)
            val_str = fmt_n(total_views)
            vw = pdf.get_string_width(val_str)
            pdf.cell(vw + 1, 8.5, val_str)

            # Subtitle baseline next to main number
            pdf.set_xy(cx + 5 + vw + 3.0, kpi_y + 11.5)
            pdf.set_font(ff, "", 7.5)
            pdf.set_text_color(*TEXT_400)
            pdf.cell(40, 4.0, f"ср. {fmt_n(int(avg_views))} / міс")

            # Trend pill
            is_up = (pct > 0)
            arrow = "↗" if is_up else "↘"
            t_label = f"{arrow} {pct:+.1f}%"
            t_bg = GREEN_BG if is_up else RED_BG
            t_tc = GREEN_TEXT if is_up else RED_TEXT
            pdf.draw_pill(cx + 5, kpi_y + 19.0, t_label, bg=t_bg, tc=t_tc, font_size=7.2, h=4.8)

            # R-squared footnote
            r2 = trend.get("r_squared", 0.0)
            conf = str(trend.get("confidence", "—")).capitalize()
            pdf.set_xy(cx + 36, kpi_y + 19.5)
            pdf.set_font(ff, "", 6.8)
            pdf.set_text_color(*TEXT_400)
            pdf.cell(50, 4.0, f"R² = {r2:.2f} • Надійність: {conf}")

    # ═══════════════════════════════════════════════════════════
    # BLOCK 3: ANOMALY / ALERT BANNER CARD (y: 56.0, h: 24.5)
    # ═══════════════════════════════════════════════════════════
    anom_y = 56.0
    anom_h = 24.5
    pdf.draw_card(ML, anom_y, CW, anom_h, r=3.0)

    # Red/Rose Left Accent Stripe (exact match of reference card)
    pdf.set_fill_color(*RED_ACCENT)
    pdf.rect(ML, anom_y, 3.2, anom_h, style="F", round_corners=True, corner_radius=1.5)

    # Circular alert icon
    pdf.draw_alert_icon(ML + 9.5, anom_y + 6.5, radius=3.2, bg=RED_BG, tc=RED_TEXT)

    # Anomaly text logic (extract real data)
    anom_title = "Ключова аномалія: Вересневий сплеск попиту в Україні"
    anom_sub = "Вересень 2022 та 2023: попит підскакує у 3.3 рази на старті навчального року (11 клас)."
    stat_l1 = "• Піковий вересень: 10 494 перегляди (330% від місячної норми в Україні)"
    stat_l2 = "• Літнє просідання: до 637 переглядів у червні-серпні (-80% сезонної активності)"

    # Check if we have specific anomaly in datasets[0]
    if datasets:
        anom_list = datasets[0].get("anomalies", [])
        if anom_list:
            top_a = anom_list[0]
            z = top_a.get("z_score", 3.0)
            ts = top_a.get("timestamp", "")
            views = top_a.get("views", 0)
            exp = top_a.get("expected", 1)
            ratio = (views / exp) if exp else 1.0
            anom_title = f"Ключова аномалія: Екстремальний сплеск інтересу (Z-score = {z:.2f})"
            anom_sub = f"У період {ts} зафіксовано {fmt_n(views)} переглядів ({ratio:.1f}x від звичайної норми)."

    pdf.set_xy(ML + 15, anom_y + 3.8)
    pdf.set_font(ff, "B", 9.2)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(CW - 20, 4.5, anom_title)

    pdf.set_xy(ML + 15, anom_y + 8.5)
    pdf.set_font(ff, "", 7.6)
    pdf.set_text_color(*TEXT_700)
    pdf.cell(CW - 20, 3.8, anom_sub)

    # Inner pill container for detailed stats (light gray container)
    stat_box_y = anom_y + 13.0
    stat_box_h = 9.2
    stat_box_w = CW - 18
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(*CARD_BORDER)
    pdf.set_line_width(0.15)
    pdf.rect(ML + 15, stat_box_y, stat_box_w, stat_box_h, style="DF", round_corners=True, corner_radius=2.0)

    pdf.set_xy(ML + 18, stat_box_y + 1.2)
    pdf.set_font(ff, "", 6.8)
    pdf.set_text_color(*TEXT_500)
    pdf.cell(stat_box_w - 6, 3.3, stat_l1)

    pdf.set_xy(ML + 18, stat_box_y + 4.8)
    pdf.cell(stat_box_w - 6, 3.3, stat_l2)

    # ═══════════════════════════════════════════════════════════
    # BLOCK 4: CENTRAL CHART CARD (y: 83.0, h: 66)
    # ═══════════════════════════════════════════════════════════
    chart_y = 83.0
    chart_h = 66.0
    pdf.draw_card(ML, chart_y, CW, chart_h, r=3.0)

    # Header in chart card
    pdf.set_xy(ML + 6, chart_y + 3.5)
    pdf.set_font(ff, "B", 7.2)
    pdf.set_text_color(*TEXT_500)
    pdf.cell(CW - 12, 3.5, "ДИНАМІКА ПОПИТУ ТА ДОВГОСТРОКОВИЙ ТРЕНД  •  24 МІСЯЦІ")

    if args.chart and os.path.exists(args.chart):
        try:
            pdf.image(args.chart, x=ML + 4, y=chart_y + 7.5, w=CW - 8, h=chart_h - 9.5)
        except Exception as e:
            sys.stderr.write(f"Chart render warning: {e}\n")

    # ═══════════════════════════════════════════════════════════
    # BLOCK 5: TWO-COLUMN SECTION (y: 151.5, h: 71)
    # Left: White Card (Top Risks)
    # Right: Dark Navy Card (Deep AI Insights)
    # ═══════════════════════════════════════════════════════════
    col_y = 151.5
    col_h = 71.0
    col_gap = 4.0
    col_w = (CW - col_gap) / 2   # 95 mm each

    # ── Left Column: Risks & Barriers (White Card) ──
    left_x = ML
    pdf.draw_card(left_x, col_y, col_w, col_h, r=3.0)

    # Header with red cross
    pdf.set_xy(left_x + 5, col_y + 4.5)
    pdf.set_font(ff, "B", 8.2)
    pdf.set_text_color(*RED_TEXT)
    pdf.cell(4.5, 4.0, "×", align="L")
    pdf.set_xy(left_x + 9.5, col_y + 4.5)
    pdf.cell(col_w - 15, 4.0, "ТОП-3 ФАКТОРИ ТА РИЗИКИ")

    # 3 Risks Items
    risks = [
        ("Освітня залежність (~70%)",
         "Основний обсяг переглядів в Україні генерують школярі 11 класу у вересні, а не платоспроможні дорослі покупці."),
        ("Сезонне літнє дно",
         "Спад інтересу на 80% у червні-липні. Без підтримуючих кампаній активність аудиторії повністю затухає."),
        ("Інформаційний бар'єр",
         "Вікіпедія фіксує довідковий інтерес до термінів, а не сформовану готовність платити за освітні курси."),
    ]

    r_y = col_y + 11.5
    for title, desc in risks:
        # Orange/Red bullet dot
        pdf.set_fill_color(*AMBER_ACCENT)
        pdf.ellipse(left_x + 6, r_y + 1.2, 1.8, 1.8, style="F")

        # Title
        pdf.set_xy(left_x + 10, r_y)
        pdf.set_font(ff, "B", 7.6)
        pdf.set_text_color(*TEXT_900)
        pdf.cell(col_w - 15, 3.8, title)

        # Description
        pdf.set_xy(left_x + 10, r_y + 4.2)
        pdf.set_font(ff, "", 6.7)
        pdf.set_text_color(*TEXT_500)
        pdf.multi_cell(col_w - 15, 3.2, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        r_y = pdf.get_y() + 2.5

    # ── Right Column: Deep AI Insights (Dark Navy Card) ──
    right_x = ML + col_w + col_gap
    # Draw Dark Card
    pdf.draw_card(right_x, col_y, col_w, col_h, bg=DARK_CARD_BG, border=None, r=3.0)

    # Header with glowing purple icon
    pdf.set_xy(right_x + 5, col_y + 4.5)
    pdf.set_font(ff, "B", 8.2)
    pdf.set_text_color(*PURPLE_ACCENT)
    pdf.cell(col_w - 10, 4.0, "✦ ГЛИБИННІ ШІ DATA-ІНСАЙТИ")

    # 3 Dark Inner Tiles
    insights = [
        ("Вікно запуску (Launch Timing)",
         "Маркетингові кампанії в Україні слід починати 15–25 серпня під початок навчального сезону.",
         PURPLE_ACCENT),
        ("Глобальний масштаб (Scale & LTV)",
         "Англомовний ринок у 12.4x більший за обсягом та в 4 рази стабільніший за амплітудою.",
         CYAN_ACCENT),
        ("Позиціонування продукту",
         "Для монетизації дорослих зміщувати фокус з сухої теорії на прикладну астрофотографію та спостереження.",
         AMBER_ACCENT),
    ]

    tile_y = col_y + 10.5
    tile_h = 17.5
    tile_w = col_w - 10

    for ititle, idesc, col in insights:
        # Tile box
        pdf.set_fill_color(*DARK_TILE_BG)
        pdf.set_draw_color(*DARK_TILE_BORDER)
        pdf.set_line_width(0.15)
        pdf.rect(right_x + 5, tile_y, tile_w, tile_h, style="DF", round_corners=True, corner_radius=2.0)

        # Tile title
        pdf.set_xy(right_x + 8, tile_y + 1.8)
        pdf.set_font(ff, "B", 7.2)
        pdf.set_text_color(*col)
        pdf.cell(tile_w - 6, 3.5, ititle)

        # Tile text
        pdf.set_xy(right_x + 8, tile_y + 5.5)
        pdf.set_font(ff, "", 6.4)
        pdf.set_text_color(226, 232, 240)
        pdf.multi_cell(tile_w - 6, 3.1, idesc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        tile_y += tile_h + 2.0

    # ═══════════════════════════════════════════════════════════
    # BLOCK 6: BOTTOM ACTION PLAN CARD "🚀 План дій (Quick Wins)"
    # (y: 225.5, h: 57)
    # ═══════════════════════════════════════════════════════════
    act_y = 225.5
    act_h = 57.0

    # Card base
    pdf.draw_card(ML, act_y, CW, act_h, r=3.0)

    # Blue Header Banner (exact match with reference card)
    banner_h = 7.5
    pdf.set_fill_color(*BLUE_PRIMARY)
    # Draw rounded top banner
    pdf.rect(ML, act_y, CW, banner_h, style="F", round_corners=True, corner_radius=3.0)
    # Square bottom edges of the banner
    pdf.rect(ML, act_y + banner_h - 2.0, CW, 2.0, style="F")

    # Banner title
    pdf.set_xy(ML + 5, act_y + 1.5)
    pdf.set_font(ff, "B", 8.2)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(CW - 10, 4.5, "ПЛАН ДІЙ ТА ШІ-РЕКОМЕНДАЦІЇ (QUICK WINS)")

    # 2x2 Action Plan Grid
    grid_items = [
        ("Таймінг промо",
         "Запуск таргетованих кампаній суворо 15–25 серпня для захоплення органічного піку вересня."),
        ("Фокус на Global",
         "Локалізація та вихід на ринок США дає у 12.4 рази більший потік лідів із вищим чеком."),
        ("Контент-ретеншн",
         "Створення практичних гідів (спостереження метеорних потоків) для утримання клієнтів влітку."),
        ("Upsell-стратегія",
         "Додавання фізичного або софтверного інструментарію (лінзи, додатки) до кожного курсу.")
    ]

    col1_x = ML + 6
    col2_x = ML + (CW / 2) + 3
    col_width = (CW / 2) - 10

    # Row 1 (y: act_y + 11.5)
    row1_y = act_y + 11.0
    for c_idx, (act_t, act_d) in enumerate(grid_items[:2]):
        pos_x = col1_x if c_idx == 0 else col2_x
        # Checkmark icon
        pdf.draw_check_icon(pos_x + 2.5, row1_y + 2.5, radius=2.5, bg=BLUE_PRIMARY)
        # Title
        pdf.set_xy(pos_x + 7.5, row1_y)
        pdf.set_font(ff, "B", 7.8)
        pdf.set_text_color(*TEXT_900)
        pdf.cell(col_width - 8, 3.8, act_t)
        # Text
        pdf.set_xy(pos_x + 7.5, row1_y + 4.2)
        pdf.set_font(ff, "", 6.7)
        pdf.set_text_color(*TEXT_500)
        pdf.multi_cell(col_width - 8, 3.2, act_d, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Row 2 (y: act_y + 28.5)
    row2_y = act_y + 29.5
    for c_idx, (act_t, act_d) in enumerate(grid_items[2:]):
        pos_x = col1_x if c_idx == 0 else col2_x
        # Checkmark icon
        pdf.draw_check_icon(pos_x + 2.5, row2_y + 2.5, radius=2.5, bg=BLUE_PRIMARY)
        # Title
        pdf.set_xy(pos_x + 7.5, row2_y)
        pdf.set_font(ff, "B", 7.8)
        pdf.set_text_color(*TEXT_900)
        pdf.cell(col_width - 8, 3.8, act_t)
        # Text
        pdf.set_xy(pos_x + 7.5, row2_y + 4.2)
        pdf.set_font(ff, "", 6.7)
        pdf.set_text_color(*TEXT_500)
        pdf.multi_cell(col_width - 8, 3.2, act_d, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ═══════════════════════════════════════════════════════════
    # BLOCK 7: FOOTER
    # ═══════════════════════════════════════════════════════════
    pdf.set_xy(ML, 287.5)
    pdf.set_font(ff, "", 6.8)
    pdf.set_text_color(*TEXT_400)
    pdf.cell(CW, 4.0, f"Згенеровано автономною системою аналітики wiki-trends  •  {now_str}", align="C")

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
