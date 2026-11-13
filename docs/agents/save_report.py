#!/usr/bin/env python3
"""save_report.py TASK_ID DECK [SUBDIR]: an agent's final report, verbatim from its transcript, into docs/agents/reports/<SUBDIR>/DECK.md."""
import json, os, sys
tid, deck = sys.argv[1], sys.argv[2]; sub = sys.argv[3] if len(sys.argv) > 3 else '2026-11-13'
T = f'/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/tasks/{tid}.output'
msg = None
for line in open(T):
    if not line.strip(): continue
    r = json.loads(line); c = (r.get('message') or {}).get('content')
    if isinstance(c, list):
        for part in c:
            if part.get('type') == 'tool_use' and 'andback' in (part.get('name') or ''):
                msg = (part.get('input') or {}).get('message')
if not msg: sys.exit(f'no handback found for {tid}')
d = f'/home/user/vibefish/docs/agents/reports/{sub}'; os.makedirs(d, exist_ok=True)
S = '/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad'
msg = msg.replace(S, '<scratch>').replace('/home/user/vibefish/', '')
open(f'{d}/{deck}.md', 'w').write(f'<!-- The report of the agent that wrote this deck\'s candidate, as it handed it back (docs/agents/). <scratch> is that session\'s scratch directory, which does not outlive its container. -->\n\n{msg.rstrip()}\n')
print(f'saved {d}/{deck}.md', len(msg), 'chars')
