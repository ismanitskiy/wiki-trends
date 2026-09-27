---
name: wiki-trends
description: >-
  Analyze Wikipedia page view trends across languages to evaluate topic interest
  for B2C product decisions. Use when asked to compare topic popularity across
  Wikipedia language editions, assess whether interest in a topic is growing or
  declining, identify promising markets or languages for product launches, or
  prepare data-driven research reports on audience interest. Generates charts
  and shareable one-page PDF reports.
license: MIT
compatibility: Requires Python 3.10+ and uv (https://docs.astral.sh/uv/)
metadata:
  version: "1.0"
---

### Section 1: Overview
wiki-trends is an Agent Skill for analyzing Wikipedia page view data across different language editions to evaluate topic interest and market viability. It provides tools to resolve cross-language article titles, fetch time-series view data, and generate analytical reports and charts. This helps in making data-driven B2C product decisions by identifying audience growth or decline in specific language communities.

### Section 2: Workflow
The agent will follow these steps to fulfill user requests:

1. **Understand the request** — identify: topic, target languages (if not specified, suggest uk, pl, en, de as defaults), time period (default: last 2 years), what the user wants to know.
2. **Resolve article titles** — run `uv run scripts/resolve_articles.py --query "<topic>" --source-lang en --target-langs <langs>`.
   - *Canonical selection rule*: Pick **exactly ONE canonical article per target language** for market comparisons. Do not fetch multiple synonyms (e.g. brand + chemical name like `Ozempic` and `Semaglutide`) for the same language in a cross-market comparison.
   - *Not-found tracking*: If a target language has no article (returned in `not_found`), record it.
3. **Fetch pageview data** — for each resolved canonical article, run:
   - *Default (recommended)*: `uv run scripts/fetch_pageviews.py --project <project> --article <article> --output <file.json>`. Omitting `--start`/`--end` automatically fetches the last **24 full completed calendar months** (2 complete 12-month annual cycles).
   - *Custom dates*: If specifying `--start` and `--end` for a 2-year window, ensure exactly 24 months: from 1st of month $M$ to end of month $M-1$ two years later (e.g. `--start 20220601 --end 20240531`). Never use the same month for both start and end 2 years apart (e.g. `20220619` to `20240619` yields 25 months due to inclusive month boundaries).
4. **Analyze trends** — run `uv run scripts/analyze_trends.py --input <file1.json> ... [--not-found <lang1,lang2>] --output analysis.json`.
5. **Generate chart** — run `uv run scripts/generate_chart.py --input <file1.json> ... --title "<descriptive title>" --output chart.png --trend-line`.
6. **Generate report (if requested)** — run `uv run scripts/generate_report.py --analysis analysis.json --chart chart.png [--not-found <lang1,lang2>] [--topic "<Українська назва теми>"] --output report.pdf`.
   - **Ukrainian Topic Title Standard**: The topic name in the header must **ALWAYS be written in Ukrainian** (e.g. `Фондовий ринок — IT vs KO Wikipedia`, `Інтервальне голодування — DE vs EN Wikipedia`), even when comparing non-Ukrainian language editions. Pass `--topic "Тема"` (e.g. `--topic "Фондовий ринок"`). The language edition pills (`IT`, `KO`, `DE`, `EN`) already clearly designate the markets.
   - Standard report title format: `{Topic} — {LANG1} vs {LANG2} Wikipedia` (rendered without quotes, featuring a soft pastel indigo topic block and color-coded language pills matching KPI cards).
   - For missing languages passed via `--not-found`, the report automatically renders a dedicated placeholder card (`0 / міс`, `Ознака несформованого ринку`) preserving grid symmetry.
7. **Present findings** — summarize key insights, present chart, mention limitations. If the user asked for a report, provide the PDF.

### Section 3: Available scripts
Run any script with `--help` to see all options.

- `scripts/resolve_articles.py` — Resolves topic names across Wikipedia languages
- `scripts/fetch_pageviews.py` — Downloads pageview time-series from Wikimedia API (supports auto 24-month calculation)
- `scripts/analyze_trends.py` — Computes trends, seasonality, anomalies, confidence (supports `--not-found`)
- `scripts/generate_chart.py` — Creates comparison line charts (PNG)
- `scripts/generate_report.py` — Generates one-page PDF report (supports `--not-found`)

### Section 4: Handling follow-up queries
- If the user wants to change the time period: re-run fetch + analyze + chart
- If the user wants to add more languages: resolve + fetch for new ones, then re-analyze with all files
- If the user wants to compare different topics: start a new workflow for each topic
- Reuse previously fetched data files when possible to avoid redundant API calls

### Section 5: Gotchas
- **24 Months Standard (2 Complete Annual Cycles):** Monthly time-series must have **exactly 24 full months** (e.g. 06.2022 – 05.2024). Having 25 months happens when an agent passes identical start and end months (e.g. `20220619` to `20240619`), which includes both June 2022 and June 2024. This distorts Year-over-Year (YoY) comparison (12 months vs 13 months) and seasonality. Always rely on `fetch_pageviews.py` auto-dates or align dates to $M$ and $M-1$.
- **Language editions vs Countries:** Wikipedia per-article Pageviews API operates strictly at the **language project level** (`pt.wikipedia.org`, `es.wikipedia.org`, `en.wikipedia.org`), NOT sovereign borders. For example, `pt` covers Brazil and Portugal; `es` covers Spain and Latin America; `en` is global English. Reports should reflect language domains (`PT vs ES Wikipedia`, `UK vs EN Wikipedia`).
- Wikipedia article titles are case-sensitive (except first letter). Always use resolve_articles.py first.
- The Wikimedia API has data starting from July 2015 only.
- Views reflect reading interest, NOT purchase intent. Always mention this limitation.
- January often shows spikes (New Year resolutions topics). Account for seasonality.
- Small Wikipedia editions (e.g., Kazakh) may have very low view counts — warn the user about statistical reliability.
- If resolve_articles.py returns not_found for a language, the article does not exist in that Wikipedia edition. Pass this language to `--not-found` in `analyze_trends.py` and `generate_report.py` to render the placeholder card and highlight market vacuum.

### Section 6: Interpreting results
- **confidence "high"** = strong, consistent trend — reliable for decisions
- **confidence "medium"** = trend exists but with variance — needs additional validation
- **confidence "low"** = insufficient data or too much noise — not reliable alone
- Always present limitations from the analysis output to the user

### Section 7: Ukrainian Typography & PDF Report Standards
When generating text or configuring report layouts, strictly follow Ukrainian publishing standards:
- **No-break numbers (NBSP):** Thousand separators in figures (`3 176`, `10 494`) and number-unit pairs (`1 місяць`, `12.4x`, `(Z = 3.17)`) must use non-breaking spaces (`\u00a0`). Never allow digits or units to be torn across lines.
- **Preposition binding:** Bind 1-2 letter prepositions (`у`, `в`, `і`, `та`, `на`, `за`, `до`) with `\u00a0` to avoid dangling words at line ends.
- **Hyphenation discipline (§ 159):** Never hyphenate short words (< 8 letters such as `місяць`, `частка`, `подій`). Soft hyphens (`\u00ad`) are reserved only for long words (9+ letters) at valid syllable boundaries.
- **Orphan avoidance:** Prevent single-word orphan lines at the end of paragraphs. Calibrate sentences to fill 2 balanced lines (~75–85 chars).
- **English file naming:** Name output PDFs descriptively: `wikipedia_trends_{topic}_{langs}_period_{start}_to_{end}_date_{date}.pdf`.
- For full details, see `references/ANALYSIS_GUIDE.md` Section 6.

