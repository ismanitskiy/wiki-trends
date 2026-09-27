# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fpdf2>=2.7",
#     "pyphen>=0.14.0",
# ]
# ///
"""
generate_report.py — Executive Landscape A4 Wikipedia Trends Report.

Features:
- 100% dynamic content from analyze_trends.py JSON.
- Balanced 2-column KPI cards with zero empty dead space.
- Automatic Ukrainian syllable hyphenation (pyphen uk_UA) + non-breaking spaces.
- Beautiful, clean typography with proper left alignment (no stretched word gaps).
- Legible font sizes (7.6–8.2 pt) filling cards down to balanced margins.
- Auto-generated English filename with topic, compared languages, data period, and analysis date.
- Auto-generated title and clean period display (no 'помісячно').
- Optional --insights <file.json> for LLM-augmented product recommendations.
"""
import argparse
import json
import math
import os
import re
import sys
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

try:
    import pyphen
    _pyphen_uk = pyphen.Pyphen(lang='uk_UA', left=2, right=2)
except Exception:
    _pyphen_uk = None

SOFT_HYPHEN = "\u00ad"


# ═══════════════════════════════════════════════════════════════
# Design Tokens
# ═══════════════════════════════════════════════════════════════
PAGE_BG         = (248, 250, 252)
CARD_BG         = (255, 255, 255)
CARD_BORDER     = (226, 232, 240)
CARD_SHADOW     = (238, 242, 246)
DIVIDER_LINE    = (241, 245, 249)

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
    (37,  99,  235),   # Royal Blue
    (244, 63,  94),   # Rose / Coral
    (13,  148, 136),  # Teal
    (245, 158, 11),   # Amber
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


def smart_wrap_uk(text: str) -> str:
    """
    1. Attach short Ukrainian prepositions and conjunctions to the following word
       using non-breaking space (\\u00a0) to avoid trailing orphan words at line ends.
    2. Insert soft hyphens (\\u00ad) into Ukrainian words (6+ chars) according to
       official Ukrainian syllabic hyphenation rules (left=2, right=2).
    """
    if not text:
        return ""
    nbsp = "\u00a0"
    # Single and 2-letter prepositions/conjunctions
    preps = r'\b(в|у|і|й|та|на|за|до|по|з|із|зі|для|про|від|під|над|при|без|як|не|чи|що)\s+'
    text = re.sub(preps, r'\g<1>' + nbsp, text, flags=re.IGNORECASE)
    # Join numbers with units / multiplier (e.g. 12.4x, 3.3x)
    text = re.sub(r'(\d+)\s+([xх%])', r'\g<1>' + nbsp + r'\g<2>', text)

    # Syllabic hyphenation with soft hyphens
    if _pyphen_uk:
        def _repl(match):
            w = match.group(0)
            if len(w) >= 6:
                return _pyphen_uk.inserted(w, SOFT_HYPHEN)
            return w
        pattern = r'[а-яА-Яa-zA-ZєіїґЄІЇҐ\']+'
        text = re.sub(pattern, _repl, text)

    return text


