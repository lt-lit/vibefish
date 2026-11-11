#!/usr/bin/env python3
"""Vibefish precon league: many decks, random 4-player tables, seats balanced, one Forge game per table.

    runner/league.py schedule --league runner/precon-league.json --seed S --cycles C [--shards K --shard k]
    runner/league.py play     --league runner/precon-league.json --seed S --cycles C --out results/RUN_ID
                              [--runtime forge/runtime-snapshot] [--shards K --shard k] [-j JOBS] [--clock 1800]
                              [--turn-cap 120] [--mc off|on|max|lite] [--profile NAME] [--playbooks] [--limit N] [--dry-run]
    runner/league.py rollup   results/RUN_ID [--out DIR] [--league ... --seed S --cycles C] [--index demo-data/index.json] [--max-turn 12]

The schedule is a pure function of the league file, the seed and the number of cycles. A cycle is four rounds:
the decks (minus N mod 4 byes, rotating through the list) are shuffled into four equal groups, each round seats
one deck from every group at every table, and the group's seat shifts by one each round, so every deck sits in every
seat exactly once per cycle and meets different opponents every round. Game i gets seed S+i+1 (the harness's own
convention: --seed S plays game 1 with S+1). Shard k of K plays the games with (i-1) mod K == k-1, so partial runs
cover the league evenly; a finished game is never replayed.

Each game is one harness process (controller/vibefish-sim.sh play --games 1) writing OUT/shard-k/gNNNNN/{run.json,
games/game-001.events.jsonl}; the rollup folds them into one rollup.json (DESIGN.md §6) with per-deck statistics,
Wilson intervals and a league block, and upserts index.json like runner/rollup.py. Standard library only.
"""
import argparse
import collections
import datetime as dt
import json
import os
import random
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.dont_write_bytecode = True    # keep runner/ free of __pycache__
sys.path.insert(0, HERE)          # python3 -I does not add the script directory
import rollup as rl               # noqa: E402  (DeckStats, process_game, wilson, mean, VERSION)

EXIT_TIMEOUT = 3                  # the harness exits with 3 after a wall-clock timeout; the game is recorded as a draw


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- schedule
def schedule(league, seed, cycles):
    """List of games: {index (1-based), cycle, round, table, seed, seats: [deck id per seat]}."""
    decks = sorted(d["id"] for d in league["decks"])
    n = len(decks)
    if n < 4:
        raise SystemExit("a league needs at least four decks")
    tables = n // 4
    byes = n % 4
    games = []
    for c in range(cycles):
        rng = random.Random(seed * 7919 + c)
        bye_idx = {(c * byes + i) % n for i in range(byes)} if byes else set()
        playing = [d for i, d in enumerate(decks) if i not in bye_idx]
        rng.shuffle(playing)
        groups = [playing[g * tables:(g + 1) * tables] for g in range(4)]
        for r in range(4):
            perms = []
            for g in range(4):
                p = list(range(tables))
                rng.shuffle(p)
                perms.append(p)
            for t in range(tables):
                seats = [None] * 4
                for g in range(4):
                    seats[(g + r) % 4] = groups[g][perms[g][t]]
                i = len(games) + 1
                games.append({"index": i, "cycle": c + 1, "round": c * 4 + r + 1, "table": t + 1, "seed": seed + i, "seats": seats})
    return games


def shard_games(games, shards, shard):
    if shards <= 1:
        return list(games)
    return [g for g in games if (g["index"] - 1) % shards == shard - 1]


def game_dir(out, shard, index):
    return os.path.join(out, f"shard-{shard}", f"g{index:05d}")


def completed(gdir):
    """The harness wrote run.json with its one game recorded (a timed-out game is recorded as a draw first)."""
    rj = os.path.join(gdir, "run.json")
    if not os.path.isfile(rj):
        return False
    try:
        run = load_json(rj)
    except (OSError, ValueError):
        return False
    return bool(run.get("games"))


