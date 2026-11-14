#!/usr/bin/env python3
"""Paired A/B for one deck's AI data: the same tables and seeds, with and without the deck's data.

    runner/ab.py play --deck token-triumph --games 40 --seed 20261110 --out results/ab-token-triumph
                      [--runtime forge/runtime-snapshot] [--arms stock,data] [-j 2] [--clock 1800] [--turn-cap 120] [--opponents 3]
                      [--data playbook/precons/<deck>.json] [--shards K --shard k] [--limit N] [--dry-run]
                      [--pool runner/leagues/bots-v1.json] [--opponent-playbooks] [--deck-file /path/My Deck.dck]
    runner/ab.py rollup results/ab-token-triumph
    runner/ab.py pool --out pooled.json results/ab-token-triumph/rollup.json demo-data/ab/2026-11-09-ab-v1/token-triumph.json
    runner/ab.py join --out joined.json [--against v2] stock=run5/rollup.json:stock v2=run5/rollup.json:playbook pressure=run7/rollup.json

Game i seats the focus deck in seat (i-1) mod 4 with three opponents drawn (seeded) from the rest of the league,
all stock Forge AI, and plays that table once per arm with the same seed, so the arms differ only in what the
focus seat is given. That was the exam until 2026-11-11. Since then the opponents can be the bots:
--pool FILE draws them from another deck list (runner/leagues/bots-v1.json, the decks that have a shipped
playbook) and --opponent-playbooks seats every opponent that has a shipped playbook
(playbook/precons/<id>.json) under it, in every arm. The arms still differ only in the focus seat, so `stock`
against `playbook` at such tables asks whether the deck's playbook helps among competent pilots, not among
stock ones (DESIGN.md §24). The arms:

    stock    the deck as Forge ships it: Default profile, no data
    data     the deck's data file through the harness (--data: KeyCards, card roles, combos, pairs) and a per-deck
             AI profile Vibefish-<deck>.ai written from Default.ai plus the file's deck_plan and profile overrides
    mc       Flat Monte Carlo on for the game; the focus seat plays Monte Carlo (Default profile), the opponents keep
             the heuristic AI (Vibefish-Heuristic, from runner/make-arm-profiles.sh)
    mcdata   mc plus the deck's data and profile
    mcmax    as mc, with Forge's Monte Carlo at desktop strength (--mc max: no time budget, about three times slower)
    mcmaxdata  mcmax plus the deck's data and profile
    playbook   the deck's playbook (Phase 4: Vibefish's own cast rules, attack policy and mulligan rule through
             Forge's controller hooks, --playbook) on the focus seat; no data, Default profile, heuristic opponents
    playbookdata  playbook plus the deck's data and profile

--opponents 1 makes every table a duel against one league deck (the focus deck alternating between going first and
second): a game then turns on blocks, removal and the race, not on who the table gangs up on, it is over sooner, and
around an even win rate a pilot's edge shows in far fewer games. It is the middle instrument between goldfish (no
opponent at all) and the four-player tables (the exam); DESIGN.md §22.

Seeds: table i's opponents are drawn with seed*31 + i and its game is played on seed + i. Two runs of one deck whose
seeds are close therefore draw the same opponents for some of their tables (200-table runs do while the seeds are
fewer than seven apart: seeds two apart share 138 of 200 draws), in other seats and with other shuffles. They are
other games, and where it was measured nothing carried over (DESIGN.md §22, Hail, Caesar's confirming run), but
they are not fresh draws of opponents: keep a deck's runs ten seeds apart. `play` says so when demo-data/ab holds a
run of the deck on a nearby seed.

A deck of your own: --deck-file PATH plays that .dck in the focus seat, under the id --deck gives it (any name; an
id of the league means "this list instead of the league's", and the deck's playbook is then the default for the
playbook arms). Its opponents are drawn from the pool or the league as for any deck. Two lists of one deck on the
same tables are two runs with the same --deck and --seed and another --deck-file, lined up with `join`
(listA=runA/rollup.json:stock listB=runB/rollup.json:stock): the paired design with the list as the arm. ab.json
records the file and its SHA-256. Run `controller/vibefish-sim.sh check` on a new list first.

One harness process per game (controller/vibefish-sim.sh play --games 1), like runner/league.py; finished games
are never replayed. The rollup pairs the arms game by game: wins per arm with Wilson intervals, the paired
difference with a normal-approximation interval, the discordant pairs and an exact two-sided test that they split
evenly. `pool` adds up the same arms played with different seeds; `join` lines up arms from different runs of the
same tables (same deck and seed: a later run that played only a candidate's arm against an earlier run's stock
arm), each under a name given on the command line, every arm paired with the first and with each --against arm
(kind "ab-join"). Standard library only.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import math
import os
import random
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import league as lg          # noqa: E402  (completed, load_json, dump_json, now, EXIT_TIMEOUT)
import rollup as rl          # noqa: E402  (wilson, mean, VERSION)
import deckdata as dd        # noqa: E402  (effective)

ARMS = {
    "stock": {"data": False, "mc": "off", "focus_profile": "", "opp_profile": ""},
    "data": {"data": True, "mc": "off", "focus_profile": "deck", "opp_profile": ""},
    "mc": {"data": False, "mc": "on", "focus_profile": "", "opp_profile": "Vibefish-Heuristic"},
    "mcdata": {"data": True, "mc": "on", "focus_profile": "deck", "opp_profile": "Vibefish-Heuristic"},
    "mcmax": {"data": False, "mc": "max", "focus_profile": "", "opp_profile": "Vibefish-Heuristic"},
    "mcmaxdata": {"data": True, "mc": "max", "focus_profile": "deck", "opp_profile": "Vibefish-Heuristic"},
    "playbook": {"data": False, "mc": "off", "focus_profile": "", "opp_profile": "", "playbook": True},
    "playbookdata": {"data": True, "mc": "off", "focus_profile": "deck", "opp_profile": "", "playbook": True},
}


def schedule(league, deck_id, seed, games, opponents=3, pool=None):
    """The tables of a run. Opponents come from `pool` (a deck list) when one is given, else from the league."""
    others = sorted(d["id"] for d in (pool or league)["decks"] if d["id"] != deck_id)
    if len(others) < opponents:
        raise SystemExit(f"{len(others)} deck(s) to draw {opponents} opponent(s) from")
    out = []
    for i in range(1, games + 1):
        rng = random.Random(seed * 31 + i)
        opps = rng.sample(others, opponents)
        focus_seat = (i - 1) % (opponents + 1)
        seats = opps[:focus_seat] + [deck_id] + opps[focus_seat:]
        out.append({"index": i, "seed": seed + i, "focus_seat": focus_seat, "seats": seats})
    return out


def near_seed_runs(deck_id, seed, games, opponents, base=None, pool=None):
    """Published runs of this deck (rollups under demo-data/ab) on another seed that share opponent draws with this
    request: [(seed, shared tables, a rollup's path)]. The draw of table i is seeded with seed*31 + i (schedule)."""
    mine = {seed * 31 + i for i in range(1, games + 1)}
    found = {}
    for dirpath, _dirs, files in sorted(os.walk(base or os.path.join(ROOT, "demo-data", "ab"))):
        for name in sorted(files):
            if not name.endswith(".json"):
                continue
            path = os.path.join(dirpath, name)
            try:
                r = lg.load_json(path)
            except (OSError, ValueError):
                continue
            if not isinstance(r, dict) or r.get("deck") != deck_id or not isinstance(r.get("seed"), int) or r["seed"] == seed:
                continue
            if r.get("opponents", 3) != opponents or not isinstance(r.get("games"), dict) or r["seed"] in found:
                continue
            if r.get("pool") != pool:           # another opponent pool is another draw
                continue
            tables = max((g.get("index", 0) for arm in r["games"].values() for g in arm), default=0)
            shared = len(mine & {r["seed"] * 31 + i for i in range(1, tables + 1)})
            if shared:
                found[r["seed"]] = (shared, os.path.relpath(path, ROOT))
    return sorted((s, n, p) for s, (n, p) in found.items())


def write_deck_profile(runtime, deck_id, eff):
    """Default.ai plus the data file's deck_plan and profile overrides -> res/ai/Vibefish-<deck>.ai. Returns the name."""
    ai_dir = os.path.join(runtime, "res", "ai")
    name = f"Vibefish-{deck_id}"
    overrides = dict(eff.get("profile") or {})
    plan = eff.get("deck_plan") or "auto"
    if plan != "auto":
        overrides["FLAT_MC_DECK_PLAN"] = str(plan)
    lines = []
    with open(os.path.join(ai_dir, "Default.ai"), encoding="utf-8") as f:
        for line in f:
            key = line.split("=", 1)[0].strip() if "=" in line and not line.startswith("#") else None
            if key in overrides:
                continue
            lines.append(line.rstrip("\n"))
    lines.append(f"# Vibefish per-deck overrides for {deck_id}")
    for k, v in overrides.items():
        lines.append(f"{k}={v}")
    with open(os.path.join(ai_dir, name + ".ai"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return name, overrides


def cmd_play(args):
    league = lg.load_json(args.league)
    by_id = {d["id"]: d for d in league["decks"]}
    own_deck = None                      # --deck-file: a list of the user's own in the focus seat
    if args.deck_file:
        own_deck = os.path.abspath(args.deck_file)
        if not os.path.isfile(own_deck):
            raise SystemExit(f"{args.deck_file}: no such deck file")
    elif args.deck not in by_id:
        raise SystemExit(f"{args.deck} is not in {args.league} (a list of your own: --deck-file PATH, and --deck is the id it plays under)")
    runtime = os.path.abspath(args.runtime)
    with open(os.path.join(runtime, "VIBEFISH_FORGE_VERSION"), encoding="utf-8") as f:
        forge_version = f.readline().strip()
    precon_dir = os.path.join(runtime, league["precon_dir"])
    data_file = os.path.abspath(args.data or os.path.join(ROOT, "playbook", "precons", args.deck + ".json"))
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    for a in arms:
        if a not in ARMS:
            raise SystemExit(f"unknown arm {a}; arms: {', '.join(ARMS)}")
    needs_file = [a for a in arms if ARMS[a]["data"] or ARMS[a].get("playbook")]
    if needs_file and not os.path.isfile(data_file):
        raise SystemExit(f"arm {needs_file[0]} needs the deck's data or playbook file and {os.path.relpath(data_file, ROOT)} does not exist: "
                         f"--data FILE, or play --arms stock")
    eff = dd.effective(lg.load_json(data_file)) if any(ARMS[a]["data"] for a in arms) else {}
    deck_profile, overrides = (write_deck_profile(runtime, args.deck, eff) if eff else ("", {}))
    if any(ARMS[a]["opp_profile"] == "Vibefish-Heuristic" for a in arms) and not os.path.isfile(os.path.join(runtime, "res", "ai", "Vibefish-Heuristic.ai")):
        raise SystemExit("the mc arms need Vibefish-Heuristic.ai: run runner/make-arm-profiles.sh " + runtime)
    pool = lg.load_json(args.pool) if args.pool else None
    if pool:
        by_id = {**{d["id"]: d for d in pool["decks"]}, **by_id}
    if own_deck:
        by_id[args.deck] = {"id": args.deck, "file": own_deck, "name": os.path.splitext(os.path.basename(own_deck))[0]}
    games = schedule(league, args.deck, args.seed, args.games, args.opponents, pool)
    # --opponent-playbooks: an opponent that has a shipped playbook plays under it, in every arm
    opp_playbooks = {}
    if args.opponent_playbooks:
        for sid in sorted({s for g in games for s in g["seats"] if s != args.deck}):
            pf = os.path.join(ROOT, "playbook", "precons", sid + ".json")
            if os.path.isfile(pf) and isinstance(lg.load_json(pf).get("playbook"), dict):
                opp_playbooks[sid] = pf
    for other, shared, path in near_seed_runs(args.deck, args.seed, args.games, args.opponents, pool=pool["name"] if pool else None):
        print(f"ab.py: note: {shared} of these {args.games} tables draw the same opponents as {args.deck}'s run on seed {other} ({path}): "
              f"the draw of table i is seeded with seed*31 + i. Other seats and shuffles, so other games, but not fresh opponents; "
              f"keep a deck's runs ten seeds apart.", file=sys.stderr)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    meta_path = os.path.join(out, "ab.json")
    if not os.path.isfile(meta_path):
        lg.dump_json(meta_path, {
            "vibefish": rl.VERSION, "deck": args.deck, "deck_file": by_id[args.deck]["file"],
            **({"deck_file_sha256": hashlib.sha256(open(own_deck, "rb").read()).hexdigest()} if own_deck else {}), "league": league["name"],
            "seed": args.seed, "games": args.games, "opponents": args.opponents, "arms": arms, "data_file": os.path.relpath(data_file, ROOT),
            "pool": pool["name"] if pool else None, "pool_file": os.path.relpath(os.path.abspath(args.pool), ROOT) if pool else None,
            "opponent_playbooks": sorted(opp_playbooks),
            "data_effective": eff, "deck_profile": deck_profile, "profile_overrides": overrides,
            "forge_version": forge_version, "runtime": os.path.basename(runtime), "clock_s": args.clock, "turn_cap": args.turn_cap,
            "started": lg.now(),
        })
    todo = []
    k = 0
    for g in games:                      # a table's arms stay in one shard, so a shard's results pair up on their own
        k += 1
        if args.shards > 1 and (k - 1) % args.shards != args.shard - 1:
            continue
        for arm in arms:
            gdir = os.path.join(out, f"arm-{arm}", f"g{g['index']:04d}")
            if not lg.completed(gdir):
                todo.append((arm, g, gdir))
    if args.limit is not None:
        todo = todo[:args.limit]
    print(f"A/B {args.deck}: {args.games} tables x {len(arms)} arms ({', '.join(arms)}){f'; shard {args.shard}/{args.shards}' if args.shards > 1 else ''}; "
          f"{len(todo)} to play with {args.jobs} job(s); seed {args.seed}, runtime {forge_version}, data {os.path.relpath(data_file, ROOT)}"
          f"{'; opponents from ' + pool['name'] if pool else ''}{'; ' + str(len(opp_playbooks)) + ' opponent deck(s) under their playbook' if args.opponent_playbooks else ''}"
          f"{', profile ' + deck_profile + ' ' + json.dumps(overrides) if deck_profile else ''}", file=sys.stderr)
    if not todo:
        return 0
    if not args.dry_run:
        subprocess.run([os.path.join(ROOT, "controller", "build.sh")], check=True, env={**os.environ, "FORGE_RUNTIME": runtime}, stdout=sys.stderr)
    launcher = os.path.join(ROOT, "controller", "vibefish-sim.sh")
    log_path = os.path.join(out, "play.log")
    lock = threading.Lock()
    failures = []
    first_booted = threading.Event()

    def command(arm, g, gdir):
        spec = ARMS[arm]
        cmd = [launcher, "play", "--out", gdir, "--deck-dir", precon_dir]
        for sid in g["seats"]:
            cmd += ["--deck", f"{sid}={by_id[sid]['file']}"]
        cmd += ["--games", "1", "--seed", str(g["seed"] - 1), "--clock", str(args.clock), "--turn-cap", str(args.turn_cap),
                "--forge-version", forge_version, "--mc", spec["mc"]]
        focus_profile = deck_profile if spec["focus_profile"] == "deck" else spec["focus_profile"]
        if focus_profile or spec["opp_profile"]:
            for seat, sid in enumerate(g["seats"]):
                cmd += ["--profile", focus_profile if sid == args.deck else spec["opp_profile"]]
        if spec["data"]:
            cmd += ["--data", f"{args.deck}={data_file}"]
        if spec.get("playbook"):
            cmd += ["--playbook", f"{args.deck}={data_file}"]
        for sid in g["seats"]:
            if sid != args.deck and sid in opp_playbooks:
                cmd += ["--playbook", f"{sid}={opp_playbooks[sid]}"]
        return cmd

    def play(item):
        order, (arm, g, gdir) = item
        cmd = command(arm, g, gdir)
        if args.dry_run:
            print(" ".join(repr(c) if " " in c or not c else c for c in cmd))
            return
        first = order == 0
        if not first:
            first_booted.wait(timeout=180)
        os.makedirs(gdir, exist_ok=True)
        attempts = 0
        while True:
            attempts += 1
            t0 = dt.datetime.now()
            proc = subprocess.Popen(cmd, env={**os.environ, "FORGE_RUNTIME": runtime}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            if first and attempts == 1:
                events = os.path.join(gdir, "games", "game-001.events.jsonl")
                while proc.poll() is None and not os.path.exists(events):
                    time.sleep(0.5)
                first_booted.set()
            out_text, _ = proc.communicate()
            secs = (dt.datetime.now() - t0).total_seconds()
            ok = proc.returncode == 0 or (proc.returncode == lg.EXIT_TIMEOUT and lg.completed(gdir))
            if not ok and attempts == 1 and secs < 60 and not lg.completed(gdir):
                time.sleep(2)
                continue
            break
        line = f"{arm} game {g['index']} seat {g['focus_seat'] + 1} vs {' / '.join(s for s in g['seats'] if s != args.deck)}: {'ok' if ok else 'FAILED rc ' + str(proc.returncode)} in {secs:.0f}s"
        with lock:
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"=== {lg.now()} {line}\n{out_text}\n")
            print(line, file=sys.stderr)
            if not ok:
                failures.append((arm, g["index"]))

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        list(ex.map(play, enumerate(todo)))
    if failures:
        print(f"{len(failures)} game(s) failed: {failures}", file=sys.stderr)
        return 1
    return 0


def sum_stats(dicts):
    """Playbook counters summed over the games that have them (None when none do)."""
    if not dicts:
        return None
    out = collections.Counter()
    for d in dicts:
        out.update(d)
    out["games"] = len(dicts)
    return dict(out)


def sign_test(a, b):
    """Two-sided exact test that the discordant pairs split evenly (a tables won only by one arm, b only by the other)."""
    n = a + b
    if n == 0:
        return None
    probs = [math.comb(n, k) / 2 ** n for k in range(n + 1)]
    return round(min(1.0, sum(q for q in probs if q <= probs[a] * (1 + 1e-9))), 4)


def summarise(arms, per_arm):
    """Per-arm win statistics and the paired comparison of every other arm with the first, over games keyed the same way in each arm."""
    arm_stats = {}
    for arm, games in per_arm.items():
        n = len(games)
        w = sum(1 for g in games.values() if g["won"])
        arm_stats[arm] = {"games": n, "wins": w, "win_rate": round(w / n, 4) if n else None, "win_rate_ci95": rl.wilson(w, n),
                          "draws": sum(1 for g in games.values() if g["winner_id"] is None),
                          "avg_turns": rl.mean([g["turns"] for g in games.values()]),
                          "avg_seconds": rl.mean([(g["duration_ms"] or 0) / 1000 for g in games.values()]),
                          "avg_turn_lost": rl.mean([g["focus_lost_turn"] for g in games.values() if g["focus_lost_turn"] is not None]),
                          "wins_by_seat": [sum(1 for g in games.values() if g["won"] and g["focus_seat"] == s)
                                           for s in range(max([len(g["seats"]) for g in games.values()] or [4]))],
                          "playbook": sum_stats([g["playbook_stats"] for g in games.values() if g.get("playbook_stats")])}
    pairs = {}
    if len(arms) >= 2:
        base, other_arms = arms[0], arms[1:]
        for arm in other_arms:
            common = sorted(set(per_arm[base]) & set(per_arm[arm]))
            d = [int(per_arm[arm][i]["won"]) - int(per_arm[base][i]["won"]) for i in common]
            n = len(d)
            both = sum(1 for i in common if per_arm[arm][i]["won"] and per_arm[base][i]["won"])
            only_arm = sum(1 for x in d if x == 1)
            only_base = sum(1 for x in d if x == -1)
            mean = statistics.fmean(d) if n else None
            se = (statistics.pstdev(d) / (n ** 0.5)) if n > 1 else None
            pairs[f"{arm}_vs_{base}"] = {"pairs": n, "both_won": both, f"{arm}_only": only_arm, f"{base}_only": only_base,
                                         "neither": n - both - only_arm - only_base, "exact_p": sign_test(only_arm, only_base),
                                         "difference": round(mean, 4) if mean is not None else None,
                                         "difference_ci95": [round(mean - 1.96 * se, 4), round(mean + 1.96 * se, 4)] if se is not None else None,
                                         "identical_outcomes": sum(1 for i in common if per_arm[arm][i]["turns"] == per_arm[base][i]["turns"] and per_arm[arm][i]["winner_id"] == per_arm[base][i]["winner_id"])}
    return arm_stats, pairs


def report(deck, forge_version, arm_stats, pairs):
    print(f"A/B {deck} ({forge_version}):", file=sys.stderr)
    for arm, s in arm_stats.items():
        ci = s["win_rate_ci95"] or [0, 0]
        print(f"  {arm:<8} {s['wins']:>3}/{s['games']:<3} {(s['win_rate'] or 0) * 100:5.1f}% ({ci[0] * 100:.0f}–{ci[1] * 100:.0f}%)  draws {s['draws']}  "
              f"turns {s['avg_turns']}  eliminated at game turn {s['avg_turn_lost']}  wins by seat {s['wins_by_seat']}"
              + (f"  playbook {s['playbook']}" if s.get('playbook') else ""), file=sys.stderr)
    for k, p in pairs.items():
        ci = p["difference_ci95"] or [0, 0]
        print(f"  {k}: {p['pairs']} pairs, difference {(p['difference'] or 0) * 100:+.1f} points (95% {ci[0] * 100:+.0f} to {ci[1] * 100:+.0f}); "
              f"discordant {p[k.split('_vs_')[0] + '_only']} vs {p[k.split('_vs_')[1] + '_only']}"
              + (f" (exact test {p['exact_p']})" if p.get('exact_p') is not None else "") + f"; identical outcomes {p['identical_outcomes']}", file=sys.stderr)


def cmd_rollup(args):
    out = os.path.abspath(args.run_dir)
    meta = lg.load_json(os.path.join(out, "ab.json"))
    deck = meta["deck"]
    per_arm = {}
    for arm in meta["arms"]:
        adir = os.path.join(out, f"arm-{arm}")
        games = {}
        if os.path.isdir(adir):
            for g in sorted(os.listdir(adir)):
                rj = os.path.join(adir, g, "run.json")
                if g.startswith("g") and os.path.isfile(rj):
                    run = lg.load_json(rj)
                    if run.get("games"):
                        gm = run["games"][0]
                        seats = [d["id"] for d in sorted(run["decks"], key=lambda d: d["seat"])]
                        fs = seats.index(deck)
                        games[int(g[1:])] = {"index": int(g[1:]), "seed": gm.get("seed"), "seats": seats, "focus_seat": fs, "won": gm.get("winner") == fs,
                                             "winner_id": seats[gm["winner"]] if gm.get("winner") is not None else None, "turns": gm.get("turns"),
                                             "reason": gm.get("reason"), "duration_ms": gm.get("duration_ms"),
                                             "focus_lost_turn": next((p.get("turn_lost") for p in gm.get("players", []) if p.get("seat") == fs), None),
                                             "data": (run["decks"][fs].get("data") or {}).get("key_cards_applied"), "ai_lists": run.get("ai_lists"),
                                             "playbook_stats": gm.get("playbook_stats")}
        per_arm[arm] = games
    arm_stats, pairs = summarise(meta["arms"], per_arm)
    result = {"vibefish": rl.VERSION, "generated": lg.now(), "kind": "ab", **{k: v for k, v in meta.items() if k != "data_effective"},
              "data_effective": meta.get("data_effective"), "arm_stats": arm_stats, "paired": pairs,
              "games": {arm: [g for _, g in sorted(gs.items())] for arm, gs in per_arm.items()}}
    lg.dump_json(os.path.join(out, "rollup.json"), result)
    report(deck, meta["forge_version"], arm_stats, pairs)
    return 0


def cmd_pool(args):
    """Pool rollup.json files of the same deck and arms, played with different seeds, into one measurement: games keyed by (run seed, table)."""
    rollups = [(p, lg.load_json(p)) for p in args.rollups]
    deck, arms = rollups[0][1]["deck"], rollups[0][1]["arms"]
    for p, r in rollups[1:]:
        if r["deck"] != deck or r["arms"] != arms:
            raise SystemExit(f"{p}: deck {r['deck']} arms {r['arms']} do not match {rollups[0][0]} ({deck}, {arms})")
    seeds = [r["seed"] for _, r in rollups]
    if len(set(seeds)) != len(seeds):
        raise SystemExit(f"the rollups share a seed ({seeds}): the same tables again, not more of them")
    per_arm = {arm: {} for arm in arms}
    for _, r in rollups:
        for arm in arms:
            for g in r["games"].get(arm, []):
                per_arm[arm][(r["seed"], g["index"])] = {**g, "run_seed": r["seed"]}
    arm_stats, pairs = summarise(arms, per_arm)
    versions = sorted({r["forge_version"] for _, r in rollups})
    result = {"vibefish": rl.VERSION, "generated": lg.now(), "kind": "ab-pool", "deck": deck, "deck_file": rollups[0][1].get("deck_file"),
              "league": rollups[0][1].get("league"), "seeds": seeds, "arms": arms, "forge_version": versions[0] if len(versions) == 1 else versions,
              "sources": [{"seed": r["seed"], "generated": r.get("generated"), "started": r.get("started"), "games": {a: len(r["games"].get(a, [])) for a in arms}} for _, r in rollups],
              "arm_stats": arm_stats, "paired": pairs,
              "games": {arm: [g for _, g in sorted(gs.items())] for arm, gs in per_arm.items()}}
    if args.out:
        lg.dump_json(args.out, result)
    report(deck, result["forge_version"], arm_stats, pairs)
    return 0


def cmd_join(args):
    """Arms of several rollups of one deck on the same tables (same seed) as one measurement, each under a name of its own."""
    per_arm, sources, first = {}, [], None
    for spec in args.arms:
        name, _, rest = spec.partition("=")
        path, _, arm = rest.partition(":")
        if not name or not path:
            raise SystemExit(f"{spec}: write NAME=ROLLUP.json[:ARM]")
        r = lg.load_json(path)
        arm = arm or (r["arms"][0] if len(r["arms"]) == 1 else "playbook")
        if arm not in r["games"]:
            raise SystemExit(f"{path} has no arm {arm} (it has {list(r['games'])})")
        if first is None:
            first = r
        elif (r["deck"], r["seed"], r.get("opponents", 3), r.get("pool"), r.get("opponent_playbooks") or []) != \
                (first["deck"], first["seed"], first.get("opponents", 3), first.get("pool"), first.get("opponent_playbooks") or []):
            raise SystemExit(f"{path}: deck {r['deck']} seed {r['seed']} is not the tables of {first['deck']} seed {first['seed']}")
        games = {g["index"]: g for g in r["games"][arm]}
        for other in per_arm.values():                      # the same table index must seat the same decks
            for i in set(games) & set(other):
                if games[i]["seats"] != other[i]["seats"]:
                    raise SystemExit(f"{path}: table {i} seats {games[i]['seats']}, another arm has {other[i]['seats']}")
        if name in per_arm:
            raise SystemExit(f"two arms named {name}")
        per_arm[name] = games
        sources.append({"arm": name, "from": os.path.basename(os.path.dirname(os.path.abspath(path))) + "/" + os.path.basename(path), "source_arm": arm,
                        "data_file": r.get("data_file"), "generated": r.get("generated"), "forge_version": r.get("forge_version"), "vibefish": r.get("vibefish"),
                        **({"deck_file": r.get("deck_file"), "deck_file_sha256": r["deck_file_sha256"]} if r.get("deck_file_sha256") else {})})
    names = list(per_arm)
    arm_stats, pairs = summarise(names, per_arm)
    for base in args.against or []:
        if base not in per_arm:
            raise SystemExit(f"--against {base}: no such arm among {names}")
        _, more = summarise([base] + [n for n in names if n != base and n != names[0]], per_arm)
        pairs.update(more)
    versions = sorted({x["forge_version"] for x in sources if x["forge_version"]})
    result = {"vibefish": rl.VERSION, "generated": lg.now(), "kind": "ab-join", "deck": first["deck"], "deck_file": first.get("deck_file"),
              "league": first.get("league"), "seed": first["seed"], "opponents": first.get("opponents", 3), "arms": names,
              "forge_version": versions[0] if len(versions) == 1 else versions, "sources": sources, "note": args.note,
              "arm_stats": arm_stats, "paired": pairs,
              "games": {arm: [g for _, g in sorted(gs.items())] for arm, gs in per_arm.items()}}
    if args.out:
        lg.dump_json(args.out, result)
    report(first["deck"], result["forge_version"], arm_stats, pairs)
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("play")
    p.add_argument("--deck", required=True)
    p.add_argument("--games", type=int, default=40)
    p.add_argument("--opponents", type=int, default=3, choices=[1, 2, 3],
                   help="opponents at each table (default 3; 1 plays duels, where each game says more about combat and less about the table)")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--league", default=os.path.join(HERE, "precon-league.json"))
    p.add_argument("--runtime", default=os.environ.get("FORGE_RUNTIME") or os.path.join(ROOT, "forge", "runtime"))
    p.add_argument("--data")
    p.add_argument("--arms", default="stock,data")
    p.add_argument("-j", "--jobs", type=int, default=1)
    p.add_argument("--clock", type=int, default=1800)
    p.add_argument("--turn-cap", type=int, default=120)
    p.add_argument("--shards", type=int, default=1)
    p.add_argument("--shard", type=int, default=1)
    p.add_argument("--limit", type=int)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--pool", help="a deck list to draw the opponents from instead of the league (runner/leagues/bots-v1.json: the bot decks)")
    p.add_argument("--deck-file", help="a .dck of your own for the focus seat; --deck is then the id it plays under")
    p.add_argument("--opponent-playbooks", action="store_true",
                   help="every opponent that has a shipped playbook (playbook/precons/<id>.json) plays under it, in every arm")
    p.set_defaults(func=cmd_play)
    r = sub.add_parser("rollup")
    r.add_argument("run_dir")
    r.set_defaults(func=cmd_rollup)
    q = sub.add_parser("pool")
    q.add_argument("rollups", nargs="+", help="rollup.json files of the same deck and arms, different seeds")
    q.add_argument("--out", help="write the pooled rollup here (kind: ab-pool)")
    q.set_defaults(func=cmd_pool)
    j = sub.add_parser("join")
    j.add_argument("--out")
    j.add_argument("--against", action="append", help="also pair the later arms with this one (the first arm is always a base)")
    j.add_argument("--note")
    j.add_argument("arms", nargs="+", metavar="NAME=ROLLUP.json[:ARM]")
    j.set_defaults(func=cmd_join)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
