# Forge notes

Forge behaviour seen in Vibefish runs, with how to reproduce it. Internal reference only: Vibefish does not file Forge issues (DESIGN.md §8). Vibefish pins
`forge/VERSION`; the Monte Carlo items below are from the daily snapshot (`FORGE_CHANNEL=snapshot`),
i.e. the Flat Monte Carlo work on master that is not in 2.0.15.

Reproduce any game: `runner/make-arm-profiles.sh forge/runtime-snapshot`, then

```bash
FORGE_RUNTIME=$PWD/forge/runtime-snapshot controller/vibefish-sim.sh play --out results/repro \
  --deck-dir "$PWD/forge/runtime-snapshot/res/quest/commanderprecons" \
  --deck "mutant-menace=Mutant Menace [PIP] [2024].dck" --deck "blight-curse=Blight Curse [ECC] [2026].dck" \
  --deck "veloci-ramp-tor=Veloci-Ramp-Tor [LCC] [2023].dck" --deck "squirreled-away=Squirreled Away [BLC] [2024].dck" \
  --games 1 --seed <GAME_SEED minus 1> --clock 1800 --turn-cap 120 --mc on \
  --profile Vibefish-MC --profile Vibefish-MC --profile Vibefish-Heuristic --profile Vibefish-Heuristic
```

`--seed S` plays game 1 with game seed S+1. In the A/B runs the profile assignment rotated by one seat per game;
the seat profiles for a given game are in that run's `run.json` (`games[].profiles`).

## Flat Monte Carlo rollout failures (snapshot 2026-11-08, 2.0.16-SNAPSHOT-11.08)

Forge prints `Flat Monte Carlo rollout failed, using the heuristic choice instead: ...` and plays the heuristic
choice instead. Seen in 4-player Commander games with the pod precons:

| Message | Where seen |
|---|---|
| `java.lang.RuntimeException: Couldn't map The Monarch (756)/...` | ab1, game seed 20461111 (pass `--seed 20461110`), 5 times in that game: the Monarch effect card in the command zone does not survive the game copy |
| `java.lang.RuntimeException: Couldn't map Auntie Ool, Cursewretch (201)/...` | ab1, game seed 20361111 (pass `--seed 20361110`), 5 times in that game: a commander that had left and returned |
| `java.lang.NullPointerException: Cannot invoke "forge.game.card.Card.hasRemembered()" because "origCard" is null` | smoke runs, game seeds 778 and 20261110 (`--mc on` and `--mc max`), 5 times each |

The ab1 games used `--rotate-profiles`; both listed games are game 3 of their shard, where the profile order was
`Vibefish-Heuristic, Vibefish-Heuristic, Vibefish-MC, Vibefish-MC`. At `--mc max` one game also reported `failures=16 unsimulatableCards=11` in
`FLATMC-STATS`; the harness keeps that block per game in `run.json` as `mc_stats`.

## Observations

- With the Default profile budgets (450 ms per decision, 2 s per turn) a four-player precon board affords one or
  two rollouts per decision (about 650 ms each); Monte Carlo overrode the heuristic in about 4% of decisions, and
  7 of 23 decisions in one game were abandoned as too slow. At `--mc max` overrides rose to 35% of decisions and
  games took about three times as long. Commander may want its own budget defaults.
- Forge's AI mulligans far less than people do in Commander (about 20% of hands against Playgroup.gg's 36%) and
  its games run about three rounds longer than human games; see the calibration scorecard on the dashboard.
- Two Forge processes starting at the same moment in a runtime Forge has never booted before race on creating the
  profile directories: one of them dies in `FModel.initialize` with `java.lang.RuntimeException: cannot create profile
  directory: .../profile/decks/planar/` (seen in every shard of the first league run in Actions, where the runtime is
  fresh). Harmless once the directories exist; `runner/league.py` boots the first game of a shard alone for this reason.
- Same seed, different machine, different game in about one game in seven: in the first league run, shard 1 played in
  Actions and in the Claude Code container (same build, same seeds) agreed on 95 of 110 games; the 15 that diverged
  were the slow ones (median 200 s against 62 s), where the AI's per-decision timeouts fire (140 `TimeoutException`
  traces in the shard log). The seed fixes the shuffles, not the AI's time budgets.