# ---------------------------------------------------------------- play
def cmd_play(args):
    league = load_json(args.league)
    runtime = os.path.abspath(args.runtime)
    stamp_file = os.path.join(runtime, "VIBEFISH_FORGE_VERSION")
    if not os.path.isfile(stamp_file):
        raise SystemExit(f"No Forge runtime at {runtime}; run forge/fetch-forge.sh")
    with open(stamp_file, encoding="utf-8") as f:
        forge_version = f.readline().strip()
    precon_dir = os.path.join(runtime, league["precon_dir"])
    missing = [d["file"] for d in league["decks"] if not os.path.isfile(os.path.join(precon_dir, d["file"]))]
    if missing:
        raise SystemExit(f"{len(missing)} league deck file(s) not in {precon_dir}: {missing[:5]}{' ...' if len(missing) > 5 else ''}")
    by_id = {d["id"]: d for d in league["decks"]}
    # --playbooks: a deck that has a shipped playbook (the playbook object in playbook/precons/<id>.json) is played
    # under it in whatever seat it sits; every other seat stays stock Forge AI.
    playbooks = {}
    if args.playbooks:
        for d in league["decks"]:
            pf = os.path.join(ROOT, "playbook", "precons", d["id"] + ".json")
            if os.path.isfile(pf) and isinstance(load_json(pf).get("playbook"), dict):
                playbooks[d["id"]] = pf
    games = schedule(league, args.seed, args.cycles)
    mine = shard_games(games, args.shards, args.shard)
    todo = [g for g in mine if not completed(game_dir(args.out, args.shard, g["index"]))]
    if args.limit is not None:
        todo = todo[:args.limit]
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    meta = {
        "vibefish": rl.VERSION, "league": {k: v for k, v in league.items() if k != "decks"}, "deck_ids": sorted(by_id),
        "seed": args.seed, "cycles": args.cycles, "shards": args.shards, "games_scheduled": len(games),
        "forge_version": forge_version, "runtime": os.path.basename(runtime), "clock_s": args.clock, "turn_cap": args.turn_cap,
        "mc": args.mc, "profile": args.profile or "Default", "playbooks": sorted(playbooks), "started": now(),
    }
    for path in (os.path.join(out, "league.json"), os.path.join(out, f"shard-{args.shard}", "league.json")):
        if not os.path.isfile(path):
            dump_json(path, meta)
    print(f"league {league['name']}: {len(league['decks'])} decks, {args.cycles} cycle(s) = {len(games)} games; "
          f"shard {args.shard}/{args.shards} has {len(mine)}, {len(mine) - len(todo) if args.limit is None else '?'} done, "
          f"{len(todo)} to play with {args.jobs} job(s); seed {args.seed}, clock {args.clock}s, turn cap {args.turn_cap}, mc {args.mc}, "
          f"profile {args.profile or 'default'}, runtime {forge_version}", file=sys.stderr)
    if not todo:
        return 0
    if not args.dry_run:
        subprocess.run([os.path.join(ROOT, "controller", "build.sh")], check=True, env={**os.environ, "FORGE_RUNTIME": runtime},
                       stdout=sys.stderr)
    log_path = os.path.join(out, f"shard-{args.shard}.log")
    lock = threading.Lock()
    failures = []
    launcher = os.path.join(ROOT, "controller", "vibefish-sim.sh")
    # Forge creates its profile directories the first time it boots in a runtime, and two JVMs doing that at the same
    # moment race ("cannot create profile directory"). So the first game boots alone: the others wait until its event
    # stream exists (the harness opens it after boot) or it has exited, then launch in parallel.
    first_booted = threading.Event()

    def launch(g, gdir, cmd, first):
        proc = subprocess.Popen(cmd, env={**os.environ, "FORGE_RUNTIME": runtime}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace")
        if first:
            events = os.path.join(gdir, "games", "game-001.events.jsonl")
            while proc.poll() is None and not os.path.exists(events):
                time.sleep(0.5)
            first_booted.set()
        out_text, _ = proc.communicate()
        return proc.returncode, out_text

    def play(item):
        order, g = item
        first = order == 0
        gdir = game_dir(out, args.shard, g["index"])
        cmd = [launcher, "play", "--out", gdir, "--deck-dir", precon_dir]
        for sid in g["seats"]:
            cmd += ["--deck", f"{sid}={by_id[sid]['file']}"]
        cmd += ["--games", "1", "--seed", str(g["seed"] - 1), "--clock", str(args.clock), "--turn-cap", str(args.turn_cap),
                "--forge-version", forge_version, "--mc", args.mc]
        if args.profile:
            cmd += ["--profile", args.profile] * 4
        for sid in g["seats"]:
            if sid in playbooks:
                cmd += ["--playbook", f"{sid}={playbooks[sid]}"]
        if args.dry_run:
            print(" ".join(repr(c) if " " in c else c for c in cmd))
            return
        if not first:
            first_booted.wait(timeout=180)
        os.makedirs(gdir, exist_ok=True)
        attempts = 0
        while True:
            attempts += 1
            t0 = dt.datetime.now()
            rc, out_text = launch(g, gdir, cmd, first and attempts == 1)
            secs = (dt.datetime.now() - t0).total_seconds()
            ok = rc == 0 or (rc == EXIT_TIMEOUT and completed(gdir))
            # a process that dies before it has played anything (boot failure, a transient error) gets one more try
            if not ok and attempts == 1 and secs < 60 and not completed(gdir):
                with lock:
                    with open(log_path, "a", encoding="utf-8") as lf:
                        lf.write(f"=== {now()} game {g['index']} exited with rc {rc} after {secs:.0f}s, retrying once\n{out_text}\n")
                time.sleep(2)
                continue
            break
        line = f"game {g['index']} (cycle {g['cycle']} round {g['round']} table {g['table']}) {' / '.join(g['seats'])}: " \
               f"{'ok' if ok else 'FAILED rc ' + str(rc)} in {secs:.0f}s{' (second attempt)' if attempts > 1 else ''}"
        with lock:
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"=== {now()} {line}\n{out_text}\n")
            print(line, file=sys.stderr)
            if not ok:
                failures.append(g["index"])

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        list(ex.map(play, enumerate(todo)))
    if failures:
        print(f"{len(failures)} game(s) failed: {failures}", file=sys.stderr)
        return 1
    return 0


