"""Interactive App Review Analyzer.

Run:  python3 app.py
Then pick any App Store app in the browser tab that opens (http://localhost:8000).

Uses only Python's standard library. The page is the same dashboard report.py
builds, served in "live" mode with an app picker.
"""
import json
import re
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fetch_reviews import fetch_reviews, lookup_app, search_apps, get_json, _app_info
from report import COUNTRIES, analyze_reviews, build_payload, render_page, build_report

HOST = "127.0.0.1"
PORT = 8000
CACHE_SECONDS = 30 * 60

# Shown on the home screen as quick picks
FEATURED = ["544007664", "835599320", "389801252", "324684580", "363590051",
            "570060128", "368677368", "6448311069"]

_cache = {}
_cache_lock = threading.Lock()


def cached(key, compute):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
    value = compute()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


def analyze_app(app_id, country):
    app = lookup_app(app_id, country)
    if not app:
        raise LookupError(f"No app with ID {app_id} in the {country.upper()} App Store.")
    reviews = fetch_reviews(app_id, country=country)
    if not reviews:
        raise LookupError(f"Apple returned no reviews for {app['name']} right now. "
                          "Apple's review feed is flaky, so try again in a minute.")
    reviews, summary = analyze_reviews(reviews, app["name"])
    return reviews, summary, app


def featured(country):
    data = get_json(f"https://itunes.apple.com/lookup?id={','.join(FEATURED)}&country={country}")
    by_id = {str(r["trackId"]): _app_info(r) for r in data.get("results", []) if r.get("trackId")}
    return [by_id[i] for i in FEATURED if i in by_id]


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, content_type="application/json", extra_headers=None):
        if not isinstance(body, bytes):
            body = (json.dumps(body, ensure_ascii=False) if content_type == "application/json" else body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
        country = q.get("country", "us").lower()
        if country not in COUNTRIES:
            country = "us"
        app_id = q.get("id", "")

        try:
            if url.path == "/":
                return self.send(200, render_page(live=True), "text/html")

            if url.path == "/api/featured":
                return self.send(200, cached(("featured", country), lambda: featured(country)))

            if url.path == "/api/search":
                term = q.get("term", "").strip()[:100]
                if not term:
                    return self.send(200, [])
                return self.send(200, cached(("search", term.lower(), country), lambda: search_apps(term, country)))

            if url.path in ("/api/analyze", "/report"):
                if not re.fullmatch(r"\d{1,12}", app_id):
                    return self.send(400, {"error": "That doesn't look like an App Store app ID."})
                reviews, summary, app = cached(("analyze", app_id, country), lambda: analyze_app(app_id, country))
                if url.path == "/report":
                    slug = re.sub(r"[^a-z0-9]+", "-", app["name"].lower()).strip("-")[:40] or app_id
                    return self.send(200, build_report(reviews, summary, app, country), "text/html",
                                     {"Content-Disposition": f'attachment; filename="{slug}-review-report.html"'})
                return self.send(200, build_payload(reviews, summary, app, country))

            return self.send(404, {"error": "Not found"})
        except LookupError as e:
            return self.send(404, {"error": str(e)})
        except Exception as e:
            print(f"  error handling {url.path}: {e!r}", file=sys.stderr)
            return self.send(502, {"error": "Couldn't reach the App Store. Check your internet connection and try again."})

    def log_message(self, fmt, *args):
        pass  # keep the terminal quiet


def main():
    ports = [int(a) for a in sys.argv[1:] if a.isdigit()]
    port = ports[0] if ports else PORT
    for p in range(port, port + 20):
        try:
            server = ThreadingHTTPServer((HOST, p), Handler)
            break
        except OSError:
            continue
    else:
        sys.exit(f"Couldn't find a free port between {port} and {port + 19}.")

    url = f"http://localhost:{server.server_port}"
    print(f"App Review Analyzer is running at {url}")
    print("Leave this window open while you use it. Press Ctrl+C to stop.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