def slugify_ascii(text: str) -> str:
    """Turn string into safe lowercase ASCII alphanumeric slug."""
    text = text.lower()
    translit = {
        'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ye',
        'ж':'zh','з':'z','и':'y','і':'i','ї':'yi','й':'y','к':'k','л':'l',
        'м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
        'ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ь':'',
        'ю':'yu','я':'ya'
    }
    res = []
    for ch in text:
        if ch in translit:
            res.append(translit[ch])
        elif ch.isascii() and (ch.isalnum() or ch in ('_', '-')):
            res.append(ch)
        else:
            res.append('_')
    slug = "".join(res)
    slug = re.sub(r'[_]+', '_', slug).strip('_')
    return slug[:32] if slug else "topic"


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
        return smart_wrap_uk(summary), bullets

    ds0, ds1 = datasets[0], datasets[1]
    avg0, avg1 = ds0.get("avg_views", 1), ds1.get("avg_views", 1)
    pct0 = ds0.get("trend", {}).get("change_percent_total", 0)
    pct1 = ds1.get("trend", {}).get("change_percent_total", 0)
    proj0 = ds0.get("project", "").split(".")[0].upper()
    proj1 = ds1.get("project", "").split(".")[0].upper()

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

    both_declining = (pct0 < 0 and pct1 < 0)
    one_growing = (pct0 > 0) != (pct1 > 0)

    if both_declining:
        summary = (
            f"Обидва ринки демонструють спадний тренд: {proj0} ({pct0:+.1f}%) та {proj1} ({pct1:+.1f}%). "
            f"Ринок {l_proj} у {ratio:.1f}x більший за обсягом ({fmt_n(l_avg)} проти {fmt_n(s_avg)} переглядів/міс)."
        )
    elif one_growing:
        g_proj = proj0 if pct0 > 0 else proj1
        g_pct = pct0 if pct0 > 0 else pct1
        summary = (
            f"Ринок {g_proj} демонструє зростання ({g_pct:+.1f}%), тоді як інший ринок спадає. "
            f"За обсягом {l_proj} у {ratio:.1f}x більший ({fmt_n(l_avg)} проти {fmt_n(s_avg)} переглядів/міс)."
        )
    else:
        summary = (
            f"Обидва ринки зростають: {proj0} ({pct0:+.1f}%) та {proj1} ({pct1:+.1f}%). "
            f"За обсягом {l_proj} у {ratio:.1f}x більший ({fmt_n(l_avg)} проти {fmt_n(s_avg)} переглядів/міс)."
        )

    bullets = []
    # 1. Market scale priority
    bullets.append((
        "Пріоритет масштабування",
        smart_wrap_uk(f"Для масштабування пріоритетним є {l_proj}: попит у {ratio:.1f}x вищий ({fmt_n(l_avg)} проти {fmt_n(s_avg)}/міс).")
    ))

    # 2. Demand stability (R²)
    r2_0 = ds0.get("trend", {}).get("r_squared", 0)
    r2_1 = ds1.get("trend", {}).get("r_squared", 0)
    more_stable = proj0 if r2_0 >= r2_1 else proj1
    less_stable = proj1 if r2_0 >= r2_1 else proj0
    bullets.append((
        "Стабільність попиту (R²)",
        smart_wrap_uk(f"Ринок {more_stable} має помірніший тренд (R² = {max(r2_0, r2_1):.2f}), тоді як {less_stable} (R² = {min(r2_0, r2_1):.2f}) чутливий до сезонності.")
    ))

    # 3. Launch window / Seasonality
    seas_ds = ds0 if ds0.get("seasonality", {}).get("peak_months") else ds1
    seas_proj = seas_ds.get("project", "").split(".")[0].upper()
    peaks = seas_ds.get("seasonality", {}).get("peak_months", [])
    if peaks:
        bullets.append((
            "Сезонне вікно запуску",
            smart_wrap_uk(f"Пік попиту в {seas_proj} припадає на: {fmt_months(peaks)}. Запуск промокампаній рекомендовано за 1 місяць до підйому.")
        ))
    else:
        bullets.append((
            "Стратегія позиціонування",
            smart_wrap_uk("Рекомендовано позиціонувати продукт через вирішення практичних задач аудиторії для згладжування коливань попиту.")
        ))

    return smart_wrap_uk(summary), bullets[:3]


