#!/usr/bin/env python3
"""Live status page for runs in progress: progress bars, per-shard pace, interim wins by arm, ETA.

    runner/status.py [--results results] [--port 8787]

Serves / (a small auto-refreshing page) and /status.json, computed on every request from the run.json files
the harness rewrites after each game. Development tool for the machine the runs are on; nothing is written.
Standard library only.
"""
import argparse
import glob
import json
import os
import statistics
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vibefish runs</title><style>
:root{color-scheme:light dark;--bar:#2a78d6;--track:#e1e0d9;--ink:#0b0b0b;--muted:#52514e;--bg:#f9f9f7;--card:#fcfcfb;--border:rgba(11,11,11,.1)}
@media(prefers-color-scheme:dark){:root{--track:#2c2c2a;--ink:#f0efec;--muted:#c3c2b7;--bg:#0d0d0d;--card:#1a1a19;--border:rgba(255,255,255,.1);--bar:#3987e5}}
body{margin:0;padding:16px;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif}
h1{font-size:1.3rem;margin:0 0 4px}.muted{color:var(--muted);font-size:.9rem}
.run{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;margin:14px 0}
.bar{height:10px;background:var(--track);border-radius:5px;overflow:hidden;margin:6px 0}.bar i{display:block;height:100%;background:var(--bar);border-radius:5px}
.row{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.arm{margin-top:8px}.arm b{font-variant-numeric:tabular-nums}
table{border-collapse:collapse;font-size:.9rem;margin-top:8px}td,th{padding:3px 10px 3px 0;text-align:left;border-bottom:1px solid var(--border)}
</style></head><body><h1>Vibefish runs</h1><p class="muted" id="when">loading…</p><div id="runs"></div>
<script>
const fmt=s=>s==null?'–':(s>=3600?`${Math.floor(s/3600)} h ${Math.round(s%3600/60)} min`:s>=600?`${Math.round(s/60)} min`:s>=90?`${Math.floor(s/60)} min ${Math.round(s%60)} s`:`${Math.round(s)} s`);
async function tick(){try{const r=await fetch('status.json',{cache:'no-cache'});const d=await r.json();
document.getElementById('when').textContent=`updated ${new Date(d.now*1000).toLocaleTimeString()} · refreshes every 15 s`;
const el=document.getElementById('runs');el.replaceChildren();
for(const run of d.runs){const div=document.createElement('div');div.className='run';
const pct=run.total?Math.round(100*run.done/run.total):0;
div.innerHTML=`<div class="row"><strong></strong><span class="muted"></span></div><div class="bar"><i style="width:${pct}%"></i></div>
<div class="row muted"><span>${run.done} / ${run.total} games · ${pct}%</span><span>${run.state==='complete'?'complete':`ETA ${fmt(run.eta_s)}`} · avg ${fmt(run.avg_game_s)}/game</span></div>`;
div.querySelector('strong').textContent=run.id;div.querySelector('.row .muted').textContent=run.state==='complete'?'done':(run.stale?'no new game for a while':'running');
const t=document.createElement('table');t.innerHTML='<tr><th>Shard</th><th>Games</th><th>Avg</th><th>Last game</th></tr>';
for(const s of run.shards){const tr=document.createElement('tr');tr.innerHTML=`<td>${s.name}</td><td>${s.done} / ${s.total}</td><td>${fmt(s.avg_game_s)}</td><td>${s.last||'–'}</td>`;t.append(tr);}div.append(t);
if(run.arms&&Object.keys(run.arms).length){const a=document.createElement('div');a.className='arm';a.innerHTML='<div class="muted">Interim game wins by arm</div>';
for(const [k,v] of Object.entries(run.arms)){const p=document.createElement('div');p.innerHTML=`<b>${Math.round(100*v.share)}%</b> ${k} · ${v.wins} of ${v.games}`;a.append(p);}div.append(a);}
if(run.decks&&run.decks.length){const dk=document.createElement('div');dk.className='arm muted';dk.textContent='Deck wins: '+run.decks.map(x=>`${x.id} ${x.wins}`).join(' · ');div.append(dk);}
el.append(div);}}catch(e){document.getElementById('when').textContent='status unavailable: '+e;}}
tick();setInterval(tick,15000);
</script></body></html>"""


def run_status(run_dir):
    shards = []
    games_all = []
    decks = None
    newest = 0.0
    for rj in sorted(glob.glob(os.path.join(run_dir, "shard-*", "run.json"))):
        try:
            with open(rj, encoding="utf-8") as f:
                run = json.load(f)
        except (OSError, ValueError):
            continue  # being rewritten right now; next refresh gets it
        games = run.get("games", [])
        decks = decks or run.get("decks", [])
        durs = [g.get("duration_ms", 0) / 1000 for g in games if g.get("duration_ms")]
        newest = max(newest, os.path.getmtime(rj))
        shards.append({
            "name": os.path.basename(os.path.dirname(rj)),
            "done": len(games),
            "total": run.get("games_requested", len(games)),
            "avg_game_s": round(statistics.fmean(durs), 1) if durs else None,
            "last": (f"{games[-1].get('reason')} in {games[-1].get('turns')} turns" if games else None),
        })
        games_all.extend(games)
    if not shards:
        return None
    done = sum(s["done"] for s in shards)
    total = sum(s["total"] for s in shards)
    durs = [g.get("duration_ms", 0) / 1000 for g in games_all if g.get("duration_ms")]
    avg = statistics.fmean(durs) if durs else None
    eta = max((s["total"] - s["done"]) * (s["avg_game_s"] or avg or 0) for s in shards) if avg else None
    arms = {}
    for g in games_all:
        profs = g.get("profiles")
        if not profs:
            continue
        for p in set(profs):
            arms.setdefault(p, {"games": 0, "wins": 0})["games"] += 1
        w = g.get("winner")
        if w is not None and w < len(profs):
            arms[profs[w]]["wins"] += 1
    for a in arms.values():
        a["share"] = round(a["wins"] / a["games"], 3) if a["games"] else None
    deck_wins = []
    for d in decks or []:
        deck_wins.append({"id": d.get("id"), "wins": sum(1 for g in games_all if g.get("winner") == d.get("seat"))})
    complete = os.path.exists(os.path.join(run_dir, "rollup.json")) or (done >= total and total > 0)
    return {
        "id": os.path.basename(run_dir), "state": "complete" if complete else "running",
        "done": done, "total": total, "avg_game_s": round(avg, 1) if avg else None,
        "eta_s": None if complete else (round(eta) if eta else None),
        "stale": (not complete) and (time.time() - newest > 1800),
        "last_write": newest, "shards": shards, "arms": arms, "decks": deck_wins,
    }


def status(results_dir, limit=5):
    runs = []
    for d in glob.glob(os.path.join(results_dir, "*")):
        if os.path.isdir(d):
            st = run_status(d)
            if st:
                runs.append(st)
    runs.sort(key=lambda r: r["last_write"], reverse=True)
    return {"now": time.time(), "results": results_dir, "runs": runs[:limit]}


class Handler(BaseHTTPRequestHandler):
    results = "results"

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            body, ctype = PAGE.encode("utf-8"), "text/html; charset=utf-8"
        elif path == "/status.json":
            body, ctype = json.dumps(status(self.results)).encode("utf-8"), "application/json"
        else:
            self.send_response(404); self.end_headers(); return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"))
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--once", action="store_true", help="print status.json and exit")
    args = ap.parse_args(argv)
    if args.once:
        print(json.dumps(status(args.results), indent=1))
        return 0
    Handler.results = args.results
    srv = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"serving run status for {args.results} on port {args.port}", file=sys.stderr)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
