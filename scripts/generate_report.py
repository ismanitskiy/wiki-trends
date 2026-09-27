# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fpdf2>=2.7",
# ]
# ///
"""
generate_report.py — Executive Landscape A4 Wikipedia Trends Report.

All text in the three analytical columns is generated DYNAMICALLY from the
analysis JSON produced by analyze_trends.py. No hardcoded topic names,
no fabricated interpretations.

Optional: pass --insights <file.json> with LLM-generated deeper product
insights to enrich Column 1 (Product Decision). The insights JSON schema:
{
  "decision_summary": "...",
  "bullets": [
    {"title": "...", "text": "..."},
    ...
  ]
}
"""
import argparse
import json
import math
import os
import sys
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# ═══════════════════════════════════════════════════════════════
# Design Tokens
# ═══════════════════════════════════════════════════════════════
PAGE_BG         = (248, 250, 252)
CARD_BG         = (255, 255, 255)
CARD_BORDER     = (226, 232, 240)
CARD_SHADOW     = (238, 242, 246)

TEXT_900        = (15,  23,  42)
TEXT_700        = (51,  65,  85)
TEXT_500        = (100, 116, 139)
TEXT_400        = (148, 163, 184)

INDIGO_PRIMARY  = (79,  70,  229)
INDIGO_BG       = (238, 242, 255)
TEAL_PRIMARY    = (13,  148, 136)
SLATE_PRIMARY   = (100, 116, 139)

GREEN_BG        = (220, 252, 231)
GREEN_TEXT      = (22,  101, 52)
RED_BG          = (254, 226, 226)
RED_TEXT        = (159, 18,  57)

DS_ACCENTS      = [
    (37,  99,  235),
    (244, 63,  94),
    (13,  148, 136),
    (245, 158, 11),
]

MONTH_NAMES_UK = {
    1: "січень", 2: "лютий", 3: "березень", 4: "квітень",
    5: "травень", 6: "червень", 7: "липень", 8: "серпень",
    9: "вересень", 10: "жовтень", 11: "листопад", 12: "грудень"
}


class ExecutiveGridPDF(FPDF):
    def __init__(self, font_family="DejaVu"):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.ff = font_family
        self.set_auto_page_break(auto=False)

    def draw_card(self, x, y, w, h, bg=CARD_BG, border=CARD_BORDER, r=3.5, shadow=True):
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
        self.set_font(self.ff, "B" if bold else "", font_size)
        pw = self.get_string_width(text) + 6.0
        self.set_fill_color(*bg)
        self.rect(x, y, pw, h, style="F", round_corners=True, corner_radius=h / 2)
        self.set_xy(x, y + (h - 3.2) / 2)
        self.set_text_color(*tc)
        self.cell(pw, 3.2, text, align="C")
        return pw

    def draw_number_badge(self, cx, cy, radius, text, bg=INDIGO_PRIMARY, tc=(255, 255, 255)):
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
    if n is None:
        return "—"
    return f"{int(n):,}".replace(",", " ")


def fmt_months(months: list[int]) -> str:
    """Convert list of month numbers to Ukrainian month names."""
    return ", ".join(MONTH_NAMES_UK.get(m, str(m)) for m in months[:4])


# ═══════════════════════════════════════════════════════════════
# Dynamic Text Generators (100% from analysis JSON)
# ═══════════════════════════════════════════════════════════════