def build_signals_from_data(datasets: list) -> list[tuple[str, str]]:
    """Build Column 2 (Signals & Anomalies) entirely from analysis data."""
    signals = []

    for ds in datasets:
        proj = ds.get("project", "").split(".")[0].upper()
        avg = ds.get("avg_views", 1)

        # Anomalies
        for a in ds.get("anomalies", []):
            ts = a.get("timestamp", "")
            views = a.get("views", 0)
            z = a.get("z_score", 0)
            ratio = views / max(avg, 1)
            signals.append((
                f"Сплеск {ts} (Z = {z:.2f})",
                smart_wrap_uk(f"{proj}: {fmt_n(views)} переглядів (у {ratio:.1f}x вище норми {fmt_n(int(avg))}/міс).")
            ))

        # Seasonality peaks & troughs
        seas = ds.get("seasonality", {})
        peaks = seas.get("peak_months", [])
        troughs = seas.get("trough_months", [])
        if peaks:
            signals.append((
                f"Сезонні піки ({proj})",
                smart_wrap_uk(f"Підйом інтересу спостерігається у місяцях: {fmt_months(peaks)}.")
            ))
        if troughs:
            signals.append((
                f"Сезонний спад ({proj})",
                smart_wrap_uk(f"Мінімальна активність спостерігається у місяцях: {fmt_months(troughs)}.")
            ))

        # YoY
        yoy = ds.get("yoy_changes", [])
        if yoy:
            parts = [f"{y.get('period')}: {y.get('change_percent', 0):+.1f}%" for y in yoy[:2]]
            signals.append((
                f"Річна динаміка ({proj})",
                smart_wrap_uk(f"Динаміка за роками: {'; '.join(parts)}.")
            ))

    return signals[:4]


def build_limitations_from_data(limitations: list) -> list[tuple[str, str]]:
    """Build Column 3 (Limitations) with concise methodological explanations that fit within balanced margins."""
    items = [
        (
            "Інтерес ≠ прямий попит",
            smart_wrap_uk("Перегляди відображають інформаційний інтерес, а не готовність купувати комерційні продукти.")
        ),
        (
            "Медійні та новинні сплески",
            smart_wrap_uk("Зовнішні інфоприводи чи суспільні події створюють тимчасовий неорганічний шум у динаміці.")
        ),
        (
            "Волатильність локальних версій",
            smart_wrap_uk("Розділи з меншою аудиторією мають вищу статистичну похибку та чутливість до поодиноких сплесків.")
        ),
        (
            "Фільтрація бот-трафіку (agent=user)",
            smart_wrap_uk("Трафік ботів відфільтровано, проте невелика частка автоматизованих запитів може залишатися у вибірці.")
        )
    ]
    return items


# ═══════════════════════════════════════════════════════════════
# Filename & Title Helpers
# ═══════════════════════════════════════════════════════════════

def auto_generate_filename(datasets: list) -> str:
    """
    Generate an English, descriptive filename for email and Slack:
    e.g. 'wikipedia_trends_astronomy_uk_vs_en_period_2022-09_to_2024-08_date_2026-09-27.pdf'
    """
    topic_slug = ""
    # Try finding an English dataset first
    for ds in datasets:
        if ds.get("project", "").startswith("en"):
            topic_slug = slugify_ascii(ds.get("article", ""))
            break
    if not topic_slug and datasets:
        topic_slug = slugify_ascii(datasets[0].get("article_display", datasets[0].get("article", "")))
    if not topic_slug:
        topic_slug = "comparison"

    langs = [ds.get("project", "").split(".")[0].lower() for ds in datasets if ds.get("project")]
    lang_str = "_vs_".join(langs) if len(langs) > 1 else (langs[0] if langs else "wiki")

    start_date = datasets[0].get("start_date", "2022-09") if datasets else "start"
    end_date = datasets[0].get("end_date", "2024-08") if datasets else "end"
    today_str = datetime.now().strftime("%Y-%m-%d")

    return f"wikipedia_trends_{topic_slug}_{lang_str}_period_{start_date}_to_{end_date}_date_{today_str}.pdf"


def auto_generate_title(datasets: list) -> str:
    """Generate title: '«Астрономія» — UK vs EN Wikipedia'."""
    if not datasets:
        return "Wikipedia Trends — Аналіз ринкового інтересу"
    articles = []
    langs = []
    for ds in datasets[:3]:
        art = ds.get("article_display", "")
        proj = ds.get("project", "").split(".")[0].upper()
        if art and art not in articles:
            articles.append(art)
        if proj and proj not in langs:
            langs.append(proj)
    topic = articles[0] if articles else "Тема"
    lang_str = " vs ".join(langs) if len(langs) > 1 else (langs[0] if langs else "Wikipedia")
    return f"«{topic}» — {lang_str} Wikipedia"


