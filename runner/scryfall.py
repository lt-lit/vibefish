#!/usr/bin/env python3
"""Resolve card names to Scryfall ids and image URIs, keeping a JSON cache.

    runner/scryfall.py --cache cards/scryfall-cache.json [--from run.json|rollup.json ...] [--name "Sol Ring" ...]
                       [--refresh] [--user-agent "Vibefish/x.y"]

Uses POST /cards/collection (75 identifiers per request), waits at least 100 ms between requests and
sends a Vibefish User-Agent, per https://scryfall.com/docs/api. Only names missing from the cache
are requested unless --refresh is given. Image files are never downloaded: the cache holds the
cards.scryfall.io URLs that the dashboard hotlinks. Standard library only.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.scryfall.com/cards/collection"
BATCH = 75
MIN_INTERVAL = 0.12  # seconds between requests; Scryfall asks for 50-100 ms


def version():
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(here, "..", "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "0.0.0"


def names_from(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    names = set()
    for deck in doc.get("decks", []):
        for c in deck.get("cards", []):
            names.add(c["name"])
        for c in deck.get("commander_cards", []):
            names.add(c["name"])
        for n in deck.get("commanders", []):
            names.add(n)
    for ds in doc.get("deck_stats", []):
        for c in ds.get("cards", []):
            names.add(c["name"])
        for n in ds.get("commanders", []):
            names.add(n)
    return names


def pick_images(face):
    uris = face.get("image_uris") or {}
    # Full card images only: Scryfall's policy and ours is never to crop the card.
    return {k: uris[k] for k in ("small", "normal") if k in uris}


def entry_for(card):
    faces = card.get("card_faces") or []
    front = pick_images(card) or (pick_images(faces[0]) if faces else {})
    e = {
        "id": card.get("id"),
        "name": card.get("name"),
        "set": card.get("set"),
        "collector_number": card.get("collector_number"),
        "layout": card.get("layout"),
        "type_line": card.get("type_line"),
        "mana_cost": card.get("mana_cost"),
        "cmc": card.get("cmc"),
        "color_identity": card.get("color_identity"),
        "scryfall_uri": card.get("scryfall_uri"),
        "image_uris": front,
    }
    if len(faces) > 1 and faces[1].get("image_uris"):
        e["back_image_uris"] = pick_images(faces[1])
    return e


def request(batch, user_agent):
    body = json.dumps({"identifiers": [{"name": n} for n in batch]}).encode("utf-8")
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "User-Agent": user_agent,
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code == 429 or err.code >= 500:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("Scryfall kept failing")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--from", dest="sources", action="append", default=[], help="run.json or rollup.json to take names from")
    ap.add_argument("--name", action="append", default=[])
    ap.add_argument("--refresh", action="store_true", help="re-resolve every name, not just missing ones")
    ap.add_argument("--user-agent", default=f"Vibefish/{version()} (+https://github.com/lt-lit/vibefish)")
    args = ap.parse_args(argv)

    wanted = set(args.name)
    for src in args.sources:
        wanted |= names_from(src)
    if not wanted:
        print("no card names given", file=sys.stderr)
        return 2

    cache = {}
    if os.path.isfile(args.cache):
        with open(args.cache, encoding="utf-8") as f:
            cache = json.load(f)
    todo = sorted(wanted if args.refresh else (n for n in wanted if n not in cache))
    print(f"{len(wanted)} names wanted, {len(todo)} to resolve, {len(cache)} already cached", file=sys.stderr)

    state = {"last": 0.0}

    def resolve(names, label):
        """Requests `names` (as given) in batches; returns the names Scryfall did not know."""
        missing = []
        for i in range(0, len(names), BATCH):
            batch = names[i:i + BATCH]
            wait = MIN_INTERVAL - (time.monotonic() - state["last"])
            if wait > 0:
                time.sleep(wait)
            state["last"] = time.monotonic()
            doc = request([q for q, _ in batch], args.user_agent)
            by_name = {}
            for card in doc.get("data", []):
                by_name[card["name"].lower()] = card
                for face in card.get("card_faces") or []:
                    by_name.setdefault(face.get("name", "").lower(), card)
            for query, original in batch:
                card = by_name.get(query.lower())
                if card is None:
                    missing.append(original)
                else:
                    cache[original] = entry_for(card)
            print(f"  {label} batch {i // BATCH + 1}: {len(doc.get('data', []))} found, "
                  f"{len(doc.get('not_found', []))} not found", file=sys.stderr)
        return missing

    not_found = resolve([(n, n) for n in todo], "names")
    # Split, adventure and double-faced cards: Forge writes "Front // Back"; Scryfall's name
    # identifier wants one face, so retry those with the front face.
    retry = [(n.split(" // ")[0], n) for n in not_found if " // " in n]
    if retry:
        still = set(resolve(retry, "front-face"))
        not_found = [n for n in not_found if " // " not in n or n in still]

    os.makedirs(os.path.dirname(os.path.abspath(args.cache)), exist_ok=True)
    with open(args.cache, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(cache.items())), f, indent=1, ensure_ascii=False)
    print(f"cache: {len(cache)} cards -> {args.cache}", file=sys.stderr)
    if not_found:
        print("not found on Scryfall: " + "; ".join(not_found), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
