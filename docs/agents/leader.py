#!/usr/bin/env python3
"""leader.py DIR...: which thing a table can see says who goes on to win? A session helper (DESIGN.md section 33).

Reads every *.events.jsonl under the directories (a league's shards, an A/B run's merged shards). For each `turn` event
with three or four players alive it takes, for each score below, the one seat that is strictly highest, and counts how
often that seat is the game's eventual winner, beside chance (one in the players alive). By the round of the game
(a seat's own turn number) and overall. The scores are sums of what the `turn` event holds for a seat: `bf` (all its
permanents, lands included), `nl` (its nonland permanents: `bf` less `lands`), `life`, and `dealt` (the damage it has
dealt to other players so far), with integer weights written `3*nl`. This is where the default of an aim's judgement
of danger comes from: life plus twice the nonland permanents.

    python3 -I docs/agents/leader.py results/<league run> [results/ab-<deck> ...]
"""
import json, sys, glob, os, collections
feats = ["nl", "bf", "life", "dealt", "life+2*nl", "life+3*nl", "life+4*nl", "life+2*bf", "life+3*bf", "life+dealt", "life+2*nl+lands", "life+3*nl+dealt"]
hit = collections.defaultdict(lambda: [0, 0, 0.0])   # (bucket, feat) -> [picks, wins, chance]
games = 0
for d in sys.argv[1:]:
    for f in glob.iglob(os.path.join(d, "**", "*.events.jsonl"), recursive=True):
        winner = None; turns = []; dealt = collections.Counter(); snap = []
        for line in open(f):
            if '"e":"turn"' in line:
                e = json.loads(line); snap.append((e, dict(dealt)))
            elif '"e":"damage"' in line:
                e = json.loads(line)
                if e.get("source_seat") is not None and e["source_seat"] != e["seat"]: dealt[e["source_seat"]] += e["amount"]
            elif '"e":"game_end"' in line:
                winner = json.loads(line).get("winner")
        if winner is None: continue
        games += 1
        for e, dl in snap:
            st = [s for s in e["state"] if s["alive"]]
            if len(st) < 3: continue
            rnd = e["own_turn"]
            b = "r1-3" if rnd <= 3 else "r4-6" if rnd <= 6 else "r7-9" if rnd <= 9 else "r10+"
            for ft in feats:
                def val(s):
                    v = {"bf": s["bf"], "nl": s["bf"] - s["lands"], "lands": s["lands"], "hand": len(s["hand"]), "life": s["life"], "dealt": dl.get(s["seat"], 0)}
                    tot = 0
                    for term in ft.split("+"):
                        k = term.split("*")
                        tot += (int(k[0]) * v[k[1]]) if len(k) == 2 else v[k[0]]
                    return tot
                vals = sorted(((val(s), s["seat"]) for s in st), reverse=True)
                if vals[0][0] == vals[1][0]: continue
                for key in (b, "all"):
                    h = hit[(key, ft)]; h[0] += 1; h[1] += vals[0][1] == winner; h[2] += 1.0 / len(st)
print(f"{games} finished games")
for b in ("r1-3", "r4-6", "r7-9", "r10+", "all"):
    print(b + ": " + "  ".join(f"{ft} {100 * hit[(b, ft)][1] / max(1, hit[(b, ft)][0]):.0f}% ({100 * hit[(b, ft)][2] / max(1, hit[(b, ft)][0]):.0f}%)" for ft in feats))
