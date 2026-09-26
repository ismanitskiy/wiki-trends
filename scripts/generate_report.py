# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fpdf2>=2.7",
#     "matplotlib",
#     "numpy",
# ]
# ///
"""
generate_report.py — Premium Portrait A4 PDF for Wiki Trends Agent Skill.

Layout (Portrait A4, 210×297mm):
  Zone 1 — HERO HEADER   (0–68mm)    Dark navy gradient, giant KPI numbers per dataset
  Zone 2 — MAIN CHART    (70–158mm)  Full-width Tableau-style time-series chart
  Zone 3 — MINI CHARTS   (161–210mm) YoY % bar chart  +  Seasonality monthly chart
  Zone 4 — INSIGHT CARDS (213–286mm) Strategic conclusion · Key signals · Data quality
  Zone 5 — FOOTER        (288–297mm)
"""
import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# ═══════════════════════════════════════════════════════════════
# Design Tokens
# ═══════════════════════════════════════════════════════════════
# All fpdf2 colours are (R, G, B) int tuples 0-255
NAVY        = (15,  23,  42)    # #0F172A — hero header dark end
NAVY_MID    = (30,  58, 138)    # #1E3A8A — hero header light end
INDIGO      = (79,  70, 229)    # #4F46E5 — primary accent
INDIGO_BG   = (238, 242, 255)   # #EEF2FF
TEAL        = (13, 148, 136)    # #0D9488 — secondary accent
PAGE_BG     = (248, 250, 252)   # #F8FAFC
CARD_BG     = (255, 255, 255)
BORDER      = (226, 232, 240)   # slate-200
T400        = (148, 163, 184)   # slate-400  (muted)
T500        = (100, 116, 139)   # slate-500
T700        = (51,  65,  85)    # slate-700  (body)
T900        = (15,  23,  42)    # slate-900  (headings)
WHITE       = (255, 255, 255)
WHITE_DIM   = (226, 232, 240)   # slightly muted white (on dark)
WHITE_MUTED = (148, 163, 184)   # very muted white (on dark)

GREEN_BG = (220, 252, 231);  GREEN_T = (22, 101, 52)
RED_BG   = (255, 228, 230);  RED_T   = (159, 18,  57)

# Dataset accent colors — Tableau 10 inspired
DS_RGB = [(78, 121, 167), (225, 87, 89), (118, 183, 178), (242, 142, 43)]
DS_HEX = ['#4E79A7',      '#E15759',     '#76B7B2',        '#F28E2B']

# Insight card left-border colors
INSIGHT_ACCENTS = [INDIGO, TEAL, (100, 116, 139)]

# Layout constants (mm)
PW = 210;  PH = 297
ML = 10;   MR = 10
CW = PW - ML - MR                 # 190mm usable width

HERO_Y,  HERO_H  = 0,   68
CHART_Y, CHART_H = 70,  88
MINI_Y,  MINI_H  = 161, 50
INS_Y             = 214
INS_CARD_H        = 23
INS_GAP           = 2.5
FOOTER_Y          = 288


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _s(v) -> str:
    return str(v) if v is not None else "—"

def _n(n) -> str:
    """Format number with thin-space thousands separator."""
    if n is None:
        return "—"
    return f"{int(n):,}".replace(",", "\u2009")   # thin space

def _conf(raw) -> str:
    m = {"висока": "висока", "середня": "середня", "низька": "низька",
         "high": "висока", "medium": "середня", "low": "низька"}
    return m.get(str(raw).lower(), _s(raw))


# ═══════════════════════════════════════════════════════════════
# PDF Class
# ═══════════════════════════════════════════════════════════════

