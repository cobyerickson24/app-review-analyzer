import requests
import json


def fetch_reviews(app_id, pages=3):
    reviews = []

    for page in range(1, pages + 1):
        url = f"https://itunes.apple.com/us/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
        response = requests.get(url)
        data = response.json()

        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            break  # no more reviews

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


if __name__ == "__main__":
    reviews = fetch_reviews("544007664", pages=10)
    print(f"Got {len(reviews)} reviews")

    with open("reviews.json", "w") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    print("Saved to reviews.json")

    # count reviews by star rating
    for stars in range(5, 0, -1):
        count = sum(1 for r in reviews if r["rating"] == stars)
        print(f"{stars}-star: {count}")
