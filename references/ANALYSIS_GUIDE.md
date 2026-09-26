# Analysis Guide: Interpreting Wikipedia Trends

This guide provides a methodology for interpreting Wikipedia trends data to make B2C product decisions.

## 1. Interpreting Pageview Trends
- **R² Values (Coefficient of Determination):** Used to assess the fit of a trend line. An R² close to 1.0 indicates a highly predictable, consistent trend. An R² below 0.3 suggests high variance or noise, meaning the trend line is not a reliable predictor of future interest.
- **Trend Direction:** A positive slope indicates growing interest, while a negative slope indicates declining interest. Combine this with the R² value to determine confidence.

## 2. Seasonality Patterns
Wikipedia traffic is highly susceptible to real-world seasonality:
- **Academic Calendar:** Topics related to science, history, and literature often dip in summer and peak during exam seasons (May/June and November/December).
- **Holidays:** Topics like "Diet" or "Fitness" spike in January (New Year resolutions).
- **News Cycles:** Sudden spikes usually indicate news events, not sustainable long-term interest. Smooth out these spikes using moving averages to see the underlying trend.

## 3. Correlation with Product Demand
- **Positive Correlation:** Research-heavy purchases (e.g., "Solar panels", "Electric bicycles") often correlate with Wikipedia views as consumers educate themselves before buying.
- **Weak Correlation:** Impulse buys, brand-specific searches, or highly commercialized terms usually don't correlate with Wikipedia traffic (users go straight to Amazon/Google).
- **Limitation:** Wikipedia views reflect *curiosity* and *reading interest*, not necessarily *purchase intent*.

## 4. Comparing Across Language Editions
Comparing absolute view counts across languages is misleading because Wikipedia editions vary greatly in size and audience.
- **Normalization:** Always normalize pageviews by the total project traffic (e.g., views per 1 million total Wikipedia views in that language) or compare relative growth rates (percentages) rather than absolute numbers.
- **Language Sizes:** English Wikipedia is massive; views will always be higher. A topic getting 10,000 views/month in Ukrainian might be highly significant, whereas 10,000 views/month in English is negligible.

## 5. Statistical Significance and Red Flags
- **Low View Counts:** For small Wikipedia editions (e.g., Kazakh, Georgian), view counts might be in the single or double digits per month. Trends here lack statistical significance.
- **Bot Traffic:** Always ensure API requests use `agent=user`. Even then, some scraper bots disguise as users. Watch out for sudden, perfectly flat spikes (e.g., exactly 500 views every day).
- **Vandalism Spikes:** Sometimes an article is linked from a high-traffic source (like Reddit) or vandalized, causing a short-term massive spike. Use median-based anomaly detection to filter these out.
