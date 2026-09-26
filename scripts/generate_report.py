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

# ═══════════════════════════════════════════════════════════════
# Premium Design Tokens
# ═══════════════════════════════════════════════════════════════
# Background
BG = (248, 250, 252)       # #F8FAFC — near-white page background
CARD_BG = (255, 255, 255)  # White cards
CARD_BORDER = (226, 232, 240)  # #E2E8F0 — Slate 200

# Accent — Indigo gradient endpoints
ACCENT_PRIMARY = (79, 70, 229)   # #4F46E5 — Indigo 600
ACCENT_LIGHT = (129, 140, 248)   # #818CF8 — Indigo 400
ACCENT_BG = (238, 242, 255)      # #EEF2FF — Indigo 50

# Text hierarchy
TEXT_900 = (15, 23, 42)    # #0F172A — Slate 900
TEXT_700 = (51, 65, 85)    # #334155 — Slate 700
TEXT_500 = (100, 116, 139) # #64748B — Slate 500
TEXT_400 = (148, 163, 184) # #94A3B8 — Slate 400

# Semantic colors
GREEN_BG = (220, 252, 231)   # Green 100
GREEN_TEXT = (22, 101, 52)    # Green 800
RED_BG = (255, 228, 230)     # Rose 100
RED_TEXT = (159, 18, 57)      # Rose 800

# Tableau-inspired dataset accents
DS_COLORS = [
    (78, 121, 167),  # #4E79A7 Steel Blue
    (225, 87, 89),   # #E15759 Salmon Red
    (118, 183, 178), # #76B7B2 Teal
    (242, 142, 43),  # #F28E2B Orange
]


class PremiumReportPDF(FPDF):
    """One-page landscape A4 PDF in premium pitch-deck style."""

    def __init__(self, title: str, font_family: str = "DejaVu"):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.report_title = title
        self.ff = font_family
        self.set_auto_page_break(auto=False)

    # ── Reusable primitives ──────────────────────────────────

    def draw_rounded_card(self, x, y, w, h, bg=CARD_BG, border=CARD_BORDER, r=4):
        """White card with subtle border and rounded corners."""
        self.set_fill_color(*bg)
        self.set_draw_color(*border)
        self.rect(x=x, y=y, w=w, h=h, style="DF", round_corners=True, corner_radius=r)

    def draw_pill(self, x, y, text, bg=ACCENT_BG, tc=ACCENT_PRIMARY, font_size=7):
        """Rounded pill/tag badge."""
        self.set_font(self.ff, "B", font_size)
        tw = self.get_string_width(text) + 6
        h = 5.5
        self.set_fill_color(*bg)
        self.set_draw_color(*bg)
        self.rect(x=x, y=y, w=tw, h=h, style="DF", round_corners=True, corner_radius=2.5)
        self.set_xy(x, y + (h - 3.2) / 2)
        self.set_text_color(*tc)
        self.cell(tw, 3.2, text, align="C")
        return tw

    def draw_circle_badge(self, cx, cy, radius, text, bg=ACCENT_PRIMARY, tc=(255, 255, 255)):
        """Blue circular number badge."""
        self.set_fill_color(*bg)
        self.ellipse(x=cx - radius, y=cy - radius, w=radius * 2, h=radius * 2, style="F")
        self.set_font(self.ff, "B", 8)
        self.set_text_color(*tc)
        self.set_xy(cx - radius, cy - 2)
        self.cell(radius * 2, 4, str(text), align="C")

    def draw_kpi(self, x, y, label, value, sub="", color=ACCENT_PRIMARY):
        """Single KPI metric block."""
        # Label
        self.set_xy(x, y)
        self.set_font(self.ff, "", 7.5)
        self.set_text_color(*TEXT_400)
        self.cell(40, 3.5, _safe(label))
        # Value
        self.set_xy(x, y + 4)
        self.set_font(self.ff, "B", 15)
        self.set_text_color(*color)
        self.cell(40, 7, _safe(value))
        # Subtitle
        if sub:
            self.set_xy(x, y + 12)
            self.set_font(self.ff, "", 7)
            self.set_text_color(*TEXT_500)
            self.cell(40, 3, _safe(sub))

    def draw_trend_arrow(self, x, y, pct, w=30, h=5.5):
        """Trend change badge with arrow."""
        is_up = pct > 0
        bg = GREEN_BG if is_up else RED_BG
        tc = GREEN_TEXT if is_up else RED_TEXT
        arrow = "\u25B2" if is_up else "\u25BC"
        text = f"{arrow} {pct:+.1f}%"
        self.set_fill_color(*bg)
        self.set_draw_color(*bg)
        self.rect(x=x, y=y, w=w, h=h, style="DF", round_corners=True, corner_radius=2.5)
        self.set_xy(x, y + (h - 3.2) / 2)
        self.set_text_color(*tc)
        self.set_font(self.ff, "B", 8)
        self.cell(w, 3.2, text, align="C")

    def footer(self):
        self.set_y(202)
        self.set_font(self.ff, "", 7)
        self.set_text_color(*TEXT_400)
        self.cell(0, 4, "wiki-trends  \u2022  Agent Skills  \u2022  \u0410\u0432\u0442\u043e\u043d\u043e\u043c\u043d\u0438\u0439 AI-\u0430\u043d\u0430\u043b\u0456\u0442\u0438\u043a \u0440\u0438\u043d\u043a\u043e\u0432\u043e\u0433\u043e \u043f\u043e\u043f\u0438\u0442\u0443", align="C")


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _safe(val) -> str:
    return str(val) if val is not None else ""


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
            sys.stderr.write(f"Warning: DejaVu font load failed: {e}\n")

    return "helvetica"


