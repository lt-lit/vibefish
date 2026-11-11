#!/usr/bin/env python3
"""Playbook drafts: a first set of cast rules for one deck, read off Forge's own card scripts.

    runner/playbook.py draft --deck hail-caesar [--runtime forge/runtime-snapshot] [--league runner/precon-league.json]
                             [--out playbook/variants/hail-caesar-draft.json]
    runner/playbook.py roles --deck hail-caesar [--runtime ...]     # the classification only, one card a line

A draft is where a deck's playbook starts, not where it ends. It sorts the deck's non-land cards by what their
scripts say they are and writes the cast rules every hand-written playbook so far began with:

    mana        cheap permanents with a mana ability, and sorceries that put lands onto the battlefield: first
    commander   cast from the command zone whenever it can be
    team pump   "creatures you control get/gain ... until end of turn": only before combat with attackers to use it,
                and held otherwise
    engines     enchantments, artifacts and planeswalkers that are not aimed at anything: next
    bodies      creatures and untargeted token sorceries, the dearest that can be paid for first
    card draw   untargeted draw sorceries, last

Everything else stays with Forge's AI: instants, anything aimed (a permanent whose enters trigger takes a target
included), X spells, storm spells, auras and equipment, sweepers and other symmetrical effects, and cards whose
script tells the AI when to play them (NeedsToPlay). The draft names what it
left out and why, the cards Forge's AI never casts by itself (AI:RemoveDeck:All: a card it leaves out and Forge will
not cast needs a hand-written rule), and the deck's optional triggers (candidates for a trigger rule), so the next
step is plain: goldfish it against stock (runner/goldfish.sh -P, runner/hands.py compare), read the slow games
(runner/hands.py game, held), then write the deck's own lines (playbook/README.md, Writing one).

The output is a variant file (playbook/variants/<deck>-draft.json): the harness and runner/ab.py play it as it is
(--playbook / --data), and it never replaces a deck's shipped playbook by itself. Standard library only.
"""
import argparse
import datetime as dt
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import deckdata  # noqa: E402  (CardScripts, read_dck, load_json, dump_json)

TEAM_PUMP = re.compile(r"creatures you control (get|gain|have)[^.]*until end of turn|until end of turn, creatures you control (get|gain|have)", re.I)
LAND_TO_PLAY = re.compile(r"search your library for [^.]*\bland\b[^.]*\bonto the battlefield", re.I)
SWEEPING = re.compile(r"\b(destroy|exile|sacrifice|return) (all|each)\b|\ball creatures\b|\beach (player|creature|opponent) (sacrifices|discards)\b"
                      r"|\bdeals? \w+ damage to each (creature|player|other)\b", re.I)
ENTERS_AIMED = re.compile(r"\bwhen(ever)? [^.]*\benters\b[^.]*\btarget\b", re.I)
OPTIONAL = re.compile(r"\byou may\b", re.I)


def raw_script(scripts, name):
    """The card's whole script, or None (CardScripts.get keeps only some lines)."""
    card = scripts.get(name)
    if card is None:
        return None, None
    n = scripts.index.get(scripts.key(name.replace("//", "/"))) or scripts.index.get(scripts.key(name.split("//")[0])) \
        or scripts.index.get(scripts.key(name.replace(".", "")))
    if not n:
        k = scripts.key(name.split("//")[0]) + "_"
        cands = sorted((x for x in scripts.index if x.startswith(k)), key=len)
        n = scripts.index[cands[0]] if cands else None
    return card, scripts.zip.read(n).decode("utf-8", "replace") if n else ""


