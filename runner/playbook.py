#!/usr/bin/env python3
"""Playbook drafts: a first set of cast rules for one deck, read off Forge's own card scripts.

    runner/playbook.py draft --deck hail-caesar [--runtime forge/runtime-snapshot] [--league runner/precon-league.json]
                             [--out playbook/variants/hail-caesar-draft.json]
    runner/playbook.py roles --deck hail-caesar [--runtime ...]     # the classification only, one card a line
    runner/playbook.py adapt --deck blight-curse --deck-file "/abs/My List.dck" [--base FILE] [--out FILE]
                             [--no-forge-rule] [--no-wait] [--runtime ...]   # a precon's playbook for a list of your own

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

`adapt` is for playtesting a list of your own that started as a precon (DESIGN.md section 31): the precon's playbook
(playbook/precons/<deck>.json, or --base FILE) cut to the cards the list still holds, because the harness refuses a
playbook that names a card its deck does not have. A rule loses the cards the list dropped and goes when none is
left, when its target is gone, or when it waits for a permanent the list no longer has; a hold whose release waits
for such a permanent holds for good. The cards the list added are named by no rule, so they are Forge's to cast at a
`{"forge": "unnamed", "wait": "main2"}` rule, which `adapt` puts after the commander's rule when the playbook has no
forge rule of its own (playbook/README.md: without it the rules starve what they do not name). It prints what it cut,
what is new, and which new cards Forge's AI never casts by itself (AI:RemoveDeck:All: those need a play rule written
for them, or they stay in hand). The result is written next to the list (<list>.playbook.json) for
`runner/ab.py play --deck-file LIST.dck --data LIST.playbook.json --arms stock,playbook`.
"""
import argparse
import datetime as dt
import hashlib
import json
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


CONTROLS = re.compile(r"^(not\s+)?controls\s+(.+)$")
KINDS = ("play", "activate", "hold", "forge")


def _list(v):
    return [] if v is None else list(v) if isinstance(v, list) else [v]


def adapt_playbook(pb, have, commanders, forge_rule=True, wait=True):
    """A playbook cut to the cards a list holds: (playbook, report). `have(name)` says whether the list has a card."""
    pb = json.loads(json.dumps(pb))
    rep = {"dropped_rules": [], "trimmed_rules": [], "holds_for_good": [], "dropped_triggers": [], "forge_rule": None}

    def conditions(conds, hold):
        """(kept conditions, the missing permanent the rule waits for or None, whether any condition was removed)."""
        keep, never, removed = [], None, False
        for c in _list(conds):
            m = CONTROLS.match(str(c).strip())
            if m and not have(m.group(2).strip()):
                removed = True
                if not m.group(1):
                    never = m.group(2).strip()      # "controls X" can never hold without X
                continue                             # "not controls X" always holds without X
            keep.append(c)
        return keep, never, removed

    cast = pb.get("cast")
    if isinstance(cast, dict):
        rules = []
        for i, r in enumerate(_list(cast.get("rules")), 1):
            r = dict(r)
            kind = next((k for k in KINDS if k in r), None)
            if kind is None:
                rules.append(r)
                continue
            if kind != "forge":
                names = _list(r[kind])
                kept = [n for n in names if have(n)]
                if not kept:
                    rep["dropped_rules"].append({"rule": i, "kind": kind, "cards": names, "why": "none of its cards is in the list"})
                    continue
                if len(kept) < len(names):
                    rep["trimmed_rules"].append({"rule": i, "kind": kind, "removed": [n for n in names if not have(n)]})
                    r[kind] = kept
            if r.get("target") and not have(r["target"]):
                rep["dropped_rules"].append({"rule": i, "kind": kind, "cards": _list(r.get(kind)), "why": f"its target, {r['target']}, is not in the list"})
                continue
            key = "until" if kind == "hold" else "when"
            if key in r:
                keep, never, removed = conditions(r[key], kind == "hold")
                if never and kind == "hold":
                    r.pop(key)                       # released only with a permanent the list does not have: never
                    rep["holds_for_good"].append({"rule": i, "cards": _list(r[kind]), "waited_for": never})
                elif never:
                    rep["dropped_rules"].append({"rule": i, "kind": kind, "cards": _list(r.get(kind)), "why": f"it waits for {never}, which is not in the list"})
                    continue
                elif keep:
                    r[key] = keep
                else:
                    r.pop(key)
                    if kind == "hold" and removed:
                        rep["dropped_rules"].append({"rule": i, "kind": kind, "cards": _list(r[kind]),
                                                     "why": "its release only waited for the absence of a permanent the list does not have"})
                        continue
            rules.append(r)
        if forge_rule and not any("forge" in r for r in rules):
            hits = [i for i, r in enumerate(rules) if any(c in _list(r.get("play")) for c in commanders)]
            at = hits[0] + 1 if hits else 0
            rules.insert(at, {"forge": "unnamed", "wait": "main2"} if wait else {"forge": "unnamed"})
            rep["forge_rule"] = {"position": at + 1, "after": _list(rules[at - 1].get("play"))[:3] if at else None, "wait": bool(wait)}
        cast["rules"] = rules
        if isinstance(cast.get("groups"), dict):
            cast["groups"] = {g: [n for n in _list(v) if have(n)] for g, v in cast["groups"].items()}
    triggers = []
    for i, r in enumerate(_list(pb.get("triggers")), 1):
        r = dict(r)
        key = "accept" if "accept" in r else "decline"
        names = _list(r.get(key))
        kept = [n for n in names if have(n)]
        keep, never, _removed = conditions(r.get("when"), False)
        if not kept or never:
            rep["dropped_triggers"].append({"rule": i, "cards": names, "why": "none of its cards is in the list" if not kept else f"it waits for {never}, which is not in the list"})
            continue
        r[key] = kept
        if "when" in r:
            if keep:
                r["when"] = keep
            else:
                r.pop("when")
        triggers.append(r)
    if "triggers" in pb:
        if triggers:
            pb["triggers"] = triggers
        else:
            pb.pop("triggers")
    return pb, rep