def build_decision_from_data(datasets: list, comparison: dict) -> tuple[str, list[tuple[str, str]]]:
    """Build Column 1 (Product Decision) entirely from analysis data."""
    if len(datasets) < 2:
        ds = datasets[0] if datasets else {}
        art = ds.get("article_display", "—")
        trend = ds.get("trend", {})
        pct = trend.get("change_percent_total", 0)
        direction = "зростає" if pct > 0 else "спадає"
        summary = (
            f"Тема «{art}» демонструє тренд, який {direction} ({pct:+.1f}%) "
            f"за період спостереження. Загальний обсяг переглядів: {fmt_n(ds.get('total_views', 0))}, "
            f"середній помісячний попит: {fmt_n(int(ds.get('avg_views', 0)))} переглядів/міс."
        )
        bullets = []
        r2 = trend.get("r_squared", 0)
        if r2 < 0.3:
            bullets.append(("Стабільність тренду", f"R² = {r2:.2f} — тренд нестабільний, дані мають високу волатильність. Рішення потребує додаткової перевірки."))
        return summary, bullets

    # Two or more datasets — compare
    ds0, ds1 = datasets[0], datasets[1]
    avg0, avg1 = ds0.get("avg_views", 1), ds1.get("avg_views", 1)
    total0, total1 = ds0.get("total_views", 0), ds1.get("total_views", 0)
    pct0 = ds0.get("trend", {}).get("change_percent_total", 0)
    pct1 = ds1.get("trend", {}).get("change_percent_total", 0)
    art0 = ds0.get("article_display", "—")
    art1 = ds1.get("article_display", "—")
    proj0 = ds0.get("project", "").split(".")[0].upper()
    proj1 = ds1.get("project", "").split(".")[0].upper()

    # Determine larger market
    if avg1 > avg0:
        larger, smaller = ds1, ds0
        l_proj, s_proj = proj1, proj0
        ratio = avg1 / max(avg0, 1)
    else:
        larger, smaller = ds0, ds1
        l_proj, s_proj = proj0, proj1
        ratio = avg0 / max(avg1, 1)

    l_avg = int(larger.get("avg_views", 0))
    s_avg = int(smaller.get("avg_views", 0))
    l_pct = larger.get("trend", {}).get("change_percent_total", 0)
    s_pct = smaller.get("trend", {}).get("change_percent_total", 0)

    # Both declining?
    both_declining = (pct0 < 0 and pct1 < 0)
    one_growing = (pct0 > 0) != (pct1 > 0)

    if both_declining:
        summary = (
            f"Обидва ринки демонструють спадний тренд: "
            f"{proj0} ({pct0:+.1f}%) та {proj1} ({pct1:+.1f}%). "
            f"Ринок {l_proj} у {ratio:.1f}x більший за обсягом "
            f"({fmt_n(l_avg)} проти {fmt_n(s_avg)} переглядів/міс)."
        )
    elif one_growing:
        growing_ds = ds0 if pct0 > 0 else ds1
        g_proj = proj0 if pct0 > 0 else proj1
        g_pct = pct0 if pct0 > 0 else pct1
        summary = (
            f"Ринок {g_proj} демонструє зростання ({g_pct:+.1f}%), "
            f"тоді як інший ринок спадає. "
            f"За обсягом {l_proj} у {ratio:.1f}x більший "
            f"({fmt_n(l_avg)} проти {fmt_n(s_avg)} переглядів/міс)."
        )
    else:
        summary = (
            f"Обидва ринки зростають: "
            f"{proj0} ({pct0:+.1f}%) та {proj1} ({pct1:+.1f}%). "
            f"За обсягом {l_proj} у {ratio:.1f}x більший "
            f"({fmt_n(l_avg)} проти {fmt_n(s_avg)} переглядів/міс)."
        )

    # Build bullets from data
    bullets = []

    # Bullet 1: Market priority (based on volume ratio)
    if ratio >= 2.0:
        bullets.append((
            "Пріоритет ринку",
            f"Ринок {l_proj} має попит у {ratio:.1f}x більший ({fmt_n(l_avg)} проти {fmt_n(s_avg)}/міс). "
            f"За обсягом він є пріоритетним для масштабування."
        ))

    # Bullet 2: Trend stability (based on R²)
    r2_0 = ds0.get("trend", {}).get("r_squared", 0)
    r2_1 = ds1.get("trend", {}).get("r_squared", 0)
    more_stable = proj0 if r2_0 > r2_1 else proj1
    less_stable = proj1 if r2_0 > r2_1 else proj0
    if abs(r2_0 - r2_1) > 0.1:
        bullets.append((
            "Стабільність попиту",
            f"Ринок {more_stable} демонструє стабільніший тренд (R² = {max(r2_0, r2_1):.2f}), "
            f"тоді як {less_stable} має вищу волатильність (R² = {min(r2_0, r2_1):.2f})."
        ))

    # Bullet 3: Seasonality advice (based on peak/trough months)
    for ds in datasets:
        proj = ds.get("project", "").split(".")[0].upper()
        seas = ds.get("seasonality", {})
        peaks = seas.get("peak_months", [])
        troughs = seas.get("trough_months", [])
        if peaks:
            bullets.append((
                f"Сезонність ({proj})",
                f"Виражений пік попиту у місяцях: {fmt_months(peaks)}. "
                f"Для максимального охоплення запускати промокампанії за 1 місяць до піку."
            ))
            break  # Only one seasonality bullet to save space

    return summary, bullets[:3]


