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
