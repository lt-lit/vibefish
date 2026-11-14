#!/usr/bin/env python3
"""add_row.py ROW_FILE: append one table row (the file's text, one line) to playbook/variants/README.md, after the table's last row.
A row that starts with the same first cell replaces the old one."""
import sys
p='/home/user/vibefish/playbook/variants/README.md'
row=open(sys.argv[1],encoding='utf-8').read().strip()
assert row.startswith('| `') and row.endswith('|') and '\n' not in row, 'one table row'
key=row.split('|')[1].strip()
lines=open(p,encoding='utf-8').read().split('\n')
old=[i for i,l in enumerate(lines) if l.startswith('|') and l.split('|')[1].strip()==key]
if old:
    lines[old[0]]=row; print('replaced row', key)
else:
    last=max(i for i,l in enumerate(lines) if l.startswith('| '))
    lines.insert(last+1,row); print('added row', key)
open(p,'w',encoding='utf-8').write('\n'.join(lines))