def build_signals_from_data(datasets: list) -> list[tuple[str, str]]:
    """Build Column 2 (Signals & Anomalies) entirely from analysis data."""
    signals = []

    for ds in datasets:
        proj = ds.get("project", "").split(".")[0].upper()
        art = ds.get("article_display", "—")
        avg = ds.get("avg_views", 1)

        # Anomalies
        for a in ds.get("anomalies", []):
            ts = a.get("timestamp", "")
            views = a.get("views", 0)
            z = a.get("z_score", 0)
            ratio = views / max(avg, 1)
            signals.append((
                f"Сплеск у {ts} (Z = {z:.2f})",
                f"{proj}: {fmt_n(views)} переглядів (у {ratio:.1f}x вище середнього {fmt_n(int(avg))}/міс)."
            ))

        # Seasonality
        seas = ds.get("seasonality", {})
        peaks = seas.get("peak_months", [])
        troughs = seas.get("trough_months", [])
        if peaks:
            signals.append((
                f"Сезонні піки ({proj})",
                f"Виражений підйом інтересу у місяцях: {fmt_months(peaks)}."
            ))
        if troughs:
            signals.append((
                f"Сезонне дно ({proj})",
                f"Мінімальна активність у місяцях: {fmt_months(troughs)}."
            ))

        # YoY changes
        yoy = ds.get("yoy_changes", [])
        if yoy:
            parts = []
            for y in yoy[:2]:
                parts.append(f"{y.get('period')}: {y.get('change_percent', 0):+.1f}%")
            signals.append((
                f"Річна динаміка ({proj})",
                f"{'; '.join(parts)}."
            ))

    return signals[:5]