- Two of 2,200 league games ended in an engine error (harness reason `Exception`, recorded as draws), snapshot
  2026-11-08, Monte Carlo off: game seed 20262124 (Jump Scare! / Grand Larceny / Keen Engineering / Exit from Exile,
  turn 26) died with `NullPointerException ... Card.getState(CardStateName) is null` in
  `CopyPermanentEffect.getProtoType` while a copy effect resolved; game seed 20262439 (Deadly Disguise / Call for
  Backup / Silverquill Influence / Wretched Ranks, turn 40, 190 s in) ran out of the 4 GB heap in
  `Game.copyLastState` → `CardCopyService.getLKICopy` (last-known-information copies of a large board).
- `AI:RemoveDeck:All` is a play-time filter, not only a deck-building hint: with Flat Monte Carlo off,
  `AiController.getSpellAbilityToPlay` removes every spell of a flagged card from its candidates before it chooses
  (read from the bytecode of snapshot 2026-11-10 and of 2.0.15: the `removeIf` predicate calls
  `ComputerUtilCard.isCardRemAIDeck` and drops the ability unless the Monte Carlo layer is active). So a stock seat
  never casts those cards: in the league Goblin Storm never cast Goblin Bombardment, Faithless Looting or Past in
  Flames in 96 games, and 86 of the 91 decks have at least one card they drew and never once cast. A playbook `play`
  rule casts them (DESIGN.md §21).
- Forge drops abilities flagged `skip` from its candidates for one decision, records which ones it dropped and clears
  their flags at the start of the next decision (`AiController.skipped`). A flag set from outside is therefore
  sometimes cleared before it is read; `PlaybookController.forgeChoice` works around it with one unflagged call when a
  held play gets through (public methods only).
- The stock AI finds Storm-Kiln Artist + Haze of Rage (buyback), the one infinite combo in Goblin Storm, and then does
  not stop: snapshot 2026-11-10, goldfish `runner/goldfish.sh "Goblin Storm [SLD] [2026].dck" -s 7000`, game seed 7076
  recast Haze of Rage 39 times and more in one main phase (819 storm copies and as many Treasures by then) and the
  game took 486 s where the others take 4 to 9; every recast is slower than the last. It ended on its own, well
  inside the 900 s clock, but the same loop at a table would be a candidate for the league's clock draws. Four more
  in `-s 9000` (game seeds 9001, 9021, 9049 and 9086: 561, 551, 330 and 247 s; 360 casts of Haze of Rage in that
  block of a hundred stock games).

## Seen while building the per-deck bots (snapshot 2026-11-10, 2026-11-11)

All on the heuristic AI (Monte Carlo off). The trace that names declined triggers is
`FORGE_JAVA_OPTS=-Dvibefish.trace=true` on a seat with a playbook; the unused abilities come from
`runner/hands.py abilities` (DESIGN.md §22).

- Optional triggers with a price are mostly declined. `WrappedAbility.resolve` asks `PlayerControllerAi.confirmTrigger`,
  which asks the trigger's own logic whether it would play the effect as a spell (`ImmediateTriggerAi` and friends),
  and the answer is usually no. Caesar, Legion's Emperor ("whenever you attack, you may sacrifice another creature;
  when you do, choose two"): paid on 47 of 264 attacks in forty stock goldfish games of Hail, Caesar. Seer's Sundial
  (landfall, pay {2}: draw): declined 51 times in forty games of Tricky Terrain. Mentor of the Meek (pay {1}: draw):
  declined 7 times in ten games of Token Triumph. Science!'s pay-energy triggers (Assaultron Dominator, Sentry Bot,
  Robobrain War Mind, T-45 Power Armor, The Motherlode): declined 233 times in forty games, the Dominator's 112.
  A playbook's `triggers` rule answers instead.
- Free tap abilities are left unused for whole games: Steel Overseer (0 uses in 19 turns in play), Arcade Gannon
  (0 in 28), Brotherhood Scribe (0 in 13) in Science!; Crystalline Crawler, Coretapper and Empowered Autogenerator
  in Counter Intelligence; Vitu-Ghazi (one use in 53 turns) and Selesnya Evangel (none in 19) in Token Triumph.
- Thespian's Stage was in play for 75 turns of forty Tricky Terrain games and Forge's AI never activated it (the
  seat had a playbook, but no rule of it named the Stage), so the deck's Dark Depths line does not happen by itself.
  Activated by a rule with Dark Depths as the target, the engine does the rest: the legend rule keeps the copy, the
  copy has no ice counters and is sacrificed, Marit Lage arrives.
