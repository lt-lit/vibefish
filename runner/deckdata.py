#!/usr/bin/env python3
"""Phase 3 data generator: per-deck AI data for Forge, drafted from the decklist.

    runner/deckdata.py generate [--league runner/precon-league.json] [--runtime forge/runtime-snapshot]
                                [--out playbook/precons] [--deck ID ...] [--no-spellbook]
    runner/deckdata.py show playbook/precons/token-triumph.json          # the effective data (curated over generated)
    runner/deckdata.py forge-lines playbook/precons/token-triumph.json   # the ai-card-roles / ai-combos lines it produces

For every deck it reads the .dck, asks Commander Spellbook which combos the list contains (POST /find-my-combos,
one request per deck, at least a second apart, Vibefish User-Agent; the trimmed answer is cached next to the data
files), reads oracle text, types and keywords from Forge's own card scripts (res/cardsfolder/cardsfolder.zip), and
writes playbook/precons/<id>.json with a `generated` block:

    key_cards   names the AI's tutors fetch first and its discards protect (Forge deck metadata KeyCards, via the
                harness), in order of preference: combo pieces, then finishers
    roles       Forge card roles (res/lists/ai-card-roles.txt vocabulary) found by rule: storm payoffs, overrun
                finishers, reanimation spells and their targets, cheat spells and their targets, mass payoffs
    combos      combos entirely inside the deck, as Forge ai-combos.txt lines (win / lock, one slot per card)
    pairs       two-card combos for Forge's Commander plan (ai-commander-combos.txt format)
    deck_plan   "auto": Forge classifies the deck itself (FLAT_MC_DECK_PLAN); a curated file may force an archetype
    profile     per-seat AI profile overrides (none generated; curated only)

A `curated` block, written by hand, overrides the generated one key by key and is never touched by this script.
The harness applies the effective data to the seat that plays the deck (--data id=file); the stock seats are
untouched. Standard library only.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPELLBOOK = "https://backend.commanderspellbook.com/find-my-combos"
MIN_INTERVAL = 1.5          # seconds between Spellbook requests (they ask for ~80/min at most)
SCHEMA = 1

WIN_FEATURES = ("win the game", "infinite damage", "infinite combat damage", "infinite creature tokens", "infinite mill",
                "infinite lifeloss", "infinite life loss", "infinite poison", "each opponent loses the game", "near-infinite damage",
                "infinite direct damage", "infinite draw triggers for each opponent")
LOCK_FEATURES = ("lock", "prevent all damage", "infinite turns", "opponents can't cast", "can't untap")


def version():
    try:
        with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "dev"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------- decks and card scripts
def read_dck(path):
    """[(name, count)] of the main deck and the commanders, from a Forge .dck (bare names, set tags stripped)."""
    main, cmd, sec = [], [], None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("["):
                sec = line
                continue
            if not line or sec not in ("[Main]", "[Commander]"):
                continue
            m = re.match(r"(\d+)\s+(.*)", line)
            if not m:
                continue
            name = m.group(2).split("|")[0].strip()
            (cmd if sec == "[Commander]" else main).append((name, int(m.group(1))))
    return main, cmd


class CardScripts:
    """Forge's card scripts: Name, ManaCost, Types, PT, K: keywords, A:/T:/S: lines, Oracle text, DeckHas hints."""

    def __init__(self, runtime):
        self.zip = zipfile.ZipFile(os.path.join(runtime, "res", "cardsfolder", "cardsfolder.zip"))
        self.index = {}
        for n in self.zip.namelist():
            if n.endswith(".txt"):
                self.index[os.path.basename(n)[:-4]] = n

    @staticmethod
    def key(name):
        """Forge's script file name for a card name: ASCII, lower case, punctuation dropped, words joined by _."""
        import unicodedata
        s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
        s = re.sub(r"[',:!?\"&()]", "", s)
        s = re.sub(r"[\s\-/.]+", "_", s)
        return s.strip("_")

    def get(self, name):
        n = self.index.get(self.key(name.replace("//", "/")))     # split and double-faced cards: wear_tear.txt
        if not n:
            n = self.index.get(self.key(name.split("//")[0]))      # a face name alone
        if not n:                                                    # adventure cards: murderous_rider_swift_end.txt
            k = self.key(name.split("//")[0]) + "_"
            cands = sorted((x for x in self.index if x.startswith(k)), key=len)
            n = self.index[cands[0]] if cands else None
        if not n:
            return None
        txt = self.zip.read(n).decode("utf-8", "replace")
        card = {"name": name, "types": "", "cost": "", "pt": None, "keywords": [], "oracle": "", "abilities": [], "deckhas": "", "ai": []}
        for line in txt.splitlines():
            if line.startswith("Types:"):
                card["types"] = card["types"] or line[6:].strip()
            elif line.startswith("ManaCost:"):
                card["cost"] = card["cost"] or line[9:].strip()
            elif line.startswith("PT:"):
                card["pt"] = card["pt"] or line[3:].strip()
            elif line.startswith("K:"):
                card["keywords"].append(line[2:].strip())
            elif line.startswith(("A:", "T:", "S:", "R:")):
                card["abilities"].append(line)
            elif line.startswith("Oracle:"):
                card["oracle"] += (" " if card["oracle"] else "") + line[7:].replace("\\n", " ").strip()
            elif line.startswith("DeckHas:"):
                card["deckhas"] = line[8:].strip()
            elif line.startswith("AI:"):
                card["ai"].append(line[3:].strip())
        card["cmc"] = cmc(card["cost"])
        return card


