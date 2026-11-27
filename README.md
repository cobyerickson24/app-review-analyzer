# App Review Analyzer

Turns hundreds of App Store reviews into a one-page report showing what's frustrating users most, with real quotes as evidence.

![Report screenshot](screenshot.png)

## Why I built this

At work I spend a lot of time figuring out what's actually causing customer friction, using analytics, customer feedback, and QA findings. App Store reviews are one of the most direct sources of that feedback, but nobody reads 500 of them. I wanted a tool that would read them for me, group the complaints into themes, and tell me which problems matter most.

## What it found for YouTube

Running it on the 500 most recent US reviews of the YouTube app:

- **Users are polarized.** 39% gave 5 stars and 38% gave 1 star, with very little in between.
- **Recent changes are the #1 complaint.** "Updates & UI changes" shows up in about 42% of negative reviews, ahead of ads (35%). Reviewers called out specific things, like a removed subscriptions filter and a smaller skip-ad button.
- **Pricing frustration is tied to ads.** Many Premium complaints are really about feeling pushed toward paying to escape ads.

## How it works

1. **Collect** (`fetch_reviews.py`) pulls the most recent reviews from Apple's public review feed, including rating, text, app version, and date, and saves them to `reviews.json`.
2. **Analyze** (`analyze.py`) tags each review with themes using a keyword taxonomy, then ranks the themes by how often they appear in 1–2 star reviews. It also flags negative reviews that didn't match any theme, so the taxonomy can be improved over time.
3. **Report** (`report.py`) reuses the tagging from `analyze.py` and builds `report.html`, a single self-contained interactive dashboard (no external libraries): headline stats, the rating split, ranked issues, reviews over time split into positive and negative, example quotes, and a searchable explorer of every tagged review. Click an issue or rating bar to filter the explorer, filter by rating, theme, or app version, and hover the charts for details. It opens in dark mode, with a light/dark toggle.

## Design decisions

- **Themes live in a config file, not in code.** `themes.json` holds the full taxonomy, so anyone can adapt it to a new app or add a theme without touching the code.
- **No AI.** Keyword tagging is free, fast, and fully transparent. You can see exactly why a review got tagged. The tradeoff is that it misses sarcasm and anything phrased in an unexpected way.
- **Ranked by unhappy users.** Themes are ranked by how often they show up in negative reviews, not overall, because the goal is to find what to fix.
- **The tool reports its own blind spots.** The "gaps" section lists common words in untagged negative reviews. That's how I found that "change" was missing from the Updates theme.

## Run it yourself

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests

python fetch_reviews.py   # pull reviews
python analyze.py         # tag and rank themes
python report.py          # build report.html
open report.html
```

To analyze a different app, find its ID in its App Store URL (the number after `id`), put it in `fetch_reviews.py`, update `APP_NAME` in `report.py`, and adjust the keywords in `themes.json`.

## What I'd add next

- Support for Google Play reviews
- Longer-range trends by app version, to spot when a release caused a spike in complaints
- Handling non-English reviews (several Spanish reviews currently go untagged)
- An optional AI mode for more nuanced grouping
