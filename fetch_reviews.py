"""Pull App Store data from Apple's public endpoints (standard library only).

- search_apps(term): find apps by name with the iTunes Search API
- lookup_app(app_id): name, developer, icon, etc. for one app
- fetch_reviews(app_id): the most recent reviews (up to 500) from the review RSS feed
"""
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "app-review-analyzer/1.0"}
MAX_PAGES = 10  # Apple's feed stops at 10 pages of 50 reviews


def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _app_info(r):
    return {
        "id": str(r["trackId"]),
        "name": r.get("trackName", ""),
        "developer": r.get("artistName", ""),
        "icon": r.get("artworkUrl100") or r.get("artworkUrl60", ""),
        "genre": r.get("primaryGenreName", ""),
        "rating": round(r.get("averageUserRating") or 0, 2),
        "rating_count": r.get("userRatingCount") or 0,
        "version": r.get("version", ""),
        "url": r.get("trackViewUrl", ""),
    }


def search_apps(term, country="us", limit=12):
    q = urllib.parse.urlencode({"term": term, "entity": "software", "country": country, "limit": limit})
    data = get_json(f"https://itunes.apple.com/search?{q}")
    return [_app_info(r) for r in data.get("results", []) if r.get("trackId")]


def lookup_app(app_id, country="us"):
    data = get_json(f"https://itunes.apple.com/lookup?id={urllib.parse.quote(str(app_id))}&country={country}")
    results = data.get("results", [])
    return _app_info(results[0]) if results else None


def _parse_entries(data):
    entries = data.get("feed", {}).get("entry", [])
    if isinstance(entries, dict):  # a single entry comes back as an object, not a list
        entries = [entries]
    reviews = []
    for entry in entries:
        # skip anything that isn't a review (sometimes the app info sneaks in)
        if "im:rating" not in entry:
            continue
        reviews.append({
            "rating": int(entry["im:rating"]["label"]),
            "title": entry["title"]["label"],
            "text": entry["content"]["label"],
            "version": entry["im:version"]["label"],
            "date": entry["updated"]["label"],
        })
    return reviews


def _fetch_page(app_id, page, country, attempts):
    # Apple's feed often returns an empty page at random, so retry a few times.
    url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
    for attempt in range(attempts):
        try:
            reviews = _parse_entries(get_json(f"{url}?r={attempt}"))
            if reviews:
                return reviews
        except Exception:
            pass
        time.sleep(0.3)
    return []


def fetch_reviews(app_id, pages=MAX_PAGES, country="us", attempts=12):
    """Fetch every page in parallel, retrying empty ones, then sort newest first."""
    with ThreadPoolExecutor(max_workers=pages) as pool:
        results = pool.map(lambda p: _fetch_page(app_id, p, country, attempts), range(1, pages + 1))

    seen, reviews = set(), []
    for page in results:
        for r in page:
            key = (r["date"], r["title"], r["text"][:80])
            if key not in seen:
                seen.add(key)
                reviews.append(r)
    reviews.sort(key=lambda r: r["date"], reverse=True)
    return reviews


if __name__ == "__main__":
    import sys

    app_id = sys.argv[1] if len(sys.argv) > 1 else "544007664"  # YouTube
    reviews = fetch_reviews(app_id)
    print(f"Got {len(reviews)} reviews")

    with open("reviews.json", "w") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    print("Saved to reviews.json")

    # count reviews by star rating
    for stars in range(5, 0, -1):
        count = sum(1 for r in reviews if r["rating"] == stars)
        print(f"{stars}-star: {count}")