def classify(name, card, raw, is_commander):
    """(role, why) for one non-land card. Roles: mana, ramp, commander, team_pump, engine, body, tokens, draw, forge."""
    types = card["types"]
    oracle = card["oracle"]
    cost = card["cost"]
    lines = raw.splitlines()
    spell_lines = [l for l in lines if l.startswith("A:SP$")]
    is_permanent = not re.search(r"\b(Instant|Sorcery)\b", types)
    has_x = bool(re.search(r"\bX\b", cost))
    needs_to_play = any(l.startswith("SVar:NeedsToPlay") for l in lines)
    aimed = any("ValidTgts$" in l or "TgtPrompt$" in l for l in spell_lines)
    if not is_permanent and not aimed:
        # a sub-ability of the spell may take the target (SubAbility$ X -> SVar:X:DB$ ... ValidTgts$)
        subs = set(re.findall(r"SubAbility\$ (\w+)", " ".join(spell_lines)))
        seen = set()
        while subs:
            s = subs.pop()
            if s in seen:
                continue
            seen.add(s)
            for l in lines:
                if l.startswith("SVar:" + s + ":"):
                    if "ValidTgts$" in l or "TgtPrompt$" in l:
                        aimed = True
                    subs |= set(re.findall(r"SubAbility\$ (\w+)", l))
    mana_ability = any(re.match(r"A:AB\$ Mana(Reflected)? ", l) for l in lines)

    if is_commander:
        return ("commander", "") if not has_x else ("forge", "X in its cost")
    if has_x:
        return "forge", "X in its cost"
    if needs_to_play:
        return "forge", "its script says when (NeedsToPlay)"
    if "Aura" in types or "Equipment" in types:
        return "forge", "aura or equipment"
    if is_permanent:
        if SWEEPING.search(oracle):
            return "forge", "sweeping or symmetrical"
        if ENTERS_AIMED.search(oracle):
            return "forge", "aimed when it enters"
        if mana_ability and card["cmc"] <= (2 if "Creature" in types else 3):
            return "mana", ""
        if "Creature" in types:
            return "body", ""
        return "engine", ""
    # instants and sorceries
    if "Instant" in types and not LAND_TO_PLAY.search(oracle):
        return "forge", "instant"
    if aimed:
        return "forge", "aimed"
    if SWEEPING.search(oracle):
        return "forge", "sweeping or symmetrical"
    if LAND_TO_PLAY.search(oracle) and card["cmc"] <= 5:
        return "ramp", ""
    if TEAM_PUMP.search(oracle):
        return "team_pump", ""
    if any(k.split(":")[0] == "Storm" for k in card["keywords"]):
        return "forge", "storm"
    if any(re.match(r"A:SP\$ Token ", l) for l in spell_lines):
        return "tokens", ""
    if re.search(r"\bdraw\b", oracle, re.I):
        return "draw", ""
    return "forge", "sorcery of no drafted kind"


def read_deck(league_path, runtime, deck_id):
    league = deckdata.load_json(league_path)
    entry = next((d for d in league["decks"] if d["id"] == deck_id), None)
    if entry is None:
        sys.exit(f"playbook.py: no deck {deck_id!r} in {league_path}")
    dck = os.path.join(runtime, "res", "quest", "commanderprecons", entry["file"])
    if not os.path.isfile(dck):
        sys.exit(f"playbook.py: {dck} not found (is --runtime a fetched Forge runtime?)")
    main, cmd = deckdata.read_dck(dck)
    return entry, main, cmd


def roles_of(scripts, main, cmd):
    out, missing = [], []
    for names, is_cmd in ((cmd, True), (main, False)):
        for name, _count in names:
            card, raw = raw_script(scripts, name)
            if card is None:
                missing.append(name)
                continue
            if "Land" in card["types"] and "Creature" not in card["types"]:
                continue
            role, why = classify(name, card, raw, is_cmd)
            flagged = any(a.startswith("RemoveDeck:All") for a in card["ai"])
            optional = bool(OPTIONAL.search(card["oracle"])) and any(l.startswith("T:") for l in raw.splitlines())
            out.append({"name": name, "role": role, "why": why, "cmc": card["cmc"], "types": card["types"],
                        "flagged": flagged, "optional_trigger": optional})
    return out, missing


