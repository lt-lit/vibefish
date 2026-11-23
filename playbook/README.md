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
  "triggers": [ ... ],
  "targets":  {"triggers": "danger", "min": 4, "margin": 5},
  "block":    {"survive": true},
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

`forge` (harness 0.4.0) is Forge's own attack, which is also what a playbook without an `attack` block gets; the
block is then there to carry `aim`, `finish` and `guard`.

`"aim": "danger"` (harness 0.4.5), on any policy and before `finish`, changes whom the attack goes at and nothing
else. Forge's AI builds an attack against one opponent, and at a table of four it does not pick that opponent by who
is winning: with three opponents alive 48% of a table's attackers go at the opponent that looks most dangerous (a
third would by chance), and when none does, the one attacked has the lowest life at the table three times in four
(`docs/agents/attack_danger.py` on 2,000 games at the owner's table, `DESIGN.md` §34). With the key, the attackers
the policy sent at a player are sent at the opponent that looks most dangerous instead (life plus twice its nonland
permanents, the weights of `cast.danger`) when all of this holds: that opponent is ahead of the one attacked by at
least `aim_margin` (default 5: a close table is left to the policy); the declared attack is not sure to kill the one
attacked (a kill stays where it is); every one of those attackers may attack the more dangerous opponent at no cost;
the damage that is sure to get through there whatever is blocked is at least what was sure where they were sent;
the more dangerous opponent has no more creatures that could block one of those attackers than the opponent they
were sent at; and no attacker meets a creature there that can block and destroy it unless it met one where it was
sent (Forge's own combat arithmetic on the battlefield as it stands). Which creatures attack is not changed, attackers of
planeswalkers and battles stay, and a declaration Forge's rules refuse is put back. Counters: `attack_aim_seen` (a
declaration with attackers at an opponent at least the margin behind the most dangerous one), `attack_aim` (they
were sent at the most dangerous opponent instead), `attack_aim_moved` (how many attackers), `attack_aim_kill_kept`
(the declared attack was sure to kill its target), `attack_aim_cannot` (an attacker may not attack there, or not for
free), `attack_aim_less` (less was sure to get through there), `attack_aim_blockers` (more creatures there could block
the attackers), `attack_aim_risk` (a blocker there would destroy an
attacker that was safe where it was sent), `attack_aim_already` (the policy's own attack went at the most dangerous
opponent), `attack_aim_invalid`, `attack_aim_errors`. `{"attack": {"policy": "forge", "aim": "danger"}}`.

`"open": true` (harness 0.4.5), on any policy, after `aim` and before `finish`, takes free damage. Forge's AI weighs
an attack against one opponent, and a creature it would not send into that opponent's blockers stays home even when
another opponent cannot block at all: with three opponents alive a seat attacks an opponent who cannot block on 28%
of the turns it could, attacks only an opponent with blockers on 38% and nobody on 34% (`DESIGN.md` §34). With the
key, the seat's creatures that stayed home attack an opponent with no creature that can block, the most dangerous
such opponent first, when all of this holds for a creature: it deals damage and may attack that opponent at no
cost (and is not sacrificed for attacking, as a decayed creature is); it has no ability that taps it (a creature that taps for mana or for an effect has something else to do),
unless it has vigilance; and Forge's own judgement of the seat's defence does not want it home
(`AiAttackController.notNeededAsBlockers`, the same call Forge's attack makes: its prediction of each opponent's
next attack against the blockers that would be left). An opponent that is not the most dangerous one alive is left
alone when the damage added would be sure to kill it, the order of `"finish": "leader"`. A declaration Forge's rules
refuse is put back. Counters: `attack_open_seen` (an opponent could not block and a creature that could attack it
had stayed home), `attack_open` (creatures were added), `attack_open_added` (how many), `attack_open_alone` (the
policy had declared no attack at all), `attack_open_home` (creatures Forge wanted home), `attack_open_utility`
(creatures with an ability that taps them), `attack_open_kill_left`, `attack_open_invalid`, `attack_open_errors`.
`{"attack": {"policy": "forge", "open": true}}`.

`"enable": {"with": "<a permanent of ours>", "send": "face_down"}` (harness 0.4.7), on any policy and before `aim`,
arranges an attacker for a permanent whose ability wants one. It is written for Kaust, Eyes of the Glade ("{T}: turn
target face-down attacking creature you control face up"): Forge's AI attacks with Kaust itself on a quarter of the
turns the ability could be used and sends a face-down creature on three in ten, so the deck's engine fires on a
tenth of the turns its commander is on the battlefield. On a turn the named permanent could be tapped for its ability
(on the battlefield, untapped, not summoning-sick) and the seat has a face-down creature that is a creature card face
up and may attack: if none is attacking, the one with the greatest power face up joins the attack, at the opponent
with the fewest creatures that could block it (the most dangerous of those on a tie); and the named permanent is
taken out of the attack if the policy sent it. The ability itself is used by a cast rule of the playbook with a combat
`phase` (above); this only sees to it that there is something for it to do. A declaration Forge's rules refuse is put
back. Counters: `attack_enable_seen` (the permanent was ready and a face-down creature was there), `attack_enable`
(the attack was changed), `attack_enable_sent` (a face-down creature was added), `attack_enable_home` (the permanent
was taken out of the attack), `attack_enable_ready` (nothing to change), `attack_enable_none` (no face-down creature
may attack), `attack_enable_invalid`, `attack_enable_errors`.
`{"attack": {"policy": "forge", "enable": {"with": "Kaust, Eyes of the Glade", "send": "face_down"}}}`.

`"finish": true` (harness 0.4.0), on any policy, takes a kill no block prevents. After the policy has declared its
attack, each opponent the seat is sure to kill gets enough attackers that the damage reaches its life whatever it
blocks: who may attack and block whom is Forge's own (`CombatUtil.canAttack`, `canBlock(attacker, blocker)`, so flying,
reach, protection and the like count), every blocker is assumed to stop one attacker whole (no trample is credited,
and an attacker that needs two blockers is assumed stopped by one), infect counts for nothing and an attack that
costs something is left out, so the count errs low. The opponent that looks most dangerous (life plus twice its
nonland permanents, the weights of `cast.danger`) is killed first, then any other the creatures still unassigned
can kill the same way; the heaviest attackers go first and only as many as it takes. Creatures the policy had sent
elsewhere are moved, everything else stays as the policy declared it, and if the changed attack is not a legal one
the policy's own is put back. A fog, a flash blocker or a life gain can still undo it (about one such kill in
twenty-five does not come off). Counters: `attack_kill_seen` (turns with such a kill), `attack_kill` (attackers were
added or moved for it), `attack_kill_moved` (how many), `attack_kill_already` (the policy's own attack already had
them there), `attack_kill_invalid`, `attack_kill_errors`. `{"attack": {"policy": "forge", "finish": true}}`.