class PremiumPDF(FPDF):
    def __init__(self, ff="DejaVu"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.ff = ff
        self.set_auto_page_break(auto=False)

    # ── Hero ─────────────────────────────────────────────────

    def _hero_bg(self):
        """Simulate navy→indigo vertical gradient with thin strips."""
        steps = 16
        r1, g1, b1 = NAVY
        r2, g2, b2 = NAVY_MID
        sh = HERO_H / steps
        for i in range(steps):
            t = i / max(steps - 1, 1) * 0.45   # blend only 45%
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            self.set_fill_color(r, g, b)
            self.rect(0, i * sh, PW, sh + 0.5, style="F")

    def draw_hero(self, title: str, datasets: list, now_str: str):
        self._hero_bg()

        # Top indigo accent stripe
        self.set_fill_color(*INDIGO)
        self.rect(0, 0, PW, 2.5, style="F")

        # Pill badge — top left
        self.set_font(self.ff, "B", 6.5)
        pill_lbl = "WIKIPEDIA MARKET INTELLIGENCE"
        pw = self.get_string_width(pill_lbl) + 8
        self.set_fill_color(*INDIGO)
        self.rect(ML, 7, pw, 5, style="F", round_corners=True, corner_radius=2.5)
        self.set_text_color(*WHITE)
        self.set_xy(ML, 7 + 1)
        self.cell(pw, 3, pill_lbl, align="C")

        # Date metadata — top right
        self.set_font(self.ff, "", 7.5)
        self.set_text_color(*WHITE_MUTED)
        self.set_xy(ML, 7)
        self.cell(CW, 5, f"Дата: {now_str}  •  Вибірка: 24 міс  •  Wikimedia REST API", align="R")

        # Title
        self.set_xy(ML, 14)
        self.set_font(self.ff, "B", 16)
        self.set_text_color(*WHITE)
        self.cell(CW, 7, _s(title))

        # Subtitle separator
        self.set_draw_color(*INDIGO)
        self.set_line_width(0.25)
        self.line(ML, 23, PW - MR, 23)

        # KPI blocks — split evenly for up to 3 datasets
        n = min(len(datasets), 3)
        if n == 0:
            return
        bw = CW / n
        for i, ds in enumerate(datasets[:3]):
            bx = ML + i * bw
            self._hero_kpi(bx, 26, bw, ds, i)
            if i < n - 1:
                # vertical divider
                self.set_draw_color(79, 70, 229)
                self.set_line_width(0.2)
                self.line(bx + bw, 27, bx + bw, 66)

    def _hero_kpi(self, x: float, y: float, w: float, ds: dict, idx: int):
        article = ds.get("article_display", "—")
        project = ds.get("project", "—")
        lang    = project.split(".")[0].upper() if "." in project else project[:3].upper()
        total   = ds.get("total_views", 0)
        avg     = ds.get("avg_views", 0)
        trend   = ds.get("trend", {})
        pct     = trend.get("change_percent_total", 0.0)
        r2      = trend.get("r_squared", 0.0)
        conf    = _conf(trend.get("confidence", "—"))

        # Article name
        self.set_xy(x + 4, y)
        self.set_font(self.ff, "B", 9.5)
        self.set_text_color(*WHITE_DIM)
        # Truncate long article names
        max_chars = int(w / 2.6)
        disp = article if len(article) <= max_chars else article[:max_chars - 1] + "…"
        self.cell(w - 6, 5, _s(disp))

        # Language pill
        dc = DS_RGB[idx % len(DS_RGB)]
        self.set_fill_color(*dc)
        lpw = self.get_string_width(lang) + 5
        self.rect(x + 4, y + 6, lpw, 4, style="F", round_corners=True, corner_radius=2)
        self.set_font(self.ff, "B", 6)
        self.set_text_color(*WHITE)
        self.set_xy(x + 4, y + 6.5)
        self.cell(lpw, 3, lang, align="C")

        # TOTAL label
        self.set_xy(x + 4, y + 12.5)
        self.set_font(self.ff, "", 6.5)
        self.set_text_color(*WHITE_MUTED)
        self.cell(w - 8, 3, "ЗАГАЛЬНІ ПЕРЕГЛЯДИ")

        # Giant number
        self.set_xy(x + 4, y + 16)
        self.set_font(self.ff, "B", 23)
        self.set_text_color(*WHITE)
        self.cell(w - 8, 10, _n(total))

        # Avg /mo label
        self.set_xy(x + 4, y + 27)
        self.set_font(self.ff, "", 7.5)
        self.set_text_color(*WHITE_MUTED)
        self.cell(w - 8, 3.5, f"ср. {_n(int(avg))} / місяць")

        # Trend badge
        is_up   = pct > 0
        bbg     = GREEN_BG if is_up else RED_BG
        btc     = GREEN_T  if is_up else RED_T
        arrow   = "\u25B2" if is_up else "\u25BC"
        blabel  = f"{arrow} {pct:+.1f}%"
        bw_badge = max(26, self.get_string_width(blabel) + 7)
        bh = 5.5
        by = y + 32
        self.set_fill_color(*bbg)
        self.set_draw_color(*bbg)
        self.rect(x + 4, by, bw_badge, bh, style="F", round_corners=True, corner_radius=2.5)
        self.set_font(self.ff, "B", 8)
        self.set_text_color(*btc)
        self.set_xy(x + 4, by + (bh - 3.2) / 2)
        self.cell(bw_badge, 3.2, blabel, align="C")

        # R² + confidence alongside badge
        self.set_xy(x + 4 + bw_badge + 2.5, by + (bh - 3.2) / 2)
        self.set_font(self.ff, "", 6.5)
        self.set_text_color(*WHITE_MUTED)
        self.cell(40, 3.2, f"R²={r2:.2f}  •  {conf}")

    # ── Chart zone ───────────────────────────────────────────

    def draw_chart_zone(self, chart_path: str):
        y, h = CHART_Y, CHART_H
        self.set_fill_color(*CARD_BG)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.2)
        self.rect(ML, y, CW, h, style="DF", round_corners=True, corner_radius=3)

        # Section label
        self.set_xy(ML + 5, y + 3.5)
        self.set_font(self.ff, "B", 7)
        self.set_text_color(*T500)
        self.cell(CW, 3.5, "ДИНАМІКА ПЕРЕГЛЯДІВ  •  ЧАСОВИЙ РЯД 24 МІСЯЦІ")

        if chart_path and os.path.exists(chart_path):
            try:
                self.image(chart_path, x=ML + 2, y=y + 8, w=CW - 4, h=h - 10)
            except Exception as e:
                sys.stderr.write(f"Warning: chart embed failed: {e}\n")

    # ── Mini charts zone ─────────────────────────────────────

    def draw_mini_zone(self, yoy_path: str | None, season_path: str | None):
        y, h = MINI_Y, MINI_H

        # Light band background
        self.set_fill_color(*PAGE_BG)
        self.rect(0, y - 2, PW, h + 4, style="F")

        cw = (CW - 5) / 2        # ~92.5mm per card
        ch = h - 4                # card height

        configs = [
            (yoy_path,    "РІК ДО РОКУ  (YoY ЗМІНА %)"),
            (season_path, "СЕЗОННІСТЬ ПО МІСЯЦЯХ"),
        ]
        for i, (path, label) in enumerate(configs):
            cx = ML + i * (cw + 5)
            self.set_fill_color(*CARD_BG)
            self.set_draw_color(*BORDER)
            self.set_line_width(0.2)
            self.rect(cx, y, cw, ch, style="DF", round_corners=True, corner_radius=3)

            # Left accent strip
            bar_c = [INDIGO, TEAL][i]
            self.set_fill_color(*bar_c)
            self.rect(cx, y, 2.5, ch, style="F", round_corners=True, corner_radius=1.5)

            # Label
            self.set_xy(cx + 5, y + 3.5)
            self.set_font(self.ff, "B", 7)
            self.set_text_color(*bar_c)
            self.cell(cw - 8, 3.5, label)

            if path and os.path.exists(path):
                try:
                    self.image(path, x=cx + 2.5, y=y + 9, w=cw - 5, h=ch - 11)
                except Exception as e:
                    sys.stderr.write(f"Warning: mini chart {i} embed failed: {e}\n")

    # ── Insight cards ────────────────────────────────────────

    def draw_insights(self, datasets: list, comparison: dict, limitations: list):
        for i, (title, lines, accent) in enumerate(_build_insights(datasets, comparison, limitations)):
            cy = INS_Y + i * (INS_CARD_H + INS_GAP)

            # Card background
            self.set_fill_color(*CARD_BG)
            self.set_draw_color(*BORDER)
            self.set_line_width(0.2)
            self.rect(ML, cy, CW, INS_CARD_H, style="DF", round_corners=True, corner_radius=2.5)

            # Left accent bar
            self.set_fill_color(*accent)
            self.rect(ML, cy, 4, INS_CARD_H, style="F", round_corners=True, corner_radius=2)

            # Title
            self.set_xy(ML + 7, cy + 4)
            self.set_font(self.ff, "B", 9)
            self.set_text_color(*accent)
            self.cell(CW - 10, 4.5, _s(title))

            # Body (up to 2 lines of informative text)
            by = cy + 9.5
            for line in lines[:2]:
                if by >= cy + INS_CARD_H - 2:
                    break
                self.set_xy(ML + 7, by)
                self.set_font(self.ff, "", 8.5)
                self.set_text_color(*T700)
                self.multi_cell(CW - 10, 4, _s(line),
                                new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                by = min(self.get_y() + 0.5, cy + INS_CARD_H - 2)

    # ── Footer ───────────────────────────────────────────────

    def draw_footer(self):
        self.set_draw_color(*BORDER)
        self.set_line_width(0.25)
        self.line(ML, FOOTER_Y, PW - MR, FOOTER_Y)
        self.set_xy(ML, FOOTER_Y + 2.5)
        self.set_font(self.ff, "", 6.5)
        self.set_text_color(*T400)
        self.cell(CW, 3.5,
                  "wiki-trends  •  Agent Skills  •  Автономний AI-аналітик ринкового попиту  •  Дані: Wikimedia REST API (CC BY-SA)",
                  align="C")


# ═══════════════════════════════════════════════════════════════
# Insight content builder
# ═══════════════════════════════════════════════════════════════

def _build_insights(datasets, comparison, limitations):
    """Return list of (title, [line1, line2], accent_color) for 3 insight cards."""

    # ── Card 1: Strategic conclusion ──
    rec = ""
    if isinstance(comparison, dict):
        rec = comparison.get("recommendation", "")
    if not rec and datasets:
        d0 = datasets[0]
        t = d0.get("trend", {})
        dir_uk = "зростання" if t.get("direction") == "growing" else "спад"
        rec = f"Тема «{d0.get('article_display')}» демонструє {dir_uk} інтересу: {t.get('change_percent_total', 0):+.1f}%."

    line2 = ""
    if isinstance(comparison, dict):
        fg = comparison.get("fastest_growing", {})
        la = comparison.get("largest_audience", {})
        if fg and la:
            line2 = (f"Відносний лідер росту: {fg.get('project','—')}. "
                     f"Найбільша аудиторія: {la.get('project','—')} "
                     f"({_n(int(la.get('avg_monthly_views', 0)))} переглядів/міс).")

    card1 = ("СТРАТЕГІЧНИЙ ВИСНОВОК", [rec, line2] if line2 else [rec], INDIGO)

    # ── Card 2: Key signals ──
    signals = []
    for ds in datasets:
        art = ds.get("article_display", "")
        proj = ds.get("project", "").split(".")[0].upper()
        yoy_list = ds.get("yoy_changes", [])
        anom_list = ds.get("anomalies", [])
        season = ds.get("seasonality", {})

        # YoY changes (most recent 2)
        for yc in yoy_list[:2]:
            signals.append(f"{proj} ({art}): {yc.get('period')} → {yc.get('change_percent', 0):+.1f}%")

        # Anomalies
        for a in anom_list[:1]:
            signals.append(f"{proj}: пік {a.get('timestamp')} — {_n(a.get('views', 0))} переглядів  (Z={a.get('z_score', 0):.1f}σ)")

        # Seasonality
        if isinstance(season, dict) and season.get("detected"):
            peaks = season.get("peak_months", [])
            troughs = season.get("trough_months", [])
            if peaks:
                signals.append(f"{proj}: пікові місяці — {', '.join(str(m) for m in peaks[:6])}")
            elif troughs:
                signals.append(f"{proj}: мінімальний сезон — місяці {', '.join(str(m) for m in troughs[:4])}")

    if not signals:
        signals = ["Значних сигналів не виявлено."]

    card2 = ("КЛЮЧОВІ СИГНАЛИ ТА АНОМАЛІЇ", signals[:2], TEAL)

    # ── Card 3: Data quality ──
    qual = []
    for ds in datasets[:2]:
        t = ds.get("trend", {})
        proj = ds.get("project", "").split(".")[0].upper()
        r2 = t.get("r_squared", 0.0)
        conf = _conf(t.get("confidence", "—"))
        total = ds.get("total_views", 0)
        n_pts = len([1 for _ in range(24)])  # proxy — 24-month window
        qual.append(f"{proj}: R²={r2:.2f} ({conf} тренд), {_n(total)} переглядів за вибіркою")

    if not qual:
        qual = limitations[:2] if limitations else ["Дані Wikimedia API відфільтровано від ботів (agent=user)."]

    card3 = ("ЯКІСТЬ ДАНИХ", qual[:2], (100, 116, 139))

    return [card1, card2, card3]


# ═══════════════════════════════════════════════════════════════
# Mini-chart generators (matplotlib)
# ═══════════════════════════════════════════════════════════════

def _yoy_chart(datasets: list, tmp_dir: str) -> str | None:
    """Grouped vertical bar chart of YoY % changes per dataset."""
    out = os.path.join(tmp_dir, "_yoy.png")

    # Collect union of all period labels
    all_periods: list[str] = []
    for ds in datasets:
        for yc in ds.get("yoy_changes", []):
            p = yc.get("period", "")
            if p and p not in all_periods:
                all_periods.append(p)
    all_periods.sort()
    if not all_periods:
        return None

    fig, ax = plt.subplots(figsize=(4.3, 2.4), dpi=180)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    n_ds = min(len(datasets), 2)
    n_p  = len(all_periods)
    bw   = 0.38
    x    = np.arange(n_p)

    for i, ds in enumerate(datasets[:2]):
        vals = []
        for period in all_periods:
            pct = 0.0
            for yc in ds.get("yoy_changes", []):
                if yc.get("period") == period:
                    pct = yc.get("change_percent", 0.0)
                    break
            vals.append(pct)

        offset = (i - (n_ds - 1) / 2) * bw
        bars = ax.bar(x + offset, vals, bw * 0.88,
                      color=DS_HEX[i % len(DS_HEX)], alpha=0.85,
                      edgecolor='white', linewidth=0.6)

        for bar, val in zip(bars, vals):
            ax.annotate(f"{val:+.0f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 4 if val >= 0 else -12),
                        textcoords="offset points",
                        ha='center', va='bottom' if val >= 0 else 'top',
                        fontsize=7.5, fontweight='bold', color='#1E293B')

    ax.axhline(0, color='#94A3B8', linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([p.replace(" vs ", "\nvs ") for p in all_periods],
                       fontsize=7.5, color='#6B7280')
    ax.tick_params(axis='both', length=0)
    ax.set_ylabel("Зміна %", fontsize=7, color='#94A3B8', labelpad=3)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.yaxis.grid(True, color='#F3F4F6', linewidth=0.7)
    ax.set_axisbelow(True)

    handles = [mpatches.Patch(color=DS_HEX[i],
                              label=datasets[i].get("project", "").split(".")[0].upper())
               for i in range(min(n_ds, len(datasets)))]
    ax.legend(handles=handles, frameon=False, fontsize=7,
              labelcolor='#4B5563', loc='upper right')

    plt.tight_layout(pad=0.4)
    try:
        plt.savefig(out, dpi=180, bbox_inches='tight',
                    facecolor='#FFFFFF', edgecolor='none')
    except Exception as e:
        sys.stderr.write(f"YoY chart error: {e}\n")
        return None
    finally:
        plt.close(fig)
    return out


def _seasonality_chart(datasets: list, pageviews_list: list, tmp_dir: str) -> str | None:
    """
    Monthly seasonality chart.
    If raw pageview data is provided: compute actual avg views per calendar month.
    Otherwise: render qualitative peak/trough coloring from analysis JSON.
    """
    out = os.path.join(tmp_dir, "_season.png")
    months     = list(range(1, 13))
    month_lbls = ['Січ','Лют','Бер','Кві','Тра','Чер',
                  'Лип','Сер','Вер','Жов','Лис','Гру']

    fig, ax = plt.subplots(figsize=(4.3, 2.4), dpi=180)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    n_ds = min(len(datasets), len(pageviews_list)) if pageviews_list else 1
    bw   = 0.38
    x    = np.arange(12)

    if pageviews_list:
        # Compute actual per-month averages from the raw time-series
        for i, (ds, pv) in enumerate(zip(datasets[:2], pageviews_list[:2])):
            buckets: dict[int, list[float]] = {}
            for pt in pv.get("data", []):
                ts = pt.get("timestamp", "")
                try:
                    m = int(ts[5:7]) if len(ts) >= 7 else int(ts[4:6])
                    buckets.setdefault(m, []).append(float(pt.get("views", 0)))
                except Exception:
                    pass

            avgs   = [float(np.mean(buckets.get(m, [0]))) for m in months]
            max_v  = max(avgs) if max(avgs) > 0 else 1
            normed = [v / max_v for v in avgs]

            offset = (i - (n_ds - 1) / 2) * bw
            ax.bar(x + offset, normed, bw * 0.88,
                   color=DS_HEX[i % len(DS_HEX)], alpha=0.82,
                   edgecolor='white', linewidth=0.5,
                   label=ds.get("project", "").split(".")[0].upper())
    else:
        # Qualitative: peak months in accent colour, troughs in light gray
        ds     = datasets[0]
        season = ds.get("seasonality", {})
        peaks  = set(season.get("peak_months", []))
        troughs= set(season.get("trough_months", []))

        bc, bh = [], []
        for m in months:
            if m in peaks:
                bc.append(DS_HEX[0]); bh.append(1.0)
            elif m in troughs:
                bc.append('#CBD5E1');  bh.append(0.3)
            else:
                bc.append(DS_HEX[0] + '70'); bh.append(0.62)

        ax.bar(x, bh, color=bc, edgecolor='white', linewidth=0.4)

    ax.set_xticks(x)
    ax.set_xticklabels(month_lbls, fontsize=7, color='#6B7280')
    ax.set_ylim(0, 1.22)
    ax.set_yticks([])
    ax.tick_params(axis='both', length=0)
    ax.set_ylabel("Відносний обсяг", fontsize=7, color='#94A3B8', labelpad=3)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.yaxis.grid(True, color='#F3F4F6', linewidth=0.6)
    ax.set_axisbelow(True)

    if pageviews_list and n_ds > 1:
        ax.legend(frameon=False, fontsize=7, labelcolor='#4B5563', loc='upper right')

    plt.tight_layout(pad=0.4)
    try:
        plt.savefig(out, dpi=180, bbox_inches='tight',
                    facecolor='#FFFFFF', edgecolor='none')
    except Exception as e:
        sys.stderr.write(f"Seasonality chart error: {e}\n")
        return None
    finally:
        plt.close(fig)
    return out


# ═══════════════════════════════════════════════════════════════
# Font setup
# ═══════════════════════════════════════════════════════════════

def _setup_font(pdf: FPDF) -> str:
    sd   = os.path.dirname(os.path.abspath(__file__))
    fd   = os.path.join(sd, "..", "assets", "fonts")
    reg  = os.path.join(fd, "DejaVuSans.ttf")
    bold = os.path.join(fd, "DejaVuSans-Bold.ttf")
    ital = os.path.join(fd, "DejaVuSans-Oblique.ttf")
    if os.path.exists(reg):
        try:
            pdf.add_font("DejaVu", "",   reg)
            pdf.add_font("DejaVu", "B",  bold if os.path.exists(bold) else reg)
            pdf.add_font("DejaVu", "I",  ital if os.path.exists(ital) else reg)
            pdf.add_font("DejaVu", "BI", bold if os.path.exists(bold) else reg)
            return "DejaVu"
        except Exception as e:
            sys.stderr.write(f"Font load warning: {e}\n")
    return "helvetica"


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Generate premium Portrait A4 Wikipedia Trends PDF report")
    parser.add_argument("--analysis",  required=True,
                        help="JSON from analyze_trends.py")
    parser.add_argument("--chart",     required=True,
                        help="PNG from generate_chart.py")
    parser.add_argument("--pageviews", action="append",
                        help="Raw pageview JSON files (for seasonality chart). "
                             "Can be specified multiple times.")
    parser.add_argument("--title",  default="Аналіз ринкового інтересу: Wikipedia Trends")
    parser.add_argument("--output", default="report.pdf")
    args = parser.parse_args()

    # Load analysis JSON
    try:
        with open(args.analysis, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Cannot read {args.analysis}: {e}"}))
        sys.exit(1)

    datasets    = data.get("datasets", [])
    comparison  = data.get("comparison", {}) or {}
    limitations = data.get("limitations", [])

    # Load optional raw pageview files
    pageviews_list: list[dict] = []
    if args.pageviews:
        for p in args.pageviews:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    pageviews_list.append(json.load(f))
            except Exception as e:
                sys.stderr.write(f"Warning: cannot load {p}: {e}\n")

    # Generate mini charts
    tmp = tempfile.mkdtemp()
    yoy_path    = _yoy_chart(datasets, tmp)
    season_path = _seasonality_chart(datasets, pageviews_list or [], tmp)

    # Build PDF
    pdf = PremiumPDF()
    ff  = _setup_font(pdf)
    pdf.ff = ff
    pdf.add_page()

    # Page background
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, 0, PW, PH, style="F")

    now_str = datetime.now().strftime("%d.%m.%Y  •  %H:%M")

    pdf.draw_hero(args.title, datasets, now_str)
    pdf.draw_chart_zone(args.chart)
    pdf.draw_mini_zone(yoy_path, season_path)
    pdf.draw_insights(datasets, comparison, limitations)
    pdf.draw_footer()

    # Save
    try:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        pdf.output(args.output)
        print(json.dumps({"status": "success", "output": args.output}))
        sys.stderr.write(f"Report saved → {args.output}\n")
    except Exception as e:
        print(json.dumps({"error": f"Failed to save: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
