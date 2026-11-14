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
  `mirko`, `demons`): the same three files a deck.

The reports were made from shard artifacts merged the way the workflow's rollup merges them; the win counts in them
are those of the published rollups in `demo-data/ab/`. Regenerated on 2026-11-14 05:55 UTC after `runner/playtest.py`
learnt that a split card is cast under the name of one half (until then Connive // Concoct, Find // Finality, Dusk //
Dawn and the like read as never cast): three card comparisons gained an entry, nothing else changed.
