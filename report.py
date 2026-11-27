import json
import html
from datetime import date

APP_NAME = "YouTube"  # change this when you analyze a different app


def esc(text):
    return html.escape(str(text))


def build_report(a):
    max_rating = max(a["rating_counts"].values()) or 1
    rating_rows = ""
    for stars, count in a["rating_counts"].items():
        width = 100 * count / max_rating
        pct = round(100 * count / a["total_reviews"])
        rating_rows += f"""
        <div class="bar-row">
          <span class="label">{stars}★</span>
          <div class="track"><div class="fill {'neg' if int(stars) <= 2 else ''}" style="width:{width}%"></div></div>
          <span class="value">{count} <small>({pct}%)</small></span>
        </div>"""

    top = a["themes"][0] if a["themes"] else None
    max_pct = max((t["pct_of_negative"] for t in a["themes"]), default=1) or 1

    theme_rows = ""
    for i, t in enumerate(a["themes"], 1):
        width = 100 * t["pct_of_negative"] / max_pct
        theme_rows += f"""
        <div class="bar-row">
          <span class="label rank">{i}. {esc(t['theme'])}</span>
          <div class="track"><div class="fill neg" style="width:{width}%"></div></div>
          <span class="value">{t['pct_of_negative']}%</span>
        </div>"""

    detail_cards = ""
    for t in a["themes"][:5]:
        quotes = "".join(
            f"<blockquote><span class='stars'>{'★' * q['rating']}</span> <strong>{esc(q['title'])}</strong><br>{esc(q['text'])}</blockquote>"
            for q in t["examples"][:2]
        )
        versions = ", ".join(f"v{esc(v)} ({n})" for v, n in t["versions"].items())
        detail_cards += f"""
        <section class="card">
          <h3>{esc(t['theme'])}</h3>
          <p class="meta">{t['negative_mentions']} negative reviews · avg rating {t['avg_rating']} · most cited on {versions or 'n/a'}</p>
          {quotes or '<p class="meta">No example quotes in range.</p>'}
        </section>"""

    gap_words = ", ".join(esc(w) for w, _ in a["untagged_top_words"][:10])
    headline = (
        f"<strong>{esc(top['theme'])}</strong> is the top driver of negative reviews, "
        f"showing up in {top['pct_of_negative']}% of 1–2 star reviews."
        if top else "No themes matched."
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(APP_NAME)} App Review Analysis</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1d1d1f; background: #f5f5f7; margin: 0; }}
  main {{ max-width: 820px; margin: 0 auto; padding: 40px 24px 64px; }}
  h1 {{ font-size: 28px; margin: 0 0 4px; }}
  h2 {{ font-size: 18px; margin: 0 0 16px; }}
  h3 {{ font-size: 16px; margin: 0 0 4px; }}
  .sub, .meta {{ color: #6e6e73; font-size: 14px; margin: 0 0 12px; }}
  .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 24px 0; }}
  .stat {{ background: #fff; border-radius: 12px; padding: 16px; }}
  .stat b {{ display: block; font-size: 26px; }}
  .stat span {{ color: #6e6e73; font-size: 13px; }}
  .card {{ background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; }}
  .headline {{ font-size: 16px; line-height: 1.5; }}
  .bar-row {{ display: grid; grid-template-columns: 210px 1fr 80px; align-items: center; gap: 12px; margin: 8px 0; font-size: 14px; }}
  .bar-row .label {{ white-space: nowrap; }}
  .track {{ background: #ececf0; border-radius: 4px; height: 14px; }}
  .fill {{ background: #4a6cf7; height: 100%; border-radius: 4px; }}
  .fill.neg {{ background: #e0565b; }}
  .value {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .value small {{ color: #6e6e73; }}
  blockquote {{ margin: 12px 0 0; padding: 10px 14px; background: #f5f5f7; border-left: 3px solid #e0565b; border-radius: 4px; font-size: 14px; line-height: 1.45; }}
  .stars {{ color: #f5a623; }}
  footer {{ color: #6e6e73; font-size: 12px; margin-top: 32px; }}
  @media (max-width: 600px) {{ .bar-row {{ grid-template-columns: 120px 1fr 56px; }} .stats {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<main>
  <h1>{esc(APP_NAME)} App Review Analysis</h1>
  <p class="sub">Based on the {a['total_reviews']} most recent US App Store reviews · generated {date.today():%B %d, %Y}</p>

  <div class="stats">
    <div class="stat"><b>{a['avg_rating']}</b><span>average rating</span></div>
    <div class="stat"><b>{round(100 * a['negative_reviews'] / a['total_reviews'])}%</b><span>negative (1–2 stars)</span></div>
    <div class="stat"><b>{len(a['themes'])}</b><span>issue themes detected</span></div>
  </div>

  <section class="card"><p class="headline">{headline}</p></section>

  <section class="card">
    <h2>Rating distribution</h2>
    {rating_rows}
  </section>

  <section class="card">
    <h2>Top issues among unhappy reviewers</h2>
    <p class="meta">Share of 1–2 star reviews mentioning each theme. A review can mention more than one.</p>
    {theme_rows}
  </section>

  <h2 style="margin-top:32px">What users are saying</h2>
  {detail_cards}

  <section class="card">
    <h2>Gaps in the analysis</h2>
    <p class="meta">{a['untagged_negative']} negative reviews didn't match any theme. Most common words in those: {gap_words}. These are candidates for new themes in themes.json.</p>
  </section>

  <footer>Generated by app-review-analyzer · keyword-based theme tagging, no AI</footer>
</main>
</body>
</html>"""


if __name__ == "__main__":
    with open("analysis.json") as f:
        analysis = json.load(f)
    with open("report.html", "w") as f:
        f.write(build_report(analysis))
    print("Report saved to report.html. Open it in your browser.")
