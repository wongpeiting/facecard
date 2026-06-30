"""Self-contained YouGov scrape for the interactive "face cards" chart.

Pulls the Republican + Democrat public-figure rosters from YouGov's public-data
API. Each person carries two real YouGov metrics:

  - fame       (0-100): share of Americans who know who they are
  - popularity (0-100): share with a positive opinion of them

…and the same two metrics broken down by demographic crossbreak (women, men,
millennials, generation x, baby boomers), so the chart can show how differently
each group views a figure. We also capture a popularity rank and "rising" flags,
and download the entity portrait into static/faces/ so the chart can render a
wall of faces without hotlinking.

Output: a party -> person hierarchy at static/yougov.json.

Run:  python fetch_yougov.py
"""
import datetime
import json
import re
import time
from pathlib import Path

import requests

BASE = "https://api-test.yougov.com/public-data/v5/us/search/entity/"
GROUPS = {
    "Republican": "073bb3b6-adf0-11e9-8bb2-373b0b3b3eb4",
    "Democrat": "07016957-adf0-11e9-9161-317b338eee4b",
}
# the crossbreaks YouGov exposes (besides "everyone")
DEMOS = ["women", "men", "millennials", "generationx", "babyboomers"]
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
HERE = Path(__file__).parent
OUT = HERE / "static" / "yougov.json"
FACES = HERE / "static" / "faces"


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "x"


def fetch_roster(group, crossbreak=None):
    """Page through one party's roster; return {slug: rating_data dict}.

    When crossbreak is set, the fame/popularity returned are that demographic's.
    """
    out, offset = {}, 0
    while offset < 600:
        params = {"group": group, "sort_by": "fame", "limit": 20, "offset": offset}
        if crossbreak:
            params["crossbreak"] = crossbreak
        r = requests.get(BASE, params=params, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            break
        batch = r.json().get("data", [])
        if not isinstance(batch, list) or not batch:
            break
        for e in batch:
            rd = e.get("rating_data") or {}
            if rd.get("fame") is None or rd.get("popularity") is None:
                continue
            out[slugify(e["name"])] = {"entity": e, "rating": rd}
        offset += 20
        time.sleep(0.3)
    return out


def pop_rank(group):
    """Return {slug: popularity_rank} from a popularity-sorted pass."""
    ranks, offset = {}, 0
    while offset < 600:
        r = requests.get(
            BASE,
            params={"group": group, "sort_by": "popularity", "limit": 20, "offset": offset},
            headers=HEADERS,
            timeout=30,
        )
        if r.status_code != 200:
            break
        batch = r.json().get("data", [])
        if not isinstance(batch, list) or not batch:
            break
        for e in batch:
            rd = e.get("rating_data") or {}
            if rd.get("index") is not None:
                ranks[slugify(e["name"])] = rd["index"]
        offset += 20
        time.sleep(0.3)
    return ranks


def fetch_party(party, group):
    base = fetch_roster(group)              # everyone
    demo_maps = {d: fetch_roster(group, d) for d in DEMOS}
    pranks = pop_rank(group)

    people = []
    for slug, rec in base.items():
        e, rd = rec["entity"], rec["rating"]
        values = {"everyone": {"fame": rd["fame"], "popularity": rd["popularity"]}}
        for d in DEMOS:
            hit = demo_maps[d].get(slug)
            if hit:
                values[d] = {
                    "fame": hit["rating"]["fame"],
                    "popularity": hit["rating"]["popularity"],
                }
        people.append({
            "name": e["name"],
            "slug": slug,
            "party": party,
            "type": (e.get("primary_type") or {}).get("name"),
            "fameRank": rd.get("index"),
            "popRank": pranks.get(slug),
            "rising": {
                "fame": bool(rd.get("has_fame_inc")),
                "popularity": bool(rd.get("has_popularity_inc")),
            },
            "values": values,
            "_image_url": e.get("image"),
        })
    return people


def download_face(person):
    """Save the portrait to static/faces/<slug>.jpg; return the public path or None."""
    url = person.pop("_image_url", None)
    if not url:
        return None
    dest = FACES / f"{person['slug']}.jpg"
    if dest.exists():
        return f"/faces/{dest.name}"
    try:
        img = requests.get(url, headers=HEADERS, timeout=25)
        img.raise_for_status()
        dest.write_bytes(img.content)
        time.sleep(0.1)
        return f"/faces/{dest.name}"
    except Exception as ex:
        print(f"[yougov]   face fail {person['name']}: {ex}")
        return None


def main():
    FACES.mkdir(parents=True, exist_ok=True)
    children = []
    for party, group in GROUPS.items():
        ppl = fetch_party(party, group)
        got = 0
        for p in ppl:
            p["img"] = download_face(p)
            got += 1 if p["img"] else 0
        covered = sum(1 for p in ppl if len(p["values"]) == len(DEMOS) + 1)
        print(f"[yougov] {party}: {len(ppl)} figures, {got} portraits, "
              f"{covered} with all {len(DEMOS)} crossbreaks")
        children.append({"name": party, "children": ppl})

    tree = {
        "name": "YouGov",
        "updated": datetime.date.today().isoformat(),  # date this data was pulled
        "demographics": ["everyone"] + DEMOS,
        "children": children,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(tree, indent=2))
    total = sum(len(c["children"]) for c in children)
    print(f"[yougov] wrote {total} people -> {OUT}")


if __name__ == "__main__":
    main()