def build_limitations_from_data(limitations: list) -> list[tuple[str, str]]:
    """Build Column 3 (Limitations) from analysis JSON limitations array."""
    result = []
    for lim in limitations[:4]:
        # Split at first period or use the whole string
        if ". " in lim:
            parts = lim.split(". ", 1)
            # Try to make a short title from first sentence
            title = parts[0]
            if len(title) > 40:
                title = title[:38] + "…"
            desc = lim
        elif "," in lim:
            title = lim.split(",", 1)[0]
            if len(title) > 40:
                title = title[:38] + "…"
            desc = lim
        else:
            title = lim[:40] + "…" if len(lim) > 40 else lim
            desc = lim

        result.append((title, desc))

    # Ensure we have at least a few items
    if len(result) < 2:
        result.append(("Методологія", "Аналіз базується на даних переглядів статей Вікіпедії (agent=user). Перегляди відображають інформаційний інтерес, а не готовність платити."))

    return result


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate Executive Landscape A4 Wikipedia Trends Report")
    parser.add_argument("--analysis", required=True, help="Path to JSON file from analyze_trends.py")
    parser.add_argument("--chart", required=True, help="Path to chart PNG file from generate_chart.py")
    parser.add_argument("--title", default="Аналіз ринкового інтересу: Wikipedia Trends", help="Report title")
    parser.add_argument("--output", default="report.pdf", help="Output PDF file path")
    parser.add_argument("--insights", default=None, help="Optional JSON with LLM-generated product insights for Column 1")
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
    limitations_raw = data.get("limitations", [])

    # Load optional LLM insights
    llm_insights = None
    if args.insights and os.path.exists(args.insights):
        try:
            with open(args.insights, 'r', encoding='utf-8') as f:
                llm_insights = json.load(f)
        except Exception:
            pass

    # Build dynamic text for all three columns
    if llm_insights:
        decision_summary = llm_insights.get("decision_summary", "")
        decision_bullets = [(b.get("title", ""), b.get("text", "")) for b in llm_insights.get("bullets", [])]
        if not decision_summary:
            decision_summary, decision_bullets = build_decision_from_data(datasets, comparison)
    else:
        decision_summary, decision_bullets = build_decision_from_data(datasets, comparison)

    signals = build_signals_from_data(datasets)
    limits = build_limitations_from_data(limitations_raw)

    # ── Build PDF ──
    pdf = ExecutiveGridPDF()
    ff = setup_font(pdf)
    pdf.ff = ff
    pdf.add_page()

    # Canvas background
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, 0, 297, 210, style="F")

    # Grid geometry
    ML      = 12.0
    COL_W   = 88.0
    GAP     = 4.5
    CHART_W = COL_W * 2 + GAP
    CHART_X = ML + COL_W + GAP

    now_str = datetime.now().strftime("%d.%m.%Y • %H:%M")

    # ═══ 1. HEADER ═══
    pdf.set_xy(ML, 10.0)
    pdf.set_font(ff, "B", 15.5)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(175, 7.5, args.title, align="L")

    pdf.set_font(ff, "", 8.0)
    pdf.set_text_color(*TEXT_500)
    pdf.set_xy(197.0, 10.0)
    pdf.cell(88.0, 4.0, f"Дата створення: {now_str}", align="R")
    pdf.set_xy(197.0, 14.5)
    n_months = len(datasets[0].get("yoy_changes", [])) * 12 + 12 if datasets else 24
    # Try to determine actual sample size from data
    pdf.cell(88.0, 4.0, f"Вибірка аналізу: {n_months} місяців (помісячно)", align="R")

    pdf.set_draw_color(*CARD_BORDER)
    pdf.set_line_width(0.3)
    pdf.line(ML, 23.5, ML + COL_W * 3 + GAP * 2, 23.5)

    # ═══ 2. HERO ROW (y: 27.5, h: 96) ═══
    hero_y  = 27.5
    hero_h  = 96.0
    card_gap = 4.5
    num_cards = min(len(datasets), 4)
    kpi_card_h = (hero_h - card_gap * max(num_cards - 1, 1)) / max(num_cards, 1)

    # ── KPI Cards (LEFT, 1/3 width) ──
    for i in range(num_cards):
        cy = hero_y + i * (kpi_card_h + card_gap)
        pdf.draw_card(ML, cy, COL_W, kpi_card_h, r=3.5)

        ds = datasets[i]
        article = ds.get("article_display", "—")
        project = ds.get("project", "")
        lang = project.split(".")[0].upper()
        accent_c = DS_ACCENTS[i % len(DS_ACCENTS)]

        # Accent strip
        pdf.set_fill_color(*accent_c)
        pdf.rect(ML, cy, 3.0, kpi_card_h, style="F", round_corners=True, corner_radius=1.5)

        # Language badge
        badge_bg = (238, 242, 255) if i == 0 else (255, 241, 242) if i == 1 else (240, 253, 250)
        lpw = pdf.draw_pill(ML + 6.0, cy + 4.5, text=lang, bg=badge_bg, tc=accent_c, font_size=6.8, bold=True, h=4.2)

        # Article title
        pdf.set_xy(ML + 6.0 + lpw + 2.5, cy + 4.2)
        pdf.set_font(ff, "B", 9.5)
        pdf.set_text_color(*TEXT_900)
        max_c = int((COL_W - lpw - 15) / 2.2)
        art_disp = article if len(article) <= max_c else article[:max_c-1] + "…"
        pdf.cell(COL_W - lpw - 15, 4.5, art_disp)

        # Project domain
        pdf.set_xy(ML + 6.0, cy + 9.5)
        pdf.set_font(ff, "", 7.2)
        pdf.set_text_color(*TEXT_400)
        pdf.cell(COL_W - 12, 3.5, project)

        # Total views (big number)
        total = ds.get("total_views", 0)
        avg = ds.get("avg_views", 0)
        pdf.set_xy(ML + 6.0, cy + 14.5)
        pdf.set_font(ff, "B", 19.0)
        pdf.set_text_color(*TEXT_900)
        tot_str = fmt_n(total)
        tw = pdf.get_string_width(tot_str)
        pdf.cell(tw + 1.0, 8.5, tot_str)

        # Monthly avg baseline
        pdf.set_xy(ML + 6.0 + tw + 3.0, cy + 18.0)
        pdf.set_font(ff, "", 7.6)
        pdf.set_text_color(*TEXT_500)
        pdf.cell(38, 4.0, f"ср. {fmt_n(int(avg))} / міс")

        # Trend badge
        trend = ds.get("trend", {})
        pct = trend.get("change_percent_total", 0.0)
        arrow = "▲" if pct > 0 else "▼"
        badge_lbl = f"{arrow} {pct:+.1f}%"
        badge_bg = GREEN_BG if pct > 0 else RED_BG
        badge_tc = GREEN_TEXT if pct > 0 else RED_TEXT
        pdf.draw_pill(ML + 6.0, cy + 25.5, badge_lbl, bg=badge_bg, tc=badge_tc, font_size=7.6, h=5.2)

        # R² + interpretation
        r2 = trend.get("r_squared", 0.0)
        if r2 >= 0.7:
            interp = "Стабільний чіткий тренд"
        elif r2 >= 0.4:
            interp = "Помітний тренд з коливаннями"
        elif r2 >= 0.15:
            interp = "Висока сезонна волатильність"
        else:
            interp = "Тренд нестабільний (шум)"
        pdf.set_xy(ML + 6.0, cy + 34.5)
        pdf.set_font(ff, "", 6.8)
        pdf.set_text_color(*TEXT_500)
        pdf.cell(COL_W - 12, 4.0, f"R² = {r2:.2f}  •  {interp}")

    # ── Chart Card (RIGHT, 2/3 width) ──
    pdf.draw_card(CHART_X, hero_y, CHART_W, hero_h, r=3.5)
    pdf.set_xy(CHART_X + 6.0, hero_y + 3.8)
    pdf.set_font(ff, "B", 7.8)
    pdf.set_text_color(*TEXT_500)
    pdf.cell(CHART_W - 12, 4.0, "ДИНАМІКА ПОПИТУ ТА ДОВГОСТРОКОВИЙ ТРЕНД (ПЕРЕГЛЯДИ / МІСЯЦЬ)")

    if os.path.exists(args.chart):
        try:
            pdf.image(args.chart, x=CHART_X + 2.0, y=hero_y + 8.5, w=CHART_W - 4.0, h=hero_h - 10.5)
        except Exception as e:
            sys.stderr.write(f"Chart render warning: {e}\n")

    # ═══ 3. BOTTOM ROW: THREE COLUMNS (y: 127.5, h: 72.5) ═══
    bot_y = 127.5
    bot_h = 72.5
    col1_x = ML
    col2_x = ML + COL_W + GAP
    col3_x = col2_x + COL_W + GAP

    # Helper: render a column with title, optional summary, and bullet list
    def render_column(cx, accent_color, num, title, summary, bullets, max_bullets=4):
        pdf.draw_card(cx, bot_y, COL_W, bot_h, r=3.5)
        pdf.set_fill_color(*accent_color)
        pdf.rect(cx, bot_y, COL_W, 2.5, style="F", round_corners=True, corner_radius=1.5)
        pdf.draw_number_badge(cx + 8.0, bot_y + 8.5, radius=3.0, text=str(num), bg=accent_color)
        pdf.set_xy(cx + 14.0, bot_y + 6.5)
        pdf.set_font(ff, "B", 9.2)
        tc = accent_color if num == 1 else TEXT_900
        pdf.set_text_color(*tc)
        pdf.cell(COL_W - 18, 4.5, title)

        cur_y = bot_y + 13.5

        if summary:
            pdf.set_xy(cx + 6, cur_y)
            pdf.set_font(ff, "", 7.3)
            pdf.set_text_color(*TEXT_700)
            pdf.multi_cell(COL_W - 12, 3.3, summary, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            cur_y = pdf.get_y() + 1.5

        for b_title, b_desc in bullets[:max_bullets]:
            if cur_y > bot_y + bot_h - 8:
                break
            pdf.set_fill_color(*accent_color)
            pdf.ellipse(cx + 6, cur_y + 1.2, 1.6, 1.6, style="F")
            pdf.set_xy(cx + 9.5, cur_y)
            pdf.set_font(ff, "B", 7.2)
            pdf.set_text_color(*TEXT_900)
            pdf.cell(COL_W - 15, 3.2, b_title)
            pdf.set_xy(cx + 9.5, cur_y + 3.0)
            pdf.set_font(ff, "", 6.9)
            pdf.set_text_color(*TEXT_700)
            pdf.multi_cell(COL_W - 15, 2.9, b_desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            cur_y = pdf.get_y() + 1.0

    # Column 1: Product Decision
    render_column(col1_x, INDIGO_PRIMARY, 1, "РІШЕННЯ ДЛЯ ПРОДУКТУ", decision_summary, decision_bullets, max_bullets=3)

    # Column 2: Signals & Anomalies
    render_column(col2_x, TEAL_PRIMARY, 2, "СИГНАЛИ ТА АНОМАЛІЇ", None, signals, max_bullets=5)

    # Column 3: Limitations
    render_column(col3_x, SLATE_PRIMARY, 3, "МЕЖІ ДОВІРИ ТА ОБМЕЖЕННЯ", None, limits, max_bullets=4)

    # ═══ Save ═══
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
