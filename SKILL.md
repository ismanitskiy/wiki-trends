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

1. **Understand the request** — identify: topic, target languages (if not specified, suggest uk, pl, en, de as defaults), time period (default: last 2 years), what the user wants to know
2. **Resolve article titles** — run `uv run scripts/resolve_articles.py --query "<topic>" --source-lang en --target-langs <langs>`. If the topic is not in English, try searching in the appropriate language first.
3. **Fetch pageview data** — for each resolved article, run `uv run scripts/fetch_pageviews.py --project <project> --article <article> --start <YYYYMMDD> --end <YYYYMMDD> --granularity monthly --output <file.json>`. Default to last 2 years if no period specified.
4. **Analyze trends** — run `uv run scripts/analyze_trends.py --input <file1.json> --input <file2.json> --output analysis.json`
5. **Generate chart** — run `uv run scripts/generate_chart.py --input <file1.json> --input <file2.json> --title "<descriptive title>" --output chart.png --trend-line`
6. **Generate report (if requested)** — run `uv run scripts/generate_report.py --analysis analysis.json --chart chart.png --title "<title>" --output report.pdf`
7. **Present findings** — summarize key insights, present chart, mention limitations. If the user asked for a report, provide the PDF.

### Section 3: Available scripts
Run any script with `--help` to see all options.

- `scripts/resolve_articles.py` — Resolves topic names across Wikipedia languages
- `scripts/fetch_pageviews.py` — Downloads pageview time-series from Wikimedia API
- `scripts/analyze_trends.py` — Computes trends, seasonality, anomalies, confidence
- `scripts/generate_chart.py` — Creates comparison line charts (PNG)
- `scripts/generate_report.py` — Generates one-page PDF report

### Section 4: Handling follow-up queries
- If the user wants to change the time period: re-run fetch + analyze + chart
- If the user wants to add more languages: resolve + fetch for new ones, then re-analyze with all files
- If the user wants to compare different topics: start a new workflow for each topic
- Reuse previously fetched data files when possible to avoid redundant API calls

### Section 5: Gotchas
- Wikipedia article titles are case-sensitive (except first letter). Always use resolve_articles.py first.
- The Wikimedia API has data starting from July 2015 only.
- Views reflect reading interest, NOT purchase intent. Always mention this limitation.
- January often shows spikes (New Year resolutions topics). Account for seasonality.
- Small Wikipedia editions (e.g., Kazakh) may have very low view counts — warn the user about statistical reliability.
- If resolve_articles.py returns not_found for a language, the article likely doesn't exist in that Wikipedia edition. This itself is a signal (low interest in that language community).

### Section 6: Interpreting results
- **confidence "high"** = strong, consistent trend — reliable for decisions
- **confidence "medium"** = trend exists but with variance — needs additional validation
- **confidence "low"** = insufficient data or too much noise — not reliable alone
- Always present limitations from the analysis output to the user
