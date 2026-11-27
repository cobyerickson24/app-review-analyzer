"""Build report.html: a single self-contained, interactive dashboard.

Reads reviews.json, tags every review with analyze.py's theme taxonomy, and embeds
the full tagged set in the page so the review explorer can search and filter all of
them, not just the example quotes. No external libraries or network requests.
"""
import json
from datetime import date

from analyze import load_themes, tag_reviews, summarize

APP_NAME = "YouTube"  # change this when you analyze a different app


def build_payload(reviews, summary):
    return {
        "app": APP_NAME,
        "generated": f"{date.today():%B %d, %Y}",
        "summary": summary,
        "reviews": [
            {
                "id": i,
                "rating": r["rating"],
                "title": r["title"],
                "text": r["text"],
                "version": r["version"],
                "date": r["date"],
                "themes": r["themes"],
            }
            for i, r in enumerate(reviews)
        ],
    }


def build_report(reviews, summary):
    payload = json.dumps(build_payload(reviews, summary), ensure_ascii=False)
    # keep the JSON from ever closing the <script> tag it lives in
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    title = f"{APP_NAME} App Review Analysis".replace("&", "&amp;").replace("<", "&lt;")
    return TEMPLATE.replace("__TITLE__", title).replace("__DATA__", payload)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script>
  // apply the saved theme before first paint; dark is the default
  try { var t = localStorage.getItem("ara-theme"); if (t === "light" || t === "dark") document.documentElement.dataset.theme = t; } catch (e) {}