def cmc(cost):
    total = 0
    for tok in cost.split():
        if tok.isdigit():
            total += int(tok)
        elif tok in ("X", "Y", "Z", "no", "cost"):
            continue
        elif "/" in tok:
            total += 2 if any(ch.isdigit() and int(ch) == 2 for ch in tok) else 1
        else:
            total += 1
    return total


# ---------------------------------------------------------------- Spellbook
_last_request = 0.0


def spellbook(main, cmd, cache_path, user_agent, enabled=True):
    """Trimmed find-my-combos answer for the deck; cached. Returns None when disabled and not cached."""
    if os.path.isfile(cache_path):
        return load_json(cache_path)
    if not enabled:
        return None
    global _last_request
    wait = MIN_INTERVAL - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    body = json.dumps({"main": [{"card": n, "quantity": q} for n, q in main], "commanders": [{"card": n} for n, _ in cmd]}).encode()
    req = urllib.request.Request(SPELLBOOK, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": user_agent})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise
    _last_request = time.time()
    res = data["results"]

    def trim(variants):
        out = []
        for v in variants:
            out.append({"id": v.get("id"), "cards": [u["card"]["name"] for u in v.get("uses", [])],
                        "templates": [t.get("template", {}).get("name") for t in v.get("requires", [])],
                        "produces": [p["feature"]["name"] for p in v.get("produces", [])],
                        "mana": v.get("manaNeeded"), "bracket": v.get("bracketTag"), "popularity": v.get("popularity")})
        return out
    trimmed = {"retrieved": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "identity": res.get("identity"),
               "included": trim(res.get("included", [])), "almost_included": trim(res.get("almostIncluded", [])),
               "source": SPELLBOOK}
    dump_json(cache_path, trimmed)
    return trimmed


# ---------------------------------------------------------------- roles by rule
def has_any(text, *needles):
    t = text.lower()
    return any(n in t for n in needles)


def derive_roles(cards):
    roles = {}

    def add(role, name):
        roles.setdefault(role, [])
        if name not in roles[role]:
            roles[role].append(name)

    creatures_big = []
    for c in cards:
        if c is None:
            continue
        name, o, types = c["name"], c["oracle"], c["types"]
        kws = " ".join(c["keywords"]).lower()
        is_creature = "Creature" in types
        if "storm" in kws.split() or re.search(r"\bStorm \(", o):
            add("storm_payoff", name)
        if re.search(r"creatures you control (get|gain)[^.]*\+[2-9X]/\+[0-9X]", o) and has_any(o, "until end of turn") and not is_creature:
            add("overrun", name)
        if re.search(r"creatures you control get \+X/\+X", o) and has_any(o, "until end of turn"):
            add("overrun", name)
        if re.search(r"return (target|up to \w+ target|all|any number of target) creature cards? from (your|a|all) graveyards? to the battlefield", o, re.I):
            if re.search(r"return all creature cards", o, re.I):
                add("mass_payoff", name)
            else:
                add("reanimation_spell", name)
        if re.search(r"put (a|target|an?|up to \w+|any number of) (creature|artifact|permanent|legendary) cards? from your hand onto the battlefield", o, re.I) \
                or re.search(r"cast (a|an|any number of) creature spells? from your hand[^.]*without paying", o, re.I):
            add("cheat_spell", name)
        if is_creature and c["cmc"] >= 7:
            creatures_big.append(name)
    if roles.get("reanimation_spell") or roles.get("mass_payoff"):
        for n in creatures_big:
            add("big_target", n)
    if roles.get("cheat_spell"):
        for n in creatures_big:
            add("cheat_target", n)
    return roles


def derive_combos(sb, deck_names):
    """Spellbook variants fully inside the deck -> ai-combos lines (win/lock) and two-card pairs."""
    combos, pairs = [], []
    if not sb:
        return combos, pairs
    seen = set()
    for v in sb.get("included", []):
        cards = [c for c in v["cards"] if c in deck_names]
        if len(cards) < 2 or v.get("templates") and any(v["templates"]):
            continue
        key = tuple(sorted(cards))
        if key in seen:
            continue
        seen.add(key)
        produces = " ".join(v.get("produces", [])).lower()
        kind = "win" if any(f in produces for f in WIN_FEATURES) else "lock" if any(f in produces for f in LOCK_FEATURES) else None
        if kind and len(cards) <= 4:
            combos.append({"kind": kind, "name": " + ".join(cards), "slots": [[c] for c in cards], "produces": v.get("produces", [])[:4], "spellbook": v.get("id")})
        if len(cards) == 2:
            pairs.append({"cards": cards, "produces": v.get("produces", [])[:3], "spellbook": v.get("id")})
    return combos, pairs


def derive_key_cards(roles, combos, pairs, cards_by_name, commanders):
    order = []

    def add(n):
        if n not in order and n not in commanders and n in cards_by_name:
            order.append(n)
    for c in combos:
        for slot in c["slots"]:
            add(slot[0])
    for p in pairs:
        for n in p["cards"]:
            add(n)
    for role in ("storm_payoff", "mass_payoff", "overrun"):
        for n in roles.get(role, []):
            add(n)
    for n, c in cards_by_name.items():
        if c and re.search(r"you win the game", c["oracle"], re.I) and "Creature" not in c["types"]:
            add(n)
    return order[:8]


# ---------------------------------------------------------------- data files
def effective(data):
    """The curated block laid over the generated one, key by key."""
    out = dict(data.get("generated", {}))
    for k, v in (data.get("curated") or {}).items():
        if k == "notes":
            continue
        out[k] = v
    return out


def forge_lines(eff):
    """The lines the harness feeds Forge: card roles, ai-combos entries, commander pairs."""
    roles = [f"{role} | " + " | ".join(names) for role, names in (eff.get("roles") or {}).items() if names]
    combos = [f"{c['kind']} | {c['name']} | " + " | ".join(" / ".join(s) for s in c["slots"]) for c in eff.get("combos") or []]
    pairs = [f"early_game | {p['cards'][0]} | {p['cards'][1]}" for p in eff.get("pairs") or []]
    return roles, combos, pairs


def cmd_generate(args):
    league = load_json(args.league)
    runtime = os.path.abspath(args.runtime)
    precon_dir = os.path.join(runtime, league["precon_dir"])
    scripts = CardScripts(runtime)
    ua = f"Vibefish/{version()} (+https://github.com/lt-lit/vibefish)"
    wanted = set(args.deck or [])
    today = dt.date.today().isoformat()
    n = 0
    for d in league["decks"]:
        if wanted and d["id"] not in wanted:
            continue
        main, cmd = read_dck(os.path.join(precon_dir, d["file"]))
        names = [nm for nm, _ in main]
        commanders = [nm for nm, _ in cmd]
        cards = {nm: scripts.get(nm) for nm in names + commanders}
        missing = [nm for nm, c in cards.items() if c is None]
        sb = spellbook(main, cmd, os.path.join(args.out, "spellbook", d["id"] + ".json"), ua, enabled=not args.no_spellbook)
        roles = derive_roles(list(cards.values()))
        combos, pairs = derive_combos(sb, set(names) | set(commanders))
        key_cards = derive_key_cards(roles, combos, pairs, cards, set(commanders))
        path = os.path.join(args.out, d["id"] + ".json")
        existing = load_json(path) if os.path.isfile(path) else {}
        data = {
            "schema": SCHEMA,
            "deck": d["id"], "file": d["file"], "name": d["name"], "commanders": commanders,
            "generated": {
                "on": today, "by": f"runner/deckdata.py (Vibefish {version()})",
                "key_cards": key_cards, "roles": roles, "combos": combos, "pairs": pairs,
                "deck_plan": "auto", "profile": {},
                "spellbook": {"included": len(sb["included"]), "almost_included": len(sb["almost_included"]), "identity": sb.get("identity"), "retrieved": sb.get("retrieved")} if sb else None,
                "cards_without_script": missing,
            },
            "curated": existing.get("curated") or {},
        }
        dump_json(path, data)
        n += 1
        print(f"{d['id']:<26} combos {len(combos)} pairs {len(pairs)} roles {sum(len(v) for v in roles.values()):>2} key {len(key_cards)}"
              f"  spellbook in/almost {len(sb['included']) if sb else '-'}/{len(sb['almost_included']) if sb else '-'}"
              f"{'  curated' if data['curated'] else ''}{'  NO SCRIPT: ' + ', '.join(missing) if missing else ''}", file=sys.stderr)
    print(f"{n} deck data file(s) in {args.out}", file=sys.stderr)
    return 0


def cmd_show(args):
    data = load_json(args.file)
    eff = effective(data)
    print(json.dumps({"deck": data["deck"], "commanders": data["commanders"], "effective": eff,
                      "curated_keys": sorted((data.get("curated") or {}).keys())}, indent=1, ensure_ascii=False))
    return 0


def cmd_forge_lines(args):
    eff = effective(load_json(args.file))
    roles, combos, pairs = forge_lines(eff)
    print("# ai-card-roles.txt"); print("\n".join(roles))
    print("# ai-combos.txt"); print("\n".join(combos))
    print("# ai-commander-combos.txt"); print("\n".join(pairs))
    print("# KeyCards=" + ";".join(eff.get("key_cards") or []))
    print("# FLAT_MC_DECK_PLAN=" + str(eff.get("deck_plan", "auto")) + "  profile overrides: " + json.dumps(eff.get("profile") or {}))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--league", default=os.path.join(HERE, "precon-league.json"))
    g.add_argument("--runtime", default=os.environ.get("FORGE_RUNTIME") or os.path.join(ROOT, "forge", "runtime"))
    g.add_argument("--out", default=os.path.join(ROOT, "playbook", "precons"))
    g.add_argument("--deck", action="append")
    g.add_argument("--no-spellbook", action="store_true", help="use cached Spellbook answers only")
    g.set_defaults(func=cmd_generate)
    s = sub.add_parser("show"); s.add_argument("file"); s.set_defaults(func=cmd_show)
    f = sub.add_parser("forge-lines"); f.add_argument("file"); f.set_defaults(func=cmd_forge_lines)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
