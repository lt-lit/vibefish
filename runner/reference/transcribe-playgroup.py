#!/usr/bin/env python3
"""Transcribe Playgroup.gg's public precon tier page into Vibefish's human reference file, from a SAVED COPY.

    python3 -I runner/reference/transcribe-playgroup.py precons.html forge/runtime/res/quest/commanderprecons \
        runner/reference/playgroup-commander.json /tmp/league-draft.json

This script never touches the network: save https://playgroup.gg/commander/precons from a browser (or one curl)
and pass the file. It reads the page's JSON-LD dataset facts and the tier rows (rank, tier, win rate, games, game
changers), the directory (set, release, face commander, colours), updates `precon_win_rate` and `precon_table` in
the reference file with the retrieval date, and writes a draft league manifest that matches each precon to a
Forge-bundled .dck by name, falling back to the face commander. It is a provenance record for the figures in the
reference file and the tool for the next refresh (a new reference date, a new league name); Playgroup's figures
are CC BY 4.0. Standard library only.
"""
import datetime as dt
import glob
import html
import json
import os
import re
import sys
import unicodedata

SRC = sys.argv[1]            # saved precons.html
PRECON_DIR = sys.argv[2]     # Forge res/quest/commanderprecons
REF_OUT = sys.argv[3]        # runner/reference/playgroup-commander.json (updated in place)
MANIFEST_OUT = sys.argv[4]   # draft manifest
RETRIEVED = sys.argv[5] if len(sys.argv) > 5 else dt.date.today().isoformat()   # retrieval date, YYYY-MM-DD

h = open(SRC, encoding="utf-8", errors="replace").read()

# ---- dataset facts from the page's JSON-LD
ld = re.search(r'<script type="application/ld\+json">(\{"@context":"https://schema.org","@type":"Dataset".*?)</script>', h, re.S).group(1)
dataset = json.loads(ld)
facts = {v["name"]: v["value"] for v in dataset["variableMeasured"]}

# ---- tier rows (the mobile layout: one block per ranked precon)
rows = {}
row_re = re.compile(
    r"<span class='font-oswald tabular-nums w-7 text-center shrink-0[^']*'>(?P<rank>\d+)</span>\s*"
    r"<span class='[^']*font-bold border shrink-0[^']*'>(?P<tier>[A-F])</span>.*?"
    r'<a title="(?P<title>[^"]*) precon decklist" class="[^"]*" href="(?P<href>/sets/[^/]+/precons/[^"]+)">(?P<name>[^<]+)</a>.*?'
    r"<span class='font-oswald tabular-nums text-sm[^']*'>\s*(?P<pct>[0-9.]+)%\s*</span>.*?"
    r"<span class='text-on-surface_variant text-xs'>(?P<games>[0-9,]+) games</span>"
    r"(?P<rest>.*?)</div>\s*</div>\s*<div class='shrink-0 flex items-center gap-1'>", re.S)
for m in row_re.finditer(h):
    href = m.group("href")
    gc = re.search(r">(\d+) GC<", m.group("rest"))
    rows[href] = {
        "rank": int(m.group("rank")), "tier": m.group("tier"), "name": html.unescape(m.group("name")).strip(),
        "win_rate": round(float(m.group("pct")) / 100, 4), "games": int(m.group("games").replace(",", "")),
        "game_changers": int(gc.group(1)) if gc else 0, "path": href,
    }
assert len(rows) == facts["Total Precons Ranked"], (len(rows), facts)

# ---- directory: set name, release, commander, colours per precon
dir_start = h.index("data-testid='precon-directory'")
directory = h[dir_start:]
set_re = re.compile(r'<a class="font-medium text-on-surface hover:text-primary" href="(/sets/[^"]+)">([^<]+)</a>\s*<span class=\'text-xs text-on-surface_variant\'>([^<]*)</span>')
pre_re = re.compile(r"data-testid='directory-precon'>(.*?)data-testid='directory-win-rate'>(.*?)</span>\s*</span>", re.S)
events = []
for m in set_re.finditer(directory):
    events.append((m.start(), "set", (m.group(1), html.unescape(m.group(2)).strip(), html.unescape(m.group(3)).strip())))
for m in pre_re.finditer(directory):
    events.append((m.start(), "precon", (m.group(1), m.group(2))))
events.sort()
cur_set = None
for _, kind, payload in events:
    if kind == "set":
        cur_set = payload
        continue
    body, wr = payload
    href = re.search(r'href="(/sets/[^/]+/precons/[^"]+)"', body).group(1)
    cmdr = re.search(r"text-\[11px\] ml-1'>([^<]*)</span>", body)
    colors = re.findall(r'alt="\{([WUBRGC])\}"', body)
    r = rows.get(href)
    if r is None:
        continue
    r["set"] = cur_set[1] if cur_set else None
    r["set_release"] = cur_set[2] if cur_set else None
    r["set_path"] = cur_set[0] if cur_set else None
    r["commander"] = html.unescape(cmdr.group(1)).strip() if cmdr else None
    r["colors"] = "".join(colors)
missing = [r["name"] for r in rows.values() if "commander" not in r]
assert not missing, missing

# ---- Forge precon files
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.replace("&", "and").replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