def draft(deck_id, cards):
    by = {}
    for c in cards:
        by.setdefault(c["role"], []).append(c)

    def names(role, key):
        return [c["name"] for c in sorted(by.get(role, []), key=key)]

    cheap_first = lambda c: (c["cmc"], c["name"])           # noqa: E731
    dear_first = lambda c: (-c["cmc"], c["name"])           # noqa: E731
    rules = []
    mana = names("mana", cheap_first) + names("ramp", cheap_first)
    if mana:
        rules.append({"play": mana})
    if by.get("commander"):
        rules.append({"play": names("commander", cheap_first)})
    pump = names("team_pump", cheap_first)
    if pump:
        rules.append({"play": pump, "when": ["attackers >= 4"], "phase": "main1"})
        rules.append({"hold": pump, "until": ["attackers >= 4", "main == 1"]})
    engines = names("engine", cheap_first)
    if engines:
        rules.append({"play": engines})
    bodies = [c["name"] for c in sorted(by.get("body", []) + by.get("tokens", []), key=dear_first)]
    if bodies:
        rules.append({"play": bodies})
    draw = names("draw", cheap_first)
    if draw:
        rules.append({"play": draw, "when": ["library >= 20"]})
    left = [{"card": c["name"], "why": c["why"]} for c in by.get("forge", [])]
    never = [c["name"] for c in cards if c["flagged"] and c["role"] == "forge"]
    return {
        "schema": 1,
        "deck": deck_id,
        "variant": "draft",
        "of": f"playbook/precons/{deck_id}.json",
        "about": "Drafted by runner/playbook.py from Forge's card scripts: a starting point for the deck's own playbook, "
                 "not a tuned one. Only the playbook object is read by the harness.",
        "playbook": {
            "version": 0,
            "cast": {"rules": rules},
            "notes": "Draft: mana first, the commander, team pumps only before combat with attackers, engines, creatures dearest "
                     "first, card draw last. Everything in draft.left_to_forge is still Forge's to cast.",
            "on": dt.date.today().isoformat(),
        },
        "draft": {
            "by": "runner/playbook.py " + deckdata.version(),
            "left_to_forge": left,
            "never_cast_by_forge": never,
            "cast_by_rule_though_flagged": [c["name"] for c in cards if c["flagged"] and c["role"] != "forge"],
            "optional_triggers": [c["name"] for c in cards if c["optional_trigger"]],
        },
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("draft", "roles"):
        p = sub.add_parser(name)
        p.add_argument("--deck", required=True)
        p.add_argument("--league", default=os.path.join(HERE, "precon-league.json"))
        p.add_argument("--runtime", default=os.path.join(ROOT, "forge", "runtime-snapshot"))
        if name == "draft":
            p.add_argument("--out")
    args = ap.parse_args(argv)
    entry, main_cards, cmd = read_deck(args.league, args.runtime, args.deck)
    scripts = deckdata.CardScripts(args.runtime)
    cards, missing = roles_of(scripts, main_cards, cmd)
    if missing:
        print(f"playbook.py: no script found for {missing}", file=sys.stderr)
    if args.cmd == "roles":
        for c in sorted(cards, key=lambda c: (c["role"], c["cmc"], c["name"])):
            print(f"{c['role']:<10} {c['cmc']:>2}  {c['name']}" + (f"   [{c['why']}]" if c["why"] else "")
                  + ("   AI:RemoveDeck:All" if c["flagged"] else "") + ("   optional trigger" if c["optional_trigger"] else ""))
        return 0
    out = args.out or os.path.join(ROOT, "playbook", "variants", f"{args.deck}-draft.json")
    d = draft(args.deck, cards)
    deckdata.dump_json(out, d)
    n = sum(len(r.get("play", [])) for r in d["playbook"]["cast"]["rules"])
    print(f"{out}: {len(d['playbook']['cast']['rules'])} rules over {n} cards; {len(d['draft']['left_to_forge'])} left to Forge "
          f"({len(d['draft']['never_cast_by_forge'])} of them never cast by its AI: {', '.join(d['draft']['never_cast_by_forge']) or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
