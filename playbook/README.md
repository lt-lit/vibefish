# playbook/

Per-deck data for Forge's AI (Phase 3) and, later, the playbooks (Phase 4). `precons/` holds one file per precon of
the league (`runner/precon-league.json`), written by `runner/deckdata.py` and hand-curated where someone has looked at
the deck. Decks that are not public precons live in the data repository, in the same format.

## `precons/<deck-id>.json`

```
schema        1
deck, file, name, commanders
generated     written by runner/deckdata.py from the decklist, Commander Spellbook and Forge's card scripts; rewritten on every run
curated       written by hand; overrides the generated block key by key; never touched by the generator
```

Keys of either block (the effective value is the curated one when present, else the generated one):

| key | what Forge does with it | how it reaches the seat |
|---|---|---|
| `key_cards` | ordered list of card names: the AI's tutors fetch the first one they can, its discard and exile costs spare them, the Monte Carlo plan treats them as pieces | `Deck.addKeyCard` on that seat's deck (Forge's `KeyCards=` deck metadata), by the harness `--data` |
| `roles` | `{role: [card names]}` in the vocabulary of `res/lists/ai-card-roles.txt` (`overrun`, `storm_payoff`, `reanimation_spell`, `big_target`, `cheat_spell`, `cheat_target`, `mass_payoff`, ...): what Forge's combo plan detectors look for (GO_WIDE wants two `overrun` finishers and 16 cheap bodies, STORM two payoffs and eight rituals or cantrips, ...) | added to Forge's role list for the game (`AiCardLists.configure`) |
| `combos` | `[{kind: win|lock, name, slots: [[card], [card / card]]}]`, Forge's `ai-combos.txt` lines: the AI recognises the combo in its own deck and in what opponents show | added to `ComboCatalog` for the game |
| `pairs` | `[{cards: [a, b]}]`, two-card Commander combos (`ai-commander-combos.txt`) for the Commander plan | added to Forge's pair list for the game |
| `deck_plan` | `auto` (Forge classifies the deck) or an archetype: `AGGRO`, `BURN`, `CONTROL`, `COMBO`, `RAMP`, `LANDS`, `MIDRANGE` (`FLAT_MC_DECK_PLAN`) | the seat's AI profile |
| `profile` | `{PROPERTY: value}` overrides of Forge's `Default.ai` for this seat (`PLAY_AGGRO`, `TOKEN_GENERATION_ABILITY_CHANCE`, `MIN_COUNT_FOR_STORM_SPELLS`, `HOLD_LAND_DROP_FOR_MAIN2_IF_UNUSED`, ...) | a profile `Vibefish-<deck-id>.ai` written from `Default.ai` plus the overrides, passed with `--profile` |
| `notes` | why (curated only) | nowhere |

The role and combo lists are global in Forge for the length of a game, so the other seats see the added lines too;
in practice a line only matters to a seat whose deck holds the named cards, and an opponent that recognises a visible
combo piece treats it as a removal target, which works against the data-fed seat, not for it. Seats without a data
file play stock Forge AI.

`precons/spellbook/<deck-id>.json` is the trimmed Commander Spellbook answer for the list (combos included, almost
included), kept as provenance; `runner/deckdata.py generate --no-spellbook` reuses it.

## Commands

```
runner/deckdata.py generate --runtime forge/runtime-snapshot            # every league deck; curated blocks survive
runner/deckdata.py generate --runtime forge/runtime-snapshot --deck token-triumph
runner/deckdata.py show playbook/precons/token-triumph.json             # the effective data
runner/deckdata.py forge-lines playbook/precons/token-triumph.json      # the lines Forge will be given
runner/ab.py play --deck token-triumph --games 40 --seed 20261110 --out results/ab-token-triumph --runtime forge/runtime-snapshot -j 2
runner/ab.py rollup results/ab-token-triumph                            # paired: same tables with and without the data
```