forge = []
for p in sorted(glob.glob(os.path.join(PRECON_DIR, "*.dck"))):
    fn = os.path.basename(p)
    m = re.match(r"(.*?)\s*\[([A-Z0-9]+)\]\s*\[(\d{4})\]\s*\.dck$", fn)
    if not m:
        print("unparsed file name:", fn, file=sys.stderr)
        continue
    cmdrs = []
    section = None
    for line in open(p, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("["):
            section = line
            continue
        if section == "[Commander]" and line:
            card = line.split(" ", 1)[1] if " " in line else line
            cmdrs.append(card.split("|")[0].strip())
    forge.append({"file": fn, "name": m.group(1).strip(), "set": m.group(2), "year": int(m.group(3)), "commanders": cmdrs})

by_name = {}
for f in forge:
    by_name.setdefault(norm(f["name"]), []).append(f)
by_cmdr = {}
for f in forge:
    for c in f["commanders"]:
        by_cmdr.setdefault(norm(c), []).append(f)

matched, unmatched = [], []
for href, r in sorted(rows.items(), key=lambda kv: kv[1]["rank"]):
    cands = by_name.get(norm(r["name"]), [])
    how = "name"
    if len(cands) > 1:
        # prefer the newest printing (Playgroup tracks 2022+ precons)
        cands = sorted(cands, key=lambda f: -f["year"])[:1]
        how = "name, newest printing"
    if not cands and r.get("commander"):
        cands = by_cmdr.get(norm(r["commander"]), [])
        how = "commander"
    if len(cands) == 1:
        f = cands[0]
        matched.append({"playgroup": r, "forge": f, "how": how})
    else:
        unmatched.append(r)

print(f"ranked precons: {len(rows)}; Forge files: {len(forge)}; matched: {len(matched)}; unmatched: {len(unmatched)}", file=sys.stderr)
for u in unmatched:
    print(f"  unmatched: {u['name']} ({u['set']}; {u['commander']}) {u['win_rate']*100:.2f}% {u['games']} games", file=sys.stderr)
for m in matched:
    if m["how"] != "name":
        print(f"  matched by {m['how']}: {m['playgroup']['name']} -> {m['forge']['file']}", file=sys.stderr)
    if m["playgroup"].get("commander") and norm(m["playgroup"]["commander"]) not in [norm(c) for c in m["forge"]["commanders"]]:
        print(f"  COMMANDER DIFFERS: {m['playgroup']['name']}: playgroup '{m['playgroup']['commander']}' vs forge {m['forge']['commanders']}", file=sys.stderr)

# ---- reference file
ref = json.load(open(REF_OUT, encoding="utf-8"))
ref["retrieved"] = RETRIEVED
table = {}
for href, r in sorted(rows.items(), key=lambda kv: kv[1]["rank"]):
    table[r["name"]] = {"win_rate": r["win_rate"], "games": r["games"], "rank": r["rank"], "tier": r["tier"],
                        "set": r["set"], "commander": r["commander"], "colors": r["colors"],
                        "game_changers": r["game_changers"], "page": "https://playgroup.gg" + r["path"]}
ref["precon_win_rate"] = table
ref["precon_table"] = {
    "page": "https://playgroup.gg/commander/precons",
    "page_updated": dataset.get("dateModified"),
    "license": dataset.get("license"),
    "precons_ranked": facts["Total Precons Ranked"],
    "stock_games": facts["Total Stock Games Analyzed"],
    "min_games": facts["Minimum Games Threshold"],
    "min_pilots": facts["Minimum Distinct Pilots Threshold"],
    "tiers": {"A": ">= 30%", "B": "25-30%", "C": "18-25%", "D": "< 18%"},
}
notes = [n for n in ref.get("notes", []) if not n.startswith("Precon win rates")]
notes.insert(0, "Precon win rates are for stock decklists against whatever the rest of the table played, normalised to a 4-player baseline where 25% is even; a precon needs at least 20 stock games from 10 pilots to be listed. All 92 ranked precons were transcribed from one saved copy of the public tier page on " + RETRIEVED + " (CC BY 4.0, https://playgroup.gg/commander/precons); nothing in the pipeline fetches from playgroup.gg.")
ref["notes"] = notes
json.dump(ref, open(REF_OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(REF_OUT, "a").write("\n")

# ---- draft manifest
def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", norm(s))).strip("-")
ids = {}
decks = []
for m in matched:
    f, r = m["forge"], m["playgroup"]
    i = slug(f["name"])
    if i in ids:
        i = f"{i}-{f['set'].lower()}"
    ids[i] = True
    decks.append({"id": i, "file": f["file"], "name": f["name"], "commanders": f["commanders"], "set": f["set"], "year": f["year"],
                  "reference_name": r["name"], "playgroup_tier": r["tier"], "playgroup_games": r["games"]})
manifest = {
    "name": "league-v1",
    "status": "draft",
    "chosen_on": RETRIEVED,
    "chosen_with": "snapshot-2026-11-08",
    "description": "Precon league: every Forge-bundled Commander precon that Playgroup.gg ranks by stock win rate (reference copied " + RETRIEVED + "). Decks play random 4-player tables; each deck sits in every seat once per cycle of four rounds. If this list ever changes, that is a new league with a new name and history restarts.",
    "precon_dir": "res/quest/commanderprecons",
    "reference": "runner/reference/playgroup-commander.json",
    "decks": decks,
    "unmatched_reference_precons": [{"name": u["name"], "set": u["set"], "commander": u["commander"]} for u in unmatched],
}
json.dump(manifest, open(MANIFEST_OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(MANIFEST_OUT, "a").write("\n")
print(f"reference -> {REF_OUT}; draft manifest ({len(decks)} decks) -> {MANIFEST_OUT}", file=sys.stderr)
