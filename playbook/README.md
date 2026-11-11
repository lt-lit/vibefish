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

## `playbook` (Phase 4)

A top-level `playbook` object in the same file holds the decisions Vibefish takes for the seat instead of Forge's AI
(`controller/src/vibefish/Playbook.java`, applied by `PlaybookController` through Forge's public controller hooks when
the harness is given `--playbook id=file`). Everything absent stays Forge's.

```
"playbook": {
  "version": 2,
  "attack":   {"policy": "go_wide" | "pressure", "target": "lowest_life" | "weakest_board" | "highest_life" | "biggest_board",
               "min_attackers": 3, "safety_margin": 5, "max_reserve": 3, "spread": false, "damage_per_loss": 3},
  "mulligan": {"min_lands": 2, "max_lands": 5, "max_mulligans": 2},
  "cast":     {"rules": [ ... ], "max_per_turn": 60},
  "notes": "why"
}
```

### `attack`

`go_wide` attacks the chosen opponent (`target`: the lowest life, the fewest untapped creatures, the highest life, or
the most power on the battlefield) with every creature that can attack it free of attack taxes, minus a reserve:
the toughest creatures are kept home, up to `max_reserve`, until the strongest single opponent's possible attack next
turn is below our life minus `safety_margin` (each kept blocker is assumed to absorb that opponent's biggest attacker).
With fewer than `min_attackers` able to go, or no legal declaration, Forge decides as usual. With `spread` the attack
is split: the first defender gets the biggest attackers until it is dead even if each of its untapped creatures blocks
one of them, and what is left over goes at the next opponent by the same rule; an opponent that cannot be killed this
turn takes everything still unassigned. Evasion and trample are not counted.

`pressure` keeps the same reserve and adds the blockers. First the kills: in `target` order, an opponent that is dead
even if each of its blockers stops one of our biggest attackers gets the attackers that takes. Then, with what is left,
the opponent the swing scores best on (damage that gets through, less `damage_per_loss` for every attacker a blocker
can kill; `target` order breaks near ties). Against that opponent the attackers no blocker can kill always go, and the
others go only together and only if the damage they add is at least `damage_per_loss` times the creatures the defender
can kill. Anything left at home goes wherever it is safe. Whether a blocker can block and kill an attacker is Forge's
own combat arithmetic on the battlefield as it stands (abilities that might be activated during combat are not
weighed). A turn on which nothing is worth sending is a turn without an attack, unless a creature has to attack, when
Forge declares. `min_attackers` defaults to 1 for this policy; `spread` is not used (the kills split the attack).
Against no blockers it plays exactly as `go_wide` with `spread`. Counters: `attack_none`, `attack_held`,
`attack_lethal`, `attack_expected_losses`, `attack_forced`.

The `mulligan` rule keeps a hand whose land count is within the range and never mulligans past `max_mulligans`;
without it Forge's own mulligan logic runs.

### `cast`: which card, when, aimed at what

The rules are read top to bottom every time the seat has priority in one of its own main phases with nothing on the
stack, after Forge has made the turn's land drop. The first `play` or `activate` rule that has something to do does
it, one spell or ability at a time; when none has, the choice is Forge's, minus whatever a `hold` rule keeps back.
Outside the seat's own main phases only the holds apply.

| rule | does | keys |
|---|---|---|
| `{"play": [cards]}` | casts the first listed card that is in hand (or is the commander in the command zone), legal and affordable. Forge's own opinion of the card is not asked, so this is also how a card flagged `AI:RemoveDeck:All` gets cast | `when`, `target`, `phase`, `times` (casts of one card a turn, default 1: only a card that comes back to hand, a buyback spell, can be cast again) |
| `{"activate": [permanents]}` | uses an activated ability of a listed permanent of ours (mana abilities stay Forge's to tap) | `ability` (a piece of the ability's text, when the card has several), `times` (per permanent per turn, default 1), `when`, `target`, `phase` |
| `{"hold": [cards]}` | Forge's AI may not cast these cards, from any zone, nor use the activated abilities of these permanents (`ability`: only the one whose text it quotes). A `play` or `activate` rule still may, which is how "only this way" is written. A card named by several hold rules is released as soon as one of them is | `until` (released when all of these hold; never, without it), `ability` |

- `target`: the name of a permanent we control (a token by Forge's name for it, `Goblin Token`). The spell must have
  exactly one part that takes a target, and it is pointed at that permanent and nothing else. Without `target`, a spell
  that needs no choice is cast as it is; one that needs targets or an X is cast only if Forge's own logic for the card
  agrees, since that logic is what picks them.
- `phase`: `main` (either main phase, the default), `main1` or `main2`.
- `when` / `until`: a list of conditions, all of which must hold. A condition is text:
  `"<metric> <op> <number>"` with `>= <= > < == !=`, `"<metric> <op> <metric>"` (`"opp_power > power"`), or
  `"controls <card name>"` / `"not controls <card name>"` (a permanent of ours on the battlefield).

| metric | counts |
|---|---|
| `creatures`, `tokens` | creatures we control; the creature tokens among them |
| `type:<CreatureType>` | creatures we control of that type (`type:Goblin >= 5`) |
| `attackers` | our untapped creatures without summoning sickness |
| `lands`, `hand`, `library`, `life` | lands we control, cards in hand, cards left in our library, our life |
| `mana` | Forge's estimate of the mana we can still produce this turn |
| `storm`, `drawn` | spells we have cast this turn, cards we have drawn this turn |
| `turn` | our own turn number |
| `main` | 1 in our first main phase, 2 in our second, 0 at any other time (`"main == 2"` keeps a card for after combat) |
| `opponents` | opponents still in the game |
| `power` | total power of our creatures |
| `opp_creatures`, `opp_power`, `opp_life` | the most creatures, the most total power, the highest life any one opponent has |
| `threat` | the most damage one opponent could attack us with next turn |
| `hand:<group>` | cards in hand from a named list: `"cast": {"groups": {"zada_spells": ["Expedite", ...]}, "rules": [...]}`, then `"hand:zada_spells >= 1"` |

A rule that names a card that is not in the deck, an unknown metric or a malformed condition stops the harness before
the first game (exit 2), so a typo cannot switch a rule off quietly. `max_per_turn` caps the plays the rules make in
one turn (default 60) as a guard against a free loop. A cast that does not go through (Forge could not pay for it after
all) is not tried again that turn.

The harness records the playbook per seat in `run.json` (`decks[].playbook`, the `cast` object as written) and the
policy's counters per game (`games[].playbook_stats`): `attack_decisions`, `attack_policy`, `attack_fallback`,
`attack_spread`, `attackers_declared`, `attackers_reserved`, `mulligan_decisions`, `mulligans_taken`, and for the
cast rules `cast_decisions` (times the rules were read), `cast_policy` (times one fired), `cast_rule_<n>` (per rule, by
its position in the file), `cast_hold_vetoes` (a Forge choice that a hold turned down), `cast_hold_stuck` (a hold that
could only be kept by passing), `cast_failed`, `cast_forge_declined`, `cast_turn_limit`, `cast_errors`.
`FORGE_JAVA_OPTS=-Dvibefish.trace=true` prints one line per rule decision to the shard log.

### Writing one

The loop is goldfish first, tables second (DESIGN.md §21):

```
runner/goldfish.sh "$PRECONS/Goblin Storm [SLD] [2026].dck" -n 100 -s 7000 -i gs-stock                                   # stock AI
runner/goldfish.sh "$PRECONS/Goblin Storm [SLD] [2026].dck" -n 100 -s 7000 -i gs-playbook -P playbook/precons/goblin-storm.json
runner/hands.py compare results/gs-stock results/gs-playbook      # kill turn by run, paired difference on the same seeds
runner/hands.py held results/gs-stock                             # the cards the seat sat on with the mana for them unspent
runner/hands.py game results/gs-playbook/shard-1/games/game-005.events.jsonl    # one game turn by turn: read the slow ones
runner/ab.py play --deck goblin-storm --arms stock,playbook ...   # then the same deck at real tables
```

Goldfish measures whether the seat runs its own deck (what it casts, in what order, how fast it kills three opponents
that do nothing); it says nothing about blocking, removal or being attacked, which is what the tables are for.
`runner/ab.py` has `playbook` and `playbookdata` arms.

## `variants/`

Candidate playbooks that are not the deck's shipped one: `variants/<deck>-<name>.json` holds a `playbook` object (and
says what it is a variant of). `runner/ab.py --data playbook/variants/<deck>-<name>.json` plays one locally, and the
`ab-run` workflow takes `deck@name` in its deck list, so several candidates can be measured side by side on the same
tables before one of them replaces the playbook in `precons/`. A variant carries no deck data: the data arms need the
deck's own file.