What its exam showed (`ab-run` #45, `DESIGN.md` §34): with `finish` a seat passes up 4% of its sure kills where the
shipped playbooks pass up 34%, and wins no more tables (505 against 512 of 2,000). The kill of the most dangerous
opponent alive won tables; the kill of a less dangerous one while a more dangerous one lived lost them. Hence:

`"finish": "leader"` (harness 0.4.1) takes a sure kill only from the most dangerous opponent down: the opponent that
looks most dangerous is killed if the kill is sure, then the next one with the creatures that are left, and the
walk stops at the first opponent that cannot be killed for sure, so a weaker opponent is never killed while a more
dangerous one lives. The last opponent left is always the most dangerous one. Everything else is as for `true`
(`"any"` is another spelling of `true`). One more counter: `attack_kill_left`, a turn on which a sure kill of a
lesser opponent was there and was left alone.

`"finish_commander": true` (harness 0.4.13, beside `finish`) makes a commander's damage a kill of the same kind. An
opponent the creatures cannot kill through its life is still killed for sure when a commander of the seat that may
attack it would bring the combat damage it has dealt that opponent to 21 (twice its damage with double strike) and
none of that opponent's creatures that may block can block it (Forge's `CombatUtil.canBlock(attacker, blocker)`:
flying, protection, "can't be blocked"; a commander that only two creatures together may block counts as blockable).
The commander alone is sent at that opponent, in the same walk from the most dangerous opponent down, and the other
creatures stay free for the next opponent; where the damage reaches the life total anyway nothing changes. The guard
does not take such an attacker back and does not count that opponent's answer. Counters: `attack_kill_commander_seen`
(turns with such a kill in the plan), `attack_kill_commander` (the declaration was changed on such a turn). It comes
from a count (`runner/mistakes.py`, the kills by commander damage): a flying commander with twenty power sent at the
weakest player while the strongest sat at 33 life with nothing that could block it.
`{"attack": {"policy": "forge", "finish": "leader", "finish_commander": true}}`.

`"guard": true`, on any policy and after `finish`, does not tap out into a lethal answer. For each opponent the
attack as declared is not sure to kill, the seat asks what that opponent, alone, with every creature that may attack
on its next turn, would get through the creatures that would be untapped at home, under a blocking plan the seat
could carry out: an attacker one creature may stop is stopped whole by one blocker, one that needs two by two, a
trampler loses the toughness of each creature put in front of it, and blockers go where each prevents most, a
commander whose damage would be lethal by itself first (`CombatMath.plannedLeft`). If that is at least the seat's
life, or a commander's lethal damage gets through, and keeping attackers home changes it, attackers are taken back
one at a time, each time the one whose staying home lowers the threat most and among equals the one that deals
least, until no single opponent kills the seat. The attackers of a kill the attack is sure of are never taken back;
an attack that leaves the seat dead on board whatever stays home stands as declared (the race is all there is); and
if what is left is not a legal attack the declaration is put back. `"guard_margin": N` counts the seat as dead N
life early: between an attack and the answer a seat's life often falls and the opponent's board often grows. It was
built from a count: at the owner's table one death in six in combat comes with the seat's own tapped creatures able
to have prevented it, most of them after the seat's own attack (`runner/mistakes.py`, `DESIGN.md` §34).

This is the guard's second arithmetic (harness 0.4.4). The first (0.4.1 to 0.4.3, the one `ab-run` #46 played)
asked what the opponent was sure to get through whatever the seat blocked: a lower bound that counts a trampler or
a creature with menace as stopped by one blocker and knows no commander damage. Replayed on 125 deaths it was built
for, it changed the attack before the death on six.

`"guard": "table"` asks the wider question first: do the opponents one after another get the seat's life in damage
through what stays home (each against the same blockers, summed)? When nothing kept home holds the whole table off,
the one-opponent question is asked instead. (`"one"` is another spelling of `true`.)

Counters: `attack_guard_seen` (the declared attack left the seat open by the question asked), `attack_guard`
(attackers were taken back and it is not any more), `attack_guard_back` (how many), `attack_guard_single` (asked for
the table, held off the worst single opponent), `attack_guard_all` (nothing attacked after all),
`attack_guard_hopeless` (dead on board whatever stays home: the attack stood), `attack_guard_invalid`,
`attack_guard_errors`. `{"attack": {"policy": "forge", "finish": "leader", "guard": true}}`.

The `mulligan` rule keeps a hand whose land count is within the range and never mulligans past `max_mulligans`;
without it Forge's own mulligan logic runs.

### `cast`: which card, when, aimed at what

