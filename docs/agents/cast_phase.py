#!/usr/bin/env python3
"""cast_phase.py RUN_DIR ARM DECK CARD [CARD ...]: for the seat that plays DECK, on its own turns, where each cast of CARD falls:
before the seat's attack declaration of that turn (main 1), after it (main 2), or on a turn without an attack of the seat."""
import json, sys, glob, os, collections
run, arm, deck = sys.argv[1:4]; cards = sys.argv[4:]
tot = {c: collections.Counter() for c in cards}
allc = collections.Counter()
for rj in glob.glob(os.path.join(run, f"arm-{arm}", "*", "run.json")):
    r = json.load(open(rj))
    seats = r.get("seats") or r.get("decks") or []
    focus = None
    for i, s in enumerate(seats):
        sid = s.get("id") if isinstance(s, dict) else s
        if sid == deck: focus = s.get("seat", i) if isinstance(s, dict) else i
    if focus is None: continue
    for g in glob.glob(os.path.join(os.path.dirname(rj), "games", "*.events.jsonl")):
        turn_seat = None; attacked = False; pend = []
        def flush():
            for card, after in pend:
                key = ("after attack" if after else "before attack") if attacked_turn[0] else "no attack"
                if card in tot: tot[card][key] += 1
                allc[key] += 1
        attacked_turn = [False]
        for line in open(g):
            e = json.loads(line)
            if e["e"] == "turn":
                flush(); pend = []; attacked_turn = [False]; turn_seat = e["seat"]
            elif e["e"] == "attack" and e.get("seat") == focus and turn_seat == focus:
                attacked_turn[0] = True
            elif e["e"] == "cast" and e.get("seat") == focus and turn_seat == focus and e.get("spell"):
                pend.append((e["card"], attacked_turn[0]))
        flush()
print(f"{deck} {arm}: all spells on own turn {dict(allc)}")
for c in cards:
    print(f"   {c}: {dict(tot[c])}")