# ---------------------------------------------------------------- rollup
def cmd_rollup(args):
    out = os.path.abspath(args.run_dir)
    shard_dirs = sorted(d for d in os.listdir(out) if d.startswith("shard-") and os.path.isdir(os.path.join(out, d)))
    meta = None
    for p in [os.path.join(out, "league.json")] + [os.path.join(out, s, "league.json") for s in shard_dirs]:
        if os.path.isfile(p):
            meta = load_json(p)
            break
    if args.league:
        league = load_json(args.league)
    elif meta and "decks" in meta.get("league", {}):
        league = meta["league"]
    else:
        league = load_json(os.path.join(ROOT, "runner", "precon-league.json"))
        if meta and meta["league"].get("name") != league.get("name"):
            raise SystemExit(f"league file mismatch: run is {meta['league'].get('name')}, pass --league")
    seed = args.seed if args.seed is not None else (meta or {}).get("seed")
    cycles = args.cycles if args.cycles is not None else (meta or {}).get("cycles")
    if seed is None or cycles is None:
        raise SystemExit("no league.json in the run and no --seed/--cycles given")
    games = schedule(league, seed, cycles)
    by_index = {g["index"]: g for g in games}
    by_id = {d["id"]: d for d in league["decks"]}

    stats = {}                               # deck id -> DeckStats
    seat_games = collections.defaultdict(lambda: [0, 0, 0, 0])
    seat_wins = collections.defaultdict(lambda: [0, 0, 0, 0])
    wins_by_seat = [0, 0, 0, 0]
    games_out = []
    first_run = None
    for s in shard_dirs:
        sdir = os.path.join(out, s)
        for gname in sorted(os.listdir(sdir)):
            gdir = os.path.join(sdir, gname)
            rj = os.path.join(gdir, "run.json")
            if not gname.startswith("g") or not os.path.isfile(rj):
                continue
            run = load_json(rj)
            if not run.get("games"):
                continue
            first_run = first_run or run
            index = int(gname[1:])
            sched = by_index.get(index)
            game = run["games"][0]
            seats = [d["id"] for d in sorted(run["decks"], key=lambda d: d["seat"])]
            if sched and sched["seats"] != seats:
                print(f"warning: {s}/{gname} seats {seats} differ from the schedule {sched['seats']}", file=sys.stderr)
            per_seat = {}
            for d in run["decks"]:
                st = stats.get(d["id"])
                if st is None:
                    st = stats[d["id"]] = rl.DeckStats(None, d, args.max_turn)
                per_seat[d["seat"]] = st
            ev_rel = game.get("events")
            ev_path = os.path.join(gdir, ev_rel) if ev_rel else None
            if ev_path and os.path.isfile(ev_path):
                rl.process_game(game, ev_path, per_seat, f"{s}:{index}", args.max_turn)
            else:
                print(f"missing events for {s}/{gname}", file=sys.stderr)
            winner = game.get("winner")
            for seat, sid in enumerate(seats):
                seat_games[sid][seat] += 1
                if winner == seat:
                    seat_wins[sid][seat] += 1
            if winner is not None:
                wins_by_seat[winner] += 1
            summary = {k: v for k, v in game.items() if k not in ("mc_stats", "profiles")}
            summary["players"] = [{k: v for k, v in p.items() if k != "profile"} for p in game.get("players", [])]
            summary.update({"shard": s, "game": index, "cycle": sched["cycle"] if sched else None, "round": sched["round"] if sched else None,
                            "seats": seats, "winner_id": seats[winner] if winner is not None else None,
                            "events": f"{s}/{gname}/{ev_rel}" if ev_rel else None})
            games_out.append(summary)
    if not games_out:
        print("no finished games found", file=sys.stderr)
        return 1
    games_out.sort(key=lambda g: g["game"])

    deck_stats = []
    for sid, st in stats.items():
        d = st.summary()
        d.pop("cards", None)                   # 100 cards x 90 decks would swamp the file; the pod rollups keep them
        d.pop("seat", None)
        m = by_id.get(sid, {})
        d.update({"set": m.get("set"), "year": m.get("year"), "reference_name": m.get("reference_name"),
                  "win_rate_ci95": rl.wilson(st.wins, st.games), "games_by_seat": seat_games[sid], "wins_by_seat": seat_wins[sid]})
        deck_stats.append(d)
    deck_stats.sort(key=lambda d: (-d["win_rate"], -d["games"], d["id"]))

    decided = [g for g in games_out if g.get("winner") is not None]
    run_id = args.run_id or os.path.basename(out)
    rollup = {
        "vibefish": rl.VERSION,
        "generated": now(),
        "run_id": run_id,
        "kind": "league",
        "forge_version": first_run.get("forge_version"),
        "forge_build": first_run.get("forge_build"),
        "format": first_run.get("format"),
        "pod": league["name"],
        "league": {
            "name": league["name"], "decks": len(league["decks"]), "seed": seed, "cycles": cycles, "rounds": cycles * 4,
            "tables_per_round": len(league["decks"]) // 4, "byes_per_cycle": len(league["decks"]) % 4,
            "games_scheduled": len(games), "games_played": len(games_out), "games_missing": len(games) - len(games_out),
            "games_per_deck_avg": round(sum(d["games"] for d in deck_stats) / max(1, len(deck_stats)), 1),
            "description": league.get("description"), "chosen_on": league.get("chosen_on"), "chosen_with": league.get("chosen_with"),
        },
        "seats_per_game": 4,
        "games": len(games_out),
        "completed_games": len(decided),
        "drawn_games": len(games_out) - len(decided),
        "shards": len(shard_dirs),
        "seeds": [seed],
        "clock_s": first_run.get("clock_s"),
        "turn_cap": first_run.get("turn_cap"),
        "max_turn": args.max_turn,
        "avg_game_turns": rl.mean([g.get("turns") for g in games_out]),
        "avg_game_seconds": rl.mean([g.get("duration_ms", 0) / 1000 for g in games_out]),
        "seat_win_rate": [round(w / len(decided), 4) if decided else None for w in wins_by_seat],
        "decks": [dict(d, commanders=d.get("commanders", [])) for d in sorted(league["decks"], key=lambda d: d["id"])],
        "mc": first_run.get("mc"),
        "mc_available": first_run.get("mc_available"),
        "profile": (meta or {}).get("profile") or (first_run["decks"][0].get("profile") if first_run.get("decks") else None),
        "playbooks": (meta or {}).get("playbooks") or [],     # deck ids played under their shipped playbook (league.py play --playbooks)
        "deck_stats": deck_stats,
        "game_summaries": games_out,
    }
    out_path = os.path.join(os.path.abspath(args.out) if args.out else out, "rollup.json")
    dump_json(out_path, rollup)
    print(f"league rollup: {len(games_out)} of {len(games)} games, {len(deck_stats)} decks -> {out_path}", file=sys.stderr)
    for d in deck_stats[:10]:
        ci = d["win_rate_ci95"] or [0, 0]
        print(f"  {d['id']:<28} {d['wins']:>3}/{d['games']:<3} {d['win_rate']*100:5.1f}% ({ci[0]*100:.0f}–{ci[1]*100:.0f}%)", file=sys.stderr)
    if len(deck_stats) > 10:
        print(f"  ... {len(deck_stats) - 10} more; seat win rates {rollup['seat_win_rate']}", file=sys.stderr)

    if args.index:
        index = load_json(args.index) if os.path.isfile(args.index) else {"runs": []}
        rel = os.path.relpath(out_path, os.path.dirname(os.path.abspath(args.index))).replace(os.sep, "/")
        entry = {"id": run_id, "generated": rollup["generated"], "forge_version": rollup["forge_version"], "pod": league["name"],
                 "kind": "league", "games": rollup["games"], "path": rel}
        index["runs"] = [r for r in index.get("runs", []) if r.get("id") != run_id] + [entry]
        index["runs"].sort(key=lambda r: r.get("generated", ""), reverse=True)
        dump_json(args.index, index)
        print(f"index: {len(index['runs'])} run(s) -> {args.index}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- schedule command
def cmd_schedule(args):
    league = load_json(args.league)
    games = schedule(league, args.seed, args.cycles)
    mine = shard_games(games, args.shards, args.shard) if args.shards > 1 else games
    if args.format == "json":
        json.dump(mine, sys.stdout, indent=1)
        print()
        return 0
    n = len(league["decks"])
    print(f"{league['name']}: {n} decks, {args.cycles} cycle(s), {n // 4} tables per round, {n % 4} bye(s) per cycle, {len(games)} games"
          + (f"; shard {args.shard}/{args.shards}: {len(mine)} games" if args.shards > 1 else ""))
    per_deck = collections.Counter()
    per_seat = collections.defaultdict(collections.Counter)
    for g in games:
        for s, d in enumerate(g["seats"]):
            per_deck[d] += 1
            per_seat[d][s] += 1
    counts = sorted(per_deck.values())
    print(f"games per deck: min {counts[0]}, max {counts[-1]}; every deck in every seat equally: "
          f"{all(len(set(c.values())) == 1 for c in per_seat.values())}")
    for g in mine[:args.show]:
        print(f"  game {g['index']:>5}  cycle {g['cycle']:>2} round {g['round']:>3} table {g['table']:>2}  seed {g['seed']}  {' | '.join(g['seats'])}")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--league", default=os.path.join(HERE, "precon-league.json"))
        p.add_argument("--seed", type=int, required=True)
        p.add_argument("--cycles", type=int, required=True)
        p.add_argument("--shards", type=int, default=1)
        p.add_argument("--shard", type=int, default=1)

    s = sub.add_parser("schedule", help="print the schedule")
    common(s)
    s.add_argument("--format", choices=["text", "json"], default="text")
    s.add_argument("--show", type=int, default=12)
    s.set_defaults(func=cmd_schedule)

    p = sub.add_parser("play", help="play (this shard of) the schedule through the harness")
    common(p)
    p.add_argument("--out", required=True)
    p.add_argument("--runtime", default=os.environ.get("FORGE_RUNTIME") or os.path.join(ROOT, "forge", "runtime"))
    p.add_argument("-j", "--jobs", type=int, default=1, help="harness processes at once (about 4 GB heap and 1.5 cores each)")
    p.add_argument("--clock", type=int, default=1800)
    p.add_argument("--turn-cap", type=int, default=120)
    p.add_argument("--mc", default="off", choices=["off", "on", "max", "lite"])
    p.add_argument("--profile", default="", help="AI profile for every seat (default: Forge's Default)")
    p.add_argument("--playbooks", action="store_true",
                   help="play every deck that has a shipped playbook (playbook/precons/<id>.json) under it; the other seats stay stock")
    p.add_argument("--limit", type=int, help="play at most N games of this shard (smoke tests)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_play)

    r = sub.add_parser("rollup", help="fold the finished games into rollup.json")
    r.add_argument("run_dir")
    r.add_argument("--league")
    r.add_argument("--seed", type=int)
    r.add_argument("--cycles", type=int)
    r.add_argument("--run-id")
    r.add_argument("--out", help="directory for rollup.json (default: the run directory)")
    r.add_argument("--index")
    r.add_argument("--max-turn", type=int, default=12)
    r.set_defaults(func=cmd_rollup)

    args = ap.parse_args(argv)
    if args.cmd != "rollup" and not (1 <= args.shard <= args.shards):
        ap.error("--shard must be between 1 and --shards")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
