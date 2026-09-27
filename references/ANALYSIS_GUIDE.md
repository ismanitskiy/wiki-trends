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

## 6. Стандарти української типографіки та верстки у звітах (Typography & Layout Standards)

При генерації аналітичних текстів для PDF-звітів агент та аналітичні скрипти повинні суворо дотримуватися видавничих стандартів української типографіки (за ДСТУ та Українським правописом § 159):

### 1. Нерозривні пробіли (NBSP `\u00a0`)
* **Розряди тисяч у числах:** Усі числа з розрядами тисяч (`3 176`, `10 494`, `76 230`, `945 333`) повинні розділятися **нерозривним пробілом** (`\u00a0`). Категорично заборонено розривати числа між рядками (наприклад, залишати `3` в кінці рядка і переносити `176` на наступний).
* **Число та одиниця виміру/іменник:** Число завжди склеюється з супутньою одиницею чи іменником нерозривним пробілом: `1 місяць`, `24 місяці`, `3 176/міс`, `12.4x`, `3.3x`, `10 494 переглядів`.
* **Статистичні та математичні позначення:** Вирази `(Z = 3.17)`, `R² = 0.18`, `у 3.3x вище норми` повинні бути внутрішньо нерозривними.
* **Прийменники та сполучники:** Одно- та дволітерні прийменники (`в`, `у`, `і`, `та`, `на`, `за`, `до`, `по`, `з`, `із`, `як`, `не`, `чи`, `що`) привʼязуються до наступного слова нерозривним пробілом, щоб уникнути «висячих» прийменників на кінці рядка.

### 2. Офіційні правила перенесення слів в українській мові (§ 159)
* **Поділ на склади:** Слова переносяться за складами: `від-філь-тро-ва-но`, `ін-фор-ма-цій-ний`.
* **Заборона відриву однієї літери:** Заборонено залишати в кінці рядка або переносити на наступний одну літеру, навіть якщо вона становить окремий склад (не можна `о-зеро`, `ака-демія`; правильно: `озе-ро`, `акаде-мія`).
* **Неподільні звуки:** Буквосполучення `дж`, `дз` (коли вони позначають один звук), `йо`, `ьо` не розриваються (`ра-йон`, `польо-вий`).
* **Мʼякий знак та апостроф:** Не відриваються від попередньої приголосної (`сіль-це`, `бурʼ-ян`).

### 3. Дисципліна переносів у звітних картках (Executive Card Typography)
* **Заборона переносу коротких слів:** У компактних картках та звітах заборонено розривати дефісом слова довжиною до 7–8 літер (`місяць`, `частка`, `подій`, `норми`, `вибірці`, `липень`, `вересень`). Вони завжди переносяться цілими.
* **Лише довгі слова (9+ літер):** Дефісний перенос допускається лише для багатоскладових слів (`автоматизованих`, `відфільтровано`) за умови крайньої необхідності.
* **Запобігання «словам-сиротам» (Orphans/Widows):** Останній рядок абзацу чи пункту ніколи не повинен складатися з одного-двох коротких слів (наприклад, `у вибірці.`).
* **Калібрування довжини речень:** Кожен пункт у картці має формулюватися під ширину текстового блоку (~40–45 символів у рядку) так, щоб абзац складався з **рівно 2 збалансованих рядків** (сумарно ~75–85 символів) без візуальних «дірок» і без переносів.