- X spells with no good AI logic stay in hand with the mana for them unspent (Hydroid Krasis, Finale of Revelation,
  Nissa, Steward of Elements in Tricky Terrain); cards flagged `AI:RemoveDeck:All` are never cast at all, which
  includes most of that deck's answers (Beast Within, Curse of the Swine, Oblivion Stone, Summary Dismissal).
- A three-mana commander cast on turn six: stock Tricky Terrain holds Omo, Queen of Vesuva and three six-drops with
  seven lands in play (game seed 8001 of `runner/goldfish.sh "Tricky Terrain [M3C] [2024].dck" -s 8000`).
- A wide board can make the stock AI's decisions time out one after another, and the game crawls: Token Triumph
  against Blame Game in duels (seed 20261151, table 18) ran past 1,400 s with the stock seat inside
  `ComputerUtilCard.getBestRemovalTargetAI` -> `evaluateBoardPosition` -> `predictNextCombat` on every decision, each
  decision thread about a second old. Tricky Terrain's table games crawl too (`ab-run` #11: its last shard took three
  hours, and 27 of the deck's 800 games were draws); whether for the same reason has not been looked into.
- One cause of Tricky Terrain's crawl, seen once (2026-11-11, the four bots at one table, seed 20361181, DESIGN.md
  §22): Scute Swarm. The playbook seat went from 8 lands to 20 in one turn with the Swarm in play; 384 copies entered
  on game turn 38 and 710 more on its next turn. With more than a thousand creatures on one side the game did not
  leave that turn in ten minutes (19 decision timeouts in the log, the last inside `ComputerUtilMana.sortManaAbilities`)
  and was stopped by hand. The seat was about to win; left alone, such a game ends on the clock and counts as a draw.
- Stock Tricky Terrain fails to kill three do-nothing opponents in seven of forty goldfish games
  (`runner/goldfish.sh "Tricky Terrain [M3C] [2024].dck" -s 8000`: six stop at the turn cap of twenty rounds, one on
  the 900 s clock). Why has not been looked into.

- **God-Eternal Bontu (seen 2026-11-12, snapshot 2026-11-10, Wretched Ranks goldfish):** when the card is cast, Forge's AI answers its enters trigger ("sacrifice any number of other permanents, then draw that many cards") by sacrificing every other permanent it has, lands included (2 of 12 tuning games). The choice is not an optional trigger, so a playbook cannot decline it; the deck's candidate holds the card. For our own reference only.

- **A lethal attacker left unblocked with a legal blocker at hand (seen 2026-11-21, snapshot 2026-11-10, the owner's table):** in 2,000 four-player games Forge's AI declared no block, or too few, against an attack that then killed it, although blocks existed by Forge's own `CombatUtil.canBlock(attacker, blocker)` and `CombatUtil.validateBlocks` that would have kept it alive: 54 deaths by the count that leaves commander damage out, and more among the deaths by commander damage. Fifteen such tables of `ab-run` #45 were replayed from the same seed with one added step (after the AI's own blocks, the least valuable free creature is put in front of the attacker that kills): the game was the same to that block, the seat was out of the game that turn in the AI's own game on all fifteen and on none with the added block. On all fifteen the attack had a commander about to reach 21 commander damage in it (The Wise Mothman, a flyer, on twelve), sometimes with more than the seat's life in damage besides (22 at 9 life from one attacker, blocker available). Why the AI passes on the block has not been looked into (DESIGN.md §34).

- **An attack is weighed against one opponent (read from the source and counted 2026-11-21, snapshot 2026-11-10, the owner's table):** `AiAttackController` picks one defending opponent (`choosePreferredDefenderPlayer`: the value of the opponent's board, plus the square of what its life is under 20 by, one of the top scores drawn at random) and decides which creatures attack against that opponent's blockers alone. Two things follow in four-player games. An opponent who cannot block is not attacked unless it is the one chosen: in 2,000 games a seat had a creature able to attack an opponent with no creature that could block on 19,341 turns, attacked such an opponent on 30%, attacked only an opponent with blockers on 35% and attacked nobody on 35%. And the life term draws the attack to the player nearest to dead, who is the least likely to win a four-player game: with three opponents alive 48% of the attackers go at the opponent with the most life and board together, and when none does the one attacked has the lowest life at the table three times in four. The source has a note to the same effect on the defensive side ("should also consider them as teams" in `predictNextCombatsRemainingLife`). Vibefish works on top of the declaration (a playbook's `"aim": "danger"` and `"open": true`, DESIGN.md section 34). For our own reference only.