def adapt(args):
    base_path = args.base or os.path.join(ROOT, "playbook", "precons", args.deck + ".json")
    base = deckdata.load_json(base_path)
    if not isinstance(base.get("playbook"), dict):
        sys.exit(f"playbook.py: {base_path} has no playbook object (the deck has no shipped playbook: name a candidate with --base)")
    if not os.path.isfile(args.deck_file):
        sys.exit(f"playbook.py: {args.deck_file}: no such deck file")
    main_cards, cmd = deckdata.read_dck(args.deck_file)
    in_list = {n for n, _ in main_cards} | {n for n, _ in cmd}
    commanders = [n for n, _ in cmd]

    def have(name):
        return name in in_list or name.endswith(" Token")

    pb, rep = adapt_playbook(base["playbook"], have, commanders, forge_rule=not args.no_forge_rule, wait=not args.no_wait)
    rules = _list((pb.get("cast") or {}).get("rules"))
    named = {n for r in rules for n in _list(r.get("play"))}
    scripts = deckdata.CardScripts(args.runtime) if args.runtime and os.path.isdir(args.runtime) else None
    unnamed, never_cast, unknown = [], [], []
    for name, _count in cmd + main_cards:
        if name in named:
            continue
        if scripts is None:
            unnamed.append(name)
            continue
        card, raw = raw_script(scripts, name)
        if card is None:
            unknown.append(name)
            continue
        if "Land" in card["types"] and "Creature" not in card["types"]:
            continue
        unnamed.append(name)
        if any(a.startswith("RemoveDeck:All") for a in card["ai"]):
            never_cast.append(name)
    precon_names = None
    try:
        _entry, p_main, p_cmd = read_deck(args.league, args.runtime, args.deck)
        precon_names = {n for n, _ in p_main} | {n for n, _ in p_cmd}
    except SystemExit:
        pass
    added = sorted(in_list - precon_names) if precon_names is not None else None
    cut = sorted(precon_names - in_list) if precon_names is not None else None
    out = args.out or os.path.splitext(args.deck_file)[0] + ".playbook.json"
    pb.pop("on", None)
    line = (f"Adapted by runner/playbook.py adapt for the list {os.path.basename(args.deck_file)}: the rules of {os.path.relpath(base_path, ROOT) if os.path.abspath(base_path).startswith(ROOT) else base_path} "
            "cut to the cards the list holds" + (", with a forge rule for the cards no rule names" if rep["forge_rule"] else "") + ". Not measured.")
    notes = pb.get("notes")
    pb["notes"] = (notes + [line]) if isinstance(notes, list) else ((notes + " " if notes else "") + line)
    with open(args.deck_file, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    doc = {"schema": base.get("schema"), "deck": args.deck, "variant": "list", "of": base_path if args.base else f"playbook/precons/{args.deck}.json",
           "about": f"The playbook of {args.deck} adapted to the list {os.path.basename(args.deck_file)} (runner/playbook.py adapt): only the playbook object is read.",
           "list": {"file": os.path.basename(args.deck_file), "sha256": sha, "commanders": commanders},
           "adapted": {**rep, "added_to_the_precon": added, "cut_from_the_precon": cut, "unnamed_nonland_cards": unnamed, "never_cast_by_forge": never_cast},
           "playbook": pb}
    deckdata.dump_json(out, doc)
    say = lambda *a: print(*a, file=sys.stderr)
    say(f"{out}: {len(rules)} cast rules, {len(_list(pb.get('triggers')))} trigger rules, for {os.path.basename(args.deck_file)} ({', '.join(commanders)})")
    if base["playbook"].get("cast") and commanders and not any(c in _list(r.get('play')) for r in _list(base['playbook']['cast'].get('rules')) for c in commanders):
        say(f"note: no rule of the playbook casts {', '.join(commanders)}: it was written for another commander, and most of it may not fit this list")
    if added is not None:
        say(f"against the precon: {len(added)} cards added, {len(cut)} cut")
    for d in rep["dropped_rules"]:
        say(f"  rule {d['rule']} ({d['kind']} {', '.join(d['cards'][:4])}{' ...' if len(d['cards']) > 4 else ''}) dropped: {d['why']}")
    for d in rep["trimmed_rules"]:
        say(f"  rule {d['rule']} ({d['kind']}) no longer lists: {', '.join(d['removed'])}")
    for d in rep["holds_for_good"]:
        say(f"  rule {d['rule']} now holds {', '.join(d['cards'])} for good: its release waited for {d['waited_for']}, which is not in the list")
    for d in rep["dropped_triggers"]:
        say(f"  trigger rule {d['rule']} ({', '.join(d['cards'][:4])}) dropped: {d['why']}")
    if rep["forge_rule"]:
        f = rep["forge_rule"]
        say(f"  forge rule added at position {f['position']}" + (f" (after the rule that casts {', '.join(f['after'])})" if f["after"] else " (at the top: no rule casts the commander)")
            + (", waiting for the second main phase" if f["wait"] else ""))
    own = [i + 1 for i, r in enumerate(rules) if "forge" in r and not rep["forge_rule"] and r.get("wait") != "main2"]
    if own:
        say(f"  note: the playbook's own forge rule (position {', '.join(map(str, own))}) does not wait for the second main phase: creatures and other permanents among the "
            "new cards may find the mana spent (playbook/README.md, \"wait\": \"main2\")")
    new_unnamed = [n for n in unnamed if added is None or n in added]
    say(f"named by no play rule (Forge's AI casts them, at the forge rule): {len(unnamed)} nonland cards"
        + (f", {len(new_unnamed)} of them new to the precon" + (": " + ", ".join(new_unnamed) if new_unnamed else "") if added is not None else ""))
    if never_cast:
        say("Forge's AI never casts these by itself (AI:RemoveDeck:All); without a play rule of their own they stay in hand: " + ", ".join(never_cast))
    if unknown:
        say("no card script found for: " + ", ".join(unknown))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("draft", "roles", "adapt"):
        p = sub.add_parser(name)
        p.add_argument("--deck", required=True)
        p.add_argument("--league", default=os.path.join(HERE, "precon-league.json"))
        p.add_argument("--runtime", default=os.path.join(ROOT, "forge", "runtime-snapshot"))
        if name == "draft":
            p.add_argument("--out")
        if name == "adapt":
            p.add_argument("--deck-file", required=True, help="the list as a Forge .dck (runner/decklist.py writes one)")
            p.add_argument("--base", help="a playbook file other than the deck's shipped one")
            p.add_argument("--out", help="default: next to the list, <list>.playbook.json")
            p.add_argument("--no-forge-rule", action="store_true", help="do not add a forge rule when the playbook has none")
            p.add_argument("--no-wait", action="store_true", help='the added forge rule without "wait": "main2"')
    args = ap.parse_args(argv)
    if args.cmd == "adapt":
        return adapt(args)
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
