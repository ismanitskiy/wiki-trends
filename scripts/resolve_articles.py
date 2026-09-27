# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
# ]
# ///

import argparse
import json
import sys

import requests

HEADERS = {
    "User-Agent": "WikiTrendsSkill/1.0 (wiki-trends-skill@example.com)"
}

def search_article(lang, query):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json"
    }
    sys.stderr.write(f"Searching for '{query}' in {lang}.wikipedia.org...\n")
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("query", {}).get("search", [])
        if results:
            return results[0]["title"]
    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"Error searching in {lang}: {e}\n")
    return None

def get_wikidata_sitelinks(lang, title):
    """Fetch sitelinks across all languages using Wikidata entity linked to the article."""
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageprops",
        "ppprop": "wikibase_item",
        "format": "json"
    }
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=10)
        res.raise_for_status()
        pages = res.json().get("query", {}).get("pages", {})
        wikibase_item = None
        for pdata in pages.values():
            wikibase_item = pdata.get("pageprops", {}).get("wikibase_item")
            if wikibase_item:
                break

        if not wikibase_item:
            return {}

        wd_url = "https://www.wikidata.org/w/api.php"
        wd_params = {
            "action": "wbgetentities",
            "ids": wikibase_item,
            "props": "sitelinks",
            "format": "json"
        }
        wd_res = requests.get(wd_url, params=wd_params, headers=HEADERS, timeout=10)
        wd_res.raise_for_status()
        entities = wd_res.json().get("entities", {})
        sitelinks = entities.get(wikibase_item, {}).get("sitelinks", {})

        # Mapping from language code (e.g. 'pl' from 'plwiki') to title
        links = {}
        for site_key, site_val in sitelinks.items():
            if site_key.endswith("wiki") and not site_key.startswith("commons"):
                l_code = site_key[:-4]
                links[l_code] = site_val.get("title")
        return links
    except Exception as e:
        sys.stderr.write(f"Notice: Wikidata sitelink lookup failed: {e}\n")
        return {}

def get_langlinks(lang, title):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "langlinks",
        "lllimit": 500,
        "format": "json"
    }
    sys.stderr.write(f"Fetching langlinks for '{title}' in {lang}.wikipedia.org...\n")
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        links = {}
        for page_info in pages.values():
            for ll in page_info.get("langlinks", []):
                links[ll["lang"]] = ll["*"]
        return links
    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"Error fetching langlinks: {e}\n")
    return {}

def main():
    parser = argparse.ArgumentParser(description="Resolve article titles across Wikipedia language editions.")
    parser.add_argument("--query", required=True, help="Topic to search for")
    parser.add_argument("--source-lang", default="en", help="Source language code (default: en)")
    parser.add_argument("--target-langs", required=True, help="Comma-separated target language codes (e.g., uk,pl,cs)")
    parser.add_argument("--output", help="Output file path (default: stdout)")

    args = parser.parse_args()

    target_langs = [lang.strip().lower() for lang in args.target_langs.split(",") if lang.strip()]

    # 1. Search in source language
    source_title = search_article(args.source_lang, args.query)
    if not source_title:
        # Try direct capitalized query if search fails
        source_title = args.query.strip().capitalize()

    source_title_encoded = source_title.replace(" ", "_")

    # 2. Get langlinks from Wikipedia Action API
    langlinks = get_langlinks(args.source_lang, source_title)

    # 3. Augment with Wikidata sitelinks for comprehensive resolution
    wd_sitelinks = get_wikidata_sitelinks(args.source_lang, source_title)
    for l_code, l_title in wd_sitelinks.items():
        if l_code not in langlinks:
            langlinks[l_code] = l_title

    resolved = {}
    not_found = []

    for t_lang in target_langs:
        if t_lang == args.source_lang:
            resolved[t_lang] = {
                "title": source_title_encoded,
                "display_title": source_title,
                "project": f"{t_lang}.wikipedia.org"
            }
            continue

        if t_lang in langlinks:
            target_title = langlinks[t_lang]
            resolved[t_lang] = {
                "title": target_title.replace(" ", "_"),
                "display_title": target_title,
                "project": f"{t_lang}.wikipedia.org"
            }
        else:
            # Verified check: check if article exists on target language wiki
            sys.stderr.write(f"Checking if '{args.query}' directly exists on {t_lang}.wikipedia.org...\n")
            target_title = search_article(t_lang, args.query)
            # Only accept if title is closely relevant (contains query or vice-versa)
            if target_title and (args.query.lower() in target_title.lower() or target_title.lower() in args.query.lower()):
                resolved[t_lang] = {
                    "title": target_title.replace(" ", "_"),
                    "display_title": target_title,
                    "project": f"{t_lang}.wikipedia.org"
                }
            else:
                not_found.append(t_lang)

    result = {
        "query": args.query,
        "source": {
            "lang": args.source_lang,
            "title": source_title_encoded,
            "display_title": source_title,
            "project": f"{args.source_lang}.wikipedia.org"
        },
        "resolved": resolved,
        "not_found": not_found
    }

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json + "\n")
            sys.stderr.write(f"Data saved to {args.output}\n")
        except OSError as e:
            sys.stderr.write(f"Error writing to file: {e}\n")
            sys.exit(1)
    else:
        print(output_json)

if __name__ == "__main__":
    main()