def format_period_uk(start_str: str, end_str: str, n_points: int) -> str:
    """Format period as '09.2022 – 08.2024 (24 міс.)'."""
    def _reformat(d):
        if not d:
            return ""
        pts = d.split("-")
        if len(pts) == 2:
            return f"{pts[1]}.{pts[0]}"
        return d
    s = _reformat(start_str)
    e = _reformat(end_str)
    if s and e:
        return f"{s} – {e} ({n_points} міс.)"
    return f"{n_points} місяців"


# ═══════════════════════════════════════════════════════════════
# Main Report Generation
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate Executive Landscape A4 Wikipedia Trends Report")
    parser.add_argument("--analysis", required=True, help="Path to JSON file from analyze_trends.py")
    parser.add_argument("--chart", required=True, help="Path to chart PNG file from generate_chart.py")
    parser.add_argument("--title", default=None, help="Report title (auto-generated if omitted)")
    parser.add_argument("--output", default=None, help="Output PDF file path (auto-generated if omitted)")
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

    # Extract dates & data points
    start_date = datasets[0].get("start_date", "2022-09") if datasets else "2022-09"
    end_date = datasets[0].get("end_date", "2024-08") if datasets else "2024-08"
    n_points = datasets[0].get("data_points", 24) if datasets else 24

    # Determine Title and Output Filename
    report_title = args.title if args.title else auto_generate_title(datasets)
    output_path = args.output if args.output else auto_generate_filename(datasets)

    # Optional LLM insights
    llm_insights = None
    if args.insights and os.path.exists(args.insights):
        try:
            with open(args.insights, 'r', encoding='utf-8') as f:
                llm_insights = json.load(f)
        except Exception:
            pass

    if llm_insights:
        decision_summary = smart_wrap_uk(llm_insights.get("decision_summary", ""))
        decision_bullets = [(b.get("title", ""), smart_wrap_uk(b.get("text", ""))) for b in llm_insights.get("bullets", [])]
        if not decision_summary:
            decision_summary, decision_bullets = build_decision_from_data(datasets, comparison)
    else:
        decision_summary, decision_bullets = build_decision_from_data(datasets, comparison)

    signals = build_signals_from_data(datasets)
    limits = build_limitations_from_data(limitations_raw)

    # ── PDF Init ──
    pdf = ExecutiveGridPDF()
    ff = setup_font(pdf)
    pdf.ff = ff
    pdf.add_page()

    # Page background
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, 0, 297, 210, style="F")

    # Grid geometry
    ML      = 12.0
    COL_W   = 88.0
    GAP     = 4.5
    CHART_W = COL_W * 2 + GAP
    CHART_X = ML + COL_W + GAP

    now_str = datetime.now().strftime("%d.%m.%Y • %H:%M")
    period_str = format_period_uk(start_date, end_date, n_points)

    # ═══ 1. HEADER (y: 10.0 – 23.5) ═══
    pdf.set_xy(ML, 10.0)
    pdf.set_font(ff, "B", 15.0)
    pdf.set_text_color(*TEXT_900)
    pdf.cell(175, 7.5, report_title, align="L")

    pdf.set_font(ff, "", 8.0)
    pdf.set_text_color(*TEXT_500)
    pdf.set_xy(197.0, 9.5)
    pdf.cell(88.0, 4.0, f"Дата аналізу: {now_str}", align="R")
    pdf.set_xy(197.0, 14.5)
    pdf.cell(88.0, 4.0, f"Період даних: {period_str}", align="R")

    pdf.set_draw_color(*CARD_BORDER)
    pdf.set_line_width(0.3)
    pdf.line(ML, 23.5, ML + COL_W * 3 + GAP * 2, 23.5)

    # ═══ 2. HERO ROW (y: 27.5, h: 96) ═══
    hero_y  = 27.5
    hero_h  = 96.0
    card_gap = 4.5
    num_cards = min(len(datasets), 4)
    kpi_card_h = (hero_h - card_gap * max(num_cards - 1, 1)) / max(num_cards, 1)

    # ── KPI Cards (LEFT 1/3) ──
    for i in range(num_cards):
        cy = hero_y + i * (kpi_card_h + card_gap)
        pdf.draw_card(ML, cy, COL_W, kpi_card_h, r=3.5)

        ds = datasets[i]
        article = ds.get("article_display", "—")
        project = ds.get("project", "")
        lang = project.split(".")[0].upper()
        accent_c = DS_ACCENTS[i % len(DS_ACCENTS)]

        # Left accent stripe
        pdf.set_fill_color(*accent_c)
        pdf.rect(ML, cy, 3.2, kpi_card_h, style="F", round_corners=True, corner_radius=1.5)

        # ── Card Top Header Row (cy + 3.8) ──
        badge_bg = (238, 242, 255) if i == 0 else (255, 241, 242) if i == 1 else (240, 253, 250)
        lpw = pdf.draw_pill(ML + 6.0, cy + 3.6, text=lang, bg=badge_bg, tc=accent_c, font_size=6.8, bold=True, h=4.4)

        # Domain Badge (Right-aligned)
        pdf.set_xy(ML + COL_W - 35.0, cy + 3.6)
        pdf.set_font(ff, "", 7.2)
        pdf.set_text_color(*TEXT_400)
        pdf.cell(29.0, 4.4, project, align="R")

        # ── Article Title (cy + 9.0, full card width, 10.2pt Bold) ──
        pdf.set_xy(ML + 6.0, cy + 9.0)
        pdf.set_font(ff, "B", 10.2)
        pdf.set_text_color(*TEXT_900)
        avail_art_w = COL_W - 12.0  # 76.0 mm available!
        art_wrapped = smart_wrap_uk(article)
        if pdf.get_string_width(article) <= avail_art_w:
            pdf.cell(avail_art_w, 5.0, article)
        else:
            pdf.multi_cell(avail_art_w, 4.4, art_wrapped, align="L")

        # Subtle card divider line
        pdf.set_draw_color(*DIVIDER_LINE)
        pdf.set_line_width(0.3)
        pdf.line(ML + 6.0, cy + 15.0, ML + COL_W - 6.0, cy + 15.0)

        # ── Metrics 2-Column Section (cy + 16.5) ──
        total = ds.get("total_views", 0)
        avg = ds.get("avg_views", 0)
        tot_str = fmt_n(total)
        avg_str = fmt_n(int(avg))

        # Metric 1: Total Views (Left column)
        pdf.set_xy(ML + 6.0, cy + 16.5)
        pdf.set_font(ff, "B", 6.8)
        pdf.set_text_color(*TEXT_400)
        pdf.cell(38.0, 3.2, "ЗАГАЛЬНИЙ ПОПИТ")

        pdf.set_xy(ML + 6.0, cy + 20.0)
        pdf.set_font(ff, "B", 17.0)
        pdf.set_text_color(*TEXT_900)
        pdf.cell(38.0, 7.5, tot_str)

        # Metric 2: Monthly Average (Right column)
        pdf.set_xy(ML + 47.0, cy + 16.5)
        pdf.set_font(ff, "B", 6.8)
        pdf.set_text_color(*TEXT_400)
        pdf.cell(35.0, 3.2, "СЕРЕДНІЙ ПОМІСЯЧНО")

        pdf.set_xy(ML + 47.0, cy + 20.8)
        pdf.set_font(ff, "B", 12.5)
        pdf.set_text_color(*TEXT_700)
        pdf.cell(35.0, 6.5, f"{avg_str} / міс")

        # ── Bottom Status Row (cy + 33.5) ──
        trend = ds.get("trend", {})
        pct = trend.get("change_percent_total", 0.0)
        arrow = "▲" if pct > 0 else "▼"
        badge_lbl = f"{arrow} {pct:+.1f}%"
        badge_bg = GREEN_BG if pct > 0 else RED_BG
        badge_tc = GREEN_TEXT if pct > 0 else RED_TEXT
        tpw = pdf.draw_pill(ML + 6.0, cy + 33.5, badge_lbl, bg=badge_bg, tc=badge_tc, font_size=7.6, h=5.2)

        # R² + Business Interpretation
        r2 = trend.get("r_squared", 0.0)
        if r2 >= 0.7:
            interp = "Стійкий тренд"
        elif r2 >= 0.4:
            interp = "Помітний тренд"
        elif r2 >= 0.15:
            interp = "Сезонна волатильність"
        else:
            interp = "Нестабільний попит"

        pdf.set_xy(ML + 6.0 + tpw + 3.5, cy + 34.2)
        pdf.set_font(ff, "", 7.2)
        pdf.set_text_color(*TEXT_500)
        pdf.cell(COL_W - tpw - 15.0, 3.8, f"R² = {r2:.2f}  •  {interp}")

    # ── Chart Card (RIGHT 2/3) ──
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

    def render_column(cx, accent_color, num, title, summary, bullets, max_bullets=4):
        pdf.draw_card(cx, bot_y, COL_W, bot_h, r=3.5)
        # Accent top line
        pdf.set_fill_color(*accent_color)
        pdf.rect(cx, bot_y, COL_W, 2.5, style="F", round_corners=True, corner_radius=1.5)

        # Number circle badge & Header title
        pdf.draw_number_badge(cx + 8.0, bot_y + 8.5, radius=3.0, text=str(num), bg=accent_color)
        pdf.set_xy(cx + 14.0, bot_y + 6.5)
        pdf.set_font(ff, "B", 9.2)
        tc = accent_color if num == 1 else TEXT_900
        pdf.set_text_color(*tc)
        pdf.cell(COL_W - 18, 4.5, title)

        cur_y = bot_y + 13.5
        bottom_limit = bot_y + bot_h - 3.0

        if summary:
            pdf.set_xy(cx + 6.0, cur_y)
            pdf.set_font(ff, "", 7.8)
            pdf.set_text_color(*TEXT_700)
            # CRITICAL: align="L" to completely prevent justify space gaps!
            pdf.multi_cell(COL_W - 12.0, 3.6, summary, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            cur_y = pdf.get_y() + 2.0

        for b_title, b_desc in bullets[:max_bullets]:
            if cur_y > bottom_limit - 6.0:
                break
            # Bullet point indicator
            pdf.set_fill_color(*accent_color)
            pdf.ellipse(cx + 6.0, cur_y + 1.2, 1.5, 1.5, style="F")

            # Bullet title
            pdf.set_xy(cx + 9.5, cur_y)
            pdf.set_font(ff, "B", 8.0)
            pdf.set_text_color(*TEXT_900)
            pdf.cell(COL_W - 16.0, 3.4, b_title)
            cur_y += 3.6

            if cur_y > bottom_limit - 3.0:
                break

            # Bullet description
            pdf.set_xy(cx + 9.5, cur_y)
            pdf.set_font(ff, "", 7.4)
            pdf.set_text_color(*TEXT_700)
            # CRITICAL: align="L" to completely prevent justify space gaps!
            pdf.multi_cell(COL_W - 16.0, 3.2, b_desc, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            cur_y = pdf.get_y() + 1.8

    # Column 1: Product Decision
    render_column(col1_x, INDIGO_PRIMARY, 1, "РІШЕННЯ ДЛЯ ПРОДУКТУ", decision_summary, decision_bullets, max_bullets=3)

    # Column 2: Signals & Anomalies
    render_column(col2_x, TEAL_PRIMARY, 2, "СИГНАЛИ ТА АНОМАЛІЇ", None, signals, max_bullets=4)

    # Column 3: Limitations
    render_column(col3_x, SLATE_PRIMARY, 3, "МЕЖІ ДОВІРИ ТА ОБМЕЖЕННЯ", None, limits, max_bullets=4)

    # ═══ Save PDF ═══
    try:
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        pdf.output(output_path)
        print(json.dumps({"status": "success", "output": output_path}), file=sys.stdout)
        sys.stderr.write(f"Report saved → {output_path}\n")
    except Exception as e:
        print(json.dumps({"error": f"Failed to save report: {str(e)}"}), file=sys.stdout)
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
