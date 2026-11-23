#!/usr/bin/env python3
"""land_stall.py RUN_DIR...: the seat-games in which a seat held only lands that return a land and played none, and its wins in them.

A session helper; read-only (DESIGN.md section 46). RUN_DIR is a league run (shard-N/gNNNNN) or an ab.py run directory
(arm-*/gNNNN). Per deck: the lands of that kind in its list, its games and wins, the games with at least one own turn at
four lands or fewer on which every land in its hand was one that returns a land as it enters and it played no land (and was
not out of the game that turn), its wins in those games, the number of such turns, and the same for two such turns or more.
`runner/mistakes.py` (LAND DROPS) counts the turns; this counts the games and what became of them. The lands are known by
name (the Ravnica cycle and Guildless Commons).
"""
import collections, glob, gzip, json, os, sys
BOUNCE={'Golgari Rot Farm','Boros Garrison','Gruul Turf','Selesnya Sanctuary','Dimir Aqueduct','Rakdos Carnarium','Orzhov Basilica','Simic Growth Chamber','Izzet Boilerworks','Azorius Chancery','Guildless Commons'}
if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__)
    sys.exit(0)
D=collections.defaultdict(collections.Counter)
for root in sys.argv[1:]:
    for rj in sorted(glob.glob(os.path.join(root,'shard-*','*','run.json'))+glob.glob(os.path.join(root,'arm-*','*','run.json'))):
        run=json.load(open(rj)); g=run['games'][0]
        evf=os.path.join(os.path.dirname(rj),'games',os.path.basename(g['events']))
        if not os.path.exists(evf): evf+='.gz'
        op=gzip.open if evf.endswith('.gz') else open
        with op(evf,'rt',encoding='utf-8') as f: evs=[json.loads(l) for l in f if l.strip()]
        ids={d['seat']:d['id'] for d in run['decks']}
        lands={d['seat']:{c['name'] for c in d.get('cards') or [] if c.get('land')} for d in run['decks']}
        has={d['seat']:sum(c.get('count',1) for c in d.get('cards') or [] if c['name'] in BOUNCE) for d in run['decks']}
        w=next((p['seat'] for p in g['players'] if p.get('won')),None)
        stall=collections.Counter(); early=collections.Counter(); cur=None
        def close(c):
            if c is None or not c['held'] or c['played'] or c['lost']: return
            if all(x in BOUNCE for x in c['held']):
                stall[c['seat']]+=1
                if c['lands']<=4: early[c['seat']]+=1
        for e in evs:
            k=e['e']
            if k=='turn':
                close(cur)
                st=next((p for p in e.get('state') or [] if p['seat']==e.get('seat')),None)
                cur=None if st is None else {'seat':e['seat'],'held':[c for c in st.get('hand') or [] if c in lands[e['seat']]],'lands':st.get('lands') or 0,'played':False,'lost':False}
            elif cur is not None:
                if k=='land' and e.get('seat')==cur['seat']: cur['played']=True
                elif k=='lost' and e.get('seat')==cur['seat']: cur['lost']=True
        close(cur)
        for s,i in ids.items():
            d=D[i]; d['games']+=1; d['wins']+=(w==s); d['bounce_cards']=has[s]
            if early[s]>=1:
                d['games_early']+=1; d['wins_early']+=(w==s); d['turns_early']+=early[s]
            if early[s]>=2:
                d['games_early2']+=1; d['wins_early2']+=(w==s)
tot=collections.Counter()
print(f"{'deck':22} {'bounce lands':>12} {'games':>6} {'wins':>5}   {'games with such a turn at 4 lands or fewer':>42} {'wins':>5} {'turns':>6}   {'two turns or more':>18} {'wins':>5}")
for k,v in sorted(D.items()):
    print(f"{k:22} {v['bounce_cards']:12} {v['games']:6} {v['wins']:5}   {v['games_early']:42} {v['wins_early']:5} {v['turns_early']:6}   {v['games_early2']:18} {v['wins_early2']:5}")
    for kk in ('games','wins','games_early','wins_early','turns_early','games_early2','wins_early2'): tot[kk]+=v[kk]
print(f"{'all':22} {'':12} {tot['games']:6} {tot['wins']:5}   {tot['games_early']:42} {tot['wins_early']:5} {tot['turns_early']:6}   {tot['games_early2']:18} {tot['wins_early2']:5}")
