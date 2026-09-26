# Wikimedia API Reference

This document serves as a reference for interacting with Wikimedia APIs, specifically for resolving article links and fetching pageviews. Read this when encountering API issues.

## 1. Pageviews API
**Endpoint:** `GET https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{access}/{agent}/{article}/{granularity}/{start}/{end}`

### Parameters:
- `project`: Project domain (e.g., `en.wikipedia.org`, `uk.wikipedia.org`).
- `access`: Access method. Options: `all-access`, `desktop`, `mobile-app`, `mobile-web`. (Usually `all-access`).
- `agent`: User agent type. Options: `all-agents`, `user`, `spider`, `automated`. (Usually `user` to filter out bots).
- `article`: Article title, URL-encoded.
- `granularity`: Time granularity. Options: `daily`, `monthly`.
- `start`: Start timestamp in `YYYYMMDDHH` format (e.g., `2023010100`). First available data is July 2015.
- `end`: End timestamp in `YYYYMMDDHH` format (e.g., `2023123100`).

### Requirements:
- **User-Agent:** You must provide a descriptive User-Agent header: `User-Agent: WikiTrendsSkill/1.0 (wiki-trends-skill@example.com)`.
- **Rate Limits:** 100 requests per second per IP. Keep it well below this.

### Example curl:
```bash
curl -H "User-Agent: WikiTrendsSkill/1.0 (wiki-trends-skill@example.com)" \
     "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/Artificial_intelligence/monthly/2023010100/2023123100"
```

## 2. MediaWiki Action API (Langlinks & Search)
**Endpoint:** `GET https://{lang}.wikipedia.org/w/api.php`

Used for resolving cross-language links (finding the equivalent article in another language).

### Langlinks Query:
Retrieve language links for a specific title.
- Parameters: `?action=query&prop=langlinks&titles={title}&llprop=url|autonym&lllimit=500&format=json`

### Search Query:
Search for an article if the exact title is unknown.
- Parameters: `?action=query&list=search&srsearch={query}&format=json`

## 3. Common Error Codes
- **404 Not Found:** The article does not exist or the title is incorrectly capitalized (Wikipedia titles are case-sensitive except for the first letter). Try using the search API to find the correct title.
- **429 Too Many Requests:** Rate limit exceeded. Implement exponential backoff and retry.
- **400 Bad Request:** Incorrect date format or granularity. Ensure `YYYYMMDDHH`.

## 4. Redirects Caveat
Pageviews API does *not* automatically follow redirects or aggregate views across redirects. You must query the exact canonical title of the article. If an article was renamed, historical views might remain at the old title.