def format_number(n) -> str:
    """Format number with space thousands separator (Ukrainian convention)."""
    if n is None:
        return "—"
    if isinstance(n, float):
        return f"{n:,.0f}".replace(",", " ")
    return f"{int(n):,}".replace(",", " ")


# ═══════════════════════════════════════════════════════════════
# Main layout builder
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate premium Wikipedia Trends PDF report")
    parser.add_argument("--analysis", required=True, help="JSON file from analyze_trends.py")
    parser.add_argument("--chart", required=True, help="Chart PNG from generate_chart.py")
    parser.add_argument("--title", default="Аналіз ринкового інтересу: Wikipedia Trends", help="Report title")
    parser.add_argument("--output", default="report.pdf", help="Output PDF path")

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

    pdf = PremiumReportPDF(title=args.title)
    ff = setup_font(pdf)
    pdf.ff = ff
    pdf.add_page()

    # Page background
    pdf.set_fill_color(*BG)
    pdf.rect(0, 0, 297, 210, style="F")

    # ┌─────────────────────────────────────────────────────────┐
    # │  HEADER: Gradient accent bar + title + metadata         │
    # └─────────────────────────────────────────────────────────┘
    # Top accent gradient bar (thin indigo line)
    pdf.set_fill_color(*ACCENT_PRIMARY)
    pdf.rect(0, 0, 297, 2.5, style="F")

    # Overtitle pill
    pdf.draw_pill(12, 7, "WIKIPEDIA MARKET INTELLIGENCE")

    # Title
    pdf.set_xy(12, 14)
    pdf.set_font(ff, "B", 15)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(200, 7, _safe(args.title), align="L")

    # Right-side metadata
    now_str = datetime.now().strftime("%d.%m.%Y  •  %H:%M")
    pdf.set_font(ff, "", 8)
    pdf.set_text_color(*TEXT_500)
    pdf.set_xy(210, 8)
    pdf.cell(75, 4, f"Дата: {now_str}", align="R")
    pdf.set_xy(210, 13)
    pdf.cell(75, 4, "Вибірка: 24 місяці  •  agent=user", align="R")

    # Thin separator
    pdf.set_draw_color(*CARD_BORDER)
    pdf.set_line_width(0.3)
    pdf.line(12, 23, 285, 23)

    # ┌─────────────────────────────────────────────────────────┐
    # │  ROW 1: KPI cards (left) + Chart (right)                │
    # └─────────────────────────────────────────────────────────┘
    row1_y = 26
    kpi_section_w = 82
    chart_section_w = 195
    row1_h = 90

    # ── KPI Cards ──
    num_ds = len(datasets)
    if num_ds == 0:
        num_ds = 1
    
    kpi_card_gap = 4
    kpi_card_h = (row1_h - kpi_card_gap * (num_ds - 1)) / num_ds if num_ds > 0 else row1_h

    for i, ds in enumerate(datasets[:3]):
        cy = row1_y + i * (kpi_card_h + kpi_card_gap)
        
        # Card
        pdf.draw_rounded_card(12, cy, kpi_section_w, kpi_card_h)

        # Color accent bar on left edge of card
        ds_color = DS_COLORS[i % len(DS_COLORS)]
        pdf.set_fill_color(*ds_color)
        pdf.rect(12, cy, 2.5, kpi_card_h, style="F", round_corners=True, corner_radius=1.2)

        # Article name
        article = ds.get("article_display", "—")
        project = ds.get("project", "")
        lang = project.split(".")[0] if project else ""

        pdf.set_xy(18, cy + 4)
        pdf.set_font(ff, "B", 10)
        pdf.set_text_color(*TEXT_900)
        pdf.cell(kpi_section_w - 10, 5, _safe(article))

        # Language pill
        if lang:
            pdf.draw_pill(18, cy + 10.5, lang.upper(), font_size=6)

        # Metrics row
        total = ds.get("total_views", 0)
        avg = ds.get("avg_views", 0)
        trend = ds.get("trend", {})
        pct = trend.get("change_percent_total", 0.0)

        # Total views KPI
        pdf.draw_kpi(18, cy + 18, "Загальні перегляди", format_number(total))

        # Average KPI
        pdf.draw_kpi(50, cy + 18, "В середньому/міс", format_number(avg), color=TEXT_700)

        # Trend badge
        pdf.draw_trend_arrow(18, cy + kpi_card_h - 10, pct, w=32)

        # Confidence text
        raw_conf = str(trend.get("confidence", "—")).capitalize()
        pdf.set_xy(52, cy + kpi_card_h - 9)
        pdf.set_font(ff, "", 7)
        pdf.set_text_color(*TEXT_400)
        pdf.cell(35, 4, f"Надійність: {raw_conf}")

    # ── Chart card ──
    chart_x = 12 + kpi_section_w + 4
    pdf.draw_rounded_card(chart_x, row1_y, chart_section_w, row1_h)

    if os.path.exists(args.chart):
        try:
            pdf.image(args.chart, x=chart_x + 2, y=row1_y + 2, w=chart_section_w - 4, h=row1_h - 4)
        except Exception as e:
            sys.stderr.write(f"Warning: chart image load failed: {e}\n")

    # ┌─────────────────────────────────────────────────────────┐
    # │  ROW 2: Three analysis cards                            │
    # └─────────────────────────────────────────────────────────┘
    row2_y = row1_y + row1_h + 4
    card_w = 89
    card_h = 73
    card_gap = 3.5

    # ── CARD 1: Стратегічний висновок ──
    c1_x = 12
    pdf.draw_rounded_card(c1_x, row2_y, card_w, card_h, bg=ACCENT_BG, border=(199, 210, 254))

    # Number badge
    pdf.draw_circle_badge(c1_x + 7, row2_y + 7, 3.5, "1")

    # Title
    pdf.set_xy(c1_x + 14, row2_y + 4.5)
    pdf.set_font(ff, "B", 9.5)
    pdf.set_text_color(*ACCENT_PRIMARY)
    pdf.cell(card_w - 18, 5, "СТРАТЕГІЧНИЙ ВИСНОВОК")

    # Recommendation text
    rec_text = ""
    if isinstance(comparison, dict):
        rec_text = comparison.get("recommendation", "")
    if not rec_text and datasets:
        d0 = datasets[0]
        t = d0.get("trend", {})
        dir_uk = "зростання" if t.get("direction") == "growing" else "спад"
        rec_text = f"Тема \u00ab{d0.get('article_display')}\u00bb демонструє {dir_uk} інтересу на {t.get('change_percent_total', 0):+.1f}%."

    pdf.set_xy(c1_x + 6, row2_y + 13)
    pdf.set_font(ff, "", 8)
    pdf.set_text_color(*TEXT_700)
    pdf.multi_cell(card_w - 12, 4.2, _safe(rec_text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Growth leader / Largest audience
    if isinstance(comparison, dict) and comparison.get("fastest_growing"):
        fg = comparison.get("fastest_growing", {})
        la = comparison.get("largest_audience", {})
        info_y = row2_y + card_h - 18
        
        pdf.set_xy(c1_x + 6, info_y)
        pdf.set_font(ff, "B", 7.5)
        pdf.set_text_color(*ACCENT_PRIMARY)
        pdf.cell(card_w - 12, 4, f"Лідер росту: {fg.get('project', '—')}")
        
        pdf.set_xy(c1_x + 6, info_y + 5)
        pdf.cell(card_w - 12, 4, f"Найбільша аудиторія: {la.get('project', '—')}")

    # ── CARD 2: Сигнали попиту та сезонність ──
    c2_x = c1_x + card_w + card_gap
    pdf.draw_rounded_card(c2_x, row2_y, card_w, card_h)

    pdf.draw_circle_badge(c2_x + 7, row2_y + 7, 3.5, "2")

    pdf.set_xy(c2_x + 14, row2_y + 4.5)
    pdf.set_font(ff, "B", 9.5)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(card_w - 18, 5, "СИГНАЛИ ТА СЕЗОННІСТЬ")

    signals = []
    for ds in datasets:
        art = ds.get("article_display", "")
        season = ds.get("seasonality", {})
        if isinstance(season, dict) and season.get("detected"):
            peaks = season.get("peak_months", [])
            troughs = season.get("trough_months", [])
            if peaks:
                peak_str = ", ".join(str(m) for m in peaks[:4])
                signals.append(f"{art}: сезонність (пікові місяці: {peak_str})")
            elif troughs:
                trough_str = ", ".join(str(m) for m in troughs[:4])
                signals.append(f"{art}: сезонний мінімум (місяці: {trough_str})")
            else:
                signals.append(f"{art}: виявлено помірну сезонність")
        anom = ds.get("anomalies", [])
        if anom:
            dates = [a.get("timestamp", "") for a in anom[:2]]
            signals.append(f"{art}: сплеск у {', '.join(dates)}")
        yoy = ds.get("yoy_changes", [])
        if yoy:
            ch = yoy[0]
            signals.append(f"{art}: {ch.get('period')} → {ch.get('change_percent', 0):+.1f}%")
    if not signals:
        signals.append("Динаміка переглядів плавна, без екстремальних піків.")

    bullet_y = row2_y + 13
    pdf.set_font(ff, "", 7.8)
    pdf.set_text_color(*TEXT_700)
    for sig in signals[:5]:
        pdf.set_xy(c2_x + 6, bullet_y)
        pdf.multi_cell(card_w - 12, 4, f"•  {_safe(sig)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        bullet_y = pdf.get_y() + 1

    # ── CARD 3: Методологія та застереження ──
    c3_x = c2_x + card_w + card_gap
    pdf.draw_rounded_card(c3_x, row2_y, card_w, card_h)

    pdf.draw_circle_badge(c3_x + 7, row2_y + 7, 3.5, "3")

    pdf.set_xy(c3_x + 14, row2_y + 4.5)
    pdf.set_font(ff, "B", 9.5)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(card_w - 18, 5, "ЗАСТЕРЕЖЕННЯ")

    if not limitations:
        limitations = [
            "Перегляди відображають інформаційний інтерес, а не готовність платити.",
            "Зовнішні медійні події можуть створювати тимчасові сплески.",
            "Менші мовні розділи мають вищу статистичну волатильність.",
            "Трафік ботів відфільтровано (agent=user), але частина може залишатися.",
        ]

    lim_y = row2_y + 13
    pdf.set_font(ff, "", 7.8)
    pdf.set_text_color(*TEXT_700)
    for lim in limitations[:5]:
        pdf.set_xy(c3_x + 6, lim_y)
        pdf.multi_cell(card_w - 12, 4, f"•  {_safe(lim)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        lim_y = pdf.get_y() + 1

    # ┌─────────────────────────────────────────────────────────┐
    # │  SAVE                                                   │
    # └─────────────────────────────────────────────────────────┘
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