</script>
<style>
  :root, :root[data-theme="dark"] {
    color-scheme: dark;
    --bg: #111111;
    --surface: #1b1b1b;
    --surface-2: #242424;
    --border: #2f2f2f;
    --text: #efefef;
    --text-2: #9c9c9c;
    --track: #2a2a2a;
    --grid: #2c2c2c;
    --pos: #338ced;
    --neg: #eb6263;
    --neutral: #6e6e6e;
    --accent: #338ced;
    --star: #f2a600;
    --mark: rgba(242, 166, 0, 0.32);
    --tip-bg: #2a2a2a;
    --shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
  }
  :root[data-theme="light"] {
    color-scheme: light;
    --bg: #f5f5f7;
    --surface: #ffffff;
    --surface-2: #f3f3f5;
    --border: #e3e3e8;
    --text: #191919;
    --text-2: #666666;
    --track: #ececf0;
    --grid: #ececef;
    --pos: #257de0;
    --neg: #ec4647;
    --neutral: #b4b4b4;
    --accent: #257de0;
    --star: #d28e05;
    --mark: rgba(242, 166, 0, 0.35);
    --tip-bg: #ffffff;
    --shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
  }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: var(--text); background: var(--bg); margin: 0; line-height: 1.4; }
  main { max-width: 1080px; margin: 0 auto; padding: 32px 16px 64px; }
  h1 { font-size: 28px; margin: 0 0 4px; letter-spacing: -0.01em; }
  h2 { font-size: 17px; margin: 0 0 4px; }
  h3 { font-size: 15px; margin: 0 0 4px; }
  .sub, .meta { color: var(--text-2); font-size: 13px; margin: 0 0 12px; }
  header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
  button { font: inherit; color: inherit; }
  .btn { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 7px 12px; cursor: pointer; font-size: 13px; white-space: nowrap; }
  .btn:hover { background: var(--surface-2); }
  .btn:focus-visible, .bar:focus-visible, .chip:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .linkbtn { background: none; border: 0; padding: 0; color: var(--accent); cursor: pointer; font-size: 13px; }
  .linkbtn:hover { text-decoration: underline; }

  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 24px 0 16px; }
  .stat { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
  .stat b { display: block; font-size: 26px; font-variant-numeric: tabular-nums; }
  .stat span { color: var(--text-2); font-size: 13px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; min-width: 0; }
  .headline { font-size: 16px; line-height: 1.5; margin: 0; }
  .grid2 { display: grid; grid-template-columns: 5fr 7fr; gap: 16px; }
  .grid2 > .card { margin-bottom: 0; }
  .row-gap { margin-bottom: 16px; }

  /* horizontal bars (ratings, issues) */
  .bars { margin-top: 12px; }
  .bar { display: grid; grid-template-columns: var(--label-w, 44px) 1fr 76px; align-items: center; gap: 12px; width: 100%; padding: 5px 6px; margin: 0 -6px; width: calc(100% + 12px); background: none; border: 0; border-radius: 6px; cursor: pointer; text-align: left; font-size: 14px; }
  .bar:hover, .bar.active { background: var(--surface-2); }
  .bar .label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .bar.active .label { font-weight: 600; }
  .track { background: var(--track); border-radius: 4px; height: 14px; overflow: hidden; }
  .fill { height: 100%; border-radius: 0 4px 4px 0; transition: width .25s ease, filter .15s; }
  .bar:hover .fill { filter: brightness(1.15); }
  .fill.pos { background: var(--pos); } .fill.neg { background: var(--neg); } .fill.neu { background: var(--neutral); }
  .bars.dim .bar:not(.active) .fill { opacity: .35; }
  .value { text-align: right; font-variant-numeric: tabular-nums; }
  .value small { color: var(--text-2); }
  #issues { --label-w: 210px; }

  /* time chart */
  .legend { display: flex; gap: 16px; font-size: 12px; color: var(--text-2); margin: 8px 0 4px; flex-wrap: wrap; }
  .legend i { display: inline-block; width: 14px; height: 2px; vertical-align: middle; margin-right: 6px; border-radius: 1px; }
  #timechart { width: 100%; height: 264px; display: block; touch-action: pan-y; }
  #timechart text { fill: var(--text-2); font-size: 11px; font-variant-numeric: tabular-nums; }
  #timechart .endlabel { font-size: 12px; fill: var(--text); }
  .chart-scope { font-size: 12px; color: var(--text-2); }

  /* example cards */
  .examples { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px; }
  .examples .card { margin: 0; display: flex; flex-direction: column; }
  .examples .card .linkbtn { margin-top: auto; padding-top: 12px; align-self: flex-start; }
  blockquote { margin: 10px 0 0; padding: 10px 14px; background: var(--surface-2); border-left: 3px solid var(--neg); border-radius: 4px; font-size: 14px; line-height: 1.45; }
  .stars { color: var(--star); letter-spacing: 1px; }
  .stars .off { color: var(--track); }

  /* explorer */
  .filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 12px 0; }
  .filters input[type=search] { flex: 1 1 240px; min-width: 0; }
  .filters input, .filters select { background: var(--surface-2); border: 1px solid var(--border); color: var(--text); border-radius: 8px; padding: 8px 10px; font: inherit; font-size: 14px; max-width: 100%; }
  .filters select { flex: 0 1 auto; }
  .resultbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; font-size: 13px; color: var(--text-2); margin-bottom: 8px; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; padding: 3px 9px; border-radius: 999px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text); cursor: pointer; }
  .chip:hover { border-color: var(--accent); }
  .chip.removable::after { content: "×"; color: var(--text-2); margin-left: 2px; }
  .review { border-top: 1px solid var(--border); padding: 14px 0; }
  .review:first-child { border-top: 0; }
  .review .top { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; align-items: baseline; }
  .review .title { font-weight: 600; }
  .review .when { color: var(--text-2); font-size: 12px; font-variant-numeric: tabular-nums; }
  .review p { margin: 6px 0 8px; font-size: 14px; line-height: 1.5; overflow-wrap: anywhere; }
  .review mark { background: var(--mark); color: inherit; border-radius: 2px; padding: 0 1px; }
  .empty { color: var(--text-2); padding: 24px 0; text-align: center; }
  #more { margin-top: 8px; width: 100%; }

  #tip { position: fixed; z-index: 10; pointer-events: none; background: var(--tip-bg); color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; font-size: 12px; box-shadow: var(--shadow); max-width: 260px; opacity: 0; transition: opacity .1s; }
  #tip.show { opacity: 1; }
  #tip .tt-h { color: var(--text-2); margin-bottom: 4px; }
  #tip .tt-row { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
  #tip .tt-row b { font-variant-numeric: tabular-nums; font-size: 13px; }
  #tip .tt-row span { color: var(--text-2); }
  #tip .tt-key { width: 12px; height: 2px; border-radius: 1px; flex: none; }
  #tip .tt-note { color: var(--text-2); margin-top: 4px; white-space: normal; }

  footer { color: var(--text-2); font-size: 12px; margin-top: 32px; }
  @media (max-width: 820px) { .grid2, .examples { grid-template-columns: 1fr; } .stats { grid-template-columns: repeat(2, 1fr); } }
  .value { white-space: nowrap; }
  @media (max-width: 560px) { #issues { --label-w: 128px; } .bar { grid-template-columns: var(--label-w, 36px) 1fr auto; gap: 8px; } h1 { font-size: 22px; } }
</style>
</head>
<body>
<main>
  <header>
    <div>
      <h1 id="title"></h1>
      <p class="sub" id="subtitle"></p>
    </div>
    <button class="btn" id="themeToggle" type="button" aria-label="Toggle light and dark mode"></button>
  </header>

  <div class="stats" id="stats"></div>

  <section class="card row-gap"><p class="headline" id="headline"></p></section>

  <div class="grid2 row-gap">
    <section class="card">
      <h2>Rating distribution</h2>
      <p class="meta">Click a bar to filter the reviews below.</p>
      <div class="bars" id="ratings"></div>
    </section>
    <section class="card">
      <h2>Reviews over time</h2>
      <p class="meta"><span class="chart-scope" id="timeScope"></span></p>
      <div class="legend" id="timeLegend"></div>
      <svg id="timechart" role="img" aria-label="Positive and negative reviews over time"></svg>
    </section>
  </div>

  <section class="card row-gap">
    <h2>Top issues among unhappy reviewers</h2>
    <p class="meta">Share of 1–2 star reviews mentioning each theme (a review can mention several). Click a bar to explore those reviews.</p>
    <div class="bars" id="issues"></div>
  </section>

  <h2 style="margin:28px 0 12px">What users are saying</h2>
  <div class="examples" id="examples"></div>

  <section class="card row-gap" id="explorer">
    <h2>Review explorer</h2>
    <p class="meta">Every review, tagged with the themes from themes.json.</p>
    <div class="filters">
      <input type="search" id="q" placeholder="Search review text…" aria-label="Search reviews">
      <select id="fRating" aria-label="Filter by rating"></select>
      <select id="fTheme" aria-label="Filter by theme"></select>
      <select id="fVersion" aria-label="Filter by app version"></select>
      <select id="fSort" aria-label="Sort reviews">
        <option value="newest">Newest first</option>
        <option value="oldest">Oldest first</option>
        <option value="low">Lowest rating</option>
        <option value="high">Highest rating</option>
      </select>
    </div>
    <div class="resultbar">
      <span id="count"></span>
      <div class="chips" id="active"></div>
    </div>
    <div id="list"></div>
    <button class="btn" id="more" type="button" hidden>Show more</button>
  </section>

  <section class="card">
    <h2>Gaps in the analysis</h2>
    <p class="meta" id="gaps"></p>
    <button class="linkbtn" id="showUntagged" type="button">Show untagged negative reviews →</button>
  </section>

  <footer>Generated by app-review-analyzer · keyword-based theme tagging, no AI</footer>
</main>
<div id="tip" role="tooltip"></div>

<script type="application/json" id="data">__DATA__</script>
<script>
(function () {
  "use strict";
  var DATA = JSON.parse(document.getElementById("data").textContent);
  var S = DATA.summary, REVIEWS = DATA.reviews;
  var $ = function (id) { return document.getElementById(id); };
  var PAGE = 25;
  var state = { q: "", rating: "all", theme: "all", version: "all", sort: "newest", limit: PAGE };

  REVIEWS.forEach(function (r) { r.ts = +new Date(r.date); r.hay = (r.title + " " + r.text).toLowerCase(); });

  // ---------- helpers ----------
  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === "text") n.textContent = attrs[k];
      else if (k === "class") n.className = attrs[k];
      else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), attrs[k]);
      else n.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) { if (c != null) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  function svg(tag, attrs) {
    var n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  function pct(n, d) { return d ? Math.round(100 * n / d) : 0; }
  function stars(n) {
    return el("span", { class: "stars", "aria-label": n + " out of 5 stars" },
      ["★".repeat(n), el("span", { class: "off", text: "★".repeat(5 - n) })]);
  }
  function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  var MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  function fmtDay(d) { return MON[d.getMonth()] + " " + d.getDate(); }
  function fmtHour(d) { var h = d.getHours(); return (h % 12 || 12) + (h < 12 ? " AM" : " PM"); }
  function fmtDate(ts) { var d = new Date(ts); return fmtDay(d) + ", " + d.getFullYear(); }

  // ---------- tooltip ----------
  var tip = $("tip");
  function tipRow(color, value, label) {
    return el("div", { class: "tt-row" }, [
      color ? el("i", { class: "tt-key", style: "background:" + color }) : null,
      el("b", { text: String(value) }), el("span", { text: label })
    ]);
  }
  function showTip(nodes, x, y) {
    tip.replaceChildren.apply(tip, nodes);
    tip.classList.add("show");
    var w = tip.offsetWidth, h = tip.offsetHeight, pad = 12;
    var left = x + pad, top = y + pad;
    if (left + w > window.innerWidth - 8) left = x - w - pad;
    if (top + h > window.innerHeight - 8) top = y - h - pad;
    tip.style.left = Math.max(8, left) + "px";
    tip.style.top = Math.max(8, top) + "px";
  }
  function hideTip() { tip.classList.remove("show"); }
  function attachTip(node, build) {
    node.addEventListener("pointermove", function (e) { showTip(build(), e.clientX, e.clientY); });
    node.addEventListener("pointerleave", hideTip);
    node.addEventListener("focus", function () { var b = node.getBoundingClientRect(); showTip(build(), b.left + b.width / 2, b.bottom - 4); });
    node.addEventListener("blur", hideTip);
  }

  // ---------- theme toggle ----------
  function syncToggle() {
    var dark = document.documentElement.dataset.theme !== "light";
    $("themeToggle").textContent = dark ? "☀ Light mode" : "☾ Dark mode";
  }
  $("themeToggle").addEventListener("click", function () {
    var next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("ara-theme", next); } catch (e) {}
    syncToggle(); renderTime();
  });

  // ---------- static header content ----------
  $("title").textContent = DATA.app + " App Review Analysis";
  $("subtitle").textContent = "Based on the " + S.total_reviews + " most recent US App Store reviews · generated " + DATA.generated;
  [[S.avg_rating, "average rating"],
   [pct(S.negative_reviews, S.total_reviews) + "%", "negative (1–2 stars)"],
   [S.total_reviews, "reviews analyzed"],
   [S.themes.length, "issue themes detected"]].forEach(function (s) {
    $("stats").appendChild(el("div", { class: "stat" }, [el("b", { text: String(s[0]) }), el("span", { text: s[1] })]));
  });
  var top = S.themes[0];
  if (top) {
    $("headline").replaceChildren(el("strong", { text: top.theme }),
      " is the top driver of negative reviews, showing up in " + top.pct_of_negative + "% of 1–2 star reviews.");
  } else $("headline").textContent = "No themes matched.";

  // ---------- rating bars ----------
  function buildRatings() {
    var box = $("ratings"); box.replaceChildren();
    var counts = S.rating_counts, max = Math.max.apply(null, Object.values(counts)) || 1;
    Object.keys(counts).sort(function (a, b) { return b - a; }).forEach(function (s) {
      var n = counts[s], cls = s >= 4 ? "pos" : s <= 2 ? "neg" : "neu";
      var b = el("button", { class: "bar", type: "button", "data-rating": s,
        "aria-label": s + " stars: " + n + " reviews. Filter reviews.",
        onclick: function () { setFilter({ rating: state.rating === s ? "all" : s }, true); } }, [
        el("span", { class: "label", text: s + "★" }),
        el("div", { class: "track" }, [el("div", { class: "fill " + cls, style: "width:" + (100 * n / max) + "%" })]),
        el("span", { class: "value" }, [String(n) + " ", el("small", { text: "(" + pct(n, S.total_reviews) + "%)" })])
      ]);
      attachTip(b, function () {
        return [el("div", { class: "tt-h", text: s + "-star reviews" }),
                tipRow(cssVar("--" + cls), n, "reviews"),
                tipRow(null, pct(n, S.total_reviews) + "%", "of all reviews"),
                el("div", { class: "tt-note", text: state.rating === s ? "Click to clear filter" : "Click to filter reviews" })];
      });
      box.appendChild(b);
    });
  }

  // ---------- issue bars ----------
  function buildIssues() {
    var box = $("issues"); box.replaceChildren();
    var max = Math.max.apply(null, S.themes.map(function (t) { return t.pct_of_negative; })) || 1;
    S.themes.forEach(function (t, i) {
      var b = el("button", { class: "bar", type: "button", "data-theme": t.theme,
        "aria-label": t.theme + ": " + t.pct_of_negative + "% of negative reviews. Filter reviews.",
        onclick: function () { setFilter({ theme: state.theme === t.theme ? "all" : t.theme }, true); } }, [
        el("span", { class: "label", text: (i + 1) + ". " + t.theme }),
        el("div", { class: "track" }, [el("div", { class: "fill neg", style: "width:" + (100 * t.pct_of_negative / max) + "%" })]),
        el("span", { class: "value", text: t.pct_of_negative + "%" })
      ]);
      attachTip(b, function () {
        var vers = Object.keys(t.versions).map(function (v) { return "v" + v + " (" + t.versions[v] + ")"; }).join(", ");
        return [el("div", { class: "tt-h", text: t.theme }),
                tipRow(cssVar("--neg"), t.negative_mentions, "negative reviews (" + t.pct_of_negative + "%)"),
                tipRow(null, t.mentions, "total mentions (" + t.pct_of_all + "% of all)"),
                tipRow(null, t.avg_rating + "★", "avg rating when mentioned"),
                vers ? el("div", { class: "tt-note", text: "Most cited on " + vers }) : null,
                el("div", { class: "tt-note", text: state.theme === t.theme ? "Click to clear filter" : "Click to explore these reviews" })]
               .filter(Boolean);
      });
      box.appendChild(b);
    });
  }

  function syncBars() {
    [["ratings", "rating", state.rating], ["issues", "theme", state.theme]].forEach(function (c) {
      var box = $(c[0]), any = false;
      box.querySelectorAll(".bar").forEach(function (b) {
        var on = b.dataset[c[1]] === c[2]; any = any || on;
        b.classList.toggle("active", on); b.setAttribute("aria-pressed", on);
      });
      box.classList.toggle("dim", any);
    });
  }

  // ---------- example cards ----------
  S.themes.slice(0, 6).forEach(function (t) {
    var vers = Object.keys(t.versions).map(function (v) { return "v" + v + " (" + t.versions[v] + ")"; }).join(", ");
    var quotes = t.examples.slice(0, 2).map(function (q) {
      return el("blockquote", null, [stars(q.rating), " ", el("strong", { text: q.title }), el("br"), q.text]);
    });
    $("examples").appendChild(el("section", { class: "card" }, [
      el("h3", { text: t.theme }),
      el("p", { class: "meta", text: t.negative_mentions + " negative reviews · avg rating " + t.avg_rating + " · most cited on " + (vers || "n/a") })
    ].concat(quotes.length ? quotes : [el("p", { class: "meta", text: "No example quotes in range." })]).concat([
      el("button", { class: "linkbtn", type: "button", text: "Explore all " + t.mentions + " reviews mentioning this →",
        onclick: function () { setFilter({ theme: t.theme, rating: "all", q: "" }, true); } })
    ])));
  });

  // ---------- gaps ----------
  $("gaps").textContent = S.untagged_negative + " negative reviews didn't match any theme. Most common words in those: " +
    S.untagged_top_words.slice(0, 10).map(function (w) { return w[0]; }).join(", ") +
    ". These are candidates for new themes in themes.json.";
  $("showUntagged").addEventListener("click", function () { setFilter({ theme: "__none__", rating: "neg", q: "" }, true); });

  // ---------- filter controls ----------
  var RATING_OPTS = [["all", "All ratings"], ["neg", "Negative (1–2★)"], ["pos", "Positive (4–5★)"],
    ["5", "5★"], ["4", "4★"], ["3", "3★"], ["2", "2★"], ["1", "1★"]];
  RATING_OPTS.forEach(function (o) { $("fRating").appendChild(el("option", { value: o[0], text: o[1] })); });
  $("fTheme").appendChild(el("option", { value: "all", text: "All themes" }));
  S.themes.forEach(function (t) { $("fTheme").appendChild(el("option", { value: t.theme, text: t.theme + " (" + t.mentions + ")" })); });
  var untaggedAll = REVIEWS.filter(function (r) { return !r.themes.length; }).length;
  $("fTheme").appendChild(el("option", { value: "__none__", text: "No theme matched (" + untaggedAll + ")" }));
  var vc = {};
  REVIEWS.forEach(function (r) { vc[r.version] = (vc[r.version] || 0) + 1; });
  $("fVersion").appendChild(el("option", { value: "all", text: "All versions" }));
  Object.keys(vc).sort(function (a, b) { return vc[b] - vc[a] || b.localeCompare(a, undefined, { numeric: true }); })
    .forEach(function (v) { $("fVersion").appendChild(el("option", { value: v, text: "v" + v + " (" + vc[v] + ")" })); });

  $("q").addEventListener("input", function (e) { setFilter({ q: e.target.value }); });
  $("fRating").addEventListener("change", function (e) { setFilter({ rating: e.target.value }); });
  $("fTheme").addEventListener("change", function (e) { setFilter({ theme: e.target.value }); });
  $("fVersion").addEventListener("change", function (e) { setFilter({ version: e.target.value }); });
  $("fSort").addEventListener("change", function (e) { setFilter({ sort: e.target.value }); });
  $("more").addEventListener("click", function () { state.limit += PAGE; renderList(); });

  function setFilter(patch, scroll) {
    for (var k in patch) state[k] = patch[k];
    state.limit = PAGE;
    $("q").value = state.q; $("fRating").value = state.rating; $("fTheme").value = state.theme;
    $("fVersion").value = state.version; $("fSort").value = state.sort;
    render();
    if (scroll) $("explorer").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function matches(r, skipRating) {
    if (!skipRating && state.rating !== "all") {
      if (state.rating === "neg" ? r.rating > 2 : state.rating === "pos" ? r.rating < 4 : String(r.rating) !== state.rating) return false;
    }
    if (state.theme === "__none__" ? r.themes.length : state.theme !== "all" && r.themes.indexOf(state.theme) < 0) return false;
    if (state.version !== "all" && r.version !== state.version) return false;
    var q = state.q.trim().toLowerCase();
    if (q && r.hay.indexOf(q) < 0) return false;
    return true;
  }

  // ---------- review list ----------
  function highlight(text) {
    var q = state.q.trim();
    if (!q) return [text];
    var out = [], lower = text.toLowerCase(), ql = q.toLowerCase(), i = 0, j;
    while ((j = lower.indexOf(ql, i)) >= 0) {
      if (j > i) out.push(text.slice(i, j));
      out.push(el("mark", { text: text.slice(j, j + q.length) }));
      i = j + q.length;
    }
    out.push(text.slice(i));
    return out;
  }

  function renderList() {
    var rows = REVIEWS.filter(function (r) { return matches(r); });
    var sorters = {
      newest: function (a, b) { return b.ts - a.ts; },
      oldest: function (a, b) { return a.ts - b.ts; },
      low: function (a, b) { return a.rating - b.rating || b.ts - a.ts; },
      high: function (a, b) { return b.rating - a.rating || b.ts - a.ts; }
    };
    rows.sort(sorters[state.sort]);
    var shown = rows.slice(0, state.limit);
    $("count").textContent = rows.length === REVIEWS.length
      ? "Showing " + shown.length + " of all " + rows.length + " reviews"
      : "Showing " + shown.length + " of " + rows.length + " matching reviews (" + pct(rows.length, REVIEWS.length) + "% of all)";

    var list = $("list"); list.replaceChildren();
    if (!rows.length) list.appendChild(el("div", { class: "empty", text: "No reviews match these filters." }));
    shown.forEach(function (r) {
      var chips = r.themes.map(function (t) {
        return el("button", { class: "chip", type: "button", text: t, title: "Filter by " + t,
          onclick: function () { setFilter({ theme: t }); } });
      });
      list.appendChild(el("article", { class: "review" }, [
        el("div", { class: "top" }, [
          el("span", null, [stars(r.rating), "  ", el("span", { class: "title" }, highlight(r.title))]),
          el("span", { class: "when", text: fmtDate(r.ts) + " · v" + r.version })
        ]),
        el("p", null, highlight(r.text)),
        chips.length ? el("div", { class: "chips" }, chips) : null
      ]));
    });
    var left = rows.length - shown.length;
    $("more").hidden = left <= 0;
    $("more").textContent = "Show " + Math.min(PAGE, left) + " more (" + left + " remaining)";

    // active filter chips
    var act = $("active"); act.replaceChildren();
    function chip(label, patch) {
      act.appendChild(el("button", { class: "chip removable", type: "button", text: label, title: "Remove filter",
        onclick: function () { setFilter(patch); } }));
    }
    if (state.q.trim()) chip("“" + state.q.trim() + "”", { q: "" });
    if (state.rating !== "all") chip(RATING_OPTS.filter(function (o) { return o[0] === state.rating; })[0][1], { rating: "all" });
    if (state.theme !== "all") chip(state.theme === "__none__" ? "No theme matched" : state.theme, { theme: "all" });
    if (state.version !== "all") chip("v" + state.version, { version: "all" });
    if (act.children.length > 1) chip("Clear all", { q: "", rating: "all", theme: "all", version: "all" });
  }

  // ---------- reviews over time ----------
  // Buckets are fixed from the full dataset so the x-axis stays put while filters change.
  var tsAll = REVIEWS.map(function (r) { return r.ts; });
  var tMin = Math.min.apply(null, tsAll), tMax = Math.max.apply(null, tsAll);
  var spanH = (tMax - tMin) / 36e5;
  var BUCKET_H = [1, 2, 3, 6, 12, 24, 48, 168, 336, 720].filter(function (h) { return spanH / h <= 36; })[0] || 720;
  var BMS = BUCKET_H * 36e5;
  var start = new Date(tMin); start.setMinutes(0, 0, 0);
  if (BUCKET_H >= 24) start.setHours(0); else start.setHours(Math.floor(start.getHours() / BUCKET_H) * BUCKET_H);
  var T0 = +start, NB = Math.floor((tMax - T0) / BMS) + 1;

  function bucketLabel(i) {
    var a = new Date(T0 + i * BMS), b = new Date(T0 + (i + 1) * BMS);
    if (BUCKET_H < 24) return fmtDay(a) + ", " + fmtHour(a) + " – " + fmtHour(b);
    if (BUCKET_H === 24) return fmtDay(a) + ", " + a.getFullYear();
    return "Week of " + fmtDay(a);
  }

  function timeScopeText() {
    var parts = [];
    if (state.theme === "__none__") parts.push("with no theme");
    else if (state.theme !== "all") parts.push("mentioning " + state.theme);
    if (state.version !== "all") parts.push("on v" + state.version);
    if (state.q.trim()) parts.push("containing “" + state.q.trim() + "”");
    return "Reviews per " + (BUCKET_H < 24 ? BUCKET_H + "-hour window" : BUCKET_H === 24 ? "day" : "week") +
      (parts.length ? ", " + parts.join(", ") : ", all reviews") + ". Positive = 4–5★, negative = 1–2★.";
  }

  function renderTime() {
    var host = $("timechart");
    var W = Math.max(280, host.clientWidth || 600), H = 264;
    var m = { l: 34, r: 74, t: 14, b: 42 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
    host.setAttribute("viewBox", "0 0 " + W + " " + H);
    host.replaceChildren();

    var pos = new Array(NB).fill(0), neg = new Array(NB).fill(0), neu = new Array(NB).fill(0);
    REVIEWS.forEach(function (r) {
      if (!matches(r, true)) return;
      var i = Math.min(NB - 1, Math.floor((r.ts - T0) / BMS));
      if (r.rating >= 4) pos[i]++; else if (r.rating <= 2) neg[i]++; else neu[i]++;
    });
    $("timeScope").textContent = timeScopeText();
    var colPos = cssVar("--pos"), colNeg = cssVar("--neg");
    $("timeLegend").replaceChildren(
      el("span", null, [el("i", { style: "background:" + colPos }), "Positive (" + pos.reduce(function (a, b) { return a + b; }, 0) + ")"]),
      el("span", null, [el("i", { style: "background:" + colNeg }), "Negative (" + neg.reduce(function (a, b) { return a + b; }, 0) + ")"]));

    var vmax = Math.max(1, Math.max.apply(null, pos), Math.max.apply(null, neg));
    // 4 gridline steps, each a "nice" whole number so tick labels are exact
    var raw = vmax / 4, p10 = Math.pow(10, Math.floor(Math.log10(raw))), nrm = raw / p10;
    var step = Math.max(1, (nrm <= 1 ? 1 : nrm <= 2 ? 2 : nrm <= 5 ? 5 : 10) * p10);
    var ymax = step * 4;
    var x = function (i) { return m.l + (NB === 1 ? iw / 2 : iw * i / (NB - 1)); };
    var y = function (v) { return m.t + ih - ih * v / ymax; };

    for (var g = 0; g <= 4; g++) {
      var gv = g * step, gy = y(gv);
      host.appendChild(svg("line", { x1: m.l, x2: m.l + iw, y1: gy, y2: gy, stroke: cssVar(g === 0 ? "--border" : "--grid"), "stroke-width": 1 }));
      var tl = svg("text", { x: m.l - 8, y: gy + 4, "text-anchor": "end" }); tl.textContent = Math.round(gv); host.appendChild(tl);
    }
    var every = Math.max(1, Math.ceil(NB / Math.max(2, Math.floor(iw / 80))));
    var lastDay = "";
    for (var i = 0; i < NB; i += every) {
      var a = new Date(T0 + i * BMS), anchor = i === 0 ? "start" : "middle";
      var xl = svg("text", { x: x(i), y: H - 22, "text-anchor": anchor });
      xl.textContent = BUCKET_H < 24 ? fmtHour(a) : fmtDay(a); host.appendChild(xl);
      if (BUCKET_H < 24 && fmtDay(a) !== lastDay) {
        var dl = svg("text", { x: x(i), y: H - 6, "text-anchor": anchor }); dl.textContent = fmtDay(a); host.appendChild(dl);
        lastDay = fmtDay(a);
      }
    }

    function line(vals, color, name) {
      var d = vals.map(function (v, i) { return (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1); }).join("");
      host.appendChild(svg("path", { d: d, fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      if (NB === 1) host.appendChild(svg("circle", { cx: x(0), cy: y(vals[0]), r: 4, fill: color }));
      return { name: name, y: y(vals[NB - 1]), color: color };
    }
    var ends = [line(pos, colPos, "Positive"), line(neg, colNeg, "Negative")];
    // direct end labels, nudged apart if they collide
    ends.sort(function (a, b) { return a.y - b.y; });
    if (ends[1].y - ends[0].y < 14) { var mid = (ends[0].y + ends[1].y) / 2; ends[0].y = mid - 7; ends[1].y = mid + 7; }
    ends.forEach(function (e) {
      var t = svg("text", { x: x(NB - 1) + 8, y: e.y + 4, class: "endlabel" }); t.textContent = e.name; host.appendChild(t);
    });

    // crosshair + tooltip
    var hair = svg("line", { y1: m.t, y2: m.t + ih, stroke: cssVar("--text-2"), "stroke-width": 1, "stroke-dasharray": "3 3", visibility: "hidden" });
    var dP = svg("circle", { r: 4.5, fill: colPos, stroke: cssVar("--surface"), "stroke-width": 2, visibility: "hidden" });
    var dN = svg("circle", { r: 4.5, fill: colNeg, stroke: cssVar("--surface"), "stroke-width": 2, visibility: "hidden" });
    var hit = svg("rect", { x: m.l - 10, y: 0, width: iw + 20, height: H, fill: "transparent", tabindex: 0 });
    host.appendChild(hair); host.appendChild(dP); host.appendChild(dN); host.appendChild(hit);
    var cur = NB - 1;
    function show(i, cx, cy) {
      cur = i;
      [hair, dP, dN].forEach(function (n) { n.setAttribute("visibility", "visible"); });
      hair.setAttribute("x1", x(i)); hair.setAttribute("x2", x(i));
      dP.setAttribute("cx", x(i)); dP.setAttribute("cy", y(pos[i]));
      dN.setAttribute("cx", x(i)); dN.setAttribute("cy", y(neg[i]));
      showTip([el("div", { class: "tt-h", text: bucketLabel(i) }),
               tipRow(colPos, pos[i], "positive"), tipRow(colNeg, neg[i], "negative"),
               tipRow(cssVar("--neutral"), neu[i], "neutral (3★)")], cx, cy);
    }
    function hide() { [hair, dP, dN].forEach(function (n) { n.setAttribute("visibility", "hidden"); }); hideTip(); }
    hit.addEventListener("pointermove", function (e) {
      var b = host.getBoundingClientRect(), px = (e.clientX - b.left) * W / b.width;
      var i = NB === 1 ? 0 : Math.round((px - m.l) / iw * (NB - 1));
      show(Math.max(0, Math.min(NB - 1, i)), e.clientX, e.clientY);
    });
    hit.addEventListener("pointerleave", hide);
    hit.addEventListener("blur", hide);
    function kbShow() { var b = host.getBoundingClientRect(); show(cur, b.left + x(cur) * b.width / W, b.top + m.t); }
    hit.addEventListener("focus", kbShow);
    hit.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        cur = Math.max(0, Math.min(NB - 1, cur + (e.key === "ArrowRight" ? 1 : -1))); kbShow(); e.preventDefault();
      }
    });
  }

  function render() { syncBars(); renderList(); renderTime(); }

  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(renderTime, 120); });
  syncToggle(); buildRatings(); buildIssues(); setFilter({});
})();
</script>
</body>
</html>"""


if __name__ == "__main__":
    with open("reviews.json") as f:
        reviews = json.load(f)

    patterns = load_themes()
    reviews = tag_reviews(reviews, patterns)
    summary = summarize(reviews, patterns)

    with open("report.html", "w") as f:
        f.write(build_report(reviews, summary))
    print(f"Report saved to report.html with all {len(reviews)} tagged reviews. Open it in your browser.")
