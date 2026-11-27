import json
import re
from collections import Counter

# Words to ignore when looking for patterns in untagged reviews
STOPWORDS = set("""
the a an and or to of i it is in for my on this that you be was with but have so not are me just
they its it's im i'm can app youtube when all if do at what no get there from as your like even any
about up out one would been will more now has how only why then them we also because by very time
every keep make other really still don dont don't want use way too need some than their after
something same see let where much put going which through over these most never into
""".split())


def load_themes(path="themes.json"):
    """Turn each theme's keyword list into one regex. A * at the end of a keyword matches any ending."""
    with open(path) as f:
        themes = json.load(f)

    patterns = {}
    for theme, keywords in themes.items():
        parts = []
        for kw in keywords:
            if kw.endswith("*"):
                parts.append(re.escape(kw[:-1]) + r"\w*")
            else:
                parts.append(re.escape(kw))
        patterns[theme] = re.compile(r"\b(" + "|".join(parts) + r")\b", re.IGNORECASE)
    return patterns


def tag_reviews(reviews, patterns):
    """Add a 'themes' list to each review based on which keywords it mentions."""
    for r in reviews:
        text = f"{r['title']} {r['text']}"
        r["themes"] = [theme for theme, pattern in patterns.items() if pattern.search(text)]
    return reviews


def summarize(reviews, patterns):
    total = len(reviews)
    negative = [r for r in reviews if r["rating"] <= 2]

    theme_stats = []
    for theme in patterns:
        tagged = [r for r in reviews if theme in r["themes"]]
        if not tagged:
            continue
        neg_tagged = [r for r in tagged if r["rating"] <= 2]

        # example quotes: negative reviews of a readable length, newest first
        examples = [r for r in neg_tagged if 60 <= len(r["text"]) <= 300][:3]

        theme_stats.append({
            "theme": theme,
            "mentions": len(tagged),
            "pct_of_all": round(100 * len(tagged) / total, 1),
            "negative_mentions": len(neg_tagged),
            "pct_of_negative": round(100 * len(neg_tagged) / len(negative), 1) if negative else 0,
            "avg_rating": round(sum(r["rating"] for r in tagged) / len(tagged), 2),
            "versions": dict(Counter(r["version"] for r in neg_tagged).most_common(3)),
            "examples": [{"rating": r["rating"], "title": r["title"], "text": r["text"]} for r in examples],
        })

    # rank by how many unhappy reviews each theme shows up in
    theme_stats.sort(key=lambda t: t["negative_mentions"], reverse=True)

    # negative reviews no theme caught: what are they talking about?
    untagged = [r for r in negative if not r["themes"]]
    words = Counter()
    for r in untagged:
        tokens = re.findall(r"[a-z']+", f"{r['title']} {r['text']}".lower())
        words.update({t for t in tokens if t not in STOPWORDS and len(t) > 2})

    return {
        "total_reviews": total,
        "rating_counts": {str(s): sum(1 for r in reviews if r["rating"] == s) for s in range(5, 0, -1)},
        "avg_rating": round(sum(r["rating"] for r in reviews) / total, 2),
        "negative_reviews": len(negative),
        "themes": theme_stats,
        "untagged_negative": len(untagged),
        "untagged_top_words": words.most_common(15),
    }


if __name__ == "__main__":
    with open("reviews.json") as f:
        reviews = json.load(f)

    patterns = load_themes()
    reviews = tag_reviews(reviews, patterns)
    summary = summarize(reviews, patterns)

    with open("analysis.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"{summary['total_reviews']} reviews | avg rating {summary['avg_rating']} | {summary['negative_reviews']} negative (1-2 stars)\n")
    print("Top issues among unhappy reviewers:")
    for t in summary["themes"]:
        print(f"  {t['theme']:<28} in {t['pct_of_negative']:>5}% of negative reviews  (avg rating {t['avg_rating']})")

    print(f"\n{summary['untagged_negative']} negative reviews didn't match any theme.")
    print("Common words in those (ideas for new themes):")
    print("  " + ", ".join(w for w, _ in summary["untagged_top_words"]))
    print("\nFull results saved to analysis.json")
