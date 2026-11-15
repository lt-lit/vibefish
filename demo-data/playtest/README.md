# Playtest reports and card comparisons

`runner/playtest.py` reports (kind `playtest`: the deck in the seat under test, what its games say) and
`docs/agents/arm_card_diff.py` comparisons of two arms of one exam: for each nonland card, the games it was drawn and
the games it was cast under stock Forge AI and under the playbook, on the same tables. DESIGN.md §30 and §31.

`2026-11-14/`:
- the twelve pool decks, from the 200 tables each of `ab-run` #26 (seed 20261240, opponents drawn from `bots-v2` under
  their playbooks of 2026-11-12): `<deck>-stock.json`, `<deck>-playbook.json` (the shipped playbook of that day, Forge's
  attack) and `<deck>-card-diff.txt`;
- Blight Curse, Mutant Menace, Squirreled Away and Ahoy Mateys, from the stock and go-wide arms of `ab-run` #27 (seed
  20261260; the candidates `wretch`, `mothman`, `acorns`, `crew`): the same three files a deck, and for Blight Curse
  the two reports as Markdown (`blight-curse-stock.md`, `blight-curse-playbook.md`), which is what a playtest report
  looks like;
- Veloci-Ramp-Tor, Death Toll and Deadly Disguise, from the stock and go-wide arms of `ab-run` #28 (seed 20261280; the
  candidates `stampede`, `winter`, `veil`): the same three files a deck;
- Revenant Recon and Blood Rites, from the stock and go-wide arms of `ab-run` #29 (seed 20261290; the candidates
  `mirko`, `demons`): the same three files a deck;
- `pool-answers/`: the nine pool decks whose answer rules were examined in `ab-run` #31 to #33 and #35 (seed 20261300,
  playbook arms only): `<deck>-shipped.json` is the report of the shipped playbook of 2026-11-13, `<deck>-answers.json`
  (`token-triumph-answers2.json`) of the candidate on the same tables, and `<deck>-check.txt` sets the two beside the
  stock arm of `ab-run` #26 for the cards the candidate's new rules name, then lists what the candidate casts fifteen
  points less or more often than the shipped playbook and than stock AI. The candidates shipped on 2026-11-14;
- `second-pass/`: the second-pass exams of the owner's decks (`ab-run` #36 to #39, seed 20261310): for each deck the
  reports of its three arms, `<deck>-stock.json`, `<deck>-gowide.json` and `<deck>-forgeattack.json` (the stock pilot,
  the candidate with go-wide, the same rules with Forge's attack), and `<deck>-gowide-card-diff.txt` and
  `<deck>-forgeattack-card-diff.txt`: what each attack arm casts fifteen points less or more often than the stock
  pilot on the same tables. A shipped deck's notes quote the diff of the arm that shipped.

`2026-11-15/` (DESIGN.md §32):
- `owners-table/`: the ten decks of the owner's table at that table, from the 200 tables each of `ab-run` #42 (seed
  20261350, opponents drawn from the other nine decks of `owners-table-v1` under their shipped playbooks). For each deck
  `<deck>-playbook.md` and `.json` (the playtest report under the shipped playbook), `<deck>-stock.json` (the stock
  pilot on the same tables), `<deck>-pair.md` (the two side by side: `runner/playtest.py --against`, which is what a
  comparison of two lists or two pilots looks like) and `<deck>-card-diff.txt`; for Blight Curse, the deck the owner
  plays most, also `blight-curse-stock.md`. They are the example of a playtest report until there is a list of the
  owner's own. A face-down cast is logged without the card's name, so Deadly Disguise's morph and disguise creatures
  read as never cast in its reports under either pilot; that they are seldom in hand at a loss says they are cast;
- `wait-trial/`: the card check of the `forge` rule's wait option (`ab-run` #41, seed 20261340): for Blight Curse, Mutant
  Menace, Squirreled Away and Ahoy Mateys the reports of the three arms (`<deck>-stock.json`, `<deck>-forge.json`,
  `<deck>-forgewait.json`), `three-way.txt` (the cards the plain `forge` rule casts less than the stock pilot and what
  the wait does with them: `docs/agents/three_way.py`), `named-split.txt` (the three arms' casts summed over the cards
  no rule names, the cards named below the `forge` rule and the cards named above it: `docs/agents/named_split.py`) and
  `cast-phase.txt` (each arm's casts before and after its attack: `docs/agents/cast_phase.py`).

The reports were made from shard artifacts merged the way the workflow's rollup merges them; the win counts in them
are those of the published rollups in `demo-data/ab/`. Regenerated on 2026-11-14 05:55 UTC after `runner/playtest.py`
learnt that a split card is cast under the name of one half (until then Connive // Concoct, Find // Finality, Dusk //
Dawn and the like read as never cast): three card comparisons gained an entry, nothing else changed.