The rules are read top to bottom every time the seat has priority in one of its own main phases with nothing on the
stack, after Forge has made the turn's land drop. The first `play` or `activate` rule that has something to do does
it, one spell or ability at a time; when none has, the choice is Forge's, minus whatever a `hold` rule keeps back.
Outside the seat's own main phases only the holds apply, and the rules written for another moment: the seat's own
combat (`"phase": "attack"` or `"blocks"`, harness 0.4.7) and two moments of another player's turn (`"phase":
"defend"` or `"end"`, harness 0.4.12; below).

**What the rules do not name comes last, unless a `forge` rule says where it comes.** A rule that has something to do
always goes before Forge's own choice, and Forge's own choice is the only way a card no rule names is cast. A set of
engine rules (ramp, a draw spell, an activation) nearly always has something to do, so it starves the rest of the
deck: at 200 tables of bots Blight Curse's engine-only candidate cast Incremental Blight in 10 of the 54 games it was
drawn where stock AI cast it in 49 of 56, and the removal, wipes and large threats of every deck examined went the
same way (`DESIGN.md` §30). Goldfish does not show it. Two remedies, and a playbook usually wants both: a rule of its
own for each card that matters (an answer wants conditions about the board anyway), and a `{"forge": "unnamed"}` rule
at the place in the order where everything else belongs, typically after the commander and the core of the engine
and before the draw spells, the filler creatures and the mana sinks. `docs/agents/arm_card_diff.py` on the two arms of
an exam lists the cards a playbook casts less than stock AI does.

**Forge's AI casts most permanents after combat.** On the turns it attacks, stock AI makes seven of ten casts in its
second main phase: creatures, planeswalkers and sagas that do nothing for the combat wait for it. The rules are read in
both main phases and spend the mana in the first, so a `forge` rule that asks Forge there gets back only the cards
Forge casts before combat (the sorceries, the creatures whose arrival matters for the attack); `ab-run` #34 measured
that (`DESIGN.md` §30). `"wait": "main2"` on the rule is the remedy: in the first main phase, when Forge wants none
of the unnamed plays now but says of an unnamed card it could pay for that it is waiting for its second main phase,
the rules below the `forge` rule are not read and the seat passes; after combat the rules are read from the top
again, Forge chooses among the unnamed first, and the rules below get what is left. "Waiting for its second main
phase" is read off the card's own AI class (`MissingPhaseRestrictions` for a permanent, where a card Forge does not
want at all reads `CantPlayAi`; Forge's general answer does not tell the two apart). Forge sometimes keeps a card and
then does not cast it after combat either (Soul Snuffers in a deck of -1/-1 counters): the rules wait for such a card
once and not again in that game. What the option costs is that the plays below the rule happen after combat on a turn
it waits, so the rules whose cards matter for the attack (an anthem, haste, an equip) belong above it. Without the
option nothing changes for a playbook that was measured without it.

| rule | does | keys |
|---|---|---|
| `{"play": [cards]}` | casts the first listed card that is in hand (or is the commander in the command zone), legal and affordable. Forge's own opinion of the card is not asked, so this is also how a card flagged `AI:RemoveDeck:All` gets cast | `when`, `target` or `aim`, `phase`, `times` (casts of one card a turn, default 1: only a card that comes back to hand, a buyback spell, can be cast again) |
| `{"activate": [permanents]}` | uses an activated ability of a listed permanent of ours (mana abilities stay Forge's to tap) | `ability` (a piece of the ability's text, when the card has several), `times` (per permanent per turn, default 1), `when`, `target` or `aim`, `phase` |
| `{"forge": "unnamed"}` | at this place in the order Forge's own AI chooses among the plays no rule names: the spells of cards no `play` rule lists and the abilities no `activate` rule covers, the holds in force left out. It casts what it would have cast with only those to choose from (its own judgement of each card and its own targets); when it wants none of them, the rules below are read. A card a `play` rule lists with a `when` that does not hold is still a named card: it waits for its rule, or for the end of the rules. With `"wait": "main2"` the rules below are not read in the first main phase while Forge's AI keeps an unnamed card it could pay for for its second main phase (above) | `when`, `phase`, `wait` |
| `{"hold": [cards]}` | Forge's AI may not cast these cards, from any zone, nor use the activated abilities of these permanents (`ability`: only the one whose text it quotes). A `play` or `activate` rule still may, which is how "only this way" is written. A card named by several hold rules is released as soon as one of them is | `until` (released when all of these hold; never, without it), `ability` |

- `target`: the name of a permanent we control (a token by Forge's name for it, `Goblin Token`). The spell must have
  exactly one part that takes a target, and it is pointed at that permanent and nothing else. An Equip ability is not
  used on the creature that already wears the equipment (since 2026-11-12: Forge allows it, and a rule without that
  check paid for the same equip every turn). Without `target`, a spell
  that needs no choice is cast as it is; one that needs targets or an X is cast only if Forge's own logic for the card
  agrees, since that logic is what picks them.
- `aim` (play, activate; harness 0.3.4): the spell's one target is an opponent's permanent, chosen by the harness:
  `"aim": "permanent"` (any nonland permanent), `"creature"`, `"noncreature"`, `"artifact"`, `"enchantment"` or
  `"planeswalker"`. As with `target`, the spell must have exactly one part that takes a target; the candidates are the
  opponents' permanents of that kind that the spell can legally target (and, for a destroy effect, that are not
  indestructible). `aim_min` (default 0) is the least a permanent must be worth to be aimed at: its mana value, or a
  creature's power when that is more, so that removal is not spent on the first mana rock. `aim_toughness` (harness
  0.4.9; default none) keeps the aim to creatures of at most that toughness, for an effect that kills by a fixed amount
  (two -1/-1 counters: `"aim_toughness": 2`); the harness still does not work out what an amount kills, the rule says. `aim_at` says whose:
  `"danger"` (the default) takes the opponents in the order of how dangerous they look and aims at the best such
  permanent of the first opponent that has one; `"any"` aims at the best one on any opponent's side. "Best" is Forge's
  own rating (`ComputerUtilCard.getBestAI`: the best creature by its evaluation of creatures, else the most expensive
  permanent). **How dangerous an opponent looks** is its life plus twice its nonland permanents, which in the games of
  the owner's table picks the player who goes on to win in 42% of the turns of rounds 7 to 9 and 52% later, where the
  widest board alone, which is where Forge's AI sends most of its attackers and removal, picks 32% and 40% (`DESIGN.md`
  §33). The two weights are the playbook's: `"cast": {"danger": {"life": 1, "permanents": 2}, "rules": [...]}`. An aim
  is for removal that works on whatever it hits (destroy, exile, steal, bounce): the harness does not ask whether three
  damage kills the creature, so damage and -X/-X spells stay with Forge's own aiming (no `aim`, no `target`). It is
  also the way to cast a targeted card Forge's AI never casts (Maelstrom Pulse, Atomize, New Blood). A rule takes
  `target` or `aim`, not both. `{"play": ["Maelstrom Pulse"], "aim": "permanent", "aim_min": 4}`. Counters: `cast_aim`,
  `cast_aim_most_dangerous`, `cast_aim_next` (the permanent chosen belonged to the opponent that looked most dangerous,
  or that opponent had nothing to aim at and a later one did), `cast_aim_none` (nothing to aim at: the rule did not
  fire).
- `divide`, `divide_min` (play, activate, on a rule that has `aim`; harness 0.4.6): for a spell that divides an X among
  any number of targets (Fire Covenant: "pay X life, X damage divided as you choose among any number of target
  creatures"). `"divide": 3` is the most targets. The amount the rule may spend is what the cost allows (the mana the
  rest of the cost leaves, or for an X paid in life the life above `x_keep_life`), capped by the rule's `x` when it
  gives one. Each of the opponents' permanents of the aimed kind that the spell can target and that is worth `aim_min`
  has a price, the least amount that destroys it by Forge's own arithmetic (`ComputerUtilCombat.getEnoughDamageToKill`:
  damage already marked, indestructible and prevention are in it), and a rating (Forge's evaluation of a creature). The
  rule takes the set of at most `divide` of them with the highest total rating that the amount pays for, the cheaper
  set on a tie: with `aim_at` `"danger"` (the default) from the side of the opponent that looks most dangerous first
  and then from the next opponent's with what is left, with `"any"` over every opponent's side at once. X is the sum
  of the prices and each target is allocated its own. Nothing is cast for fewer than `divide_min` targets (default 1)
  or an X below `x_min`. `{"play": ["Fire Covenant"], "aim": "creature", "aim_min": 4, "divide": 3, "divide_min": 2,
  "x": 12, "x_keep_life": 18}`: two or three creatures worth four or more for at most twelve life, never paid below
  eighteen. Counters: `cast_divide`, `cast_divide_targets`, `cast_divide_x` (casts, targets and X summed over them),
  `cast_divide_few` (fewer targets than `divide_min` could be paid for), `cast_divide_invalid` (Forge refused the
  targets or the cost), `cast_divide_unfit` (the card named does not divide an X).
- `target_player` (play; harness 0.4.6): `"target_player": "self"` aims the spell's one target at the seat itself, for
  a spell that asks for a player and is meant for its own caster (Pact of the Serpent: "target player draws X cards and
  loses X life, where X is the number of creatures they control of the chosen type"). What such a spell asks as it
  resolves is Forge's to answer (it names the creature type the seat's deck holds most of). A rule takes `target`,
  `aim` or `target_player`, one of them. `{"play": ["Pact of the Serpent"], "target_player": "self",
  "when": ["type:Vampire >= 3", "life >= 20"]}`. Counter: `cast_self`.
- `take` (play; harness 0.4.14): for a spell that removes any number of counters from among the permanents on the
  battlefield and charges its caster for each (Eventide's Shadow: "You draw that many cards and lose that much life").
  Which counters go is asked as the spell resolves, and Forge's AI answers with every counter it would like gone,
  however many that is: all the counters it does not count as harmful on the opponents' permanents and all the -1/-1
  counters on the seat's own, 84 and 85 of them in two games, and the seat pays a life for each. In two leagues of
  the owner's table that answer left Blight Curse out of the game that same turn on 8 of the 21 casts (DESIGN §44). With `"take": {"keep_life": 15, "max": 8, "min": 3, "own_except": ["Tree of Perdition"]}`
  the rule answers instead, with the counters whose going helps the seat and no others: first +1/+1 counters from
  creatures and loyalty from planeswalkers an opponent controls, the largest stacks first; then -1/-1 counters from
  creatures of its own, the most shrunken first, never from a permanent `own_except` names (the deck wants those as
  they are). One kind of counter a permanent; at most `max` counters in all (default 8) and never more than the life
  the seat has above `keep_life` (default 15), so a cast cannot bring it under that. The rule does not cast while
  fewer than `min` counters (default 3) can be taken that way. Every other counter stays where it is: -1/-1 on an
  opponent's creature, +1/+1 on the seat's own, and the kinds the rule does not know. Only a play rule takes `take`, and the
  spell has to be one Forge resolves with its `RemoveCounter` effect; on any other card the block does nothing but
  hold the cast back until `min` is met. Counters: `cast_take`, `cast_take_counters` (the spell's resolutions the rule
  answered and the counters it took over them), `cast_take_short` (times the rule was read with fewer than `min` to
  take).
- `phase`: `main` (either main phase, the default), `main1` or `main2`; or, since harness 0.4.7, a step of the seat's
  own combat, with an empty stack: `attack`, after its attackers are declared, or `blocks`, after the blocks are
  declared. A play or activate rule with a combat phase is read only there and goes before Forge's own choice at that
  moment (an instant, a creature with flash, an activated ability); the main-phase rules are not read in combat. It is
  how a deck says "after blocks" (`{"activate": ["Kaust, Eyes of the Glade"], "own": "face_down", "phase": "blocks"}`).
  Counter: `cast_combat`.
- `own` (play, activate; harness 0.4.7): `"own": "face_down"` makes the spell's or ability's one target a face-down
  creature of the seat's own, chosen by the harness among those it can legally target: one that is a creature card face
  up (a manifested land is not turned up in combat), an unblocked attacker before any other once blocks are declared (it
  deals its damage to a player as what it really is), then the greater power face up. `"own": "attacker"` (0.4.8)
  makes it an attacking creature of the seat's own: an unblocked one first once blocks are declared, then the greater
  power; the rule's `x` applies as it does with `target`, so a mana sink is written
  `{"activate": ["Kessig Wolf Run"], "own": "attacker", "x": "max", "x_min": 3, "phase": "blocks",
  "when": ["unblocked >= 1"]}`: after blocks, all the mana that is left into an attacker nobody blocked. Forge's
  count of the mana left can run far ahead of what its payment then finds (two Regal Behemoths and the monarchy: a
  count of 28 where the untapped lands paid for four), and a payment that fails loses the play; so for a rule with
  `own`, when that count is more than three above one mana a source, X is what one mana a source pays for
  (`cast_x_capped`). `"own": "minus_counter"` (0.4.9) makes it a permanent of the seat's own that has -1/-1 counters
  and no other kind of counter, a creature before anything else, the better creature first. A rule takes
  `target`, `aim`, `target_player` or `own`, one of them, with one exception since 0.4.9: a rule with `own` and `aim`
  is for a spell or ability with two targets, in that order. Its first part that takes a target gets the seat's own
  permanent, its second an opponent's, chosen as any aim is: `{"activate": ["Nesting Grounds"], "ability": "Move a
  counter", "own": "minus_counter", "aim": "creature", "aim_toughness": 1}` moves a -1/-1 counter from a creature of
  ours onto a creature it kills. Nothing is cast unless both are found. `own_except` (0.4.10) lists permanents of the
  seat's own that an `own` selector never takes: a deck that puts counters on some of its own creatures on purpose
  (Tree of Perdition, whose toughness an opponent's life is exchanged with; Carnifex Demon and Grim Poppet, whose
  counters are what their abilities spend) does not want them moved off, and a selector cannot know that. Counters:
  `cast_own`, `cast_own_unblocked`,
  `cast_own_blocked`, `cast_own_attacking` (before blocks), `cast_own_none` (no such creature: the rule did not fire).
- `keep` (harness 0.4.8): `{"keep": "mana", "when": [...]}` is a rule of its own kind. In the seat's first main phase,
  while every condition holds, the rules below it are not read and the seat goes to combat with its mana unspent; they
  are read in the second main phase. It is how a playbook pays for a play it has written for its combat: the main-phase
  rules otherwise spend the mana before the attack. `{"keep": "mana", "when": ["hand:mutation >= 1", "attackers >= 3",
  "mana >= 7"]}` above `{"play": ["Biomass Mutation"], "x": "max", "x_min": 4, "phase": "blocks",
  "when": ["unblocked >= 2"]}`. It takes only `when`. Counter: `cast_keep`.
- Other players' turns (harness 0.4.12): `"phase": "defend"` and `"phase": "end"` on a `play` or `activate` rule, the
  aim `"attacker"`, and the rule kind `reserve`. They are how a seat keeps an instant for the moment it is worth most
  instead of casting it in its own main phase, which is where every other rule acts.
  `"phase": "defend"`: the rule is read when another player has declared attackers, at least one creature attacks the
  seat itself (not a planeswalker of its), the stack is empty and the seat has priority, so before blocks.
  `"phase": "end"`: the rule is read in the end step of the turn after which the seat's own turn comes, with an empty
  stack: the last moment a card kept through the table's turns can be used before the seat untaps.
  `"aim": "attacker"` (on a `defend` rule): the spell's one target is a creature attacking the seat, chosen by the
  harness: a legal target (not an indestructible one for a spell that destroys; `aim_toughness` as for any aim), and
  the one that leaves the least damage once it is gone and the seat blocks as well as it can (the arithmetic of
  `block.survive`: a trampler or a creature one blocker may not block counts as unstoppable, a commander's
  twenty-first damage counts as the end). When the attack as it stands ends the seat's game, only an attacker whose
  removal changes that is taken; when none does the rule does not fire, and the card is not spent on a lost game.
  When the attack does not end its game, the attacker has to take at least `aim_min` damage away with it (at least
  1). The conditions `attacked` (creatures attacking the seat), `incoming` (their damage through its best blocks) and
  `lethal` (1 when that ends its game) are for these rules; all three are 0 outside another player's combat.
  `{"reserve": [cards], "when": [...]}` is a rule of its own kind: on the seat's own turn, while every condition
  holds and one of the cards is in hand, the mana that card costs is kept untapped through the turn (Forge's own
  bookkeeping of held mana sources, `AiController.reserveManaSources`: neither a rule's cast nor Forge's own choice
  pays with a held source), and given back when the seat reaches one of the two moments above, when a rule of its own
  turn casts the card after all, or when the card leaves the hand. Without it a `defend` or `end` rule casts only with
  what the seat's own turn happened to leave untapped. A reserve rule may carry an `aim` (with `aim_at`, `aim_min`,
  `aim_toughness`, as on a play rule): the mana is then kept only while the card has a target of that aim on the table
  now, so that nothing is kept for a card with nothing to hit.
  A card named by a `defend` or `end` play rule, or by a `reserve` rule, has to be named by a `hold` rule as well
  (checked when the file is read): Forge's AI casts an instant on the seat's own turn if it may, and the card would
  be gone. A `play` rule for the main phase may still name it, for the target that cannot wait.
  `{"hold": ["Terminate"]}`, `{"reserve": ["Terminate"], "aim": "permanent", "aim_min": 3, "when": ["lands >= 3"]}`,
  `{"play": ["Terminate"], "phase": "defend", "aim": "attacker", "when": ["lethal == 1"]}`,
  `{"play": ["Terminate"], "phase": "defend", "aim": "attacker", "aim_min": 6}`,
  `{"play": ["Terminate"], "phase": "end", "aim": "permanent", "aim_min": 3}`.
  Counters: `react_defend_seen`, `react_end_seen` (turns on which the seat reached the moment), `cast_react`,
  `cast_react_defend`, `cast_react_end` (plays a rule made there), `cast_aim_attacker`, `react_lethal_answered` and
  `react_damage_answered` (a defend rule fired at an attack that would, or would not, have ended the seat's game),
  `react_damage_taken_away` (the damage those casts took away), `react_lethal_seen` and `react_lethal_hopeless`
  (turns on which a defend rule with a card to cast met a lethal attack; those on which no one removal changed it),
  `reserve_kept`, `reserve_short` and `reserve_no_target` (turns on which the mana was kept; on which it was not there
  to keep; on which the card had nothing to hit).
- `before_land` (play, activate): `true` tries the rule before the turn's land is played as well, while a land can still be played. The rules otherwise run after the land drop, since they all want the mana; a landfall deck wants its payoffs down first so the land triggers them (`{"play": ["Tatyova, Benthic Druid", "Scute Swarm"], "before_land": true}`). Counter: `cast_before_land`.
- `x`, `x_min` (play, activate): for a spell with X in its cost that is not aimed by Forge (no targets, or the rule's own `target`). `"x": "max"` pays all the mana the rest of the cost leaves, `"x": 6` at most six, and the rule does not cast below `x_min` (default 1): `{"play": ["Hydroid Krasis"], "x": "max", "x_min": 4}`. Without `x` an X spell is cast only when Forge's own logic would cast it, with the X Forge picks; a rule that aims an X spell with `target` and names no `x` does not cast it. Since harness 0.3.4 `x` can also be a metric, and X is then that number: `"x": "opp_toughness"` sizes a wipe to the largest creature an opponent has. And an X that is paid in life (Toxic Deluge: "pay X life, all creatures get -X/-X") is the rule's to name the same way; the mana cap does not apply to it, `x_keep_life` (default 10) does: the rule never pays the seat below that much life. `{"play": ["Toxic Deluge"], "x": "opp_toughness", "x_min": 3, "x_keep_life": 12, "when": ["opp_creatures >= 6", "opp_power > power"]}`. A spell that divides its X among targets (Fire Covenant) takes `divide`, above.
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
| `table_creatures`, `table_power` | the creatures and the total power all the opponents have together (harness 0.4.14): two opponents with five creatures each are ten to a wipe, where `opp_creatures` says five |
| `threat` | the most damage one opponent could attack us with next turn |
| `opp_toughness` | the largest toughness among the opponents' creatures (also as an `x`) |
| `attacking`, `unblocked` | our creatures in the current combat; those nobody blocked, once blocks are declared (both 0 outside our combat; for rules with a combat `phase`, harness 0.4.8) |
| `attacked`, `incoming`, `lethal` | another player's attack on us: the creatures attacking us, their damage through our best blocks, and 1 when that ends our game (all 0 outside another player's combat; for rules with `"phase": "defend"`, harness 0.4.12) |
| `hand:<group>` | cards in hand from a named list: `"cast": {"groups": {"zada_spells": ["Expedite", ...]}, "rules": [...]}`, then `"hand:zada_spells >= 1"` |

A rule that names a card that is not in the deck, an unknown metric or a malformed condition stops the harness before
the first game (exit 2), so a typo cannot switch a rule off quietly. `max_per_turn` caps the plays the rules make in
one turn (default 60) as a guard against a free loop. A cast that does not go through (Forge could not pay for it after
all) is not tried again that turn.

`"keep_life": 4` on the `cast` block (harness 0.4.15; `"cast": {"keep_life": 4, "rules": [...]}`): the seat casts no
spell, and uses no ability, whose own script would take it under that much life. Forge's AI casts Reanimate ("you
lose life equal to its mana value") for a creature that costs more life than the seat has, pays the seat's last life
for an alternative cost, and a `play` rule with nothing to aim does not ask Forge's opinion at all: at the owner's
table a seat was out of the game by the price of its own spell in one game of thirty (DESIGN §45; `runner/mistakes.py`
counts it). What the guard reads is what the script says when the spell is cast: life paid as a cost (not an X, which
`x_keep_life` is for), and the parts of the effect that make "you" lose life or deal damage to "you" by an amount
that can be calculated then; where that amount is the mana value of the card the spell is aimed at, it is read off
the target as Forge has set it. A rule's play that costs too much is not made (`cast_life_kept`), and Forge's own
choice that costs too much is taken out of its candidates the way a held play is and Forge is asked again
(`cast_life_vetoes`; `cast_life_stuck` when Forge would have nothing else and the seat passes). What is decided as
the spell resolves is not seen: a charm's mode, the number of counters Eventide's Shadow removes (`take`), the
colours of mana spent on a converge spell, a "target player" that turns out to be the caster. Those want a rule of
their own with a condition on `life`. Without the key nothing changes.

`"bounce_lands": true` on the `cast` block (harness 0.4.16): for a deck that holds lands which return a land to hand
as they enter (Gruul Turf, Selesnya Sanctuary and the rest of that cycle, Guildless Commons). Forge's scripts tell its
AI to play such a land only while it controls a basic land, so a seat whose lands are all nonbasic keeps it in hand
turn after turn: at two tables every turn at four lands or fewer on which a seat held a land and played none was
that, and Deadly Disguise sat on three lands with three such lands in hand for a whole game (DESIGN §46;
`runner/mistakes.py` counts it under LAND DROPS). And when the AI does play one, it plays it first thing in its turn
and returns an untapped land, which costs the turn that land's mana. With the key three things change, and nothing
else about the seat's lands: such a land is not played before the rules have spent the turn's mana (Forge's choice of
it as the land drop is taken after the rules have nothing left to do, not before); at the end of the second main
phase, when the seat may still play a land, holds one of these and Forge's AI is about to pass, the land is played
(it needs one other land on the battlefield to return); and the land it returns is the rule's choice: a tapped one
before an untapped one, a basic before a nonbasic, another land of this kind last, never the one that has just
entered while there is another. Counters: `cast_bounce_land` (plays Forge's AI would not have made),
`cast_bounce_land_later` (turns on which Forge's own play of such a land was put behind the rules),
`cast_bounce_land_returned`, `cast_bounce_land_returned_tapped`, `cast_bounce_land_returned_untapped`. A seat with no
land on the battlefield and only such lands in hand is not helped: that hand should not have been kept.

The harness records the playbook per seat in `run.json` (`decks[].playbook`, the `cast` object as written) and the
policy's counters per game (`games[].playbook_stats`): `attack_decisions`, `attack_policy`, `attack_fallback`,
`attack_spread`, `attackers_declared`, `attackers_reserved`, `mulligan_decisions`, `mulligans_taken`, and for the
cast rules `cast_decisions` (times the rules were read), `cast_policy` (times one fired), `cast_rule_<n>` (per rule, by
its position in the file), `cast_hold_vetoes` (a Forge choice that a hold turned down), `cast_hold_stuck` (a hold that
could only be kept by passing), `cast_failed`, `cast_forge_declined`, `cast_turn_limit`, `cast_errors`, and for a
`forge` rule `cast_forge_unnamed` (times Forge took a play at it), `cast_forge_unnamed_main2` (those of them in the
second main phase), `cast_forge_wait` (times a rule with `"wait": "main2"` made the rules below it wait),
`cast_forge_wait_unused` (waits after which Forge did not cast the card it had kept, though it could still pay for
it: the rules do not wait for that card again) and `cast_forge_stuck` (Forge kept choosing a named play and the rules
below decided), and for an aimed rule `cast_aim`, `cast_aim_most_dangerous`, `cast_aim_next` and `cast_aim_none`
(above).
`FORGE_JAVA_OPTS=-Dvibefish.trace=true` prints one line per rule decision to the shard log.

### `triggers`: the seat's answer to "you may"

Forge's AI turns down most optional triggers whose price it cannot value: stock Hail, Caesar pays for its commander's
attack trigger (sacrifice another creature for two attacking Soldiers and a burn equal to its tokens) on fewer than a
fifth of its attacks. A trigger rule answers for the deck:

```
"triggers": [
  {"accept":  ["Caesar, Legion's Emperor"], "when": ["tokens >= 1"]},
  {"decline": ["Some Card"], "ability": "a piece of the trigger's text", "when": ["life <= 10"]}
]
```

When Forge asks whether to use an optional trigger of a listed card of ours, the first rule that names the card and
whose `when` conditions all hold answers (`accept`: yes, `decline`: no); with none, Forge's AI answers as before.
`ability` narrows a rule to the trigger whose text contains it. The conditions are the cast rules' (a `hand:<group>`
condition counts a group from `cast.groups`). What an accepted trigger costs and does is still chosen by Forge: it
sacrifices its lowest-rated creature and picks the modes and targets, so the conditions are where the file says the
price is right (`tokens >= 1`: there is a token to give up). Mandatory triggers are never asked about. Counters:
`trigger_decisions`, `trigger_accepted`, `trigger_declined`, `trigger_rule_<n>`, `trigger_errors`; the rules are
recorded in `run.json` under `decks[].playbook.triggers`.

`"effect": true` on a trigger rule (harness 0.4.15) is for a "you may" that Forge asks while an effect of the card
resolves, and not as an optional trigger. Cemetery Tampering and Crawling Sensation ("at the beginning of your upkeep,
you may mill three cards") are scripted that way (`Optional$ True` on the effect), so an ordinary trigger rule never
sees the question, and Forge's AI says yes with three cards left in the library: Death Toll was out of cards on its
own turn in 12 of 400 league games (DESIGN §45). `{"decline": ["Crawling Sensation", "Cemetery Tampering"],
"effect": true, "when": ["library <= 15"]}` answers it. A rule with `effect` answers nothing else, and a rule without
it never answers an effect's question, so every rule written before 0.4.15 is read as before; `per_turn` is not for
these rules. Counters: `trigger_effect_accepted`, `trigger_effect_declined`, and the rule's `trigger_rule_<n>`.

An `accept` without a condition says yes every time, and a trigger that feeds itself then has no end. Miracle Worker's
version 3 accepted Ondu Spiritdancer's copy that way; with Secret Arcade unlocked a Spiritdancer that enters copies
itself, the copy does the same, and 22 of the 25 games without a winner in 2,000 were that chain, stopped by Forge's
clock (DESIGN.md §35). Give such a rule a count and a `decline` after it:

```
{"accept":  ["Ondu Spiritdancer"], "when": ["type:Kor <= 20"]},
{"decline": ["Ondu Spiritdancer"]}
```

A count of permanents does not stop a chain whose pieces die as they are made (Blight Curse's Blowfly Infestation with
Flourishing Defenses: a -1/-1 counter kills a 1/1 token, the death puts a counter on the next, the counter makes a new
token). For that an `accept` rule takes `"per_turn": N` (harness 0.4.11): it says yes at most N times in one turn and
then stops answering, so that the next rule that names the card does:

```
{"accept":  ["Flourishing Defenses"], "per_turn": 30},
{"decline": ["Flourishing Defenses"]}
```

Without a rule after it Forge's AI answers once the limit is reached, which may be yes again. The limit is counted for
each rule by itself and starts anew with every turn of the game, anybody's. Counter: `trigger_limit` (the times a rule
was passed over because it had reached its limit). A chain whose trigger is not optional cannot be capped by a rule
(Hapatra's Snake with Blowfly Infestation); only its target can end it, which the rules do not choose yet.

### `targets`: where the seat's removal triggers aim

A spell can be aimed by its rule (`aim`, above); most of the removal in these precons is not a spell but a creature's
enters trigger, and its target is chosen by Forge's AI when the trigger goes on the stack. Counted at the owner's
table (`docs/agents/aimed_at.py`, `DESIGN.md` §34): of 11,053 triggered abilities aimed at an opponent's permanent in
2,000 games, 49% went at the opponent that looks most dangerous and 58% at the widest board, where a random opponent
is 38%; about 4,000 of them destroy, exile or bounce one permanent.

```
"targets": {"triggers": "danger", "min": 4, "margin": 5}
```

With `"triggers": "danger"` (harness 0.4.2) a triggered ability of the seat that removes one permanent an opponent
controls (it destroys it, exiles it, or returns it to hand or library; exactly one target) is aimed by the judgement
of danger the cast rules use (`cast.danger`: life plus twice the nonland permanents by default). Forge's AI chooses
first. When its target belongs to the most dangerous opponent, or to one that looks nearly as dangerous (within
`margin`, default 5: a close table is left to Forge, whose pick of the permanent is as good as any), nothing changes.
Otherwise the opponents that look more dangerous by that margin are asked in turn, the most dangerous first, for a
permanent of the same kind (a creature for a creature, a noncreature for a
noncreature) that the ability can target, that is not indestructible if it is to be destroyed, and that is worth at
least as much as Forge's choice or at least `min` (mana value, or power if higher; default 4): the best of the first
opponent that has one (`ComputerUtilCard.getBestAI`) is targeted instead. If none has one, Forge's target stands.
Damage, -X/-X, fights, steals, taps and anything with several targets are left alone: what they should hit depends
on more than who is ahead. The hook is Forge's public `orderAndPlaySimultaneousSa`: the seat's own plain triggers are
prepared by Forge's AI (`AiController.doTrigger`) and put on the stack (`ComputerUtil.playStack`) exactly as Forge
does, with the aim in between; charms, copies and triggers another player aims go through Forge's method untouched.
Counters: `trigger_aim_seen` (a removal trigger aimed at an opponent's permanent), `trigger_aim_already` (at the most
dangerous opponent already), `trigger_aim_moved`, `trigger_aim_kept` (nothing worth it on a more dangerous
opponent's side), `trigger_aim_errors`; the block is recorded in `run.json` under `decks[].playbook.targets`.

`"counters": {"cards": ["Blowfly Infestation"], "own_per_turn": 5}` (harness 0.4.14; with or without `triggers`) is
for a named permanent of the seat whose trigger puts a -1/-1 counter on one target creature. Forge's AI may aim such
a trigger at a creature of the seat's own that the counter kills, and where that death triggers the permanent again
the chain has no end: Blowfly Infestation ("Whenever a creature dies, if it had a -1/-1 counter on it, put a -1/-1
counter on target creature") with Hapatra, whose Snake for every counter is the next creature to die. Forge then
closes the game as a draw. The rule lets the counter go on a dying creature of the seat's own `own_per_turn` times a
turn (default 0; a deck that draws a card for each such counter wants a few) and after that puts it on a creature an
opponent controls: the most dangerous opponent that has one the trigger can target, and there the creature with the
lowest toughness, the largest among equals. When no opponent's creature can be targeted it goes on a creature of the
seat's own that survives it, the one with the highest toughness, which ends the chain as well. A target Forge chose
that is an opponent's creature, or a creature of the seat's own that survives the counter, is left alone, and so is
every trigger of a card the list does not name. Counters: `trigger_counter_own_seen` (Forge aimed the counter at a
dying creature of the seat's own), `trigger_counter_own` (allowed), `trigger_counter_moved` (put on an opponent's
creature instead), `trigger_counter_ended` (put on a creature of its own that survives), `trigger_counter_stuck`
(nothing else to put it on).

`"types": {"cards": ["Winter, Cynical Opportunist"], "leave": ["Deadbridge Chant"]}` (harness 0.4.17; with or without
the other keys) is for a named permanent of the seat whose trigger exiles "any number of cards from your graveyard
with four or more card types among them" and puts a permanent card from among them onto the battlefield. Forge asks
for the cards one at a time and its AI hands over the whole graveyard: 550 of the 558 uses of Winter's trigger in
200 league games took every card or all but one, which ends delirium and empties what the rest of Death Toll counts
and brings back (DESIGN §47). The rule answers instead. It picks the permanent to bring back (the creature Forge's
own rating puts highest, or another permanent by its mana value; never a land, and never a card `leave` names, which
is for a permanent whose arrival the deck cannot afford, like a ten-card mill); then the fewest other cards that make
the number of types with it, the ones the graveyard misses least: spent instants and sorceries and lands before
permanents, and a type the graveyard holds twice before one it holds once. Nothing is exiled when no permanent in the
graveyard is worth it. Every other choice of a card to move stays Forge's. Counters: `trigger_types_seen` (times the
question was asked), `trigger_types_exiled` (cards handed over), `trigger_types_back` (permanents brought back by the
rule's choice), `trigger_types_declined` (nothing worth bringing back).

### `block`: not dying to an attack the seat could have blocked

Blocks are Forge's AI's, and under a lethal attack they are nearly always sound: of 4,146 deaths in combat at the
owner's table, at most 135 were to an attack the seat's own creatures could have blocked down to less than its life
(`runner/mistakes.py`, `DESIGN.md` §34), most of them with no block made at all against one or two attackers.

```
"block": {"survive": true}
```

With `"survive": true` (harness 0.4.3) Forge's AI declares the seat's blocks first. When they leave at least the
seat's life in damage unblocked (an unblocked attacker's damage, twice with double strike), the seat looks for blocks
that would not: one blocker an attacker, by Forge's own `CombatUtil.canBlock(attacker, blocker)`; an attacker that
tramples or that one creature alone may not block is not counted as stopped. Blocks are added to Forge's own, the
least valuable creatures that are not blocking yet (`ComputerUtilCard.evaluateCreature`) in front of the heaviest
unblocked attackers, and only as many as it takes for the unblocked damage to fall under the seat's life. If adding
is not enough and another set of blocks would be, the seat's blocks are declared anew that way. Blocks Forge's rules
refuse (`CombatUtil.validateBlocks`) are taken back and Forge's own stand. Nothing else about blocking changes: which
attacker to kill, when to trade, when to take the damage are Forge's. Counters: `block_lethal_seen` (Forge's blocks
left the seat dead), `block_survive` (blocks were added and it is not), `block_survive_added` (how many),
`block_survive_reblocked` (declared anew), `block_lethal_hopeless` (no such blocks exist), `block_survive_invalid`,
`block_survive_errors`; the block is recorded in `run.json` under `decks[].playbook.block`.

### Writing one

The loop is goldfish first, then duels, then tables (DESIGN.md §21, §22):

```
runner/playbook.py draft --deck goblin-storm --runtime forge/runtime-snapshot    # a first set of cast rules from Forge's card scripts -> variants/goblin-storm-draft.json
runner/playbook.py adapt --deck blight-curse --deck-file "/abs/My List.dck"         # the deck's playbook cut to a list of your own that started as this precon -> "/abs/My List.playbook.json"
runner/goldfish.sh "$PRECONS/Goblin Storm [SLD] [2026].dck" -n 100 -s 7000 -i gs-stock                                   # stock AI
runner/goldfish.sh "$PRECONS/Goblin Storm [SLD] [2026].dck" -n 100 -s 7000 -i gs-playbook -P playbook/precons/goblin-storm.json
runner/hands.py compare results/gs-stock results/gs-playbook      # kill turn by run, paired difference on the same seeds
runner/hands.py held results/gs-stock                             # the cards the seat sat on with the mana for them unspent
runner/hands.py game results/gs-playbook/shard-1/games/game-005.events.jsonl    # one game turn by turn: read the slow ones
runner/hands.py abilities results/gs-stock --runtime forge/runtime-snapshot         # activated abilities the seat had in play and how often it used them
runner/ab.py play --deck goblin-storm --arms stock,playbook --opponents 1 --games 60 ...   # duels: blockers, removal and the race, ten seconds a game
runner/ab.py play --deck goblin-storm --arms stock,playbook ...   # then the same deck at real tables (three stock opponents: the exam until 2026-11-11)
runner/ab.py play --deck goblin-storm --arms stock,playbook --pool runner/leagues/bots-v1.json --opponent-playbooks ...   # the exam now: the opponents are the bot decks, each under its shipped playbook
```

`runner/playbook.py draft` sorts the deck's cards by what their scripts say they are (mana, the commander, team pumps,
engines, creatures, card draw) and writes the cast rules every playbook here began with, as a variant file; it lists
what it left to Forge and why, the cards Forge's AI will never cast by itself, and the deck's optional triggers.
`runner/playbook.py roles --deck ID` prints the sorting alone. A draft is a starting point: the deck's own lines (what
its commander wants, what to hold for which moment, which trigger to take) are written by reading its slow games.
With `FORGE_JAVA_OPTS=-Dvibefish.trace=true` the shard log also names every optional trigger Forge's AI turned down
on the playbook seat, which is where a trigger rule comes from.

Goldfish measures whether the seat runs its own deck (what it casts, in what order, how fast it kills three opponents
that do nothing); it says nothing about blocking, removal or being attacked, which is what the tables are for.
`runner/ab.py` has `playbook` and `playbookdata` arms.

## `variants/`

Candidate playbooks that are not the deck's shipped one: `variants/<deck>-<name>.json` holds a `playbook` object (and
says what it is a variant of). `runner/ab.py --data playbook/variants/<deck>-<name>.json` plays one locally, and the
`ab-run` workflow takes `deck@name` in its deck list, so several candidates can be measured side by side on the same
tables before one of them replaces the playbook in `precons/`. A variant carries no deck data: the data arms need the
deck's own file, unless the variant brings a `curated` block of its own (key cards for the tutors, say), which the `playbookdata` arm then reads from the same file. `<deck>-draft.json` is the output of `runner/playbook.py draft`.

A candidate needs only its own arm when the tables have been played before: run it with `--arms playbook` on the seed
of an earlier run, and `runner/ab.py join` lines its games up with that run's stock arm table by table
(`runner/ab.py join --out joined.json --against v2 stock=run5.json:stock v2=run5.json:playbook pressure=run7.json`).

A file chosen among several on the same tables owes a confirming run: stock against it alone, on a seed of its own
ten or more from every seed the deck has been played on (nearby seeds draw the same opponents; `runner/ab.py`, Seeds).
`variants/README.md` lists every candidate here and what came of it; keep it current, so that no dead end is
measured twice.