- **An optional trigger that feeds itself is answered yes without end (seen 2026-11-21, snapshot 2026-11-10, the owner's table):** Ondu Spiritdancer ("whenever an enchantment you control enters, you may create a token that's a copy of it; do this only once each turn") with Secret Arcade unlocked ("nonland permanents you control are enchantments"). A Spiritdancer that enters sees itself enter and triggers; the copy does the same, and each new object has its own once-a-turn. Under a playbook whose trigger rule accepted that card every time the chain never ended: Forge called one such game a draw after 51 copies (every player "has accepted that the game is a draw") and let 21 others in 2,000 run to the thirty-minute clock with 270 to 1,900 copies on the battlefield, so its loop detection does not see this chain reliably. The same shape with Blowfly Infestation and Flourishing Defenses (a -1/-1 counter kills a 1/1 token, the death puts a counter on the next one, the counter makes a new token) ended in an exception after going round 3,663 times; with Hapatra's Snakes, which are not optional, in a draw. What stock Forge AI answers to the optional ones was not looked at; our rules answered. Miracle Worker's is capped by a count since its version 4 (DESIGN §35); Blight Curse's are not yet (the tokens die as they are made, so a count does not stop them).

- **A game with Quick Draw at the table ends in an exception now and then (seen 2026-11-22, snapshot 2026-11-10, the pool's tables):** in `ab-run` #58 and #59 three, five and none of the 2,400 games of the three arms ended with the harness's reason `Exception` and no long chain in the last turn, every one with Quick Draw at the table (its own tables 108 and 113 in two arms; the last lines hold Stella Lee, Wild Card, Crackling Spellslinger, Serum Visions, Faithless Looting, or nothing). Forge's own outcome lines for such a game say that every player still in it "has won because all opponents have lost", and the harness records no winner. The harness's logger reports no error of its own (`logger_errors` 0). The exception itself is in the run's console output, which the shard artifacts do not keep; a table can be replayed alone to see it (`runner/ab.py play ... --shards 200 --shard 108` from the run's commit). Not read yet. It is not a hook's doing: it happens under the playbooks without any.

- **The AI pays its last life for its own spell (counted 2026-11-23, snapshot 2026-11-10, the owner's table):** in two leagues of 504 four-player games a seat was out of the game on its own turn by the price of a spell it cast itself 33 times (`runner/mistakes.py`, ITS OWN TURN; DESIGN.md section 45). Reanimate 18 times: the AI aims it at the best creature card in a graveyard and casts it when that card's mana value is the seat's life or more (5 life for Mulldrifter, 3 life for Order of Sacred Dusk); 18 of 207 casts ended the caster's game. Eventide's Shadow 5 times ("remove any number of counters ... you draw that many cards and lose that much life": `CountersRemoveAi.chooseNumber` answers the most there is for every counter it would like gone and never asks what they cost: 84 and 85 counters). Rakdos Charm 4 times (`CharmAi` picks "each creature deals 1 damage to its controller" at 2 and 5 life with more creatures than that). Pact of the Serpent once, cast free through Etali, Primal Storm and aimed at its own seat for ten at 8 life. The other five were cards a playbook rule cast without asking Forge (Notion Rain at 2 life twice, Hoarder's Greed twice, Painful Truths once), which is ours. Counted apart, because the life is paid before the spell is on the stack: Demon of Fate's Design twice (the alternative cost "pay life equal to its mana value", paid with exactly the life the seat had: 8 life for One with the Multiverse). The harness has a guard a playbook can ask for (`cast.keep_life`, 0.4.15) for the ones a script lets it read before the spell is cast, and `take` for Eventide's Shadow.

- **A land that returns a land is held for want of a basic (counted 2026-11-23, snapshot 2026-11-10, both tables):** the scripts of Gruul Turf and the other lands of that cycle carry `SVar:NeedsToPlay:Land.Basic+YouCtrl`, so the AI plays one only while it controls a basic land. A seat whose lands are all nonbasic keeps it in hand: of 190 own turns at four lands or fewer with a land in hand and none played, in three leagues, 187 were that (`runner/mistakes.py`, LAND DROPS; DESIGN.md section 46), one seat on three lands with three such lands in hand from its fourth turn to the end of the game. When the AI does play one, it is its land drop at the start of the turn and the land it returns is untapped. A playbook can ask for the hook that plays them (`cast.bounce_lands`, harness 0.4.16).
