#!/usr/bin/env python3
"""The request of a league-run workflow run, as `key=value` lines for $GITHUB_OUTPUT.

Called by .github/workflows/league-run.yml from the repository root. A run started with Run workflow takes its
values from the form (the IN_* environment variables); a run started by a push takes them from
runner/queue/league-run.json. Either way a value that is missing gets the default below, and a value that is not
what its field allows stops the run here with a message, before any shard starts. Standard library only.

    EVENT=push python3 -I runner/queue/league_request.py       # prints what the queued request would run
"""
import datetime
import json
import os
import re
import sys

DEFAULTS = {
    "league": "runner/precon-league.json", "cycles": "25", "shards": "20", "jobs_per_shard": "2", "seed": "",
    "run_id": "", "forge_channel": "snapshot", "forge_snapshot_build": "2.0.16-SNAPSHOT-11.10", "profile": "",
    "mc": "off", "playbooks": "false", "publish": "false",
}
QUEUE = os.path.join("runner", "queue", "league-run.json")


def text(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v).strip()


def main():
    vals = dict(DEFAULTS)
    if os.environ.get("EVENT") == "push":
        with open(QUEUE, encoding="utf-8") as f:
            queued = json.load(f)
        vals.update({k: text(v) for k, v in queued.items() if k in vals})
    else:
        for k in vals:
            v = os.environ.get("IN_" + k.upper(), "").strip()
            if v:
                vals[k] = v

    def refuse(msg):
        sys.exit("league-run request refused: " + msg)

    league = vals["league"]
    if not re.fullmatch(r"runner/[A-Za-z0-9_./-]+\.json", league) or ".." in league or not os.path.isfile(league):
        refuse(f"league must be a league file under runner/ (got {league!r})")
    with open(league, encoding="utf-8") as f:
        name = json.load(f).get("name") or ""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        refuse(f"{league} has no usable name")
    for k, lo, hi in (("cycles", 1, 1000), ("shards", 1, 20), ("jobs_per_shard", 1, 4)):
        if not vals[k].isdigit() or not lo <= int(vals[k]) <= hi:
            refuse(f"{k} must be a number from {lo} to {hi} (got {vals[k]!r})")
    now = datetime.datetime.now(datetime.timezone.utc)
    seed = vals["seed"] or now.strftime("%Y%m%d")
    if not seed.isdigit():
        refuse(f"seed must be a number (got {seed!r})")
    if vals["forge_channel"] not in ("pinned", "snapshot"):
        refuse(f"forge_channel must be pinned or snapshot (got {vals['forge_channel']!r})")
    build = vals["forge_snapshot_build"] if vals["forge_channel"] == "snapshot" else ""
    if vals["forge_channel"] == "snapshot":
        m = re.fullmatch(r"[0-9.]+-SNAPSHOT-([0-9]{2})\.([0-9]{2})", build)
        if not m:
            refuse(f"forge_snapshot_build must look like 2.0.16-SNAPSHOT-11.10 (got {build!r})")
        year = now.year - 1 if now.strftime("%m.%d") < f"{m.group(1)}.{m.group(2)}" else now.year
        forge = f"snapshot-{year}-{m.group(1)}-{m.group(2)}"          # the stamp fetch-forge.sh gives the runtime
    else:
        with open(os.path.join("forge", "VERSION"), encoding="utf-8") as f:
            forge = f.read().strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]*", vals["profile"]):
        refuse(f"profile must be an AI profile name (got {vals['profile']!r})")
    if vals["mc"] not in ("off", "on", "max", "lite"):
        refuse(f"mc must be off, on, max or lite (got {vals['mc']!r})")
    for k in ("playbooks", "publish"):
        if vals[k] not in ("true", "false"):
            refuse(f"{k} must be true or false (got {vals[k]!r})")
    run_id = vals["run_id"] or f"{now.strftime('%Y-%m-%d')}-{name}-{forge}-s{seed}{'-bots' if vals['playbooks'] == 'true' else ''}"
    if not re.fullmatch(r"[A-Za-z0-9._-]+", run_id):
        refuse(f"run_id may hold letters, digits, dots, dashes and underscores (got {run_id!r})")

    out = {"league": league, "cycles": vals["cycles"], "shards": vals["shards"], "jobs_per_shard": vals["jobs_per_shard"],
           "seed": seed, "run_id": run_id, "forge_channel": vals["forge_channel"], "snapshot_build": build,
           "profile": vals["profile"], "mc": vals["mc"], "playbooks": vals["playbooks"], "publish": vals["publish"],
           "matrix": json.dumps(list(range(1, int(vals["shards"]) + 1)))}
    for k, v in out.items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
