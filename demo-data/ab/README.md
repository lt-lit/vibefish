# demo-data/ab

Paired A/B results for per-deck AI data (`runner/ab.py rollup`, DESIGN.md §19), one file per deck and run. The dashboard
does not read these yet; the numbers are summarised in DESIGN.md. Each file holds the arms' win rates with Wilson
intervals, the paired differences, and every game's seats, seed, winner and length.

Dated `*-local/` directories hold 20- to 40-table checks played on a session's machine rather than in Actions, named by
deck and the arms they ran; the same format, smaller.
